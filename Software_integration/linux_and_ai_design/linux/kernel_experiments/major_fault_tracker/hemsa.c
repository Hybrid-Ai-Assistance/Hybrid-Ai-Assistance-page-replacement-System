#include <linux/module.h>
#include <linux/mm.h>
#include <linux/mm_types.h>
#include <linux/sched.h>
#include <linux/ktime.h>
#include <linux/kprobes.h>
#include <linux/swap.h>
#include <linux/swapops.h>
#include <asm/pgtable.h>

DEFINE_PER_CPU(u64, swap_start_time);
DEFINE_PER_CPU(unsigned long, swap_start_va);

// Store folio information
struct swap_folio_info {
    struct folio *folio;
    unsigned long va;
    u64 start_time;
};

static DEFINE_PER_CPU(struct swap_folio_info, current_swap);

// ====================== DO_SWAP_PAGE START ==========================
static int do_swap_pre(struct kprobe *p, struct pt_regs *regs)
{   
    struct vm_fault *vmf = (struct vm_fault *)regs->di;
    u64 start_time = ktime_get_ns();
    
    this_cpu_write(swap_start_time, start_time);
    
    if (vmf) {
        this_cpu_write(swap_start_va, vmf->address);
        
        // Initialize current swap info
        struct swap_folio_info *info = this_cpu_ptr(&current_swap);
        info->folio = NULL;
        info->va = vmf->address;
        info->start_time = start_time;
        
        if (current) {
            printk(KERN_INFO "🟠 [SWAP-START] PID=%d | COMM=%s | VA=0x%lx | Time=%llu ns\n",
                   current->pid, current->comm, vmf->address, start_time);
        }
    }
    return 0;
}

// ====================== SWAPIN_READAHEAD for folio tracking =========
static int swapin_readahead_pre(struct kprobe *p, struct pt_regs *regs)
{
    // swapin_readahead(swp_entry_t entry, gfp_t gfp_mask, ...)
    // We can extract swap entry and potentially get folio info
    swp_entry_t entry = (swp_entry_t)regs->di;
    
    if (swp_type(entry) >= MAX_SWAPFILES) {
        return 0;
    }
    
    struct swap_folio_info *info = this_cpu_ptr(&current_swap);
    info->start_time = this_cpu_read(swap_start_time);
    
    printk(KERN_INFO "📖 [SWAPIN-READAHEAD] Entry=0x%lx | Type=%d | Offset=%lu\n",
           entry.val, swp_type(entry), swp_offset(entry));
    
    return 0;
}

// ====================== VMA_OPERATIONS FAULT ========================
static int do_fault_pre(struct kprobe *p, struct pt_regs *regs)
{
    struct vm_fault *vmf = (struct vm_fault *)regs->di;
    
    if (vmf && vmf->vma && current) {
        printk(KERN_INFO "⚡ [PAGE-FAULT] PID=%d | COMM=%s | VA=0x%lx | Flags=0x%lx\n",
               current->pid, current->comm, vmf->address, vmf->flags);
    }
    return 0;
}

// ====================== FINISH_FAULT with folio info ================
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
    struct swap_folio_info *info = this_cpu_ptr(&current_swap);

    if (pte_present(pte_val)) {
        unsigned long pfn = pte_pfn(pte_val);
        struct page *page = pfn_to_page(pfn);
        struct folio *folio = page_folio(page);
        
        // Store folio info
        info->folio = folio;
        
        printk(KERN_INFO "🟢 [SWAP-DONE] PID=%d | COMM=%s | VA=0x%lx | PFN=0x%lx\n",
               current->pid, current->comm, vmf->address, pfn);
        printk(KERN_INFO "   📄 [FOLIO-INFO] Folio=%px | Order=%u | Refs=%d | Mapping=%px\n",
               folio, folio_order(folio), folio_ref_count(folio), folio->mapping);
        printk(KERN_INFO "   ⏱  [LATENCY] Latency=%llu ns\n", latency);
        
        // Additional folio details if available
        if (folio_test_swapbacked(folio)) {
            printk(KERN_INFO "   🔄 [FOLIO-FLAGS] SwapBacked | ");
        }
        if (folio_test_dirty(folio)) {
            printk(KERN_INFO "Dirty | ");
        }
        if (folio_test_locked(folio)) {
            printk(KERN_INFO "Locked | ");
        }
        if (folio_test_uptodate(folio)) {
            printk(KERN_INFO "Uptodate");
        }
        printk(KERN_INFO "\n");
        
    } else {
        printk(KERN_INFO "⚠ [SWAP-DONE] PID=%d | COMM=%s | VA=0x%lx | Page NOT PRESENT | Lat=%llu ns\n",
               current->pid, current->comm, vmf->address, latency);
    }
}

// ====================== TRACK FOLIO SPECIFIC OPERATIONS =============
static int folio_file_page_pre(struct kprobe *p, struct pt_regs *regs)
{
    // This probes filemap_fault to track file-backed folios
    struct vm_fault *vmf = (struct vm_fault *)regs->di;
    
    if (vmf && vmf->vma && current) {
        printk(KERN_INFO "📁 [FILEMAP-FAULT] PID=%d | COMM=%s | VA=0x%lx | File=%s\n",
               current->pid, current->comm, vmf->address,
               vmf->vma->vm_file ? vmf->vma->vm_file->f_path.dentry->d_name.name : "anon");
    }
    return 0;
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

static struct kprobe kp_swapin_readahead = {
    .symbol_name = "swapin_readahead",
    .pre_handler = swapin_readahead_pre,
};

static struct kprobe kp_vma_fault = {
    .symbol_name = "handle_pte_fault",
    .pre_handler = do_fault_pre,
};

static struct kprobe kp_folio_fault = {
    .symbol_name = "filemap_fault",
    .pre_handler = folio_file_page_pre,
};

// ====================== MODULE INIT/EXIT ============================
static int __init swap_tracker_init(void)
{
    int ret;
    int ret2, ret3, ret4;
    
    printk(KERN_INFO "🔍 Loading Enhanced Swap Tracker Module...\n");

    // Register main swap probes
    ret = register_kprobe(&kp_swap_start);
    if (ret < 0) {
        printk(KERN_ERR "Failed to register kprobe for do_swap_page: %d\n", ret);
        return ret;
    }

    ret2 = register_kprobe(&kp_swap_done);
    if (ret2 < 0) {
        printk(KERN_ERR "Failed to register kprobe for finish_fault: %d\n", ret2);
        goto err_swap_done;
    }

    // Register additional probes for better folio tracking
    ret3 = register_kprobe(&kp_swapin_readahead);
    if (ret3 < 0) {
        printk(KERN_WARNING "Failed to register kprobe for swapin_readahead: %d\n", ret3);
        // Continue without this probe
    }

    ret4 = register_kprobe(&kp_vma_fault);
    if (ret4 < 0) {
        printk(KERN_WARNING "Failed to register kprobe for handle_pte_fault: %d\n", ret4);
        // Continue without this probe
    }

    printk(KERN_INFO "✅ Enhanced Swap Tracker Module Loaded Successfully!\n");
    printk(KERN_INFO "📊 Tracking: Swap Latency, PFN, Folio info, and Page Fault details\n");
    return 0;

err_swap_done:
    unregister_kprobe(&kp_swap_start);
    return ret2;
}

static void __exit swap_tracker_exit(void)
{
    unregister_kprobe(&kp_swap_start);
    unregister_kprobe(&kp_swap_done);
    unregister_kprobe(&kp_swapin_readahead);
    unregister_kprobe(&kp_vma_fault);
    unregister_kprobe(&kp_folio_fault);
    
    printk(KERN_INFO "🧹 Enhanced Swap Tracker Module Unloaded.\n");
}

module_init(swap_tracker_init);
module_exit(swap_tracker_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Shubham");
MODULE_DESCRIPTION("Enhanced Swap Tracker with Folio Information");