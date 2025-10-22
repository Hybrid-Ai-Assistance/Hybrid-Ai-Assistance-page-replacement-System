#!/bin/bash

# Get the absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"
mkdir -p "$DATA_DIR"

LOG_DIR="$DATA_DIR/memory_data_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

DURATION=60    # 1 minute for testing (change to 300 for full collection)
INTERVAL=1      # 1 second intervals

echo "=== Page Replacement Data Collection ==="
echo "Duration: $DURATION seconds"
echo "Interval: $INTERVAL second"
echo "Log Directory: $LOG_DIR"
echo "Started at: $(date)"
echo "========================================"

# Create header file with collection info
cat > "$LOG_DIR/collection_info.txt" << INFO
Page Replacement Data Collection
Start Time: $(date)
Duration: $DURATION seconds
Interval: $INTERVAL second
VM Info: $(uname -a)
Memory: $(grep MemTotal /proc/meminfo)
INFO

for ((i=1; i<=DURATION; i++)); do
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    echo "[$i/$DURATION] Collecting sample at $TIMESTAMP..."
    
    # 1. System memory information
    cat /proc/meminfo > "$LOG_DIR/meminfo_$TIMESTAMP.txt"
    
    # 2. Virtual memory statistics
    cat /proc/vmstat > "$LOG_DIR/vmstat_$TIMESTAMP.txt"
    
    # 3. Process-level page faults
    echo "PID    PPID   Minor-Faults Major-Faults RSS(KB) Command" > "$LOG_DIR/process_faults_$TIMESTAMP.txt"
    ps -eo pid,ppid,minflt,majflt,rss,comm --sort=-majflt --no-headers | head -20 >> "$LOG_DIR/process_faults_$TIMESTAMP.txt"
    
    # 4. Kernel slab information
    cat /proc/slabinfo | head -30 > "$LOG_DIR/slabinfo_$TIMESTAMP.txt"
    
    # 5. Detailed VM statistics
    vmstat -w > "$LOG_DIR/vmstat_detailed_$TIMESTAMP.txt"
    
    sleep $INTERVAL
done

# Create summary file
echo "=== Collection Summary ===" > "$LOG_DIR/summary.txt"
echo "Total samples collected: $DURATION" >> "$LOG_DIR/summary.txt"
echo "End time: $(date)" >> "$LOG_DIR/summary.txt"
echo "Data size: $(du -sh "$LOG_DIR")" >> "$LOG_DIR/summary.txt"

echo ""
echo "=== Data Collection Complete ==="
echo "Data saved in: $LOG_DIR"
echo "Total samples: $DURATION"
