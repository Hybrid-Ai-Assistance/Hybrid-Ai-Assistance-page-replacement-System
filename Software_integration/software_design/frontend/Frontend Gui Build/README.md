# ai_pager_ui
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


### requirement.txt

PySide6>=6.5.0