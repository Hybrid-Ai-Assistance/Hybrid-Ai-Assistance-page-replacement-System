#!/bin/bash

LATEST_DIR=$(find data -name "memory_data_*" -type d | sort | tail -1)

if [ -z "$LATEST_DIR" ]; then
    echo "No data found! Run the experiment first."
    exit 1
fi

echo "=== QUICK DATA ANALYSIS ==="
echo "Data directory: $LATEST_DIR"

# Count samples
SAMPLE_COUNT=$(ls $LATEST_DIR/meminfo_*.txt 2>/dev/null | wc -l)
echo "Samples collected: $SAMPLE_COUNT"

# Extract page fault trends
echo ""
echo "=== PAGE FAULT ANALYSIS ==="
for file in $(ls $LATEST_DIR/vmstat_*.txt | head -5); do
    timestamp=$(basename $file | cut -d'_' -f2 | cut -d'.' -f1)
    pgfault=$(grep "pgfault" $file | awk '{print $2}')
    pgmajfault=$(grep "pgmajfault" $file | awk '{print $2}')
    echo "Time: $timestamp - Minor: $pgfault, Major: $pgmajfault"
done

# Show memory usage trend
echo ""
echo "=== MEMORY USAGE ==="
for file in $(ls $LATEST_DIR/meminfo_*.txt | head -5); do
    timestamp=$(basename $file | cut -d'_' -f2 | cut -d'.' -f1)
    available=$(grep "MemAvailable" $file | awk '{print $2}')
    echo "Time: $timestamp - Available: ${available}KB"
done

# Process fault summary
echo ""
echo "=== PROCESS FAULT SUMMARY ==="
echo "Top faulting processes during experiment:"
cat $LATEST_DIR/process_faults_*.txt 2>/dev/null | awk '{print $6, $4}' | sort | uniq -c | sort -rn | head -10
