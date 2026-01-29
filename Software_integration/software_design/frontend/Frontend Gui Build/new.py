import psutil
import sys
import os
import re
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

class RealTimeProcessManager:
    """Real-time process manager with advanced tracking including swap info"""
    
    def __init__(self):
        self.previous_processes = {}
        self.process_cache = []
        self.update_count = 0
        self.cpu_history = {}
        self.memory_history = {}
        self.swap_info = {}
        
    def get_memory_usage(self, memory_info):
        """Universal memory usage calculation"""
        try:
            if hasattr(memory_info, 'working_set'):
                return memory_info.working_set
            elif hasattr(memory_info, 'rss'):
                return memory_info.rss
            else:
                return getattr(memory_info, list(memory_info._fields)[0])
        except:
            return 0

    def get_swap_info(self):
        """Get swap information from /proc/swaps and process swap usage"""
        swap_data = {}
        try:
            # Read /proc/swaps
            with open('/proc/swaps', 'r') as f:
                lines = f.readlines()
                # Skip header line
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 5:
                        swap_file = parts[0]
                        swap_type = parts[1]
                        swap_size = int(parts[2]) * 1024  # Convert to bytes
                        swap_used = int(parts[3]) * 1024  # Convert to bytes
                        swap_priority = parts[4] if len(parts) > 4 else "-"
                        
                        swap_data[swap_file] = {
                            'type': swap_type,
                            'size_bytes': swap_size,
                            'used_bytes': swap_used,
                            'free_bytes': swap_size - swap_used,
                            'usage_percent': (swap_used / swap_size * 100) if swap_size > 0 else 0,
                            'priority': swap_priority
                        }
            
            # Get per-process swap usage from /proc/*/smaps
            process_swap_usage = {}
            for proc_dir in Path('/proc').glob('[0-9]*'):
                try:
                    pid = int(proc_dir.name)
                    swap_used = 0
                    
                    # Read smaps file to get swap usage for this process
                    smaps_file = proc_dir / 'smaps'
                    if smaps_file.exists():
                        with open(smaps_file, 'r') as f:
                            content = f.read()
                            # Extract Swap usage from smaps
                            swap_matches = re.findall(r'Swap:\s+(\d+)\s*kB', content)
                            for match in swap_matches:
                                swap_used += int(match) * 1024  # Convert to bytes
                    
                    if swap_used > 0:
                        process_swap_usage[pid] = swap_used
                        
                except (PermissionError, FileNotFoundError, ValueError):
                    continue
            
            return {
                'swap_devices': swap_data,
                'process_swap_usage': process_swap_usage,
                'total_swap_used': sum(swap_data[dev]['used_bytes'] for dev in swap_data),
                'total_swap_size': sum(swap_data[dev]['size_bytes'] for dev in swap_data)
            }
            
        except Exception as e:
            print(f"Error reading swap info: {e}")
            return {'swap_devices': {}, 'process_swap_usage': {}, 'total_swap_used': 0, 'total_swap_size': 0}

    def get_process_details_from_proc(self, pid):
        """Get detailed process information from /proc filesystem"""
        try:
            proc_path = Path(f'/proc/{pid}')
            status_file = proc_path / 'status'
            cmdline_file = proc_path / 'cmdline'
            
            process_details = {
                'name': '',
                'state': '',
                'ppid': 0,
                'vm_size': 0,
                'vm_rss': 0,
                'vm_swap': 0,
                'full_cmd': ''
            }
            
            # Read status file
            if status_file.exists():
                with open(status_file, 'r') as f:
                    for line in f:
                        if line.startswith('Name:'):
                            process_details['name'] = line.split(':', 1)[1].strip()
                        elif line.startswith('State:'):
                            process_details['state'] = line.split(':', 1)[1].strip()
                        elif line.startswith('PPid:'):
                            process_details['ppid'] = int(line.split(':', 1)[1].strip())
                        elif line.startswith('VmSize:'):
                            process_details['vm_size'] = int(line.split(':')[1].strip().split()[0]) * 1024
                        elif line.startswith('VmRSS:'):
                            process_details['vm_rss'] = int(line.split(':')[1].strip().split()[0]) * 1024
                        elif line.startswith('VmSwap:'):
                            process_details['vm_swap'] = int(line.split(':')[1].strip().split()[0]) * 1024
            
            # Read command line
            if cmdline_file.exists():
                with open(cmdline_file, 'r') as f:
                    cmdline = f.read().replace('\x00', ' ').strip()
                    process_details['full_cmd'] = cmdline if cmdline else process_details['name']
            
            return process_details
            
        except Exception as e:
            print(f"Error reading /proc/{pid}: {e}")
            return None

    def get_changed_processes(self):
        """Get processes with real-time tracking data including swap info"""
        current_processes = {}
        changed_processes = []
        
        try:
            # Update swap information
            self.swap_info = self.get_swap_info()
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'status', 'username']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    cpu_percent = proc.info['cpu_percent'] or 0
                    status = proc.info['status']
                    username = proc.info['username'] or "Unknown"
                    
                    memory_bytes = self.get_memory_usage(proc.info['memory_info'])
                    memory_mb = memory_bytes / 1024 / 1024
                    
                    if memory_mb < 0.1:
                        continue
                    
                    # Get detailed info from /proc
                    proc_details = self.get_process_details_from_proc(pid)
                    if proc_details:
                        name = proc_details['name']
                    
                    # Get swap usage for this process
                    swap_usage_bytes = self.swap_info['process_swap_usage'].get(pid, 0)
                    swap_usage_mb = swap_usage_bytes / 1024 / 1024
                    
                    # Track CPU history for sparklines
                    if pid not in self.cpu_history:
                        self.cpu_history[pid] = []
                    self.cpu_history[pid].append(cpu_percent)
                    if len(self.cpu_history[pid]) > 10:
                        self.cpu_history[pid].pop(0)
                    
                    # Track memory history
                    if pid not in self.memory_history:
                        self.memory_history[pid] = []
                    self.memory_history[pid].append(memory_mb)
                    if len(self.memory_history[pid]) > 10:
                        self.memory_history[pid].pop(0)
                    
                    current_process = {
                        'pid': pid,
                        'name': name,
                        'memory_mb': memory_mb,
                        'cpu_percent': cpu_percent,
                        'status': status,
                        'username': username,
                        'swap_usage_mb': swap_usage_mb,
                        'cpu_history': self.cpu_history[pid][-5:],  # Last 5 values
                        'memory_trend': self.get_memory_trend(pid),
                        'cpu_trend': self.get_cpu_trend(pid),
                        'activity_level': self.get_activity_level(pid),
                        'proc_details': proc_details
                    }
                    
                    current_processes[pid] = current_process
                    
                    # Check for changes
                    if pid not in self.previous_processes:
                        current_process['type'] = 'new'
                        changed_processes.append(current_process)
                    else:
                        prev = self.previous_processes[pid]
                        if (abs(memory_mb - prev['memory_mb']) > 0.5 or 
                            abs(cpu_percent - prev['cpu_percent']) > 1.0 or
                            abs(swap_usage_mb - prev.get('swap_usage_mb', 0)) > 0.1):
                            current_process['type'] = 'updated'
                            changed_processes.append(current_process)
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    continue
            
            # Find removed processes
            removed_pids = set(self.previous_processes.keys()) - set(current_processes.keys())
            for pid in removed_pids:
                changed_processes.append({'pid': pid, 'type': 'removed'})
                # Cleanup history
                if pid in self.cpu_history:
                    del self.cpu_history[pid]
                if pid in self.memory_history:
                    del self.memory_history[pid]
            
            self.previous_processes = current_processes
            self.process_cache = list(current_processes.values())
            self.update_count += 1
            
        except Exception as e:
            print(f"Error in real-time update: {e}")
        
        return changed_processes
    
    def get_memory_trend(self, pid):
        """Calculate memory trend (increasing/decreasing/stable)"""
        if pid not in self.memory_history or len(self.memory_history[pid]) < 2:
            return "stable"
        history = self.memory_history[pid]
        if history[-1] > history[-2] + 1.0:
            return "increasing"
        elif history[-1] < history[-2] - 1.0:
            return "decreasing"
        return "stable"
    
    def get_cpu_trend(self, pid):
        """Calculate CPU trend"""
        if pid not in self.cpu_history or len(self.cpu_history[pid]) < 2:
            return "stable"
        history = self.cpu_history[pid]
        if history[-1] > history[-2] + 5.0:
            return "increasing"
        elif history[-1] < history[-2] - 5.0:
            return "decreasing"
        return "stable"
    
    def get_activity_level(self, pid):
        """Determine activity level based on recent CPU usage"""
        if pid not in self.cpu_history:
            return "low"
        recent_cpu = self.cpu_history[pid][-3:] if len(self.cpu_history[pid]) >= 3 else self.cpu_history[pid]
        avg_cpu = sum(recent_cpu) / len(recent_cpu)
        if avg_cpu > 30:
            return "high"
        elif avg_cpu > 10:
            return "medium"
        return "low"
    
    def get_all_processes(self):
        """Get all processes with real-time data"""
        return self.process_cache
    
    def get_swap_summary(self):
        """Get swap summary information"""
        return self.swap_info

class SortableTableWidget(QTableWidget):
    """Enhanced table with Task Manager-like sorting"""
    
    def __init__(self):
        super().__init__()
        self.sort_order = {}
        self.current_sort_column = 2  # Default sort by Memory
        self.current_sort_order = Qt.DescendingOrder
        
    def setup_sorting(self):
        """Setup column sorting"""
        self.horizontalHeader().sectionClicked.connect(self.sort_table)
        
    def sort_table(self, column):
        """Sort table by column with visual indicators"""
        if column == self.current_sort_column:
            # Toggle order
            self.current_sort_order = Qt.DescendingOrder if self.current_sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.current_sort_column = column
            self.current_sort_order = Qt.DescendingOrder
        
        self.sortItems(column, self.current_sort_order)
        self.update_sort_indicators()
    
    def update_sort_indicators(self):
        """Update sort indicators in header"""
        header = self.horizontalHeader()
        for i in range(header.count()):
            header.setSortIndicator(i, Qt.NoOrder)
        header.setSortIndicator(self.current_sort_column, self.current_sort_order)

class TaskManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Task Manager - Real Time Monitor with Swap Info")
        self.setMinimumSize(1400, 800)
        
        # Real-time manager
        self.process_manager = RealTimeProcessManager()
        self.is_auto_refresh = True
        self.process_row_map = {}
        self.sort_column = 2  # Memory column
        self.sort_order = Qt.DescendingOrder
        
        self._setup_ui()
        self.setup_real_time_updates()

    def setup_real_time_updates(self):
        """Setup real-time updates"""
        QTimer.singleShot(100, self.refresh_processes_full)
        
        # Real-time updates
        self.real_time_timer = QTimer()
        self.real_time_timer.timeout.connect(self.refresh_processes_real_time)
        self.real_time_timer.start(2000)  # 2 seconds
        
        # Performance metrics
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_performance_metrics)
        self.metrics_timer.start(1000)

    def _setup_ui(self):
        """Setup Task Manager-like UI"""
        self._setup_toolbar()
        self._setup_tabs()
        self._setup_statusbar()

    def _setup_toolbar(self):
        """Setup Task Manager toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # View options
        view_menu = QComboBox()
        view_menu.addItems(["All Processes", "Apps Only", "Background Processes", "High Memory", "High Swap"])
        view_menu.currentTextChanged.connect(self.change_view)
        toolbar.addWidget(QLabel("View:"))
        toolbar.addWidget(view_menu)

        toolbar.addSeparator()

        # Refresh controls
        self.refresh_btn = QPushButton("🔄 Refresh Now")
        self.refresh_btn.clicked.connect(self.refresh_processes_full)
        toolbar.addWidget(self.refresh_btn)

        self.auto_refresh_btn = QPushButton("⏸️ Pause")
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setChecked(True)
        self.auto_refresh_btn.toggled.connect(self.toggle_auto_refresh)
        toolbar.addWidget(self.auto_refresh_btn)

        toolbar.addSeparator()

        # Search
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search processes...")
        self.search_box.textChanged.connect(self.filter_processes)
        self.search_box.setMinimumWidth(200)
        toolbar.addWidget(self.search_box)

    def _setup_tabs(self):
        """Setup tabs like Task Manager"""
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self._setup_processes_tab()
        self._setup_performance_tab()
        self._setup_swap_tab()

    def _setup_processes_tab(self):
        """Setup processes tab with Task Manager styling"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create sortable table
        self.table = SortableTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Name", "PID", "Memory (MB) ▲", "CPU %", "Swap (MB)", "Status", "User", "Trend", "Activity"
        ])
        
        # Configure header
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # PID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Memory
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # CPU
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Swap
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # User
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Trend
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Activity
        
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.setup_sorting()
        
        # Set initial sort by Memory descending
        self.table.sortItems(2, Qt.DescendingOrder)
        
        layout.addWidget(self.table)

        # Bottom info bar
        self._setup_info_bar(layout)

        self.tabs.addTab(tab, "Processes")

    def _setup_swap_tab(self):
        """Setup swap information tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)

        # Swap summary
        summary_group = QGroupBox("Swap Summary")
        summary_layout = QGridLayout(summary_group)
        
        self.total_swap_label = QLabel("Total Swap: 0 MB")
        self.used_swap_label = QLabel("Used Swap: 0 MB")
        self.free_swap_label = QLabel("Free Swap: 0 MB")
        self.swap_usage_label = QLabel("Swap Usage: 0%")
        
        for label in [self.total_swap_label, self.used_swap_label, 
                     self.free_swap_label, self.swap_usage_label]:
            label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        summary_layout.addWidget(self.total_swap_label, 0, 0)
        summary_layout.addWidget(self.used_swap_label, 0, 1)
        summary_layout.addWidget(self.free_swap_label, 1, 0)
        summary_layout.addWidget(self.swap_usage_label, 1, 1)
        
        layout.addWidget(summary_group)

        # Swap devices table
        devices_group = QGroupBox("Swap Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        self.swap_table = QTableWidget()
        self.swap_table.setColumnCount(5)
        self.swap_table.setHorizontalHeaderLabels([
            "Device/File", "Type", "Size (MB)", "Used (MB)", "Usage %"
        ])
        
        devices_layout.addWidget(self.swap_table)
        layout.addWidget(devices_group)

        # Top swap using processes
        processes_group = QGroupBox("Top Swap Using Processes")
        processes_layout = QVBoxLayout(processes_group)
        
        self.top_swap_table = QTableWidget()
        self.top_swap_table.setColumnCount(4)
        self.top_swap_table.setHorizontalHeaderLabels([
            "Process Name", "PID", "Swap Usage (MB)", "Command"
        ])
        
        processes_layout.addWidget(self.top_swap_table)
        layout.addWidget(processes_group)

        layout.addStretch()
        self.tabs.addTab(tab, "Swap Info")

    def _setup_info_bar(self, layout):
        """Setup Task Manager-like info bar"""
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(10, 5, 10, 5)
        
        self.process_count_label = QLabel("Processes: 0")
        self.thread_count_label = QLabel("Threads: 0")
        self.cpu_usage_label = QLabel("CPU Usage: 0%")
        self.memory_usage_label = QLabel("Memory: 0 MB")
        self.swap_usage_label = QLabel("Swap: 0 MB")
        self.uptime_label = QLabel("Up time: 0s")
        
        # Style like Task Manager
        for label in [self.process_count_label, self.thread_count_label, 
                     self.cpu_usage_label, self.memory_usage_label, 
                     self.swap_usage_label, self.uptime_label]:
            label.setStyleSheet("font-weight: bold;")
        
        info_layout.addWidget(self.process_count_label)
        info_layout.addWidget(self.thread_count_label)
        info_layout.addWidget(self.cpu_usage_label)
        info_layout.addWidget(self.memory_usage_label)
        info_layout.addWidget(self.swap_usage_label)
        info_layout.addWidget(self.uptime_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)

    def _setup_performance_tab(self):
        """Setup performance tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)

        # Performance metrics grid
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        # CPU
        metrics_layout.addWidget(QLabel("CPU:"), 0, 0)
        self.cpu_value = QLabel("0%")
        self.cpu_value.setStyleSheet("font-weight: bold; font-size: 16px; color: #0078d7;")
        metrics_layout.addWidget(self.cpu_value, 0, 1)
        
        # Memory
        metrics_layout.addWidget(QLabel("Memory:"), 0, 2)
        self.memory_value = QLabel("0%")
        self.memory_value.setStyleSheet("font-weight: bold; font-size: 16px; color: #e81123;")
        metrics_layout.addWidget(self.memory_value, 0, 3)
        
        # Swap
        metrics_layout.addWidget(QLabel("Swap:"), 0, 4)
        self.swap_percent_value = QLabel("0%")
        self.swap_percent_value.setStyleSheet("font-weight: bold; font-size: 16px; color: #ff6b00;")
        metrics_layout.addWidget(self.swap_percent_value, 0, 5)
        
        # Disk
        metrics_layout.addWidget(QLabel("Disk:"), 1, 0)
        self.disk_value = QLabel("0%")
        self.disk_value.setStyleSheet("font-weight: bold; font-size: 16px; color: #107c10;")
        metrics_layout.addWidget(self.disk_value, 1, 1)
        
        # Network
        metrics_layout.addWidget(QLabel("Network:"), 1, 2)
        self.network_value = QLabel("0 MB/s")
        self.network_value.setStyleSheet("font-weight: bold; font-size: 16px; color: #8e44ad;")
        metrics_layout.addWidget(self.network_value, 1, 3)
        
        layout.addWidget(metrics_group)
        layout.addStretch()

        self.tabs.addTab(tab, "Performance")

    def _setup_statusbar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready")
        self.update_count_label = QLabel("Updates: 0")
        self.refresh_rate_label = QLabel("Refresh: 2s")
        
        self.status_bar.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.update_count_label)
        self.status_bar.addPermanentWidget(self.refresh_rate_label)

    def refresh_processes_full(self):
        """Full refresh with sorting preservation"""
        self.status_label.setText("🔄 Full refresh...")
        
        try:
            processes = self.process_manager.get_all_processes()
            self.process_row_map.clear()
            
            # Suspend sorting during update
            self.table.setSortingEnabled(False)
            self.table.setRowCount(len(processes))
            
            total_memory = 0
            total_swap = 0
            total_threads = 0
            
            for row, process in enumerate(processes):
                self.process_row_map[process['pid']] = row
                self._add_process_to_table(row, process)
                total_memory += process['memory_mb']
                total_swap += process.get('swap_usage_mb', 0)
                total_threads += 1
            
            # Restore sorting
            self.table.setSortingEnabled(True)
            self.table.sortItems(self.sort_column, self.sort_order)
            
            # Update info
            self.process_count_label.setText(f"Processes: {len(processes)}")
            self.thread_count_label.setText(f"Threads: {total_threads}")
            self.memory_usage_label.setText(f"Memory: {total_memory:.0f} MB")
            self.swap_usage_label.setText(f"Swap: {total_swap:.0f} MB")
            self.status_label.setText("✅ Ready")
            
            # Update swap tab
            self.update_swap_tab()
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")

    def update_swap_tab(self):
        """Update swap information tab"""
        try:
            swap_info = self.process_manager.get_swap_summary()
            
            # Update summary
            total_swap_mb = swap_info['total_swap_size'] / 1024 / 1024
            used_swap_mb = swap_info['total_swap_used'] / 1024 / 1024
            free_swap_mb = total_swap_mb - used_swap_mb
            swap_usage_percent = (used_swap_mb / total_swap_mb * 100) if total_swap_mb > 0 else 0
            
            self.total_swap_label.setText(f"Total Swap: {total_swap_mb:.1f} MB")
            self.used_swap_label.setText(f"Used Swap: {used_swap_mb:.1f} MB")
            self.free_swap_label.setText(f"Free Swap: {free_swap_mb:.1f} MB")
            self.swap_usage_label.setText(f"Swap Usage: {swap_usage_percent:.1f}%")
            
            # Update swap devices table
            self.swap_table.setRowCount(len(swap_info['swap_devices']))
            for row, (device, info) in enumerate(swap_info['swap_devices'].items()):
                self.swap_table.setItem(row, 0, QTableWidgetItem(device))
                self.swap_table.setItem(row, 1, QTableWidgetItem(info['type']))
                self.swap_table.setItem(row, 2, QTableWidgetItem(f"{info['size_bytes']/1024/1024:.1f}"))
                self.swap_table.setItem(row, 3, QTableWidgetItem(f"{info['used_bytes']/1024/1024:.1f}"))
                self.swap_table.setItem(row, 4, QTableWidgetItem(f"{info['usage_percent']:.1f}%"))
            
            # Update top swap processes
            processes_with_swap = [(p['pid'], p.get('swap_usage_mb', 0), p['name'], p.get('proc_details', {}).get('full_cmd', '')) 
                                 for p in self.process_manager.get_all_processes() 
                                 if p.get('swap_usage_mb', 0) > 0]
            processes_with_swap.sort(key=lambda x: x[1], reverse=True)
            top_processes = processes_with_swap[:20]  # Top 20
            
            self.top_swap_table.setRowCount(len(top_processes))
            for row, (pid, swap_usage, name, cmd) in enumerate(top_processes):
                self.top_swap_table.setItem(row, 0, QTableWidgetItem(name))
                self.top_swap_table.setItem(row, 1, QTableWidgetItem(str(pid)))
                self.top_swap_table.setItem(row, 2, QTableWidgetItem(f"{swap_usage:.1f}"))
                self.top_swap_table.setItem(row, 3, QTableWidgetItem(cmd[:100] + "..." if len(cmd) > 100 else cmd))
                
        except Exception as e:
            print(f"Error updating swap tab: {e}")

    def refresh_processes_real_time(self):
        """Real-time incremental updates"""
        if not self.is_auto_refresh:
            return
        
        try:
            changed_processes = self.process_manager.get_changed_processes()
            
            if not changed_processes:
                return
            
            update_count = 0
            self.table.setSortingEnabled(False)
            
            for process in changed_processes:
                pid = process['pid']
                change_type = process.get('type', 'updated')
                
                if change_type == 'new':
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.process_row_map[pid] = row
                    self._add_process_to_table(row, process)
                    update_count += 1
                    
                elif change_type == 'removed':
                    if pid in self.process_row_map:
                        row = self.process_row_map[pid]
                        self.table.removeRow(row)
                        del self.process_row_map[pid]
                        self._update_row_mappings(row)
                        update_count += 1
                        
                elif change_type == 'updated':
                    if pid in self.process_row_map:
                        row = self.process_row_map[pid]
                        self._update_process_in_table(row, process)
                        update_count += 1
            
            self.table.setSortingEnabled(True)
            self.update_count_label.setText(f"Updates: {self.process_manager.update_count}")
            
            if update_count > 0:
                self.status_label.setText(f"🔄 Updated {update_count} processes")
                QTimer.singleShot(2000, lambda: self.status_label.setText("✅ Ready"))
            
            # Update swap info in real-time
            self.update_swap_tab()
            
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Real-time update error: {e}")

    def _add_process_to_table(self, row, process):
        """Add process to table with real-time data"""
        # Name
        name_item = QTableWidgetItem(process['name'])
        self.table.setItem(row, 0, name_item)
        
        # PID
        pid_item = QTableWidgetItem(str(process['pid']))
        self.table.setItem(row, 1, pid_item)
        
        # Memory with trend indicator
        memory_text = f"{process['memory_mb']:.1f}"
        if process['memory_trend'] == 'increasing':
            memory_text += " ↗"
        elif process['memory_trend'] == 'decreasing':
            memory_text += " ↘"
        memory_item = QTableWidgetItem(memory_text)
        self.table.setItem(row, 2, memory_item)
        
        # CPU with color coding
        cpu_item = QTableWidgetItem(f"{process['cpu_percent']:.1f}%")
        if process['cpu_percent'] > 50:
            cpu_item.setBackground(QColor(255, 200, 200))
        elif process['cpu_percent'] > 20:
            cpu_item.setBackground(QColor(255, 235, 156))
        self.table.setItem(row, 3, cpu_item)
        
        # Swap usage
        swap_item = QTableWidgetItem(f"{process.get('swap_usage_mb', 0):.1f}")
        if process.get('swap_usage_mb', 0) > 10:
            swap_item.setForeground(QColor(200, 0, 0))
        self.table.setItem(row, 4, swap_item)
        
        # Status
        status_item = QTableWidgetItem(process['status'])
        self.table.setItem(row, 5, status_item)
        
        # User
        user_item = QTableWidgetItem(process['username'].split('\\')[-1] if '\\' in process['username'] else process['username'])
        self.table.setItem(row, 6, user_item)
        
        # Trend
        trend_item = QTableWidgetItem()
        if process['cpu_trend'] == 'increasing' or process['memory_trend'] == 'increasing':
            trend_item.setText("📈 High")
            trend_item.setForeground(QColor(200, 0, 0))
        elif process['cpu_trend'] == 'decreasing' and process['memory_trend'] == 'decreasing':
            trend_item.setText("📉 Low")
            trend_item.setForeground(QColor(0, 150, 0))
        else:
            trend_item.setText("➡️ Stable")
        self.table.setItem(row, 7, trend_item)
        
        # Activity
        activity_item = QTableWidgetItem()
        if process['activity_level'] == 'high':
            activity_item.setText("🔴 High")
        elif process['activity_level'] == 'medium':
            activity_item.setText("🟡 Medium")
        else:
            activity_item.setText("🟢 Low")
        self.table.setItem(row, 8, activity_item)

    def _update_process_in_table(self, row, process):
        """Update process data in table"""
        # Update memory with trend
        memory_text = f"{process['memory_mb']:.1f}"
        if process['memory_trend'] == 'increasing':
            memory_text += " ↗"
        elif process['memory_trend'] == 'decreasing':
            memory_text += " ↘"
        self.table.item(row, 2).setText(memory_text)
        
        # Update CPU
        cpu_item = self.table.item(row, 3)
        cpu_item.setText(f"{process['cpu_percent']:.1f}%")
        if process['cpu_percent'] > 50:
            cpu_item.setBackground(QColor(255, 200, 200))
        elif process['cpu_percent'] > 20:
            cpu_item.setBackground(QColor(255, 235, 156))
        else:
            cpu_item.setBackground(QColor(255, 255, 255))
        
        # Update swap
        swap_item = self.table.item(row, 4)
        swap_item.setText(f"{process.get('swap_usage_mb', 0):.1f}")
        if process.get('swap_usage_mb', 0) > 10:
            swap_item.setForeground(QColor(200, 0, 0))
        else:
            swap_item.setForeground(QColor(0, 0, 0))
        
        # Update status if changed
        self.table.item(row, 5).setText(process['status'])
        
        # Update trend
        trend_item = self.table.item(row, 7)
        if process['cpu_trend'] == 'increasing' or process['memory_trend'] == 'increasing':
            trend_item.setText("📈 High")
            trend_item.setForeground(QColor(200, 0, 0))
        elif process['cpu_trend'] == 'decreasing' and process['memory_trend'] == 'decreasing':
            trend_item.setText("📉 Low")
            trend_item.setForeground(QColor(0, 150, 0))
        else:
            trend_item.setText("➡️ Stable")
            trend_item.setForeground(QColor(0, 0, 0))
        
        # Update activity
        activity_item = self.table.item(row, 8)
        if process['activity_level'] == 'high':
            activity_item.setText("🔴 High")
        elif process['activity_level'] == 'medium':
            activity_item.setText("🟡 Medium")
        else:
            activity_item.setText("🟢 Low")

    def _update_row_mappings(self, removed_row):
        """Update row mappings after removal"""
        for pid, row in list(self.process_row_map.items()):
            if row > removed_row:
                self.process_row_map[pid] = row - 1

    def update_performance_metrics(self):
        """Update real-time performance metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_value.setText(f"{cpu_percent:.1f}%")
            self.cpu_usage_label.setText(f"CPU: {cpu_percent:.1f}%")
            
            # Memory
            memory = psutil.virtual_memory()
            self.memory_value.setText(f"{memory.percent:.1f}%")
            
            # Swap
            swap = psutil.swap_memory()
            self.swap_percent_value.setText(f"{swap.percent:.1f}%")
            
            # Disk
            disk = psutil.disk_usage('/')
            self.disk_value.setText(f"{disk.percent:.1f}%")
            
            # Uptime
            uptime = psutil.boot_time()
            self.uptime_label.setText(f"Up time: {int(uptime)}s")
            
        except Exception as e:
            print(f"Metrics error: {e}")

    def change_view(self, view):
        """Change process view"""
        self.status_label.setText(f"View: {view}")
        # View filtering logic can be added here
        if view == "High Swap":
            self.filter_high_swap_processes()
        elif view == "High Memory":
            self.filter_high_memory_processes()
        else:
            self.clear_filters()

    def filter_high_swap_processes(self):
        """Show only processes with high swap usage"""
        for row in range(self.table.rowCount()):
            swap_item = self.table.item(row, 4)
            if swap_item:
                swap_usage = float(swap_item.text())
                self.table.setRowHidden(row, swap_usage < 1.0)

    def filter_high_memory_processes(self):
        """Show only processes with high memory usage"""
        for row in range(self.table.rowCount()):
            memory_item = self.table.item(row, 2)
            if memory_item:
                memory_text = memory_item.text().replace('↗', '').replace('↘', '').strip()
                memory_usage = float(memory_text)
                self.table.setRowHidden(row, memory_usage < 10.0)

    def clear_filters(self):
        """Clear all filters"""
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)

    def toggle_auto_refresh(self, checked):
        """Toggle auto-refresh"""
        self.is_auto_refresh = checked
        if checked:
            self.real_time_timer.start(2000)
            self.auto_refresh_btn.setText("⏸️ Pause")
            self.status_label.setText("🔄 Real-time monitoring")
        else:
            self.real_time_timer.stop()
            self.auto_refresh_btn.setText("▶️ Resume")
            self.status_label.setText("⏸️ Monitoring paused")

    def filter_processes(self):
        """Filter processes based on search"""
        search_text = self.search_box.text().lower()
        for row in range(self.table.rowCount()):
            should_show = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            self.table.setRowHidden(row, not should_show)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        import psutil
        window = TaskManagerWindow()
        window.show()
        sys.exit(app.exec())
    except ImportError:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("psutil library required")
        msg.setInformativeText("Please install: pip install psutil")
        msg.exec()