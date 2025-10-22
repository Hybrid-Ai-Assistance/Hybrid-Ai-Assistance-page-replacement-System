# main.py - Windows Task Manager Style UI
import sys, random, os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QLabel, QToolBar, QPushButton, QLineEdit, QStatusBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QCheckBox, QSlider, QHBoxLayout, QListWidget, QListWidgetItem,
    QComboBox, QMessageBox, QProgressBar, QSplitter, QTextEdit,
    QGridLayout, QGroupBox
)
from PySide6.QtGui import QIcon, QPalette, QColor, QPainter, QFont, QLinearGradient
from PySide6.QtCore import Qt, QTimer, QDateTime

class TaskManagerTheme:
    """Windows Task Manager inspired theme"""
    
    COLORS = {
        "background": "#121111",
        "surface": "#171515",
        "surface_light": "#161414FF",
        "primary": "#3c2ca1d0",
        "primary_light": "#F8FBFF",
        "secondary": "#ffffff",
        "accent": "#107c10",
        "text_primary": "#FAFAFA",
        "text_secondary": "#E4DED8",
        "text_tertiary": "#605e5c",
        "success": "#107c10",
        "warning": "#d83b01",
        "error": "#e71111",
        "border": "#FFFFFF",
        "border_light": "#e1dfdd",
        "header_bg": "#101010",
        "row_even": "#2E2A4D7A",
        "row_odd": "#2327397C",
        "selection": "#BFBFD6C6"
    }

class AILRUBackend:
    """AI LRU Cache Backend Simulation"""
    def __init__(self):
        super().__init__()
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_operations = 0
        self.ai_predictions = 0
        self.cache_size = 0
        self.max_cache_size = 1000
        self.memory_saved = 45
        
    def get_stats(self):
        hit_rate = (self.cache_hits / self.total_operations * 100) if self.total_operations > 0 else 0
        return {
            'hit_rate': hit_rate,
            'total_operations': self.total_operations,
            'cache_size': self.cache_size,
            'max_cache_size': self.max_cache_size,
            'ai_predictions': self.ai_predictions,
            'efficiency': f"{(hit_rate / 100) * 0.85:.1%}",
            'memory_saved': self.memory_saved
        }
    
    def simulate_operation(self):
        """Simulate cache operations"""
        self.total_operations += 1
        if random.random() > 0.3:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            
        if random.random() > 0.5:
            self.ai_predictions += 1
            
        self.cache_size = random.randint(50, 800)
        self.memory_saved = random.randint(40, 50)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # WINDOW SETUP - call these on self (MainWindow)
        self.setWindowTitle("AI LRU Cache Manager")
        self.setMinimumSize(400, 300)  # Allow proper minimization
        self.resize(1200, 800)  # Default size
        
        # Create backend AFTER window setup
        self.backend = AILRUBackend()
        
        # Set window icon
        self.setup_icon()
        self._setup_ui()
        self.apply_theme()
        
        # Timers
        self.setup_timers()

    def setup_icon(self):
        """Setup application icon with fallback"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                self.setWindowIcon(QIcon.fromTheme("applications-system"))
        except Exception as e:
            print(f"Icon setup failed: {e}")

    def setup_timers(self):
        """Setup various timers for updates"""
        self.telemetry_timer = QTimer()
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(2000)

    def apply_theme(self):
        """Apply Windows Task Manager theme"""
        theme = TaskManagerTheme.COLORS
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {theme['background']};
                color: {theme['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid {theme['row_odd']};
                background: {theme['surface']};
            }}
            
            QTabBar::tab {{
                background: {theme['header_bg']};
                color: {theme['text_secondary']};
                padding: 8px 16px;
                margin: 0px;
                border: 1px solid {theme['border']};
                border-bottom: 1px solid {theme['border']};
                font-weight: normal;
            }}
            
            QTabBar::tab:selected {{
                background: {theme['surface_light']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-bottom: 1px solid {theme['border']};
            }}
            
            QToolBar {{
                background: {theme['surface']};
                border: none;
                border-bottom: 1px solid {theme['border']};
                spacing: 8px;
                padding: 6px 12px;
            }}
            
            QPushButton {{
                background: {theme['surface']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 2px;
                padding: 6px 12px;
                font-weight: normal;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background: {theme['surface_light']};
                border: 1px solid {theme['border_light']};
            }}
            
            QPushButton:pressed {{
                background: {theme['border_light']};
            }}
            
            QPushButton:disabled {{
                background: {theme['surface_light']};
                color: {theme['text_tertiary']};
            }}
            
            QLineEdit {{
                background: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 2px;
                padding: 6px 8px;
                color: {theme['text_primary']};
                font-size: 13px;
            }}
            
            QLineEdit:focus {{
                border: 1px solid {theme['primary']};
            }}
            
            QTableWidget {{
                background: {theme['row_even']};
                alternate-background-color: {theme['row_odd']};
                gridline-color: {theme['border_light']};
                border: 1px solid {theme['border']};
                outline: none;
            }}
            
            QHeaderView::section {{
                background: {theme['header_bg']};
                color: {theme['text_primary']};
                padding: 8px 6px;
                border: none;
                border-right: 1px solid {theme['border_light']};
                border-bottom: 1px solid {theme['border']};
                font-weight: 600;
                font-size: 12px;
            }}
            
            QHeaderView::section:last {{
                border-right: none;
            }}
            
            QStatusBar {{
                background: {theme['surface']};
                color: {theme['text_secondary']};
                border-top: 1px solid {theme['border']};
                padding: 4px 8px;
            }}
            
            QProgressBar {{
                border: 1px solid {theme['border']};
                border-radius: 2px;
                text-align: center;
                background: {theme['surface']};
                font-size: 11px;
            }}
            
            QProgressBar::chunk {{
                background: {theme['primary']};
            }}
            
            QCheckBox {{
                color: {theme['text_primary']};
                spacing: 6px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {theme['border']};
                border-radius: 2px;
                background: {theme['surface']};
            }}
            
            QCheckBox::indicator:checked {{
                background: {theme['primary']};
                border: 1px solid {theme['primary']};
            }}
            
            QComboBox {{
                background: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 2px;
                padding: 6px 8px;
                color: {theme['text_primary']};
                min-width: 120px;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QListWidget {{
                background: {theme['surface']};
                border: 1px solid {theme['border']};
                outline: none;
            }}
            
            QListWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {theme['border_light']};
            }}
            
            QListWidget::item:selected {{
                background: {theme['selection']};
            }}
        """)

    def _setup_ui(self):
        """Setup main UI components"""
        self._setup_toolbar()
        self._setup_tabs()
        self._setup_statusbar()

    def _setup_toolbar(self):
        """Setup toolbar with controls"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # File menu button
        file_btn = QPushButton("File")
        toolbar.addWidget(file_btn)

        # Options menu button  
        options_btn = QPushButton("Options")
        toolbar.addWidget(options_btn)

        toolbar.addSeparator()

        # Control buttons
        self.start_btn = QPushButton("Start Monitoring")
        self.start_btn.clicked.connect(self.start_monitoring)
        toolbar.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        toolbar.addWidget(self.stop_btn)

        toolbar.addSeparator()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        toolbar.addWidget(self.refresh_btn)

        # Search
        toolbar.addSeparator()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search processes...")
        self.search_box.textChanged.connect(self.filter_processes)
        self.search_box.setMinimumWidth(200)
        toolbar.addWidget(self.search_box)

    def _setup_tabs(self):
        """Setup main tab widget"""
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)

        self._setup_processes_tab()
        self._setup_performance_tab()
        self._setup_ai_control_tab()
        self._setup_logs_tab()

    def _setup_processes_tab(self):
        """Setup processes monitoring tab - Windows Task Manager style"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Processes table - exactly like Windows Task Manager
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Network", "CPU", "Memory", "Disk", "GPU"
        ])
        
        # Configure header
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Name column stretches
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Set column widths similar to Task Manager
        self.table.setColumnWidth(1, 100)  # Network
        self.table.setColumnWidth(2, 80)   # CPU
        self.table.setColumnWidth(3, 100)  # Memory
        self.table.setColumnWidth(4, 80)   # Disk
        self.table.setColumnWidth(5, 80)   # GPU
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.populate_processes_table()
        layout.addWidget(self.table)

        # Bottom controls
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(12, 8, 12, 12)
        
        # Left side - action buttons
        left_controls = QHBoxLayout()
        
        run_task_btn = QPushButton("Run new task")
        left_controls.addWidget(run_task_btn)
        
        end_task_btn = QPushButton("End task")
        left_controls.addWidget(end_task_btn)
        
        left_controls.addStretch()
        
        # Right side - efficiency mode
        right_controls = QHBoxLayout()
        
        efficiency_label = QLabel("Efficiency mode:")
        right_controls.addWidget(efficiency_label)
        
        efficiency_toggle = QCheckBox()
        efficiency_toggle.setChecked(False)
        right_controls.addWidget(efficiency_toggle)
        
        right_controls.addStretch()
        
        bottom_layout.addLayout(left_controls)
        bottom_layout.addLayout(right_controls)
        layout.addLayout(bottom_layout)

        self.tabs.addTab(tab, "Processes")

    def populate_processes_table(self):
        """Populate processes table with Windows Task Manager style data"""
        processes = [
            ("Search (3)", "0 Mbps", "0%", "237.1 MB", "0 Mbps", "0%"),
            ("Phone Link (3)", "0 Mbps", "0%", "118.4 MB", "0 Mbps", "0%"),
            ("Desktop Window Manager", "0 Mbps", "0.5%", "60.0 MB", "0 Mbps", "0.5%"),
            ("Task Manager", "0 Mbps", "5.5%", "56.8 MB", "0.1 Mbps", "0%"),
            ("CIT Leader", "0 Mbps", "0%", "56.6 MB", "0 Mbps", "0%"),
            ("Start (2)", "0 Mbps", "0%", "51.7 MB", "0 Mbps", "0%"),
            ("Secure System", "0 Mbps", "0%", "47.9 MB", "0 Mbps", "0%"),
            ("Service Host: Clipboard User S...", "0 Mbps", "0%", "45.2 MB", "0 Mbps", "0%"),
            ("Microsoft Windows Search Hub...", "0 Mbps", "0%", "39.4 MB", "0 Mbps", "0%"),
            ("Microsoft Office Quick-to-Burn L...", "0 Mbps", "0%", "32.1 MB", "0 Mbps", "0%"),
            ("Service Host: UtcSrc", "0 Mbps", "0%", "38.2 MB", "0 Mbps", "0%"),
            ("Mobile devices (2)", "0 Mbps", "0%", "28.8 MB", "0 Mbps", "0%"),
            ("Service Host: Diagnostic Policy...", "0 Mbps", "0%", "25.8 MB", "0 Mbps", "0%"),
            ("waspprs", "0 Mbps", "0%", "18.4 MB", "0 Mbps", "0%"),
            ("LocalServiceNotNetworkHome...", "0 Mbps", "0%", "14.7 MB", "0 Mbps", "0%"),
            ("Service Host: Windows Event L...", "0 Mbps", "0%", "12.9 MB", "0 Mbps", "0%"),
            ("Service Host: State Reporting ...", "0 Mbps", "0%", "12.7 MB", "0 Mbps", "0%"),
            ("Microsoft OneDriveFile Co-Au...", "0 Mbps", "0%", "12.2 MB", "0 Mbps", "0%"),
            ("Service Host: Local System", "0 Mbps", "0%", "11.9 MB", "0 Mbps", "0%"),
            ("Microsoft Network Realtime In...", "0 Mbps", "0%", "11.1 MB", "0 Mbps", "0%"),
            ("Local Security Authority Proce...", "0 Mbps", "0%", "9.9 MB", "0 Mbps", "0%"),
            ("Registry", "0 Mbps", "0%", "9.7 MB", "0 Mbps", "0%"),
            ("Service Host: DCOM Server Pr...", "0 Mbps", "0%", "9.4 MB", "0 Mbps", "0%")
        ]
        
        self.table.setRowCount(len(processes))
        for row, (name, network, cpu, memory, disk, gpu) in enumerate(processes):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(network))
            self.table.setItem(row, 2, QTableWidgetItem(cpu))
            self.table.setItem(row, 3, QTableWidgetItem(memory))
            self.table.setItem(row, 4, QTableWidgetItem(disk))
            self.table.setItem(row, 5, QTableWidgetItem(gpu))

    def _setup_performance_tab(self):
        """Setup performance monitoring tab with Windows Task Manager style"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for left and right panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Performance metrics
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(12, 12, 6, 12)

        # CPU Section
        cpu_group = QGroupBox("CPU")
        cpu_group.setMinimumHeight(120)
        cpu_layout = QVBoxLayout(cpu_group)
        
        # CPU utilization
        cpu_util_layout = QHBoxLayout()
        cpu_util_layout.addWidget(QLabel("Utilization:"))
        self.cpu_util_label = QLabel("3%")
        self.cpu_util_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        cpu_util_layout.addWidget(self.cpu_util_label)
        cpu_util_layout.addStretch()
        
        # CPU speed
        cpu_speed_layout = QHBoxLayout()
        cpu_speed_layout.addWidget(QLabel("Speed:"))
        self.cpu_speed_label = QLabel("1.76 GHz")
        self.cpu_speed_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        cpu_speed_layout.addWidget(self.cpu_speed_label)
        cpu_speed_layout.addStretch()
        
        cpu_layout.addLayout(cpu_util_layout)
        cpu_layout.addLayout(cpu_speed_layout)
        
        # CPU graph placeholder
        cpu_graph = QFrame()
        cpu_graph.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078d7, stop:0.03 #0078d7, stop:0.031 #f3f3f3, 
                    stop:0.05 #f3f3f3, stop:0.051 #0078d7, stop:0.08 #0078d7,
                    stop:0.081 #f3f3f3, stop:0.1 #f3f3f3, stop:0.101 #0078d7);
                border: 1px solid #d2d0ce;
                border-radius: 2px;
            }
        """)
        cpu_graph.setMinimumHeight(20)
        cpu_layout.addWidget(cpu_graph)
        left_layout.addWidget(cpu_group)

        # Memory Section
        memory_group = QGroupBox("Memory")
        memory_group.setMinimumHeight(100)
        memory_layout = QVBoxLayout(memory_group)
        
        # Memory usage
        memory_usage_layout = QHBoxLayout()
        memory_usage_layout.addWidget(QLabel("Usage:"))
        self.memory_usage_label = QLabel("9.3/15.4 GB (60%)")
        self.memory_usage_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        memory_usage_layout.addWidget(self.memory_usage_label)
        memory_usage_layout.addStretch()
        
        memory_layout.addLayout(memory_usage_layout)
        
        # Memory graph placeholder
        memory_graph = QFrame()
        memory_graph.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e81123, stop:0.6 #e81123, stop:0.601 #f3f3f3);
                border: 1px solid #d2d0ce;
                border-radius: 2px;
            }
        """)
        memory_graph.setMinimumHeight(20)
        memory_layout.addWidget(memory_graph)
        
        left_layout.addWidget(memory_group)

        # Disk Section
        disk_group = QGroupBox("Disk 0 (C: D:)")
        disk_group.setMinimumHeight(100)
        disk_layout = QVBoxLayout(disk_group)
        
        # Disk usage
        disk_usage_layout = QHBoxLayout()
        disk_usage_layout.addWidget(QLabel("Usage:"))
        self.disk_usage_label = QLabel("1%")
        self.disk_usage_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        disk_usage_layout.addWidget(self.disk_usage_label)
        disk_usage_layout.addStretch()
        
        # Disk activity
        disk_activity_layout = QHBoxLayout()
        disk_activity_layout.addWidget(QLabel("Active time:"))
        self.disk_activity_label = QLabel("SC50 (90 Mb)")
        self.disk_activity_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        disk_activity_layout.addWidget(self.disk_activity_label)
        disk_activity_layout.addStretch()
        
        disk_layout.addLayout(disk_usage_layout)
        disk_layout.addLayout(disk_activity_layout)
        
        # Disk graph placeholder
        disk_graph = QFrame()
        disk_graph.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #107c10, stop:0.01 #107c10, stop:0.011 #f3f3f3);
                border: 1px solid #d2d0ce;
                border-radius: 2px;
            }
        """)
        disk_graph.setMinimumHeight(20)
        disk_layout.addWidget(disk_graph)
        
        left_layout.addWidget(disk_group)

        # Network Section
        network_group = QGroupBox("Wi-Fi")
        network_group.setMinimumHeight(100)
        network_layout = QVBoxLayout(network_group)
        
        # Network usage
        network_usage_layout = QHBoxLayout()
        network_usage_layout.addWidget(QLabel("Usage:"))
        self.network_usage_label = QLabel("S-0 R-0 Mbps")
        self.network_usage_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        network_usage_layout.addWidget(self.network_usage_label)
        network_usage_layout.addStretch()
        
        network_layout.addLayout(network_usage_layout)
        
        # Network graph placeholder
        network_graph = QFrame()
        network_graph.setStyleSheet("""
            QFrame {
                background: #f3f3f3;
                border: 1px solid #d2d0ce;
                border-radius: 2px;
            }
        """)
        network_graph.setMinimumHeight(20)
        network_layout.addWidget(network_graph)
        
        left_layout.addWidget(network_group)

        # GPU Section
        gpu_group = QGroupBox("GPU 0")
        gpu_group.setMinimumHeight(120)
        gpu_layout = QVBoxLayout(gpu_group)
        
        # GPU usage
        gpu_usage_layout = QHBoxLayout()
        gpu_usage_layout.addWidget(QLabel("Usage:"))
        self.gpu_usage_label = QLabel("1%")
        self.gpu_usage_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        gpu_usage_layout.addWidget(self.gpu_usage_label)
        gpu_usage_layout.addStretch()
        
        # GPU temperature
        gpu_temp_layout = QHBoxLayout()
        gpu_temp_layout.addWidget(QLabel("Temperature:"))
        self.gpu_temp_label = QLabel("42 °C")
        self.gpu_temp_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        gpu_temp_layout.addWidget(self.gpu_temp_label)
        gpu_temp_layout.addStretch()
        
        # GPU model
        gpu_model_layout = QHBoxLayout()
        gpu_model_layout.addWidget(QLabel("Model:"))
        self.gpu_model_label = QLabel("AMD Radeon™ Graphics")
        self.gpu_model_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        gpu_model_layout.addWidget(self.gpu_model_label)
        gpu_model_layout.addStretch()
        
        gpu_layout.addLayout(gpu_usage_layout)
        gpu_layout.addLayout(gpu_temp_layout)
        gpu_layout.addLayout(gpu_model_layout)
        
        # GPU graph placeholder
        gpu_graph = QFrame()
        gpu_graph.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078d7, stop:0.01 #0078d7, stop:0.011 #f3f3f3);
                border: 1px solid #d2d0ce;
                border-radius: 2px;
            }
        """)
        gpu_graph.setMinimumHeight(20)
        gpu_layout.addWidget(gpu_graph)
        
        left_layout.addWidget(gpu_group)
        left_layout.addStretch()

        # Right panel - Memory composition
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(6, 12, 12, 12)

        # Memory composition section
        memory_comp_group = QGroupBox("Memory composition")
        memory_comp_layout = QVBoxLayout(memory_comp_group)

        # In use section
        in_use_layout = QHBoxLayout()
        in_use_layout.addWidget(QLabel("In use (Compressed):"))
        self.in_use_label = QLabel("9.3 GB (0 MB)")
        self.in_use_label.setStyleSheet("font-weight: bold;")
        in_use_layout.addWidget(self.in_use_label)
        in_use_layout.addStretch()
        memory_comp_layout.addLayout(in_use_layout)

        # Available section
        available_layout = QHBoxLayout()
        available_layout.addWidget(QLabel("Available:"))
        self.available_label = QLabel("6.0 GB")
        self.available_label.setStyleSheet("font-weight: bold;")
        available_layout.addWidget(self.available_label)
        available_layout.addStretch()
        memory_comp_layout.addLayout(available_layout)

        # Speed section
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_label = QLabel("3200 MT/s")
        self.speed_label.setStyleSheet("font-weight: bold;")
        speed_layout.addWidget(self.speed_label)
        speed_layout.addStretch()
        memory_comp_layout.addLayout(speed_layout)

        # Slots used section
        slots_layout = QHBoxLayout()
        slots_layout.addWidget(QLabel("Slots used:"))
        self.slots_label = QLabel("2 of 2")
        self.slots_label.setStyleSheet("font-weight: bold;")
        slots_layout.addWidget(self.slots_label)
        slots_layout.addStretch()
        memory_comp_layout.addLayout(slots_layout)

        # Form factor section
        form_factor_layout = QHBoxLayout()
        form_factor_layout.addWidget(QLabel("Form factor:"))
        self.form_factor_label = QLabel("SODIMM")
        self.form_factor_label.setStyleSheet("font-weight: bold;")
        form_factor_layout.addWidget(self.form_factor_label)
        form_factor_layout.addStretch()
        memory_comp_layout.addLayout(form_factor_layout)

        # Hardware reserved section
        hardware_layout = QHBoxLayout()
        hardware_layout.addWidget(QLabel("Hardware reserved:"))
        self.hardware_label = QLabel("864 MB")
        self.hardware_label.setStyleSheet("font-weight: bold;")
        hardware_layout.addWidget(self.hardware_label)
        hardware_layout.addStretch()
        memory_comp_layout.addLayout(hardware_layout)

        # Committed section
        committed_layout = QHBoxLayout()
        committed_layout.addWidget(QLabel("Committed:"))
        self.committed_label = QLabel("10.5/19.9 GB")
        self.committed_label.setStyleSheet("font-weight: bold;")
        committed_layout.addWidget(self.committed_label)
        committed_layout.addStretch()
        memory_comp_layout.addLayout(committed_layout)

        # Cached section
        cached_layout = QHBoxLayout()
        cached_layout.addWidget(QLabel("Cached:"))
        self.cached_label = QLabel("5.7 GB")
        self.cached_label.setStyleSheet("font-weight: bold;")
        cached_layout.addWidget(self.cached_label)
        cached_layout.addStretch()
        memory_comp_layout.addLayout(cached_layout)

        # Paged pool section
        paged_layout = QHBoxLayout()
        paged_layout.addWidget(QLabel("Paged pool:"))
        self.paged_label = QLabel("656 MB")
        self.paged_label.setStyleSheet("font-weight: bold;")
        paged_layout.addWidget(self.paged_label)
        paged_layout.addStretch()
        memory_comp_layout.addLayout(paged_layout)

        # Non-paged pool section
        non_paged_layout = QHBoxLayout()
        non_paged_layout.addWidget(QLabel("Non-paged pool:"))
        self.non_paged_label = QLabel("402 MB")
        self.non_paged_label.setStyleSheet("font-weight: bold;")
        non_paged_layout.addWidget(self.non_paged_label)
        non_paged_layout.addStretch()
        memory_comp_layout.addLayout(non_paged_layout)

        # Memory composition visualization
        memory_viz_frame = QFrame()
        memory_viz_frame.setMinimumHeight(40)
        memory_viz_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e81123, stop:0.6 #e81123, 
                    stop:0.601 #107c10, stop:0.65 #107c10,
                    stop:0.651 #0078d7, stop:0.9 #0078d7,
                    stop:0.901 #f3f3f3);
                border: 1px solid #d2d0ce;
                border-radius: 2px;
            }
        """)
        memory_comp_layout.addWidget(memory_viz_frame)

        right_layout.addWidget(memory_comp_group)

        # AI Cache Performance section
        ai_cache_group = QGroupBox("AI Cache Performance")
        ai_cache_layout = QVBoxLayout(ai_cache_group)

        # Cache Hit Rate
        hit_rate_layout = QHBoxLayout()
        hit_rate_layout.addWidget(QLabel("Cache Hit Rate:"))
        self.hit_rate_label = QLabel("85%")
        self.hit_rate_label.setStyleSheet("color: #107c10; font-weight: bold; font-size: 14px;")
        hit_rate_layout.addWidget(self.hit_rate_label)
        hit_rate_layout.addStretch()
        ai_cache_layout.addLayout(hit_rate_layout)

        # AI Accuracy
        accuracy_layout = QHBoxLayout()
        accuracy_layout.addWidget(QLabel("AI Accuracy:"))
        self.accuracy_label = QLabel("92%")
        self.accuracy_label.setStyleSheet("color: #107c10; font-weight: bold; font-size: 14px;")
        accuracy_layout.addWidget(self.accuracy_label)
        accuracy_layout.addStretch()
        ai_cache_layout.addLayout(accuracy_layout)

        # Memory Saved
        saved_layout = QHBoxLayout()
        saved_layout.addWidget(QLabel("Memory Saved:"))
        self.saved_label = QLabel("45 MB")
        self.saved_label.setStyleSheet("color: #107c10; font-weight: bold; font-size: 14px;")
        saved_layout.addWidget(self.saved_label)
        saved_layout.addStretch()
        ai_cache_layout.addLayout(saved_layout)

        # Active Processes
        active_layout = QHBoxLayout()
        active_layout.addWidget(QLabel("Active Processes:"))
        self.active_label = QLabel("24")
        self.active_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        active_layout.addWidget(self.active_label)
        active_layout.addStretch()
        ai_cache_layout.addLayout(active_layout)

        # AI Cache visualization
        ai_cache_viz_frame = QFrame()
        ai_cache_viz_frame.setMinimumHeight(40)
        ai_cache_viz_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #107c10, stop:0.85 #107c10, stop:0.851 #f3f3f3);
                border: 1px solid #d2d0ce;
                border-radius: 2px;
            }
        """)
        ai_cache_layout.addWidget(ai_cache_viz_frame)

        right_layout.addWidget(ai_cache_group)
        right_layout.addStretch()

        # Add panels to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter)
        self.tabs.addTab(tab, "Performance")

        # Timer for updating performance metrics
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.update_performance_metrics)
        self.performance_timer.start(1000)

    def update_performance_metrics(self):
        """Update performance metrics with realistic values"""
        # Simulate realistic fluctuations
        cpu_util = max(1, min(100, random.randint(2, 8)))  # 2-8% range
        cpu_speed = round(1.5 + random.random() * 0.8, 2)  # 1.5-2.3 GHz range
        
        memory_used = round(8.5 + random.random() * 2, 1)  # 8.5-10.5 GB range
        memory_total = 15.4
        memory_percent = int((memory_used / memory_total) * 100)
        
        disk_usage = random.randint(0, 3)  # 0-3% range
        network_send = random.randint(0, 5)
        network_recv = random.randint(0, 5)
        gpu_usage = random.randint(0, 3)  # 0-3% range
        gpu_temp = random.randint(40, 45)  # 40-45°C range

        # Update labels
        self.cpu_util_label.setText(f"{cpu_util}%")
        self.cpu_speed_label.setText(f"{cpu_speed} GHz")
        self.memory_usage_label.setText(f"{memory_used}/{memory_total} GB ({memory_percent}%)")
        self.disk_usage_label.setText(f"{disk_usage}%")
        self.network_usage_label.setText(f"S-{network_send} R-{network_recv} Mbps")
        self.gpu_usage_label.setText(f"{gpu_usage}%")
        self.gpu_temp_label.setText(f"{gpu_temp} °C")
        
        # Update memory composition (simulate small changes)
        in_use = memory_used
        available = round(memory_total - memory_used, 1)
        committed = round(10.3 + random.random() * 0.4, 1)
        cached = round(5.5 + random.random() * 0.4, 1)
        
        self.in_use_label.setText(f"{in_use} GB (0 MB)")
        self.available_label.setText(f"{available} GB")
        self.committed_label.setText(f"{committed}/19.9 GB")
        self.cached_label.setText(f"{cached} GB")

    def _setup_ai_control_tab(self):
        """Setup AI control and configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # AI Mode Selection
        mode_group = QGroupBox("AI Operation Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_toggle = QCheckBox("Enforced Mode (AI takes automatic actions)")
        self.mode_toggle.setChecked(True)
        mode_layout.addWidget(self.mode_toggle)
        
        mode_desc = QLabel("Advisory Mode: Suggests actions\nEnforced Mode: Automatically optimizes")
        mode_desc.setStyleSheet("color: #605e5c; font-size: 12px; margin-top: 8px;")
        mode_layout.addWidget(mode_desc)
        
        layout.addWidget(mode_group)

        # Configuration
        config_group = QGroupBox("AI Configuration")
        config_layout = QVBoxLayout(config_group)

        # Fault threshold
        slider1_layout = QHBoxLayout()
        slider1_layout.addWidget(QLabel("Fault Threshold:"))
        self.slider_faults = QSlider(Qt.Horizontal)
        self.slider_faults.setRange(10, 100)
        self.slider_faults.setValue(50)
        self.slider_faults.valueChanged.connect(self.on_config_changed)
        slider1_layout.addWidget(self.slider_faults)
        self.fault_label = QLabel("50%")
        self.fault_label.setStyleSheet("font-weight: bold; min-width: 40px;")
        slider1_layout.addWidget(self.fault_label)
        config_layout.addLayout(slider1_layout)

        # Memory threshold
        slider2_layout = QHBoxLayout()
        slider2_layout.addWidget(QLabel("Memory Threshold:"))
        self.slider_memory = QSlider(Qt.Horizontal)
        self.slider_memory.setRange(10, 100)
        self.slider_memory.setValue(70)
        self.slider_memory.valueChanged.connect(self.on_config_changed)
        slider2_layout.addWidget(self.slider_memory)
        self.memory_label = QLabel("70%")
        self.memory_label.setStyleSheet("font-weight: bold; min-width: 40px;")
        slider2_layout.addWidget(self.memory_label)
        config_layout.addLayout(slider2_layout)

        layout.addWidget(config_group)

        # AI Status
        status_group = QGroupBox("AI Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("ACTIVE - Optimizing System Performance")
        self.status_label.setStyleSheet("color: #107c10; font-weight: bold; padding: 8px;")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)

        # Action buttons
        button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.clicked.connect(self.apply_settings)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_settings)
        
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()
        self.tabs.addTab(tab, "AI Control")

    def _setup_logs_tab(self):
        """Setup logs and activity tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Summary
        summary = QLabel("AI saved 128 page faults in last 15 minutes (32% improvement)")
        summary.setStyleSheet("""
            background: #231F1F;
            border: 1px solid #d2d0ce;
            padding: 12px;
            border-radius: 2px;
            font-weight: bold;
        """)
        layout.addWidget(summary)

        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_logs = QLineEdit()
        self.search_logs.setPlaceholderText("Search logs...")
        self.search_logs.textChanged.connect(self.filter_logs)
        self.search_logs.setMinimumWidth(200)
        filter_layout.addWidget(self.search_logs)

        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_dropdown = QComboBox()
        self.filter_dropdown.addItems(["All", "INFO", "WARN", "ERROR", "AI", "OPTIMIZATION"])
        self.filter_dropdown.currentTextChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.filter_dropdown)

        self.clear_logs_btn = QPushButton("Clear Logs")
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        filter_layout.addWidget(self.clear_logs_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Logs list
        self.log_list = QListWidget()
        self.log_list.setAlternatingRowColors(True)
        self.all_logs = []
        
        # Sample logs
        sample_logs = [
            f"[{QDateTime.currentDateTime().toString('hh:mm:ss')}] INFO - AI LRU Monitoring started",
            f"[{QDateTime.currentDateTime().toString('hh:mm:ss')}] AI - Pattern detected: Chrome memory usage cyclical",
            f"[{QDateTime.currentDateTime().toString('hh:mm:ss')}] OPTIMIZATION - Reduced page faults by 15% for python.exe",
            f"[{QDateTime.currentDateTime().toString('hh:mm:ss')}] WARN - High memory pressure detected (85%)",
            f"[{QDateTime.currentDateTime().toString('hh:mm:ss')}] AI - Predictive cache optimization applied",
            f"[{QDateTime.currentDateTime().toString('hh:mm:ss')}] INFO - Cache hit rate improved to 87%",
            f"[{QDateTime.currentDateTime().toString('hh:mm:ss')}] ERROR - Failed to read process metrics for PID 1234"
        ]
        
        for log in sample_logs:
            self.all_logs.append(log)
            item = QListWidgetItem(log)
            
            # Color coding
            if "ERROR" in log:
                item.setForeground(QColor("#e71111"))
            elif "WARN" in log:
                item.setForeground(QColor("#d83b01"))
            elif "AI" in log or "OPTIMIZATION" in log:
                item.setForeground(QColor("#0078d7"))
            elif "INFO" in log:
                item.setForeground(QColor("#107c10"))
                
            self.log_list.addItem(item)

        layout.addWidget(self.log_list)
        self.tabs.addTab(tab, "Activity Logs")

    def _setup_statusbar(self):
        """Setup status bar"""
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        
        self.mode_label = QLabel("AI: Active")
        self.status.addWidget(self.mode_label)
        
        self.telemetry_label = QLabel("System Ready")
        self.status.addPermanentWidget(self.telemetry_label)

    # -------------------- EVENT HANDLERS --------------------
    def start_monitoring(self):
        """Start AI monitoring"""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.search_box.setEnabled(True)
        
        self.telemetry_label.setText("Monitoring: Active")
        self.add_log_entry("Monitoring started", "INFO")
        QMessageBox.information(self, "Monitoring Started", 
                              "AI LRU monitoring is now active and optimizing system performance.")

    def stop_monitoring(self):
        """Stop AI monitoring"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.search_box.setEnabled(False)
        
        self.telemetry_label.setText("Monitoring: Stopped")
        self.add_log_entry("Monitoring stopped", "INFO")

    def refresh_data(self):
        """Refresh all data"""
        self.backend.simulate_operation()
        self.populate_processes_table()
        self.add_log_entry("Data refreshed", "INFO")

    def update_telemetry(self):
        """Update telemetry information"""
        stats = self.backend.get_stats()
        telemetry_text = f"Cache: {stats['hit_rate']:.1f}% | AI Eff: {stats['efficiency']} | Ops: {stats['total_operations']}"
        self.telemetry_label.setText(telemetry_text)

    def on_config_changed(self):
        """Handle configuration changes"""
        self.fault_label.setText(f"{self.slider_faults.value()}%")
        self.memory_label.setText(f"{self.slider_memory.value()}%")
        self.apply_btn.setEnabled(True)

    def apply_settings(self):
        """Apply AI configuration settings"""
        self.apply_btn.setEnabled(False)
        self.add_log_entry(f"AI configuration updated - Faults: {self.slider_faults.value()}%, Memory: {self.slider_memory.value()}%", "AI")
        QMessageBox.information(self, "Settings Applied", "AI configuration has been updated successfully.")

    def reset_settings(self):
        """Reset to default settings"""
        self.slider_faults.setValue(50)
        self.slider_memory.setValue(70)
        self.apply_btn.setEnabled(False)
        self.add_log_entry("Settings reset to defaults", "INFO")

    def filter_processes(self):
        """Filter processes based on search text"""
        search_text = self.search_box.text().lower()
        for row in range(self.table.rowCount()):
            should_show = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            self.table.setRowHidden(row, not should_show)

    def filter_logs(self):
        """Filter logs based on search and category"""
        text = self.search_logs.text().lower()
        category = self.filter_dropdown.currentText()

        self.log_list.clear()
        for entry in self.all_logs:
            if text and text not in entry.lower():
                continue
            if category != "All" and category not in entry:
                continue
            
            item = QListWidgetItem(entry)
            
            # Color coding
            if "ERROR" in entry:
                item.setForeground(QColor("#e71111"))
            elif "WARN" in entry:
                item.setForeground(QColor("#d83b01"))
            elif "AI" in entry or "OPTIMIZATION" in entry:
                item.setForeground(QColor("#0078d7"))
            elif "INFO" in entry:
                item.setForeground(QColor("#107c10"))
                
            self.log_list.addItem(item)

    def clear_logs(self):
        """Clear all logs"""
        reply = QMessageBox.question(self, "Clear Logs", 
                                   "Are you sure you want to clear all logs?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.log_list.clear()
            self.all_logs.clear()
            self.add_log_entry("Logs cleared", "INFO")

    def add_log_entry(self, message, category="INFO"):
        """Add a new log entry"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        log_entry = f"[{timestamp}] {message}"
        
        self.all_logs.append(log_entry)
        
        item = QListWidgetItem(log_entry)
        if category == "ERROR":
            item.setForeground(QColor("#e71111"))
        elif category == "WARN":
            item.setForeground(QColor("#d83b01"))
        elif category in ["AI", "OPTIMIZATION"]:
            item.setForeground(QColor("#0078d7"))
        elif category == "INFO":
            item.setForeground(QColor("#107c10"))
            
        self.log_list.addItem(item)
        self.log_list.scrollToBottom()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application-wide properties
    app.setApplicationName("AI LRU Cache Manager")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("AI Systems")
    
    # Set application icon
    try:
        if os.path.exists("favicon.ico"):
            app.setWindowIcon(QIcon("favicon.ico"))
    except:
        pass

    # Apply modern styling
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())