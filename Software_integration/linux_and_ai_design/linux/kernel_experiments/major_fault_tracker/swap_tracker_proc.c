#include <linux/module.h>
#include <linux/mm.h>
#include <linux/mm_types.h>
#include <linux/sched.h>
#include <linux/ktime.h>
#include <linux/kprobes.h>
#include <linux/slab.h>
#include <linux/pgtable.h>
#include <linux/hashtable.h>
#include <linux/spinlock.h>
#include <linux/list.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <asm/pgtable.h>

#ifndef pte_swp
#define pte_swp(pte) (!pte_present(pte) && !pte_none(pte))
#endif

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Shubham");
MODULE_DESCRIPTION("Accurate Swap Latency Tracker with /proc logging");
MODULE_VERSION("2.0");

#define MAX_PROC_TRACKED 15
#define PER_PROC_MAX_ENTRIES 200
#define MAX_TOTAL_ENTRIES (MAX_PROC_TRACKED * PER_PROC_MAX_ENTRIES)
#define PROC_NAME "swap_entry"

/* ---------- (PID, VA) → start time hash ---------- */
#define START_HASH_BITS 10
#define START_HASH_MAX 2048

struct start_time_item {
    pid_t pid;
    unsigned long va;
    u64 start_ns;
    struct hlist_node node;
};
DEFINE_PER_CPU(u64, swap_start_time);
static DEFINE_HASHTABLE(start_ht, START_HASH_BITS);
static DEFINE_SPINLOCK(start_ht_lock);
static int start_ht_size = 0;


/* ---------- Logging structures ---------- */
struct swap_entry_data {
    unsigned long va;
    unsigned long pfn;
    unsigned long folio_idx;
    void *mapping;
    u64 start_ns;
    u64 latency_ns;
};

struct process_swap_log {
    pid_t pid;
    char comm[TASK_COMM_LEN];
    int count;
    struct swap_entry_data entries[PER_PROC_MAX_ENTRIES];
    struct list_head list;
};

static LIST_HEAD(proc_swap_list);
static DEFINE_SPINLOCK(proc_swap_lock);
static int proc_nodes = 0;
static int total_entries = 0;

/* ---------- Helpers ---------- */
static struct process_swap_log *find_proc_log_locked(pid_t pid)
{
    struct process_swap_log *p;
    list_for_each_entry(p, &proc_swap_list, list) {
        if (p->pid == pid)
            return p;
    }
    return NULL;
}

static struct process_swap_log *find_or_create_proc_log(pid_t pid)
{
    struct process_swap_log *p;
    unsigned long flags;

    spin_lock_irqsave(&proc_swap_lock, flags);
    p = find_proc_log_locked(pid);
    if (p) {
        spin_unlock_irqrestore(&proc_swap_lock, flags);
        return p;
    }

    if (proc_nodes >= MAX_PROC_TRACKED) {
        spin_unlock_irqrestore(&proc_swap_lock, flags);
        return NULL;
    }

    p = kzalloc(sizeof(*p), GFP_ATOMIC);
    if (!p) {
        spin_unlock_irqrestore(&proc_swap_lock, flags);
        return NULL;
    }

    p->pid = pid;
    get_task_comm(p->comm, current);
    p->count = 0;
    INIT_LIST_HEAD(&p->list);
    list_add_tail(&p->list, &proc_swap_list);
    proc_nodes++;
    spin_unlock_irqrestore(&proc_swap_lock, flags);
    return p;
}

static void clear_all_process_logs(void)
{
    struct process_swap_log *p, *tmp;
    unsigned long flags;

    spin_lock_irqsave(&proc_swap_lock, flags);
    list_for_each_entry_safe(p, tmp, &proc_swap_list, list) {
        list_del(&p->list);
        kfree(p);
    }
    proc_nodes = 0;
    total_entries = 0;
    spin_unlock_irqrestore(&proc_swap_lock, flags);
}

/* ---------- Logging ---------- */
static void log_swap_done(pid_t pid, unsigned long va, unsigned long pfn,
                          u64 start_time, u64 latency, void *mapping,
                          unsigned long folio_idx)
{
    struct process_swap_log *p;
    unsigned long flags;

    if (READ_ONCE(total_entries) >= MAX_TOTAL_ENTRIES)
        return;

    p = find_or_create_proc_log(pid);
    if (!p)
        return;

    spin_lock_irqsave(&proc_swap_lock, flags);

    if (p->count < PER_PROC_MAX_ENTRIES && total_entries < MAX_TOTAL_ENTRIES) {
        struct swap_entry_data *e = &p->entries[p->count++];
        e->va = va;
        e->pfn = pfn;
        e->mapping = mapping;
        e->folio_idx = (mapping ? folio_idx : 0);
        e->start_ns = start_time;
        e->latency_ns = latency;
        total_entries++;
    }

    spin_unlock_irqrestore(&proc_swap_lock, flags);
}

/* ---------- Kprobe Handlers ---------- */
static int do_swap_pre(struct kprobe *p, struct pt_regs *regs)
{
    struct vm_fault *vmf = (struct vm_fault *)regs->di;
    if (!vmf || !vmf->vma)
        return 0;

    if (!pte_swp(vmf->orig_pte))
        return 0;

    u64 now = ktime_get_ns();
    // start_ht_insert(current->pid, vmf->address, now);
    this_cpu_write(swap_start_time, ktime_get_ns());
    u64 start_time = this_cpu_read(swap_start_time);

    printk_ratelimited(KERN_INFO
        "🟠 [SWAP-START] PID=%d | COMM=%s | VA=0x%lx | Time=%llu ns\n",
        current->pid, current->comm, vmf->address, now);
    return 0;
}

static void finish_fault_post(struct kprobe *p, struct pt_regs *regs, unsigned long flags)
{
    struct vm_fault *vmf = (struct vm_fault *)regs->di;
    if (!vmf || !vmf->pte || !vmf->vma)
        return;
    u64 start_time = this_cpu_read(swap_start_time);
    u64 end_time = ktime_get_ns();

    u64 latency = end_time - start_time;
    pte_t pte_val = READ_ONCE(*(vmf->pte));


    if (pte_present(pte_val)) {
        unsigned long pfn = pte_pfn(pte_val);
        struct folio *folio = page_folio(pfn_to_page(pfn));
        void *mapping = NULL;
        unsigned long fidx = 0;

        if (folio && folio->mapping) {
            mapping = folio->mapping;
            fidx = folio->index;
        }

        log_swap_done(current->pid, vmf->address, pfn, start_time, latency, mapping, fidx);

        printk_ratelimited(KERN_INFO
            "🟢 [SWAP-DONE] PID=%d | COMM=%s | VA=0x%lx | PFN=0x%lx | index=%lu | Lat=%llu ns\n",
            current->pid, current->comm, vmf->address, pfn, fidx, latency);
    }
}

/* ---------- /proc file ---------- */
static int swap_proc_show(struct seq_file *m, void *v)
{
    struct process_swap_log *p;
    unsigned long flags;
    int i;

    seq_printf(m, "PID,COMM,VA,PFN,mapping,folio_index,start_ns,latency_ns\n");
    spin_lock_irqsave(&proc_swap_lock, flags);
    list_for_each_entry(p, &proc_swap_list, list) {
        for (i = 0; i < p->count; i++) {
            struct swap_entry_data *e = &p->entries[i];
            seq_printf(m, "%d,%s,0x%lx,0x%lx,%p,%lu,%llu,%llu\n",
                       p->pid, p->comm,
                       e->va, e->pfn, e->mapping, e->folio_idx,
                       e->start_ns, e->latency_ns);
        }
    }
    spin_unlock_irqrestore(&proc_swap_lock, flags);
    seq_printf(m, "\n# Stats: procs=%d/%d, total_entries=%d/%d\n",
               proc_nodes, MAX_PROC_TRACKED, total_entries, MAX_TOTAL_ENTRIES);
    return 0;
}

static int swap_proc_open(struct inode *inode, struct file *file)
{
    return single_open(file, swap_proc_show, NULL);
}

static const struct proc_ops proc_fops = {
    .proc_open = swap_proc_open,
    .proc_read = seq_read,
    .proc_lseek = seq_lseek,
    .proc_release = single_release,
};

/* ---------- Module Init/Exit ---------- */
static struct kprobe kp_swap_start = {
    .symbol_name = "do_swap_page",
    .pre_handler = do_swap_pre,
};
static struct kprobe kp_swap_done = {
    .symbol_name = "finish_fault",
    .post_handler = finish_fault_post,
};
static struct kprobe kp_swap_start_alt = {
    .symbol_name = "__do_swap_page",
    .pre_handler = do_swap_pre,
};

static struct proc_dir_entry *proc_entry;

static int __init swap_tracker_init(void)
{
    int ret;

    ret = register_kprobe(&kp_swap_start);
    if (ret < 0)
        pr_warn("swap_tracker: do_swap_page missing (%d)\n", ret);

    register_kprobe(&kp_swap_start_alt);
    register_kprobe(&kp_swap_done);

    proc_entry = proc_create(PROC_NAME, 0444, NULL, &proc_fops);
    if (!proc_entry) {
        pr_err("swap_tracker: failed to create /proc/%s\n", PROC_NAME);
        return -ENOMEM;
    }

    pr_info("✅ swap_tracker: running. see /proc/%s\n", PROC_NAME);
    return 0;
}

static void __exit swap_tracker_exit(void)
{
    remove_proc_entry(PROC_NAME, NULL);
    unregister_kprobe(&kp_swap_start);
    unregister_kprobe(&kp_swap_start_alt);
    unregister_kprobe(&kp_swap_done);
    clear_all_process_logs();
    pr_info("🧹 swap_tracker: unloaded.\n");
}

module_init(swap_tracker_init);
module_exit(swap_tracker_exit);
