#include <linux/module.h>
#define INCLUDE_VERMAGIC
#include <linux/build-salt.h>
#include <linux/elfnote-lto.h>
#include <linux/export-internal.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

#ifdef CONFIG_UNWINDER_ORC
#include <asm/orc_header.h>
ORC_HEADER;
#endif

BUILD_SALT;
BUILD_LTO_INFO;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef CONFIG_RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif



static const struct modversion_info ____versions[]
__used __section("__versions") = {
	{ 0x46b0be46, "single_open" },
	{ 0xc00e2b80, "seq_printf" },
	{ 0x34db050b, "_raw_spin_lock_irqsave" },
	{ 0xd35cce70, "_raw_spin_unlock_irqrestore" },
	{ 0x87a21cb3, "__ubsan_handle_out_of_bounds" },
	{ 0xb43f9365, "ktime_get" },
	{ 0x1d24c881, "___ratelimit" },
	{ 0xb8aff722, "pcpu_hot" },
	{ 0x2d0fc5c, "pv_ops" },
	{ 0xd4ec10e6, "BUG_func" },
	{ 0x1d19f77b, "physical_mask" },
	{ 0x97651e6c, "vmemmap_base" },
	{ 0xbcb36fe4, "hugetlb_optimize_vmemmap_key" },
	{ 0x9ed12e20, "kmalloc_large" },
	{ 0x69296e5c, "__get_task_comm" },
	{ 0x63cd0125, "remove_proc_entry" },
	{ 0xbb10e61d, "unregister_kprobe" },
	{ 0x37a0cba, "kfree" },
	{ 0xc1d9b323, "seq_read" },
	{ 0x7369f212, "seq_lseek" },
	{ 0x8e66928c, "single_release" },
	{ 0xbdfb6dbb, "__fentry__" },
	{ 0x3f66a26e, "register_kprobe" },
	{ 0x2dbde678, "proc_create" },
	{ 0x122c3a7e, "_printk" },
	{ 0x5b8239ca, "__x86_return_thunk" },
	{ 0xe2fd41e5, "module_layout" },
};

MODULE_INFO(depends, "");


MODULE_INFO(srcversion, "D1F166DF7740827E4143C25");
