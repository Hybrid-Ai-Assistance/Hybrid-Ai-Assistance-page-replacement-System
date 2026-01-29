#!/bin/bash

echo "=== Testing Project Setup ==="

# Check if we're in the right directory
if [ ! -d "workloads" ] || [ ! -d "scripts" ]; then
    echo "ERROR: Please run this script from the project root directory"
    exit 1
fi

echo "✓ Project structure is correct"

# Test compiling workloads
echo ""
echo "=== Testing Workload Compilation ==="
cd workloads
gcc sequential_access.c -o sequential_access -O2
if [ $? -eq 0 ]; then
    echo "✓ sequential_access compiled successfully"
else
    echo "✗ sequential_access compilation failed"
fi

gcc random_access.c -o random_access -O2
if [ $? -eq 0 ]; then
    echo "✓ random_access compiled successfully"
else
    echo "✗ random_access compilation failed"
fi

gcc mixed_workload.c -o mixed_workload -O2
if [ $? -eq 0 ]; then
    echo "✓ mixed_workload compiled successfully"
else
    echo "✗ mixed_workload compilation failed"
fi

# Test running a workload
echo ""
echo "=== Testing Workload Execution ==="
./sequential_access &
PID=$!
sleep 2
if ps -p $PID > /dev/null; then
    echo "✓ Workload ran successfully (PID: $PID)"
    kill $PID 2>/dev/null
else
    echo "✗ Workload failed to run"
fi

cd ..

echo ""
echo "=== Testing Data Collection ==="
./scripts/collect_basic_data_fixed.sh &
sleep 5

if ps aux | grep -q "collect_basic_data_fixed"; then
    echo "✓ Data collection is running"
    # Stop it after test
    pkill -f collect_basic_data_fixed
    sleep 2
else
    echo "✗ Data collection failed to start"
fi

echo ""
echo "=== Setup Test Complete ==="
