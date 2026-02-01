from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QComboBox, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
import qtawesome as qta
from src.core.supabase_manager import supabase_manager
from src.core.local_config import local_config
from src.ui.button_styles import style_button

class LoginWindow(QWidget):
    login_success = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AFEX POS Login")
        self.setFixedSize(450, 600)
        self.init_ui()
        self.refresh_installers()
        
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(50, 50, 50, 50)
        self.layout.setSpacing(15)
        
        self.setStyleSheet("background-color: white; border-radius: 20px;")
        
        # Logo Icon
        self.logo_lbl = QLabel()
        self.logo_lbl.setPixmap(qta.icon("fa5s.user-shield", color="#4318ff").pixmap(80, 80))
        self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.logo_lbl)
        
        self.title = QLabel("System Login")
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1b2559;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title)
        
        self.subtitle = QLabel("Online authentication required")
        self.subtitle.setStyleSheet("font-size: 13px; color: #a3aed0;")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.subtitle)
        
        self.layout.addSpacing(20)
        
        # Fields
        self.user_combo = QComboBox()
        self.layout.addWidget(QLabel("Select Authorized User"))
        self.layout.addWidget(self.user_combo)

        # Add default admin option if not in list
        self.refresh_installers()
        
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setPlaceholderText("Password")
        self.layout.addWidget(QLabel("Password"))
        self.layout.addWidget(self.pass_edit)
        
        self.layout.addSpacing(10)
        
        self.login_btn = QPushButton(" Login Securely")
        self.login_btn.setIcon(qta.icon("fa5s.lock", color="white"))
        style_button(self.login_btn, variant="primary")
        self.login_btn.setFixedHeight(50)
        self.login_btn.clicked.connect(self.handle_login)
        self.layout.addWidget(self.login_btn)
        
        self.layout.addStretch()
        
        # Footer info
        sys_id = local_config.get("system_id")
        self.footer = QLabel(f"Machine ID: {sys_id}")
        self.footer.setStyleSheet("font-size: 10px; color: #cbd5e0;")
        self.footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.footer)

    def refresh_installers(self):
        self.user_combo.clear()
        self.user_combo.addItem("Loading online users...")
        self.user_combo.setEnabled(False)
        QTimer.singleShot(100, self._do_refresh_installers)

    def _do_refresh_installers(self):
        try:
            # Fetch authorized installers for login (as per spec)
            users = supabase_manager.get_installers()
            self.user_combo.clear()
            if users:
                self.user_combo.addItems(users)
                # Try to select the installer we used during registration
                prev_user = local_config.get("installed_by")
                if prev_user:
                    idx = self.user_combo.findText(prev_user)
                    if idx >= 0: self.user_combo.setCurrentIndex(idx)
            else:
                # If no installers found, show error
                self.user_combo.addItem("No installers available")
                print("❌ No installers found in authorized_persons table")
        except Exception as e:
            print(f"Error loading installers: {e}")
            self.user_combo.clear()
            self.user_combo.addItem("Connection error")
        self.user_combo.setEnabled(True)
        
    def handle_login(self):
        username = self.user_combo.currentText()
        password = self.pass_edit.text()
        
        if not password:
            QMessageBox.warning(self, "Required", "Please enter password.")
            return

        print(f"🔑 Authenticating installer {username} online...")
        # 1. Verify credentials against authorized_persons table
        if supabase_manager.verify_installer(username, password):
            # 2. Safety check: Verify this machine's status
            status_data = supabase_manager.get_installation_status(local_config.get("system_id"))
            if status_data:
                if status_data.get('status') == 'deactivated':
                    QMessageBox.critical(self, "System Locked", "This installation has been deactivated. Contact support.")
                    return
                
                # Success - Login established
                local_config.set("client_username", username)
                local_config.save()
                
                self.pass_edit.clear()
                self.login_success.emit()
                self.close()
            else:
                 QMessageBox.critical(self, "Registration Error", "Machine ID not recognized in cloud.")
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
