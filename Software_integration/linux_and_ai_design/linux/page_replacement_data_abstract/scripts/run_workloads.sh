#!/bin/bash

WORKLOAD_DIR="../workloads"
LOG_DIR="../logs"
mkdir -p "$LOG_DIR"

echo "=== Compiling Workloads ==="

# Compile all workloads
cd "$WORKLOAD_DIR"
gcc sequential_access.c -o sequential_access -O2
gcc random_access.c -o random_access -O2
gcc mixed_workload.c -o mixed_workload -O2

if [ ! -f "sequential_access" ] || [ ! -f "random_access" ] || [ ! -f "mixed_workload" ]; then
    echo "Error: Failed to compile workloads!"
    exit 1
fi

echo "Workloads compiled successfully!"

echo ""
echo "=== Starting Workload Execution ==="
echo "Workloads will run for approximately 2 minutes..."
echo "Logs will be saved to: $LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Function to run workload with logging
run_workload() {
    local name=$1
    local executable=$2
    echo "Starting $name..."
    "./$executable" > "$LOG_DIR/${name}_${TIMESTAMP}.log" 2>&1 &
    local pid=$!
    echo "$name started with PID: $pid"
    echo $pid >> "$LOG_DIR/workload_pids.txt"
}

# Run workloads in background
run_workload "sequential" "sequential_access"
run_workload "random" "random_access" 
run_workload "mixed" "mixed_workload"

# Run stress-ng for additional memory pressure
echo "Starting memory stressor..."
stress-ng --vm 2 --vm-bytes 1G --timeout 120s > "$LOG_DIR/stress_ng_${TIMESTAMP}.log" 2>&1 &
echo $! >> "$LOG_DIR/workload_pids.txt"

echo ""
echo "All workloads started!"
echo "Check logs in: $LOG_DIR"
echo "Use 'ps aux | grep -E \"(sequential|random|mixed|stress-ng)\"' to see running processes"
echo "Use './scripts/stop_workloads.sh' to stop all workloads"

# Wait for completion
echo ""
echo "Waiting for workloads to complete (120 seconds)..."
sleep 120

echo "Workload execution time completed."
echo "Note: Some processes may still be running."
echo "Use './scripts/stop_workloads.sh' to ensure all processes are stopped"
