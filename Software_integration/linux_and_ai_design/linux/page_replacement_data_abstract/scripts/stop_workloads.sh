#!/bin/bash

echo "=== Stopping All Workloads ==="

# Stop specific workload processes
pkill -f sequential_access
pkill -f random_access  
pkill -f mixed_workload
pkill -f stress-ng

# Check if any are still running
RUNNING=$(ps aux | grep -E "(sequential|random|mixed|stress-ng)" | grep -v grep)
if [ -n "$RUNNING" ]; then
    echo "The following workload processes are still running:"
    echo "$RUNNING"
    echo "Use 'pkill -9 -f [process_name]' to force kill if necessary"
else
    echo "All workload processes stopped successfully."
fi

# Clean up PID file
rm -f ../logs/workload_pids.txt
