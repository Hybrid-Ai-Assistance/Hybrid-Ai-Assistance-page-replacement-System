#!/bin/bash

# Configuration
LOG_DIR="../data/memory_data_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

DURATION=300    # 5 minutes collection
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
    
    # 2. Virtual memory statistics (page faults, swaps, etc.)
    cat /proc/vmstat > "$LOG_DIR/vmstat_$TIMESTAMP.txt"
    
    # 3. Process-level page faults (top 20 processes)
    echo "PID    PPID   Minor-Faults Major-Faults RSS(KB) Command" > "$LOG_DIR/process_faults_$TIMESTAMP.txt"
    ps -eo pid,ppid,minflt,majflt,rss,comm --sort=-majflt --no-headers | head -20 >> "$LOG_DIR/process_faults_$TIMESTAMP.txt"
    
    # 4. Kernel slab information (caches)
    cat /proc/slabinfo | head -30 > "$LOG_DIR/slabinfo_$TIMESTAMP.txt"
    
    # 5. Detailed VM statistics
    vmstat -w > "$LOG_DIR/vmstat_detailed_$TIMESTAMP.txt"
    
    # 6. I/O statistics
    cat /proc/diskstats > "$LOG_DIR/diskstats_$TIMESTAMP.txt"
    
    # 7. CPU and system load
    uptime > "$LOG_DIR/loadavg_$TIMESTAMP.txt"
    cat /proc/loadavg >> "$LOG_DIR/loadavg_$TIMESTAMP.txt"
    
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
echo "Use './scripts/analyze_basic_data.sh' to analyze the data"
