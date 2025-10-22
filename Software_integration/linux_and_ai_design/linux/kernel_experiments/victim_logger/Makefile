obj-m += victim_logger.o

# ✅ CORRECT PATH - yeh actually available hai
KDIR := /usr/src/linux-headers-6.8.0-85-generic


all:
	@echo "🔍 Using: $(KDIR)"
	@if [ -d "$(KDIR)" ]; then \
		echo "✅ Headers directory found!"; \
		make -C $(KDIR) M=$(PWD) modules; \
	else \
		echo "❌ Directory not found: $(KDIR)"; \
		echo "📝 Available headers directories:"; \
		ls -d /usr/src/linux-* 2>/dev/null | head -10; \
		exit 1; \
	fi

clean:
	@if [ -d "$(KDIR)" ]; then \
		make -C $(KDIR) M=$(PWD) clean; \
	fi
	rm -f *.ko *.o *.mod.* modules.order Module.symvers

install:
	sudo insmod victim_logger.ko

uninstall:
	sudo rmmod victim_logger.ko

debug:
	@echo "=== WSL2 Debug ==="
	@echo "Current Kernel: $(shell uname -r)"
	@echo "Headers Path: $(KDIR)"
	@echo "Path Exists: $(if $(wildcard $(KDIR)),YES,NO)"
	@echo "Makefile in headers: $(if $(wildcard $(KDIR)/Makefile),YES,NO)"