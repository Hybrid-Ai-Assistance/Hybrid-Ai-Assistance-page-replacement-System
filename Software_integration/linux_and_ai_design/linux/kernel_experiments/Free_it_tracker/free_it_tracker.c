#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/mm.h>
#include <linux/slab.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/list.h>
#include <linux/spinlock.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Shubham");
MODULE_DESCRIPTION("free_it Victim Tracker - Module Only");

#define MAX_VICTIMS 5000

struct free_it_victim {
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

// Export this function - baad mein kernel patch ke bina use karenge
void track_free_it_folio(struct folio *folio, int nr_pages)
{
    struct free_it_victim *victim;
    unsigned long flags;
    
    if (victim_count >= MAX_VICTIMS)
        return;
        
    victim = kmalloc(sizeof(*victim), GFP_ATOMIC);
    if (!victim)
        return;
    
    // IMPORTANT: Yahi data aapko chahiye
    victim->pfn = folio_pfn(folio);
    victim->nr_pages = nr_pages;
    victim->lru_type = folio_test_active(folio) ? 1 : 0;
    victim->anon = folio_test_anon(folio);
    victim->timestamp = jiffies;
    INIT_LIST_HEAD(&victim->list);
    
    spin_lock_irqsave(&victim_lock, flags);
    list_add_tail(&victim->list, &victim_list);
    victim_count++;
    spin_unlock_irqrestore(&victim_lock, flags);
    
    printk(KERN_INFO "FREE_IT: pfn=0x%lx pages=%lu type=%s lru=%s\n",
           victim->pfn, victim->nr_pages,
           victim->anon ? "ANON" : "FILE",
           victim->lru_type ? "ACTIVE" : "INACTIVE");
}
EXPORT_SYMBOL(track_free_it_folio);

// /proc interface for data export
static int victim_proc_show(struct seq_file *m, void *v)
{
    struct free_it_victim *victim;
    
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

static int __init free_it_module_init(void)
{
    proc_create_single("free_it_data", 0, NULL, victim_proc_show);
    
    printk(KERN_INFO "🔍 free_it Tracker Module Loaded\n");
    printk(KERN_INFO "📊 Ready to capture PFN data from free_it victims\n");
    printk(KERN_INFO "💡 Use: cat /proc/free_it_data > pfn_analysis.csv\n");
    
    return 0;
}

static void __exit free_it_module_exit(void)
{
    struct free_it_victim *victim, *tmp;
    
    printk(KERN_INFO "=== FREE_IT VICTIM SUMMARY ===\n");
    printk(KERN_INFO "Total victims captured: %d\n", victim_count);
    
    // Cleanup
    list_for_each_entry_safe(victim, tmp, &victim_list, list) {
        list_del(&victim->list);
        kfree(victim);
    }
    
    remove_proc_entry("free_it_data", NULL);
    printk(KERN_INFO "free_it Tracker Module Unloaded\n");
}

module_init(free_it_module_init);
module_exit(free_it_module_exit);