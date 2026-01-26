# obj-m += final_kprobe_tracker.o

# KDIR := /usr/src/linux-headers-$(shell uname -r)

# all:
# 	$(MAKE) -C $(KDIR) M=$(PWD) modules

# clean:
# 	$(MAKE) -C $(KDIR) M=$(PWD) clean

# obj-m += process_wise_tracker.o

# KDIR := /usr/src/linux-headers-$(shell uname -r)

# all:
# 	$(MAKE) -C $(KDIR) M=$(PWD) modules

# clean:
# 	$(MAKE) -C $(KDIR) M=$(PWD) clean
# obj-m += complete_page_tracker.o

# KDIR := /usr/src/linux-headers-$(shell uname -r)

# all:
# 	$(MAKE) -C $(KDIR) M=$(PWD) modules

# clean:
# 	$(MAKE) -C $(KDIR) M=$(PWD) clean
# obj-m += major_fault_tracker.o

# KDIR := /usr/src/linux-headers-$(shell uname -r)

# all:
# 	$(MAKE) -C $(KDIR) M=$(PWD) modules

# clean:
# 	$(MAKE) -C $(KDIR) M=$(PWD) clean

# obj-m += pfn_kprobe.o

# all:
# 	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

# clean:
# 	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

obj-m += swap_tracker_proc.o
# obj-m += hemsa.o

all:
		make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
		make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean