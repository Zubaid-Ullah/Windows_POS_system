import sys
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import qtawesome as qta
from src.core.supabase_manager import supabase_manager

class ConnectionWorker(QThread):
    result_ready = pyqtSignal(bool)
    
    def run(self):
        try:
            # Robust check
            online = supabase_manager.check_connection()
            self.result_ready.emit(online)
        except Exception as e:
            print(f"[ConnectionWorker] Error: {e}")
            self.result_ready.emit(False)

class ConnectionMonitorWindow(QWidget):
    """
    Separate small window to monitor internet connection in the background.
    """
    def __init__(self):
        super().__init__()
        # Frameless, stays on top, tool window (doesn't show in taskbar)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setFixedSize(140, 35)
        self.init_ui()
        
        # Default positioning at bottom right
        self.reposition()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_now)
        # Check every 60 seconds (user mentioned strings of 30-120 seconds or 5-10 minutes)
        self.timer.start(60000) 
        
        self.active_thread = None
        # Start first check immediately
        QTimer.singleShot(100, self.check_now)

    def reposition(self):
        # Adjust based on screen geometry
        screen = self.screen().geometry()
        self.move(screen.width() - 150, screen.height() - 80)

    def init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget#container {
                background-color: rgba(20, 30, 60, 220);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 8px;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI', Arial;
                font-weight: bold;
                border: none;
                background: transparent;
            }
        """)
        
        self.container = QWidget(self)
        self.container.setObjectName("container")
        self.container.setFixedSize(140, 35)
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(qta.icon("fa5s.clock", color="#a3aed0").pixmap(14, 14))
        layout.addWidget(self.icon_lbl)
        
        self.status_lbl = QLabel("CONNECTING...")
        self.status_lbl.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.status_lbl)
        
        # Add a small drag handle icon
        self.drag_lbl = QLabel()
        self.drag_lbl.setPixmap(qta.icon("fa5s.grip-lines-vertical", color="rgba(255,255,255,40)").pixmap(10, 14))
        layout.addWidget(self.drag_lbl)

    def check_now(self):
        if self.active_thread and self.active_thread.isRunning():
            return
            
        self.active_thread = ConnectionWorker()
        self.active_thread.result_ready.connect(self.update_status)
        self.active_thread.start()
        
    def update_status(self, online):
        if online:
            self.icon_lbl.setPixmap(qta.icon("fa5s.wifi", color="#10b981").pixmap(16, 16))
            self.status_lbl.setText("CLOUD ACTIVE")
            self.status_lbl.setStyleSheet("font-size: 10px; color: #10b981;")
        else:
            self.icon_lbl.setPixmap(qta.icon("fa5s.wifi-slash", color="#ee5d50").pixmap(16, 16))
            self.status_lbl.setText("OFFLINE MODE")
            self.status_lbl.setStyleSheet("font-size: 10px; color: #ee5d50;")

    # Dragging logic
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'oldPos'):
            delta = event.globalPosition().toPoint() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()
