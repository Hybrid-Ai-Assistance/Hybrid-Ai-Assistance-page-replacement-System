#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kprobes.h>
#include <linux/mm.h>
#include <linux/slab.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/list.h>
#include <linux/spinlock.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Shubham");
MODULE_DESCRIPTION("Kprobe-based Folio Data Capture");

#define MAX_VICTIMS 10000

struct folio_victim {
    unsigned long pfn;
    unsigned long nr_pages;
    int lru_type;
    bool anon;
    unsigned long timestamp;
    struct list_head list;
};

static LIST_HEAD(victim_list);
static DEFINE_SPINLOCK(victim_lock);
static int victim_count = 0;

// Kprobe for shrink_folio_list
static struct kprobe kp = {
    .symbol_name = "shrink_folio_list",
};

// Function to extract folio from shrink_folio_list parameters
static struct folio* extract_folio_from_params(struct pt_regs *regs)
{
    struct list_head *folio_list;
    struct folio *folio = NULL;
    
    // x86_64 calling convention: 
    // RDI = folio_list, RSI = pgdat, RDX = sc, RCX = stat
    folio_list = (struct list_head *)regs->di;
    
    if (folio_list && !list_empty(folio_list)) {
        // Get first folio from the list
        folio = list_first_entry(folio_list, struct folio, lru);
    }
    
    return folio;
}

// Main kprobe handler
static int handler_pre(struct kprobe *p, struct pt_regs *regs)
{
    struct folio *folio;
    struct folio_victim *victim;
    unsigned long flags;
    int nr_pages = 1;
    
    // Extract folio from function parameters
    folio = extract_folio_from_params(regs);
    
    if (!folio || victim_count >= MAX_VICTIMS)
        return 0;
    
    // Folio information capture karein
    victim = kmalloc(sizeof(*victim), GFP_ATOMIC);
    if (!victim)
        return 0;
    
    // ACTUAL FOLIO DATA CAPTURE - YAHI AAPKO CHAHIYE
    victim->pfn = folio_pfn(folio);
    victim->nr_pages = folio_nr_pages(folio);
    victim->lru_type = folio_test_active(folio) ? 1 : 0;
    victim->anon = folio_test_anon(folio);
    victim->timestamp = jiffies;
    INIT_LIST_HEAD(&victim->list);
    
    spin_lock_irqsave(&victim_lock, flags);
    list_add_tail(&victim->list, &victim_list);
    victim_count++;
    spin_unlock_irqrestore(&victim_lock, flags);
    
    // Real-time logging
    printk(KERN_INFO "KPROBE_FOLIO: pfn=0x%lx pages=%lu type=%s lru=%s count=%d\n",
           victim->pfn, victim->nr_pages,
           victim->anon ? "ANON" : "FILE", 
           victim->lru_type ? "ACTIVE" : "INACTIVE",
           victim_count);
    
    return 0;
}

// /proc interface for data export
static int victim_proc_show(struct seq_file *m, void *v)
{
    struct folio_victim *victim;
    
    seq_printf(m, "pfn,nr_pages,lru_type,memory_type,timestamp\n");
    
    list_for_each_entry(victim, &victim_list, list) {
        seq_printf(m, "0x%lx,%lu,%d,%s,%lu\n",
                   victim->pfn, victim->nr_pages,
                   victim->lru_type,
                   victim->anon ? "anon" : "file", 
                   victim->timestamp);
    }
    return 0;
}

static int __init kprobe_folio_init(void)
{
    int ret;
    
    kp.pre_handler = handler_pre;
    ret = register_kprobe(&kp);
    
    if (ret < 0) {
        printk(KERN_ERR "Kprobe registration failed: %d\n", ret);
        return ret;
    }
    
    proc_create_single("kprobe_folio_data", 0, NULL, victim_proc_show);
    
    printk(KERN_INFO "🎯 Kprobe Folio Tracker Loaded\n");
    printk(KERN_INFO "📊 Capturing actual folio data from shrink_folio_list\n");
    printk(KERN_INFO "💡 Monitoring memory reclaim in real-time\n");
    
    return 0;
}

static void __exit kprobe_folio_exit(void)
{
    struct folio_victim *victim, *tmp;
    
    unregister_kprobe(&kp);
    
    printk(KERN_INFO "=== KPROBE FOLIO SUMMARY ===\n");
    printk(KERN_INFO "Total folios captured: %d\n", victim_count);
    
    // Data analysis
    if (victim_count > 0) {
        struct folio_victim *first = list_first_entry(&victim_list, struct folio_victim, list);
        printk(KERN_INFO "First victim: pfn=0x%lx, type=%s\n", 
               first->pfn, first->anon ? "anon" : "file");
    }
    
    // Cleanup
    list_for_each_entry_safe(victim, tmp, &victim_list, list) {
        list_del(&victim->list);
        kfree(victim);
    }
    
    remove_proc_entry("kprobe_folio_data", NULL);
    printk(KERN_INFO "Kprobe Folio Tracker Unloaded\n");
}

module_init(kprobe_folio_init);
module_exit(kprobe_folio_exit);