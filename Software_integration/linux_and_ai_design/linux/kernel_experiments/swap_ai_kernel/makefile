# ==============================
#  Makefile for swap_ai_bridge
# ==============================

obj-m := swap_ai_bridge.o

# Kernel build directory
KDIR := /lib/modules/$(shell uname -r)/build

# Current module source directory
PWD := $(shell pwd)

# Default target: build module
all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

# Clean generated files
clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# Install module to kernel tree (optional)
install:
	sudo cp swap_ai_bridge.ko /lib/modules/$(shell uname -r)/kernel/
	sudo depmod -a
	echo "Installed swap_ai_bridge.ko"

# Load module
load:
	sudo insmod swap_ai_bridge.ko && echo "Loaded swap_ai_bridge"

# Unload module
unload:
	sudo rmmod swap_ai_bridge && echo "Unloaded swap_ai_bridge"
