#!/bin/bash

DATA_DIR="../data"
LATEST_DIR=$(find "$DATA_DIR" -name "memory_data_*" -type d | sort | tail -1)

if [ -z "$LATEST_DIR" ]; then
    echo "Error: No data directory found in $DATA_DIR"
    echo "Please run './scripts/collect_basic_data.sh' first"
    exit 1
fi

echo "=== Analyzing Data from: $LATEST_DIR ==="

# Create analysis directory
ANALYSIS_DIR="${LATEST_DIR}_analysis"
mkdir -p "$ANALYSIS_DIR"

echo "Creating analysis reports..."

# 1. Extract key metrics over time
echo "Timestamp,AvailableMemory,PageFaults,MajorFaults" > "$ANALYSIS_DIR/memory_timeline.csv"

for memfile in "$LATEST_DIR"/meminfo_*.txt; do
    timestamp=$(basename "$memfile" | cut -d'_' -f2 | cut -d'.' -f1)
    
    available_mem=$(grep "MemAvailable" "$memfile" | awk '{print $2}')
    page_faults=$(grep "pgfault" "$LATEST_DIR/vmstat_${timestamp}.txt" 2>/dev/null | awk '{print $2}' || echo "0")
    major_faults=$(grep "pgmajfault" "$LATEST_DIR/vmstat_${timestamp}.txt" 2>/dev/null | awk '{print $2}' || echo "0")
    
    echo "$timestamp,$available_mem,$page_faults,$major_faults" >> "$ANALYSIS_DIR/memory_timeline.csv"
done

# 2. Create summary report
cat > "$ANALYSIS_DIR/summary_report.txt" << REPORT
Page Replacement Data Analysis Report
=====================================
Data Directory: $LATEST_DIR
Analysis Time: $(date)

Summary Statistics:
------------------

REPORT

# Calculate basic statistics
total_samples=$(ls "$LATEST_DIR"/meminfo_*.txt | wc -l)
echo "Total samples analyzed: $total_samples" >> "$ANALYSIS_DIR/summary_report.txt"

# Process fault statistics
if [ -f "$ANALYSIS_DIR/memory_timeline.csv" ]; then
    avg_faults=$(tail -n +2 "$ANALYSIS_DIR/memory_timeline.csv" | awk -F',' '{sum+=$3} END {print sum/NR}')
    avg_major_faults=$(tail -n +2 "$ANALYSIS_DIR/memory_timeline.csv" | awk -F',' '{sum+=$4} END {print sum/NR}')
    
    echo "Average page faults per second: $avg_faults" >> "$ANALYSIS_DIR/summary_report.txt"
    echo "Average major faults per second: $avg_major_faults" >> "$ANALYSIS_DIR/summary_report.txt"
fi

# 3. Create simple visualization data
cat > "$ANALYSIS_DIR/visualization_data.js" << JS
// Data for simple visualization
const memoryData = [
JS

tail -n +2 "$ANALYSIS_DIR/memory_timeline.csv" | while IFS=',' read timestamp available faults major; do
    echo "  {timestamp: '$timestamp', available: $available, faults: $faults, majorFaults: $major}," >> "$ANALYSIS_DIR/visualization_data.js"
done

cat >> "$ANALYSIS_DIR/visualization_data.js" << JS
];
JS

echo ""
echo "=== Analysis Complete ==="
echo "Analysis saved in: $ANALYSIS_DIR"
echo ""
echo "Files created:"
echo "- memory_timeline.csv: Timeline of memory usage and faults"
echo "- summary_report.txt: Statistical summary"
echo "- visualization_data.js: Data for web visualization"
echo ""
echo "To view basic stats: cat $ANALYSIS_DIR/summary_report.txt"
