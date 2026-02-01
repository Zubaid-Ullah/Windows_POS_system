from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QFrame)
from PyQt6.QtCore import Qt
import qtawesome as qta
from src.ui.button_styles import style_button

class LockedWindow(QWidget):
    def __init__(self, message="This system is deactivated. Contact support.", contact_info=None):
        super().__init__()
        self.setWindowTitle("System Access Restricted")
        self.setFixedSize(500, 450)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.contact_info = contact_info or {}
        self.init_ui(message)
        
    def init_ui(self, message):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(20)
        
        self.setStyleSheet("background-color: #111c44; border-radius: 20px; border: 2px solid #ee5d50;")
        
        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.lock", color="#ee5d50").pixmap(100, 100))
        self.layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("ACCESS DENIED")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)
        
        msg = QLabel(message)
        msg.setStyleSheet("font-size: 16px; color: #a3aed0;")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(msg)
        
        # Contact Details
        contact_frame = QFrame()
        contact_lay = QVBoxLayout(contact_frame)
        
        if self.contact_info.get("phone"):
            p = QLabel(f"Phone: {self.contact_info['phone']}")
            p.setStyleSheet("color: white; font-weight: bold;")
            contact_lay.addWidget(p)
            
        if self.contact_info.get("email"):
            e = QLabel(f"Email: {self.contact_info['email']}")
            e.setStyleSheet("color: white; font-weight: bold;")
            contact_lay.addWidget(e)
            
        self.layout.addWidget(contact_frame)
        
        exit_btn = QPushButton(" Exit Application")
        style_button(exit_btn, variant="danger")
        exit_btn.setFixedHeight(45)
        exit_btn.clicked.connect(lambda: exit(0))
        self.layout.addWidget(exit_btn)
