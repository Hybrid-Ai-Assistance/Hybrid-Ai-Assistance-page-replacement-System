#!/bin/bash

# Get the absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"
mkdir -p "$DATA_DIR"

LOG_DIR="$DATA_DIR/memory_data_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

DURATION=300    # 5 minutes for real collection
INTERVAL=1      # 1 second intervals

echo "=== Page Replacement Data Collection (No Sudo) ==="
echo "Duration: $DURATION seconds"
echo "Interval: $INTERVAL second"
echo "Log Directory: $LOG_DIR"
echo "Started at: $(date)"
echo "=================================================="

# Create header file with collection info
cat > "$LOG_DIR/collection_info.txt" << INFO
Page Replacement Data Collection (No Sudo)
Start Time: $(date)
Duration: $DURATION seconds
Interval: $INTERVAL second
VM Info: $(uname -a)
Memory: $(grep MemTotal /proc/meminfo)
INFO

for ((i=1; i<=DURATION; i++)); do
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    echo "[$i/$DURATION] Collecting sample at $TIMESTAMP..."
    
    # Collect data that doesn't require sudo
    # 1. System memory information
    cat /proc/meminfo > "$LOG_DIR/meminfo_$TIMESTAMP.txt"
    
    # 2. Virtual memory statistics (includes page faults!)
    cat /proc/vmstat > "$LOG_DIR/vmstat_$TIMESTAMP.txt"
    
    # 3. Process-level page faults
    echo "PID    PPID   Minor-Faults Major-Faults RSS(KB) Command" > "$LOG_DIR/process_faults_$TIMESTAMP.txt"
    ps -eo pid,ppid,minflt,majflt,rss,comm --sort=-majflt --no-headers | head -20 >> "$LOG_DIR/process_faults_$TIMESTAMP.txt"
    
    # 4. Detailed VM statistics
    vmstat -w > "$LOG_DIR/vmstat_detailed_$TIMESTAMP.txt"
    
    # 5. System load
    uptime > "$LOG_DIR/loadavg_$TIMESTAMP.txt"
    cat /proc/loadavg >> "$LOG_DIR/loadavg_$TIMESTAMP.txt"
    
    # 6. I/O statistics (if accessible)
    cat /proc/diskstats 2>/dev/null > "$LOG_DIR/diskstats_$TIMESTAMP.txt" || echo "No diskstats" > "$LOG_DIR/diskstats_$TIMESTAMP.txt"
    
    # 7. Current running processes for context
    ps aux --sort=-%mem | head -10 > "$LOG_DIR/top_processes_$TIMESTAMP.txt"
    
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
