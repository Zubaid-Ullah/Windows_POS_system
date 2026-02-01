from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta
from src.core.pharmacy_auth import PharmacyAuth
from src.ui.button_styles import style_button
from src.ui.theme_manager import theme_manager

class PharmacyLoginView(QWidget):
    login_success = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card = QFrame()
        card.setFixedWidth(400)
        card.setObjectName("login_card")
        card.setStyleSheet("""
            QFrame#login_card {
                background: white;
                border-radius: 20px;
                padding: 40px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.prescription-bottle-alt", color="#3b82f6").pixmap(80, 80))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_lbl)
        
        title = QLabel("Pharmacy Secure Login")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e293b;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Pharmacy Username")
        self.username.setFixedHeight(45)
        card_layout.addWidget(self.username)
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setFixedHeight(45)
        self.password.returnPressed.connect(self.handle_login)
        card_layout.addWidget(self.password)
        
        login_btn = QPushButton("Login to Pharmacy")
        style_button(login_btn, variant="primary")
        login_btn.setFixedHeight(45)
        login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(login_btn)
        
        layout.addWidget(card)
        
        # Dark mode support for login card
        if theme_manager.is_dark:
            card.setStyleSheet(card.styleSheet().replace("background: white;", "background: #111c44;"))
            title.setStyleSheet(title.styleSheet() + "color: white;")

    def handle_login(self):
        user = self.username.text().strip()
        pw = self.password.text().strip()
        
        if PharmacyAuth.login(user, pw):
            self.username.clear()
            self.password.clear()
            self.login_success.emit()
        else:
            QMessageBox.critical(self, "Failed", "Invalid Pharmacy Credentials")
