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
	{ 0x999e8297, "vfree" },
	{ 0x122c3a7e, "_printk" },
	{ 0xb43f9365, "ktime_get" },
	{ 0xfc9dd0b0, "remap_vmalloc_range" },
	{ 0x5635a60a, "vmalloc_user" },
	{ 0xfb578fc5, "memset" },
	{ 0xe3ec2f2b, "alloc_chrdev_region" },
	{ 0x22d6de43, "cdev_init" },
	{ 0xec957a9, "cdev_add" },
	{ 0x6ca9b86a, "class_create" },
	{ 0x2e3443fd, "device_create" },
	{ 0x8c75b508, "init_net" },
	{ 0xb31530df, "__netlink_kernel_create" },
	{ 0x3f66a26e, "register_kprobe" },
	{ 0xcbd4898c, "fortify_panic" },
	{ 0xf0fdf6cb, "__stack_chk_fail" },
	{ 0xb8aff722, "pcpu_hot" },
	{ 0x2d0fc5c, "pv_ops" },
	{ 0xd4ec10e6, "BUG_func" },
	{ 0x1d19f77b, "physical_mask" },
	{ 0x97651e6c, "vmemmap_base" },
	{ 0xbcb36fe4, "hugetlb_optimize_vmemmap_key" },
	{ 0xba8fbd64, "_raw_spin_lock" },
	{ 0xa916b694, "strnlen" },
	{ 0xdd64e639, "strscpy" },
	{ 0xb5b54b34, "_raw_spin_unlock" },
	{ 0x4f8c5665, "__alloc_skb" },
	{ 0x682299ba, "__nlmsg_put" },
	{ 0x130edf8d, "netlink_unicast" },
	{ 0x30b86e62, "kfree_skb_reason" },
	{ 0x87a21cb3, "__ubsan_handle_out_of_bounds" },
	{ 0xbdfb6dbb, "__fentry__" },
	{ 0x5b8239ca, "__x86_return_thunk" },
	{ 0xbb10e61d, "unregister_kprobe" },
	{ 0xc23562b8, "netlink_kernel_release" },
	{ 0x19edaabb, "device_destroy" },
	{ 0x75646747, "class_destroy" },
	{ 0xb1b9cfc9, "cdev_del" },
	{ 0x6091b333, "unregister_chrdev_region" },
	{ 0xe2fd41e5, "module_layout" },
};

MODULE_INFO(depends, "");


MODULE_INFO(srcversion, "5D36854DE9B7EF6973E1D7E");
