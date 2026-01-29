import psutil
import sys
import os
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

class RealTimeProcessManager:
    """Real-time process manager with advanced tracking"""
    
    def __init__(self):
        self.previous_processes = {}
        self.process_cache = []
        self.update_count = 0
        self.cpu_history = {}
        self.memory_history = {}
        
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

    def get_changed_processes(self):
        """Get processes with real-time tracking data"""
        current_processes = {}
        changed_processes = []
        
        try:
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
                        'cpu_history': self.cpu_history[pid][-5:],  # Last 5 values
                        'memory_trend': self.get_memory_trend(pid),
                        'cpu_trend': self.get_cpu_trend(pid),
                        'activity_level': self.get_activity_level(pid)
                    }
                    
                    current_processes[pid] = current_process
                    
                    # Check for changes
                    if pid not in self.previous_processes:
                        current_process['type'] = 'new'
                        changed_processes.append(current_process)
                    else:
                        prev = self.previous_processes[pid]
                        if (abs(memory_mb - prev['memory_mb']) > 0.5 or 
                            abs(cpu_percent - prev['cpu_percent']) > 1.0):
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

class SortableTableWidget(QTableWidget):
    """Enhanced table with Task Manager-like sorting"""
    
    def __init__(self):
        super().__init__()
        self.sort_order = {}
        self.current_sort_column = 1  # Default sort by Memory
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
        self.setWindowTitle("Task Manager - Real Time Monitor")
        self.setMinimumSize(1200, 800)
        
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
        self.real_time_timer.start(1500)  # 1.5 seconds
        
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
        view_menu.addItems(["All Processes", "Apps Only", "Background Processes"])
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

    def _setup_processes_tab(self):
        """Setup processes tab with Task Manager styling"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create sortable table
        self.table = SortableTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Name", "PID", "Memory (MB) ▲", "CPU %", "Status", "User", "Trend", "Activity"
        ])
        
        # Configure header
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # PID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Memory
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # CPU
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # User
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Trend
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Activity
        
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

    def _setup_info_bar(self, layout):
        """Setup Task Manager-like info bar"""
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(10, 5, 10, 5)
        
        self.process_count_label = QLabel("Processes: 0")
        self.thread_count_label = QLabel("Threads: 0")
        self.cpu_usage_label = QLabel("CPU Usage: 0%")
        self.memory_usage_label = QLabel("Memory: 0 MB")
        self.uptime_label = QLabel("Up time: 0s")
        
        # Style like Task Manager
        for label in [self.process_count_label, self.thread_count_label, 
                     self.cpu_usage_label, self.memory_usage_label, self.uptime_label]:
            label.setStyleSheet("font-weight: bold;")
        
        info_layout.addWidget(self.process_count_label)
        info_layout.addWidget(self.thread_count_label)
        info_layout.addWidget(self.cpu_usage_label)
        info_layout.addWidget(self.memory_usage_label)
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
        self.refresh_rate_label = QLabel("Refresh: 1.5s")
        
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
            total_threads = 0
            
            for row, process in enumerate(processes):
                self.process_row_map[process['pid']] = row
                self._add_process_to_table(row, process)
                total_memory += process['memory_mb']
                total_threads += 1  # Simplified thread count
            
            # Restore sorting
            self.table.setSortingEnabled(True)
            self.table.sortItems(self.sort_column, self.sort_order)
            
            # Update info
            self.process_count_label.setText(f"Processes: {len(processes)}")
            self.thread_count_label.setText(f"Threads: {total_threads}")
            self.memory_usage_label.setText(f"Memory: {total_memory:.0f} MB")
            self.status_label.setText("✅ Ready")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")

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
        
        # Status
        status_item = QTableWidgetItem(process['status'])
        self.table.setItem(row, 4, status_item)
        
        # User
        user_item = QTableWidgetItem(process['username'].split('\\')[-1] if '\\' in process['username'] else process['username'])
        self.table.setItem(row, 5, user_item)
        
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
        self.table.setItem(row, 6, trend_item)
        
        # Activity
        activity_item = QTableWidgetItem()
        if process['activity_level'] == 'high':
            activity_item.setText("🔴 High")
        elif process['activity_level'] == 'medium':
            activity_item.setText("🟡 Medium")
        else:
            activity_item.setText("🟢 Low")
        self.table.setItem(row, 7, activity_item)

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
        
        # Update status if changed
        self.table.item(row, 4).setText(process['status'])
        
        # Update trend
        trend_item = self.table.item(row, 6)
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
        activity_item = self.table.item(row, 7)
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

    def toggle_auto_refresh(self, checked):
        """Toggle auto-refresh"""
        self.is_auto_refresh = checked
        if checked:
            self.real_time_timer.start(1500)
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