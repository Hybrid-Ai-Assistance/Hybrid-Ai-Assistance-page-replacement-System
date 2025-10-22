#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Shubham");
MODULE_DESCRIPTION("WSL2 Cross-Kernel Test");

static int __init victim_logger_init(void)
{
    printk(KERN_INFO "🎉 WSL2 Cross-Kernel Test: SUCCESS!\n");
    printk(KERN_INFO "📊 Current Kernel: 6.6.87\n");
    printk(KERN_INFO "📊 Compiled with Headers: 6.14.0\n");
    printk(KERN_INFO "✅ Cross-kernel compilation working!\n");
    return 0;
}

static void __exit victim_logger_exit(void)
{
    printk(KERN_INFO "🎉 WSL2 Cross-Kernel Test: Unloaded\n");
}

module_init(victim_logger_init);
module_exit(victim_logger_exit);