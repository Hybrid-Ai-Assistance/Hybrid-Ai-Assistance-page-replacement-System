#!/bin/bash

echo "=== FINAL Page Replacement Experiment ==="
echo "This will run for 5 minutes and collect real OS memory data"
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Step 1: Compile workloads
echo "Step 1: Compiling workloads..."
cd workloads
gcc sequential_access.c -o sequential_access -O2
gcc random_access.c -o random_access -O2
gcc mixed_workload.c -o mixed_workload -O2
gcc sequential_access_long.c -o sequential_access_long -O2
cd ..

echo "✓ Workloads compiled"

# Step 2: Start workloads in background
echo "Step 2: Starting memory workloads..."
cd workloads
./sequential_access_long &
SEQ_PID=$!
./random_access &
RAND_PID=$!
./mixed_workload &
MIXED_PID=$!
cd ..

# Start stress-ng
stress-ng --vm 2 --vm-bytes 1G --timeout 300s &
STRESS_PID=$!

echo "✓ Workloads started:"
echo "  Sequential: PID $SEQ_PID"
echo "  Random: PID $RAND_PID" 
echo "  Mixed: PID $MIXED_PID"
echo "  Stress: PID $STRESS_PID"

# Step 3: Start data collection
echo "Step 3: Starting data collection for 300 seconds (5 minutes)..."
echo "Data will be saved to: data/memory_data_*/"
./scripts/collect_basic_data_final.sh &
COLLECT_PID=$!

echo "✓ Data collection started: PID $COLLECT_PID"

# Step 4: Monitor progress
echo ""
echo "=== Experiment Running ==="
echo "Start time: $(date)"
echo "Will run for 5 minutes..."
echo ""

# Show what's running
echo "Current processes:"
ps aux | grep -E "(sequential|random|mixed|stress-ng|collect_basic)" | grep -v grep

# Wait for data collection to complete
echo ""
echo "Waiting for data collection to complete..."
wait $COLLECT_PID

echo ""
echo "=== Experiment Complete ==="
echo "End time: $(date)"

# Stop workloads
echo "Stopping workloads..."
kill $SEQ_PID 2>/dev/null
kill $RAND_PID 2>/dev/null
kill $MIXED_PID 2>/dev/null
kill $STRESS_PID 2>/dev/null

echo ""
echo "=== Data Collected ==="
LATEST_DIR=$(find data -name "memory_data_*" -type d | sort | tail -1)
if [ -n "$LATEST_DIR" ]; then
    echo "Data location: $LATEST_DIR"
    echo "Sample count: $(ls $LATEST_DIR/meminfo_*.txt 2>/dev/null | wc -l)"
    echo "Total files: $(ls $LATEST_DIR/*.txt 2>/dev/null | wc -l)"
    
    # Show some sample data
    echo ""
    echo "=== Sample Data ==="
    if [ -f "$LATEST_DIR/collection_info.txt" ]; then
        cat "$LATEST_DIR/collection_info.txt"
    fi
else
    echo "No data directory found!"
fi

echo ""
echo "Use './scripts/analyze_basic_data.sh' to analyze the collected data"
