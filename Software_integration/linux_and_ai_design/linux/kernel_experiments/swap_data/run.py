#!/usr/bin/env python3

import os
import time

def get_current_processes():
    processes = []
    seen_pids = set()
    
    try:
        with open('/proc/swap_entry', 'r') as f:
            # Skip header
            next(f)
            
            for line in f:
                if len(processes) >= 15:
                    break
                    
                parts = line.strip().split()
                if len(parts) < 2:
                    continue
                    
                pid, comm = parts[0], parts[1]
                
                if pid in seen_pids:
                    continue
                seen_pids.add(pid)
                
                # Get memory usage
                try:
                    with open(f'/proc/{pid}/statm', 'r') as statm:
                        memory_pages = int(statm.readline().split()[0])
                        memory_mb = (memory_pages * 4) / 1024.0
                except:
                    memory_mb = 0
                
                processes.append(
                    (comm, "0 Mbps", "0%", f"{memory_mb:.1f} MB", "0 Mbps", "0%")
                )
                
    except FileNotFoundError:
        pass
    
    return processes

# Continuous monitoring
while True:
    os.system('clear')
    processes = get_current_processes()
    
    print("processes = [")
    for i, proc in enumerate(processes):
        comma = "," if i < len(processes) - 1 else ""
        print(f"            {proc}{comma}")
    print("        ]")
    
    time.sleep(2)