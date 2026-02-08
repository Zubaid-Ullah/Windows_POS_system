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
        self.setWindowTitle("FaqiriTech POS Login")
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
        from src.core.blocking_task_manager import task_manager
        
        def fetch_users():
            try:
                users = supabase_manager.get_installers()
                return users or []
            except Exception as e:
                print(f"Error fetching users: {e}")
                return []
        
        task_manager.run_task(fetch_users, on_finished=self._on_users_fetched)

    def _on_users_fetched(self, users):
        self.user_combo.clear()
        all_options = ["SuperAdmin"]
        if users: all_options.extend(users)
        self.user_combo.addItems(all_options)
        
        prev_user = local_config.get("installed_by")
        if prev_user:
            idx = self.user_combo.findText(prev_user)
            if idx >= 0: self.user_combo.setCurrentIndex(idx)
        self.user_combo.setEnabled(True)
        
    def handle_login(self):
        username = self.user_combo.currentText()
        password = self.pass_edit.text()
        
        if not password:
            QMessageBox.warning(self, "Required", "Please enter password.")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText(" Verifying...")
        
        # 1. Start background auth
        from src.core.blocking_task_manager import task_manager
        import platform
        
        system_id = local_config.get("system_id")
        
        def authenticate():
            try:
                # Log attempt
                supabase_manager.log_activation_attempt(username, system_id, platform.node())
                
                if supabase_manager.verify_installer(username, password):
                    status = supabase_manager.get_installation_status(system_id)
                    return {"success": True, "status_data": status or {}}
                else:
                    return {"success": False, "status_data": {}}
            except Exception as e:
                print(f"Auth error: {e}")
                return {"success": False, "status_data": {}}
        
        def on_auth_finished(result):
            self._on_auth_result(result["success"], result["status_data"])
        
        task_manager.run_task(authenticate, on_finished=on_auth_finished)

    def _on_auth_result(self, success, status_data):
        self.login_btn.setEnabled(True)
        self.login_btn.setText(" Login Securely")
        
        if success:
            if status_data.get('status') == 'deactivated':
                QMessageBox.critical(self, "System Locked", "This installation has been deactivated. Contact support.")
                return
            
            local_config.set("client_username", self.user_combo.currentText())
            local_config.save()
            self.pass_edit.clear() # Clear password on success
            self.login_success.emit()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid credentials or network error.")
