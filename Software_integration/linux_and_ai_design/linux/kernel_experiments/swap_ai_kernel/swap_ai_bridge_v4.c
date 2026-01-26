// SPDX-License-Identifier: GPL-2.0
// swap_ai_v4.c — V4: kernel-managed window + filtering + debounce notify
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kprobes.h>
#include <linux/mm.h>
#include <linux/mm_types.h>
#include <linux/pgtable.h>
#include <linux/sched.h>
#include <linux/ktime.h>
#include <linux/spinlock.h>
#include <linux/uaccess.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/vmalloc.h>
#include <linux/netlink.h>
#include <net/sock.h>
#include <linux/jiffies.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Shubham + ChatGPT");
MODULE_DESCRIPTION("Swap AI V4: kernel-side queue+filter + /dev/swap_ai + netlink debounce");
MODULE_VERSION("0.4");

/* ---------- Tunables (module params) ---------- */
static int MAX_PROCS = 15;
module_param(MAX_PROCS, int, 0444);
MODULE_PARM_DESC(MAX_PROCS, "Max PID slots");

static int SEQ_LEN = 30;
module_param(SEQ_LEN, int, 0444);
MODULE_PARM_DESC(SEQ_LEN, "Per-PID window length");

static u64 DEBOUNCE_NS = 100000000ULL; /* 100 ms */
module_param(DEBOUNCE_NS, ull, 0644);
MODULE_PARM_DESC(DEBOUNCE_NS, "Netlink debounce (ns)");

static int TRIGGER_EVERY = 5; /* notify each N faults per PID */
module_param(TRIGGER_EVERY, int, 0644);
MODULE_PARM_DESC(TRIGGER_EVERY, "Notify every N events per PID");

/* ---------- Char dev basics ---------- */
#define DEV_NAME "swap_ai"

/* ---------- Netlink ---------- */
#define NL_PROTO NETLINK_USERSOCK

/* ---------- Feature vector (8 dims) ----------
 * [0] Va_L2           = (va >> 21) & 0x1FF  (0..511)
 * [1] Va_L1           = (va >> 12) & 0x1FF
 * [2] PFN_Top_region  = (pfn >> 20) & 0x1
 * [3] PFN_slice_4     = (pfn >> 16) & 0xF
 * [4] PFN_slice_3     = (pfn >> 12) & 0xF
 * [5] PFN_slice_2     = (pfn >>  8) & 0xF
 * [6] PFN_slice_1     = (pfn >>  4) & 0xF
 * [7] PFN_slice_0     = (pfn >>  0) & 0xF
 *
 * Aux (per-push retained for last feat):
 *  folio_index (u32), mapping_id (u32), lat_cluster (u32)
 *  start_ns (u64), latency_ns (u64) kept too (optional diagnostics)
 */
struct feat8 {
	__u16 x[8];           /* 8 small ints (0..511/15) */
	__u32 folio_index;
	__u32 mapping_id;
	__u32 lat_cluster;    /* 0..4 buckets */
	__u64 start_ns;
	__u64 latency_ns;
};

/* Per-PID rolling window */
struct swap_window {
	__u32 pid;
	__u32 count;               /* <= SEQ_LEN */
	char  comm[16];
	struct feat8 feats[];      /* [SEQ_LEN] flexible after header */
};

/* Shared region header */
struct shared_region {
	__u32 nslots;              /* MAX_PROCS */
	__u32 seq_len;             /* SEQ_LEN */
	__u64 version;             /* ++ on any change */
	__u64 last_notify_ns;      /* last global notify time */
	/* Windows laid out back-to-back; each size depends on SEQ_LEN */
	/* struct swap_window win0; ... */
};

/* ---------- Globals ---------- */
static struct shared_region *shm;
static void *shm_kva;
static size_t shm_size;
static dev_t devno;
static struct cdev cdev_obj;
static struct class *dev_class;
static struct sock *nl_sock;
static u32 userspace_nl_pid;
static DEFINE_SPINLOCK(win_lock);

/* kprobe timing */
static DEFINE_PER_CPU(u64, swap_start_time);
static struct kprobe kp_start;
static struct kprobe kp_done;

/* ---------- Helpers ---------- */
static inline __u16 va_l2(u64 va) { return (va >> 21) & 0x1FF; }
static inline __u16 va_l1(u64 va) { return (va >> 12) & 0x1FF; }

static inline __u16 pfn_top(u64 pfn) { return (pfn >> 20) & 0x1; }
static inline __u16 pfn_s4(u64 pfn)  { return (pfn >> 16) & 0xF; }
static inline __u16 pfn_s3(u64 pfn)  { return (pfn >> 12) & 0xF; }
static inline __u16 pfn_s2(u64 pfn)  { return (pfn >>  8) & 0xF; }
static inline __u16 pfn_s1(u64 pfn)  { return (pfn >>  4) & 0xF; }
static inline __u16 pfn_s0(u64 pfn)  { return (pfn >>  0) & 0xF; }

static inline __u32 mapping_id_from_ptr(void *p)
{
	/* cheap stable hash */
	u64 v = (u64)(unsigned long)p;
	v ^= v >> 33; v *= 0xff51afd7ed558ccdULL;
	v ^= v >> 33; v *= 0xc4ceb9fe1a85ec53ULL;
	v ^= v >> 33;
	return (u32)(v & 0xFFFFFFFFu);
}

static inline __u32 latency_bucket(u64 ns)
{
	/* 0:<50us, 1:<200us, 2:<1ms, 3:<5ms, 4:>=5ms */
	if (ns <  50 * 1000ULL) return 0;
	if (ns < 200 * 1000ULL) return 1;
	if (ns <   1 * 1000 * 1000ULL) return 2;
	if (ns <   5 * 1000 * 1000ULL) return 3;
	return 4;
}

/* shared layout: header + N windows, each with flexible array */
static size_t window_bytes(int seq_len)
{
	return sizeof(struct swap_window) + sizeof(struct feat8) * seq_len;
}

static size_t region_bytes(int nslots, int seq_len)
{
	return sizeof(struct shared_region) + nslots * window_bytes(seq_len);
}

static struct swap_window *win_at(void *base, int idx, int seq_len)
{
	char *p = (char *)base + sizeof(struct shared_region) + idx * window_bytes(seq_len);
	return (struct swap_window *)p;
}

static int find_or_make_slot(pid_t pid, const char *comm)
{
	int i, free_idx = -1;
	for (i = 0; i < MAX_PROCS; i++) {
		struct swap_window *w = win_at(shm, i, SEQ_LEN);
		if (w->pid == pid) return i;
		if (free_idx < 0 && w->pid == 0) free_idx = i;
	}
	if (free_idx >= 0) {
		struct swap_window *w = win_at(shm, free_idx, SEQ_LEN);
		w->pid = pid;
		w->count = 0;
		memset(w->feats, 0, sizeof(struct feat8) * SEQ_LEN);
		strscpy(w->comm, comm ? comm : "", sizeof(w->comm));
		return free_idx;
	}
	return -1;
}

static void lifo_push_feat(int slot, const struct feat8 *f)
{
	struct swap_window *w = win_at(shm, slot, SEQ_LEN);
	if (w->count < SEQ_LEN) {
		w->feats[w->count++] = *f;
	} else {
		int i;
		for (i = 1; i < SEQ_LEN; i++)
			w->feats[i-1] = w->feats[i];
		w->feats[SEQ_LEN-1] = *f;
	}
	shm->version++;
}

/* ---------- Netlink ---------- */
static void nl_send_pid_update_debounced(pid_t pid)
{
	u64 now = ktime_get_ns();
	if (now - shm->last_notify_ns < DEBOUNCE_NS)
		return;
	if (!nl_sock || !userspace_nl_pid)
		return;

	/* payload = pid (u32) */
	struct sk_buff *skb = nlmsg_new(sizeof(u32), GFP_ATOMIC);
	if (!skb) return;

	struct nlmsghdr *nlh = nlmsg_put(skb, 0, 0, NLMSG_DONE, sizeof(u32), 0);
	if (!nlh) { kfree_skb(skb); return; }
	memcpy(nlmsg_data(nlh), &pid, sizeof(u32));

	int res = nlmsg_unicast(nl_sock, skb, userspace_nl_pid);
	if (res < 0) {
		/* don't spam kernel log — silent drop */
		return;
	}
	shm->last_notify_ns = now;
}

static void nl_recv_cb(struct sk_buff *skb)
{
	struct nlmsghdr *nlh;
	if (!skb) return;
	nlh = nlmsg_hdr(skb);
	userspace_nl_pid = nlh->nlmsg_pid; /* register sender */
}

/* ---------- Char device (mmap) ---------- */
static int sai_open(struct inode *ino, struct file *filp) { return 0; }
static int sai_release(struct inode *ino, struct file *filp) { return 0; }

static int sai_mmap(struct file *filp, struct vm_area_struct *vma)
{
	size_t len = vma->vm_end - vma->vm_start;
	if (len != shm_size) return -EINVAL;
	return remap_vmalloc_range(vma, shm_kva, 0);
}

static const struct file_operations sai_fops = {
	.owner   = THIS_MODULE,
	.open    = sai_open,
	.release = sai_release,
	.mmap    = sai_mmap,
};

/* ---------- Kprobes (collect + push) ---------- */
static int start_pre(struct kprobe *p, struct pt_regs *regs)
{
	this_cpu_write(swap_start_time, ktime_get_ns());
	return 0;
}

static void finish_post(struct kprobe *p, struct pt_regs *regs, unsigned long flags)
{
	struct vm_fault *vmf = (struct vm_fault *)regs->di;
	u64 end_ns = ktime_get_ns();
	u64 start_ns = this_cpu_read(swap_start_time);
	u64 lat = end_ns - start_ns;

	if (!vmf || !vmf->pte || !current) return;

	pte_t pte_val = READ_ONCE(*(vmf->pte));
	if (!pte_present(pte_val)) return;

	unsigned long pfn = pte_pfn(pte_val);
	struct folio *folio = page_folio(pfn_to_page(pfn));

	struct feat8 f = {0};
	u64 va = vmf->address;

	f.x[0] = va_l2(va);
	f.x[1] = va_l1(va);
	f.x[2] = pfn_top(pfn);
	f.x[3] = pfn_s4(pfn);
	f.x[4] = pfn_s3(pfn);
	f.x[5] = pfn_s2(pfn);
	f.x[6] = pfn_s1(pfn);
	f.x[7] = pfn_s0(pfn);

	f.folio_index = folio ? (u32)folio->index : 0;
	f.mapping_id  = mapping_id_from_ptr(folio && folio->mapping ? folio->mapping : NULL);
	f.lat_cluster = latency_bucket(lat);
	f.start_ns    = start_ns;
	f.latency_ns  = lat;

	spin_lock(&win_lock);
	{
		int slot = find_or_make_slot(current->pid, current->comm);
		if (slot >= 0) {
			struct swap_window *w = win_at(shm, slot, SEQ_LEN);
			lifo_push_feat(slot, &f);
			/* count based notify throttle */
			if (w->count % TRIGGER_EVERY == 0)
				nl_send_pid_update_debounced(current->pid);
		}
	}
	spin_unlock(&win_lock);
}

/* ---------- Init / Exit ---------- */
static int __init sai_init(void)
{
	int i, ret;

	shm_size = region_bytes(MAX_PROCS, SEQ_LEN);
	shm_kva  = vmalloc_user(shm_size);
	if (!shm_kva) return -ENOMEM;
	memset(shm_kva, 0, shm_size);
	shm = (struct shared_region *)shm_kva;
	shm->nslots = MAX_PROCS;
	shm->seq_len = SEQ_LEN;
	shm->version = 1;

	/* init windows headers */
	for (i = 0; i < MAX_PROCS; i++) {
		struct swap_window *w = win_at(shm, i, SEQ_LEN);
		w->pid = 0;
		w->count = 0;
		memset(w->comm, 0, sizeof(w->comm));
		memset(w->feats, 0, sizeof(struct feat8)*SEQ_LEN);
	}

	/* chardev */
	ret = alloc_chrdev_region(&devno, 0, 1, DEV_NAME);
	if (ret) goto fail_chr;

	cdev_init(&cdev_obj, &sai_fops);
	ret = cdev_add(&cdev_obj, devno, 1);
	if (ret) goto fail_cdev;

	dev_class = class_create(DEV_NAME); /* new API (6.8+) */
	if (IS_ERR(dev_class)) { ret = PTR_ERR(dev_class); goto fail_class; }

	if (!device_create(dev_class, NULL, devno, NULL, DEV_NAME)) {
		ret = -ENODEV; goto fail_dev;
	}

	/* netlink */
	nl_sock = netlink_kernel_create(&init_net, NL_PROTO,
		&(struct netlink_kernel_cfg){ .input = nl_recv_cb });
	if (!nl_sock) { ret = -ENOMEM; goto fail_nl; }

	/* kprobes */
	kp_start.symbol_name = "do_swap_page";
	kp_start.pre_handler = start_pre;
	ret = register_kprobe(&kp_start);
	if (ret) { pr_err("kprobe do_swap_page failed %d\n", ret); goto fail_kp1; }

	kp_done.symbol_name = "finish_fault";
	kp_done.post_handler = finish_post;
	ret = register_kprobe(&kp_done);
	if (ret) { pr_err("kprobe finish_fault failed %d\n", ret); goto fail_kp2; }

	pr_info("swap_ai: ready. /dev/%s mmap=%zu; MAX_PROCS=%d SEQ_LEN=%d\n",
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
	if (nl_sock) netlink_kernel_release(nl_sock);
	device_destroy(dev_class, devno);
	class_destroy(dev_class);
	cdev_del(&cdev_obj);
	unregister_chrdev_region(devno, 1);
	vfree(shm_kva);
	pr_info("swap_ai: unloaded\n");
}

module_init(sai_init);
module_exit(sai_exit);
