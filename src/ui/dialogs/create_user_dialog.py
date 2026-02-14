from src.core.auth import Auth
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QGroupBox, 
                             QGridLayout, QComboBox, QMessageBox, QScrollArea, QWidget, QDateEdit, QFileDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPixmap
from src.ui.button_styles import style_button
from src.ui.theme_manager import theme_manager

from src.utils.camera import capture_image
import os
import time

class CreateUserDialog(QDialog):
    def __init__(self, parent=None, user_data=None):
        self.user_data = user_data
        super().__init__(parent)
        self.setWindowTitle("Edit User" if user_data else "Create New User")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self.profile_picture_path = None
        self.init_ui()
        if user_data:
            self.populate_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # User Info Section
        info_group = QGroupBox("User Information")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(15)
        
        # Username
        info_layout.addWidget(QLabel("Username:"), 0, 0)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setFixedHeight(40)
        info_layout.addWidget(self.username_input, 0, 1)
        
        # Title/Position
        info_layout.addWidget(QLabel("Title:"), 1, 0)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g., Supervisor, Cashier, Manager")
        self.title_input.setFixedHeight(40)
        info_layout.addWidget(self.title_input, 1, 1)
        
        # Password
        info_layout.addWidget(QLabel("Password:"), 2, 0)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(40)
        info_layout.addWidget(self.password_input, 2, 1)
        
        # Role
        info_layout.addWidget(QLabel("Role:"), 3, 0)
        self.role_combo = QComboBox()
        roles = ["Salesman", "Manager", "PriceChecker"]
        
        curr_user = Auth.get_current_user()
        is_super = curr_user and curr_user.get('is_super_admin')
        
        if is_super:
            roles.extend(["Pharmacy Manager", "Pharmacist"])
            
        self.role_combo.addItems(roles)
        self.role_combo.setFixedHeight(40)
        info_layout.addWidget(self.role_combo, 3, 1)

        if is_super:
            info_layout.addWidget(QLabel("Contract End Date:"), 4, 0)
            self.contract_date_input = QDateEdit()
            self.contract_date_input.setCalendarPopup(True)
            self.contract_date_input.setDate(QDate.currentDate().addYears(1))
            self.contract_date_input.setFixedHeight(40)
            info_layout.addWidget(self.contract_date_input, 4, 1)

        # Base Salary
        info_layout.addWidget(QLabel("Base Salary (AFN):"), 5, 0)
        self.salary_input = QLineEdit()
        self.salary_input.setPlaceholderText("0.0")
        self.salary_input.setFixedHeight(40)
        info_layout.addWidget(self.salary_input, 5, 1)

        # Profile Picture (Required)
        info_layout.addWidget(QLabel("Profile Picture *:"), 6, 0)
        pic_row = QHBoxLayout()
        self.picture_preview = QLabel("No Image")
        self.picture_preview.setFixedSize(60, 60)
        self.picture_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.picture_preview.setStyleSheet("border: 1px solid #d1d5db; border-radius: 6px;")
        pic_row.addWidget(self.picture_preview)
        
        self.picture_btn = QPushButton("Select Image")
        style_button(self.picture_btn, variant="outline", size="small")
        self.picture_btn.clicked.connect(self.select_profile_picture)
        pic_row.addWidget(self.picture_btn)
        
        self.camera_btn = QPushButton("📷 Take Photo")
        style_button(self.camera_btn, variant="primary", size="small")
        self.camera_btn.clicked.connect(self.take_photo)
        pic_row.addWidget(self.camera_btn)
        
        pic_row.addStretch()
        info_layout.addLayout(pic_row, 6, 1)
        
        layout.addWidget(info_group)
        
        # Permissions Section
        perm_group = QGroupBox("Access Permissions (Limits)")
        perm_scroll = QScrollArea()
        perm_scroll.setWidgetResizable(True)
        perm_scroll.setFixedHeight(300)
        
        perm_widget = QWidget()
        perm_layout = QGridLayout(perm_widget)
        perm_layout.setSpacing(10)
        
        # All available permissions
        self.permission_checkboxes = {}
        
        all_permissions = [
            ("dashboard", "Dashboard", "Access to main dashboard"),
            ("sales", "Sales", "Process sales transactions"),
            ("finance", "Finance", "Manage expenses and payroll"),
            ("inventory", "Inventory", "Manage products and stock"),
            ("customers", "Customers", "Manage customer data"),
            ("loans", "Loans", "Manage customer loans"),
            ("reports", "Reports", "View sales reports"),
            ("suppliers", "Suppliers", "Manage suppliers"),
            ("pharmacy", "Pharmacy", "Access pharmacy module"),
            ("pharmacy_settings", "Pharmacy Settings", "Manage pharmacy specific configurations"),
            ("settings", "Settings", "System settings"),
            ("price_check", "Price Check", "Price checking terminal"),
            ("returns", "Returns", "Process returns"),
            ("users", "User Management", "Manage users and roles"),
        ]
        
        # Filter permissions
        if not is_super:
            permissions = [p for p in all_permissions if p[0] not in ('pharmacy',)]
        else:
            permissions = all_permissions
        
        row = 0
        for key, label, description in permissions:
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.setStyleSheet("font-weight: bold; font-size: 14px;")
            self.permission_checkboxes[key] = cb
            
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            
            perm_layout.addWidget(cb, row, 0)
            perm_layout.addWidget(desc_label, row, 1)
            row += 1
        
        perm_scroll.setWidget(perm_widget)
        perm_group_layout = QVBoxLayout(perm_group)
        perm_group_layout.addWidget(perm_scroll)
        
        layout.addWidget(perm_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        style_button(cancel_btn, variant="outline")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Save Changes" if self.user_data else "Create User")
        style_button(create_btn, variant="success")
        create_btn.clicked.connect(self.validate_and_accept)
        btn_layout.addWidget(create_btn)
        
        layout.addLayout(btn_layout)
        
        # Apply theme
        self.apply_theme()
    
    def apply_theme(self):
        t = theme_manager.DARK if theme_manager.is_dark else theme_manager.QUICKMART
        self.setStyleSheet(f"""
            QDialog {{ background-color: {t['bg_main']}; }}
            QGroupBox {{
                font-weight: bold; font-size: 16px; color: {t['text_main']};
                border: 2px solid {t['border']}; border-radius: 8px; margin-top: 10px; padding-top: 10px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
            QLabel {{ color: {t['text_main']}; }}
            QCheckBox {{ color: {t['text_main']}; }}
        """)

    def populate_data(self):
        self.username_input.setText(self.user_data['username'])
        self.title_input.setText(self.user_data['title'])
        self.role_combo.setCurrentText(self.user_data['role'])
        if self.user_data.get('base_salary'):
            self.salary_input.setText(str(self.user_data['base_salary']))
        self.profile_picture_path = self.user_data.get('profile_picture')
        if self.profile_picture_path and os.path.exists(self.profile_picture_path):
            pix = QPixmap(self.profile_picture_path)
            if not pix.isNull():
                self.picture_preview.setPixmap(pix.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.password_input.setPlaceholderText("Leave blank to keep current password")
        
        if hasattr(self, 'contract_date_input') and self.user_data.get('valid_until'):
            try:
                date_str = self.user_data['valid_until']
                if " " in date_str: date_str = date_str.split(" ")[0]
                self.contract_date_input.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
            except:
                pass
        
        # Set permissions
        perms = self.user_data.get('permissions', '').split(',')
        if perms and perms != ['']:
            for cb in self.permission_checkboxes.values():
                cb.setChecked(False)
            for p in perms:
                if p in self.permission_checkboxes:
                    self.permission_checkboxes[p].setChecked(True)
                elif p == '*':
                   for cb in self.permission_checkboxes.values(): cb.setChecked(True)
    
    def validate_and_accept(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username:
             QMessageBox.warning(self, "Validation Error", "Username is required")
             return

        if not self.user_data and not password:
            QMessageBox.warning(self, "Validation Error", "Password is required")
            return
        
        if password and len(password) < 4:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 4 characters")
            return

        # Profile picture optional for now or strictly required?
        # User said "make profile picture required" implicitly?
        # "Add `profile_picture` column... implement profile picture capture/upload"
        # I'll make it required ONLY if user is new.
        if not self.user_data and not self.profile_picture_path:
            QMessageBox.warning(self, "Validation Error", "Profile picture is required")
            return
        
        self.accept()

    def select_profile_picture(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Picture", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not path: return
        pix = QPixmap(path)
        if pix.isNull():
            QMessageBox.warning(self, "Image Error", "Could not load selected image.")
            return

        # Copy to data dir for persistence
        import shutil
        app_data = os.path.join(os.getcwd(), "data", "user_photos")
        os.makedirs(app_data, exist_ok=True)
        filename = f"user_photo_{int(time.time())}_{os.path.basename(path)}"
        save_path = os.path.join(app_data, filename)
        try:
            shutil.copy2(path, save_path)
            self.profile_picture_path = save_path
            self.picture_preview.setPixmap(pix.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image: {e}")

    def take_photo(self):
        # Save to temporary or permanent location?
        # Ideally, we should save to a proper 'users/photos' directory in app data
        app_data = os.path.join(os.getcwd(), "data", "user_photos")
        os.makedirs(app_data, exist_ok=True)
        filename = f"user_photo_{int(time.time())}.jpg"
        save_path = os.path.join(app_data, filename)
        
        success, err = capture_image(save_path, parent=self)
        if success:
            self.profile_picture_path = save_path
            pix = QPixmap(save_path)
            self.picture_preview.setPixmap(pix.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            if err:
                QMessageBox.warning(self, "Camera Error", err)

    def get_user_data(self):
        selected_permissions = [key for key, cb in self.permission_checkboxes.items() if cb.isChecked()]
        try:
            salary = float(self.salary_input.text())
        except:
            salary = 0.0

        data = {
            'username': self.username_input.text().strip(),
            'password': self.password_input.text().strip(),
            'title': self.title_input.text().strip() or "Staff",
            'role': self.role_combo.currentText(),
            'base_salary': salary,
            'permissions': ','.join(selected_permissions),
            'profile_picture': self.profile_picture_path,
        }
        
        if hasattr(self, 'contract_date_input') and self.contract_date_input.isVisible():
            data['valid_until'] = self.contract_date_input.date().toString("yyyy-MM-dd")
        else:
            data['valid_until'] = self.user_data.get('valid_until') if self.user_data else None
            
        return data
