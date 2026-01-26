// swap_ai_bridge.c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kprobes.h>
#include <linux/mm.h>
#include <linux/mm_types.h>
#include <linux/pgtable.h>
#include <linux/sched.h>
#include <linux/ktime.h>
#include <linux/slab.h>
#include <linux/spinlock.h>
#include <linux/uaccess.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/vmalloc.h>
#include <linux/netlink.h>
#include <linux/smp.h>
#include <net/sock.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Shubham + ChatGPT");
MODULE_DESCRIPTION("Swap LIFO windows + /dev/swap_ai + netlink notifier");
MODULE_VERSION("0.3");

/* ---------- Tunables (match userspace) ---------- */
#define MAX_PROCS      15
#define SEQ_LEN        30           /* was 10; match daemon SEQ_LEN */
#define DEV_NAME       "swap_ai"
#define NL_PROTO       NETLINK_USERSOCK

/* ---------- Shared buffer layout (mmap to userspace) ---------- */
struct swap_feat {
	__u64 va;
	__u64 pfn;
	__u64 mapping;       /* pointer value (correlation only) */
	__u64 start_ns;
	__u64 latency_ns;
	__u32 folio_index;
	__u32 reserved;
};

struct swap_window {
	__u32 pid;
	__u32 count;                  /* <= SEQ_LEN */
	char  comm[16];               /* task name snapshot */
	struct swap_feat feats[SEQ_LEN]; /* LIFO: feats[count-1] is newest */
};

/* Single shared region: array of windows */
struct shared_region {
	__u32 nslots; /* == MAX_PROCS */
	__u32 seq_len;/* == SEQ_LEN  */
	struct swap_window slots[MAX_PROCS];
};

/* ---------- Globals ---------- */
static DEFINE_PER_CPU(u64, swap_start_time);
static struct kprobe kp_start;
static struct kprobe kp_done;

static struct shared_region *shm;     /* what userspace sees */
static struct shared_region *shm_kva; /* vmalloc base */
static size_t shm_size;               /* PAGE_ALIGN(sizeof(struct shared_region)) */

static dev_t devno;
static struct cdev cdev_obj;
static struct class *dev_class;

static DEFINE_SPINLOCK(win_lock);     /* protects shm updates */

/* Netlink */
static struct sock *nl_sock;
static u32 userspace_nl_pid; /* set on HELLO */

/* ---------- Utils ---------- */
static int find_or_make_slot(pid_t pid, const char *comm)
{
	int free_idx = -1;
	int i;

	for (i = 0; i < MAX_PROCS; i++) {
		if (shm->slots[i].pid == pid)
			return i;
		if (free_idx < 0 && shm->slots[i].pid == 0)
			free_idx = i;
	}

	if (free_idx >= 0) {
		struct swap_window *w = &shm->slots[free_idx];
		w->pid = pid;
		w->count = 0;
		memset(w->feats, 0, sizeof(w->feats));
		strscpy(w->comm, comm ? comm : "", sizeof(w->comm));
		return free_idx;
	}
	return -1; /* full; optional: implement LRU eviction */
}

static void lifo_push_feat(int slot, const struct swap_feat *f)
{
	struct swap_window *w = &shm->slots[slot];

	/* Shift-left when full; newest ends at tail (feats[count-1]) */
	if (w->count < SEQ_LEN) {
		w->feats[w->count++] = *f;
	} else {
		int i;
		for (i = 1; i < SEQ_LEN; i++)
			w->feats[i-1] = w->feats[i];
		w->feats[SEQ_LEN-1] = *f;
	}
}

/* ---------- Netlink ---------- */
static void nl_send_pid_update(pid_t pid)
{
	struct sk_buff *skb;
	struct nlmsghdr *nlh;
	int res;

	if (!nl_sock || !userspace_nl_pid)
		return;

	/* Ensure shm writes visible to userspace before notifying */
	smp_wmb();

	skb = nlmsg_new(sizeof(pid), GFP_ATOMIC);
	if (!skb)
		return;

	nlh = nlmsg_put(skb, 0, 0, NLMSG_DONE, sizeof(pid), 0);
	if (!nlh) {
		kfree_skb(skb);
		return;
	}

	memcpy(nlmsg_data(nlh), &pid, sizeof(pid));

	res = nlmsg_unicast(nl_sock, skb, userspace_nl_pid);
	if (res < 0)
		pr_warn("swap_ai: nlmsg_unicast failed %d\n", res);
}

static void nl_recv_cb(struct sk_buff *skb)
{
	u32 portid;

	if (!skb)
		return;

	/* More reliable than nlmsg_hdr(skb)->nlmsg_pid on newer kernels */
	portid = NETLINK_CB(skb).portid;
	userspace_nl_pid = portid;

	pr_info("swap_ai: registered userspace nl_pid=%u\n", userspace_nl_pid);
}

/* ---------- Char device (mmap read-only) ---------- */
static int sai_open(struct inode *ino, struct file *filp)  { return 0; }
static int sai_release(struct inode *ino, struct file *filp){ return 0; }

static int sai_mmap(struct file *filp, struct vm_area_struct *vma)
{
	size_t len = vma->vm_end - vma->vm_start;

	if (len != shm_size) {
		pr_warn("swap_ai: mmap size mismatch: %zu vs %zu\n", len, shm_size);
		return -EINVAL;
	}
	/* Map vmalloc’d memory into user vma */
	return remap_vmalloc_range(vma, shm_kva, 0);
}

static const struct file_operations sai_fops = {
	.owner   = THIS_MODULE,
	.open    = sai_open,
	.release = sai_release,
	.mmap    = sai_mmap,
};

/* ---------- Kprobes ---------- */
/*
 * NOTE: This uses x86-64 calling convention (first arg in %rdi).
 * We read vm_fault * from regs->di in the post handler.
 * If you need portability, consider tracepoints or kretprobe with proper arg tracing.
 */
static int start_pre(struct kprobe *p, struct pt_regs *regs)
{
	this_cpu_write(swap_start_time, ktime_get_ns());
	return 0;
}

static void finish_post(struct kprobe *p, struct pt_regs *regs, unsigned long flags)
{
#ifdef CONFIG_X86_64
	struct vm_fault *vmf = (struct vm_fault *)regs->di;
#else
	struct vm_fault *vmf = NULL; /* TODO: non-x86 port requires different arg access */
#endif
	u64 end_ns = ktime_get_ns();
	u64 start_ns = this_cpu_read(swap_start_time);
	u64 lat = end_ns - start_ns;

	if (!vmf || !current)
		return;

	/* Optional: sanity checks (pte present) */
	if (vmf->pte) {
		pte_t pte_val = READ_ONCE(*(vmf->pte));
		if (pte_present(pte_val)) {
			unsigned long pfn = pte_pfn(pte_val);
			struct page *pg = pfn_to_page(pfn);
			struct folio *folio = page_folio(pg);
			struct swap_feat feat;

			feat.va          = vmf->address;
			feat.pfn         = pfn;
			feat.mapping     = (u64)(unsigned long)(folio && folio->mapping ? folio->mapping : 0);
			feat.start_ns    = start_ns;
			feat.latency_ns  = lat;
			feat.folio_index = (u32)(folio ? folio->index : 0);
			feat.reserved    = 0;

			spin_lock(&win_lock);
			{
				int slot = find_or_make_slot(current->pid, current->comm);
				if (slot >= 0)
					lifo_push_feat(slot, &feat);
			}
			spin_unlock(&win_lock);

			nl_send_pid_update(current->pid);
		}
	}
}

/* ---------- Module init/exit ---------- */
static int __init sai_init(void)
{
	int ret;
	struct device *dev;
	struct netlink_kernel_cfg cfg = {
		.input = nl_recv_cb,
	};

	/* Region size now page-aligned to map exact length */
	shm_size = PAGE_ALIGN(sizeof(struct shared_region));
	shm_kva  = vmalloc_user(shm_size);
	if (!shm_kva)
		return -ENOMEM;

	shm = shm_kva;
	memset(shm, 0, shm_size);
	shm->nslots  = MAX_PROCS;
	shm->seq_len = SEQ_LEN;

	/* Char device */
	ret = alloc_chrdev_region(&devno, 0, 1, DEV_NAME);
	if (ret)
		goto fail_chr;

	cdev_init(&cdev_obj, &sai_fops);
	ret = cdev_add(&cdev_obj, devno, 1);
	if (ret)
		goto fail_cdev;

	dev_class = class_create(DEV_NAME);

	if (IS_ERR(dev_class)) {
		ret = PTR_ERR(dev_class);
		goto fail_class;
	}

	dev = device_create(dev_class, NULL, devno, NULL, DEV_NAME);
	if (IS_ERR(dev)) {
		ret = PTR_ERR(dev);
		goto fail_dev;
	}

	/* Netlink */
	nl_sock = netlink_kernel_create(&init_net, NL_PROTO, &cfg);
	if (!nl_sock) {
		ret = -ENOMEM;
		goto fail_nl;
	}

	/* Kprobes */
	kp_start.symbol_name = "do_swap_page";
	kp_start.pre_handler = start_pre;
	ret = register_kprobe(&kp_start);
	if (ret) {
		pr_err("swap_ai: kprobe do_swap_page failed %d\n", ret);
		goto fail_kp1;
	}

	kp_done.symbol_name = "finish_fault";
	kp_done.post_handler = finish_post;
	ret = register_kprobe(&kp_done);
	if (ret) {
		pr_err("swap_ai: kprobe finish_fault failed %d\n", ret);
		goto fail_kp2;
	}

	pr_info("swap_ai: ready. /dev/%s mmap size=%zu; MAX_PROCS=%d SEQ_LEN=%d\n",
		DEV_NAME, shm_size, MAX_PROCS, SEQ_LEN);
	return 0;

fail_kp2:
	unregister_kprobe(&kp_start);
fail_kp1:
	netlink_kernel_release(nl_sock);
fail_nl:
	device_destroy(dev_class, devno);
fail_dev:
	class_destroy(dev_class);
fail_class:
	cdev_del(&cdev_obj);
fail_cdev:
	unregister_chrdev_region(devno, 1);
fail_chr:
	vfree(shm_kva);
	return ret;
}

static void __exit sai_exit(void)
{
	unregister_kprobe(&kp_done);
	unregister_kprobe(&kp_start);

	if (nl_sock)
		netlink_kernel_release(nl_sock);

	device_destroy(dev_class, devno);
	class_destroy(dev_class);
	cdev_del(&cdev_obj);
	unregister_chrdev_region(devno, 1);

	vfree(shm_kva);
	pr_info("swap_ai: unloaded\n");
}

module_init(sai_init);
module_exit(sai_exit);
