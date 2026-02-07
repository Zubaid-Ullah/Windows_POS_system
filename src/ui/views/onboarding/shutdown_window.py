from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import qtawesome as qta
from src.ui.button_styles import style_button
from datetime import datetime, timezone

class ShutdownCountdownWindow(QWidget):
    shutdown_now = pyqtSignal()

    def __init__(self, target_time):
        super().__init__()
        self.target_time = target_time # datetime object (timezone aware)
        self.setWindowTitle("Remote Shutdown Warning")
        self.setFixedSize(500, 350)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
        self.update_countdown()
        
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(20)
        
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 15px; border: 2px solid #f59e0b;")
        
        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.clock", color="#f59e0b").pixmap(80, 80))
        self.layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.title = QLabel("REMOTE SHUTDOWN")
        self.title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        self.layout.addWidget(self.title, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.msg = QLabel("The system is scheduled for shutdown by SuperAdmin.")
        self.msg.setStyleSheet("font-size: 14px; color: #94a3b8;")
        self.msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.msg)
        
        self.counter_lbl = QLabel("00:00")
        self.counter_lbl.setStyleSheet("font-size: 48px; font-weight: bold; color: #f59e0b; font-family: 'Courier New';")
        self.layout.addWidget(self.counter_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.save_msg = QLabel("Please save your work immediately.")
        self.save_msg.setStyleSheet("font-size: 13px; color: #ef4444; font-weight: bold;")
        self.save_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.save_msg)

    def update_countdown(self):
        now = datetime.now(timezone.utc)
        remaining = (self.target_time - now).total_seconds()
        
        if remaining <= 0:
            self.counter_lbl.setText("00:00")
            self.timer.stop()
            self.shutdown_now.emit()
            return
            
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        self.counter_lbl.setText(f"{mins:02d}:{secs:02d}")
        
        # Urgent styling if less than 30 seconds
        if remaining < 30:
            self.setStyleSheet("background-color: #2a1111; border-radius: 15px; border: 3px solid #ef4444;")
            self.counter_lbl.setStyleSheet("font-size: 54px; font-weight: bold; color: #ef4444; font-family: 'Courier New';")
