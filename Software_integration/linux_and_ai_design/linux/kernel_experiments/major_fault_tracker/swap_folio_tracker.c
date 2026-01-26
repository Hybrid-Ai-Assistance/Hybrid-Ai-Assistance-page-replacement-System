#include <linux/module.h>
#include <linux/mm.h>       // struct vm_fault, pte_t, etc.
#include <linux/mm_types.h> // mm_struct definitions
#include <linux/sched.h>    // current
#include <linux/ktime.h>    // ktime_get_ns()
#include <linux/kprobes.h>  // for kprobe struct
#include <asm/pgtable.h>    // for PTE operations (arch-specific)

DEFINE_PER_CPU(u64, swap_start_time);
// ====================== DO_SWAP_PAGE START ==========================
static int do_swap_pre(struct kprobe *p, struct pt_regs *regs)
{
    this_cpu_write(swap_start_time, ktime_get_ns());
    u64 start_time = this_cpu_read(swap_start_time);
    struct vm_fault *vmf = (struct vm_fault *)regs->di;
    if (vmf && current)
        printk(KERN_INFO "🟠 [SWAP-START] PID=%d | COMM=%s | VA=0x%lx | Time=%llu ns\n",
               current->pid, current->comm, vmf->address, start_time);
    return 0;
}

// ====================== FINISH_FAULT END ============================

static void finish_fault_post(struct kprobe *p, struct pt_regs *regs,
                              unsigned long flags)
{
    struct vm_fault *vmf = (struct vm_fault *)regs->di;
    u64 end_time = ktime_get_ns();
    u64 start_time = this_cpu_read(swap_start_time);
    u64 latency = end_time - start_time;

    if (!vmf || !vmf->pte)
        return;

    pte_t pte_val = READ_ONCE(*(vmf->pte));

    if (pte_present(pte_val))
    {
        unsigned long pfn = pte_pfn(pte_val);
        struct folio *folio = page_folio(pfn_to_page(pfn));
        unsigned long folio_idx = 0;
        if (folio->mapping)
            folio_idx = folio->index;

        printk(KERN_INFO "🟢 [SWAP-DONE] PID=%d | COMM=%s | VA=0x%lx | PFN=0x%lx | mapping=%p | index=%lu | Lat=%llu ns\n",
               current->pid, current->comm, vmf->address, pfn, folio->mapping, folio_idx, latency);
    }
    else
    {
        printk(KERN_INFO "⚠️ [SWAP-DONE] PID=%d |COMM=%s | VA=0x%lx | Page NOT PRESENT | Lat=%llu ns\n",
               current->pid, current->comm, vmf->address, latency);
    }
}

// ====================== KPROBE STRUCTURES ===========================
static struct kprobe kp_swap_start = {
    .symbol_name = "do_swap_page",
    .pre_handler = do_swap_pre,
};

static struct kprobe kp_swap_done = {
    .symbol_name = "finish_fault",
    .post_handler = finish_fault_post,
};

// ====================== MODULE INIT/EXIT ============================
static int __init swap_tracker_init(void)
{
    int ret;
    printk(KERN_INFO "🔍 Loading Swap Tracker Module...\n");

    ret = register_kprobe(&kp_swap_start);
    if (ret < 0)
    {
        printk(KERN_ERR "Failed to register kprobe for do_swap_page: %d\n", ret);
        return ret;
    }

    ret = register_kprobe(&kp_swap_done);
    if (ret < 0)
    {
        printk(KERN_ERR "Failed to register kprobe for finish_fault: %d\n", ret);
        unregister_kprobe(&kp_swap_start);
        return ret;
    }

    printk(KERN_INFO "✅ Swap Tracker Module Loaded Successfully!\n");
    return 0;
}

static void __exit swap_tracker_exit(void)
{
    unregister_kprobe(&kp_swap_start);
    unregister_kprobe(&kp_swap_done);
    printk(KERN_INFO "🧹 Swap Tracker Module Unloaded.\n");
}

module_init(swap_tracker_init);
module_exit(swap_tracker_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Shubham");
MODULE_DESCRIPTION("Track Swap Latency and PFN via kprobes");
