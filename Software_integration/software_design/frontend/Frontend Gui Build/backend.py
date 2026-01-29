#!/usr/bin/env python3

import psutil
import time
import json
import sys

class SystemMonitor:
    def get_all_processes(self):
        """Get all running processes in your required format"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                # Get memory in MB
                memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                
                # Get CPU percentage
                cpu_percent = proc.info['cpu_percent'] or 0
                
                # Format exactly like your UI expects
                process_info = (
                    f"{proc.info['name']} ({proc.info['pid']})",  # Name (PID)
                    "0 Mbps",                                    # Network send
                    f"{cpu_percent:.1f}%",                       # CPU usage
                    f"{memory_mb:.1f} MB",                       # Memory usage  
                    "0 Mbps",                                    # Disk usage
                    "0%"                                         # GPU usage
                )
                processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue
        
        # Sort by memory usage (descending)
        processes.sort(key=lambda x: float(x[3].split()[0]), reverse=True)
        return processes[:25]  # Return top 25 processes

    def get_performance_metrics(self):
        """Get system performance metrics"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_freq = psutil.cpu_freq()
        cpu_speed = f"{cpu_freq.current:.2f} GHz" if cpu_freq else "N/A"
        
        # Memory
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / 1024 / 1024 / 1024
        memory_total_gb = memory.total / 1024 / 1024 / 1024
        memory_percent = memory.percent
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Network
        net_io = psutil.net_io_counters()
        network_send = f"{(net_io.bytes_sent / 1024 / 1024):.1f}"
        network_recv = f"{(net_io.bytes_recv / 1024 / 1024):.1f}"
        
        return {
            'cpu_percent': cpu_percent,
            'cpu_speed': cpu_speed,
            'memory_used': memory_used_gb,
            'memory_total': memory_total_gb, 
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'network_send': network_send,
            'network_recv': network_recv
        }

def main():
    monitor = SystemMonitor()
    
    # Continuous output for UI integration
    while True:
        try:
            # Get processes data
            processes = monitor.get_all_processes()
            
            # Get performance metrics
            metrics = monitor.get_performance_metrics()
            
            # Output as JSON
            output = {
                'processes': processes,
                'metrics': metrics,
                'timestamp': time.time()
            }
            
            print(json.dumps(output))
            sys.stdout.flush()
            
            time.sleep(2)  # Update every 2 seconds
            
        except Exception as e:
            print(json.dumps({'error': str(e)}))
            time.sleep(5)

if __name__ == "__main__":
    main()