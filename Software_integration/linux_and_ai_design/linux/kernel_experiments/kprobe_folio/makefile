# obj-m += free_it_tracker.o

# KDIR := /usr/src/linux-headers-$(shell uname -r)

# all:
# 	$(MAKE) -C $(KDIR) M=$(PWD) modules

# clean:
# 	$(MAKE) -C $(KDIR) M=$(PWD) clean

obj-m += kprobe_folio.o

KDIR := /usr/src/linux-headers-$(shell uname -r)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean