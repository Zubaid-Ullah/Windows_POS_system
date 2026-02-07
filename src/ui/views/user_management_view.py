from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import qtawesome as qta
from src.database.db_manager import db_manager
from src.core.auth import Auth
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button
from src.ui.dialogs.create_user_dialog import CreateUserDialog

class UserManagementView(QWidget):
    def __init__(self):
        super().__init__()
        self.show_passwords = False
        self.password_store = {}  # Store plaintext passwords temporarily
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("User Management")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a3a8a; margin-bottom: 20px;")
        layout.addWidget(header)

        gb_add = QGroupBox("Create New User")
        form_layout = QHBoxLayout(gb_add)  # Changed to HBoxLayout
        
        # Password Visibility Toggle
        self.password_toggle_btn = QPushButton("👁️ Show Passwords")
        style_button(self.password_toggle_btn, variant="warning")
        self.password_toggle_btn.clicked.connect(self.toggle_password_visibility)
        form_layout.addWidget(self.password_toggle_btn)
        
        form_layout.addStretch()
        
        add_user_btn = QPushButton("+ Create New User")
        add_user_btn.setFixedHeight(50)
        style_button(add_user_btn, variant="success", size="large")
        add_user_btn.clicked.connect(self.open_create_user_dialog)
        form_layout.addWidget(add_user_btn)
        
        layout.addWidget(gb_add)

        # User List
        self.user_table = QTableWidget(0, 8)
        self.user_table.setHorizontalHeaderLabels(["ID", "Username", "Title", "Role", "Status", "Base Salary", "Password", "Actions"])
        style_table(self.user_table, variant="premium")
        
        # 1. Make table responsive (benefit from global ResizeToContents)
        header = self.user_table.horizontalHeader()
        # Explicit stretches for primary info columns
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Username
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Title

        layout.addWidget(self.user_table)
        
        self.load_users()
        
    def toggle_password_visibility(self):
        self.show_passwords = not self.show_passwords
        if self.show_passwords:
            self.password_toggle_btn.setText("🙈 Hide Passwords")
            QMessageBox.information(self, "Password Security", 
                                  "Passwords are securely hashed (encrypted). Only passwords set/changed in this session can be revealed.\n\n"
                                  "To see a password for an existing user, you must Reset it.")
        else:
            self.password_toggle_btn.setText("👁️ Show Passwords")
        self.load_users()
    
    def open_create_user_dialog(self):
        dialog = CreateUserDialog(self)
        if dialog.exec():
            user_data = dialog.get_user_data()
            # Store plaintext password
            if user_data.get('password'):
                self.password_store[user_data['username']] = user_data['password']
            self.create_user_with_permissions(user_data)
    
    def create_user_with_permissions(self, user_data):
        try:
            # Get role ID
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM roles WHERE name = ?", (user_data['role'],))
                role_row = cursor.fetchone()
                if not role_row:
                    QMessageBox.warning(self, "Error", f"Role '{user_data['role']}' not found")
                    return
                
                role_id = role_row['id']
                
                # Create user with permissions
                password_hash = Auth.hash_password(user_data['password'])
                
                # Handle valid_until (Contract) - only set if provided (SuperAdmin)
                valid_until = user_data.get('valid_until')
                
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role_id, title, permissions, valid_until, base_salary, is_active) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (user_data['username'], password_hash, role_id, user_data['title'], user_data['permissions'], valid_until, user_data.get('base_salary', 0)))
                
                conn.commit()
                QMessageBox.information(self, "Success", f"User '{user_data['username']}' created successfully!")
                self.load_users()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create user: {str(e)}")

    def load_users(self):
        current_user = Auth.get_current_user()
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Query Logic
            if current_user.get('username') == 'superadmin':
                query = """
                    SELECT u.id, u.username, u.title, r.name as role, u.is_active, u.permissions, u.password_hash, u.base_salary
                    FROM users u 
                    JOIN roles r ON u.role_id = r.id 
                    WHERE u.username != 'psuper'
                """
            elif current_user.get('is_super_admin'):
                query = """
                    SELECT u.id, u.username, u.title, r.name as role, u.is_active, u.permissions, u.password_hash, u.base_salary
                    FROM users u 
                    JOIN roles r ON u.role_id = r.id 
                    WHERE u.username != 'psuper'
                """
            else:
                 query = """
                    SELECT u.id, u.username, u.title, r.name as role, u.is_active, u.permissions, u.password_hash, u.base_salary
                    FROM users u 
                    JOIN roles r ON u.role_id = r.id 
                    WHERE u.is_super_admin = 0 AND u.username != 'psuper'
                """
                 
            cursor.execute(query)
            users = cursor.fetchall()
            
            self.user_table.setRowCount(0)
            for i, u in enumerate(users):
                self.user_table.insertRow(i)
                self.user_table.setItem(i, 0, QTableWidgetItem(str(u['id'])))
                self.user_table.setItem(i, 1, QTableWidgetItem(u['username']))
                self.user_table.setItem(i, 2, QTableWidgetItem(u['title'] or "Staff"))
                self.user_table.setItem(i, 3, QTableWidgetItem(u['role']))
                
                status = "Active" if u['is_active'] else "Inactive"
                status_item = QTableWidgetItem(status)
                if not u['is_active']:
                    status_item.setForeground(QColor("#e74c3c"))
                else:
                    status_item.setForeground(QColor("#2ecc71"))
                self.user_table.setItem(i, 4, status_item)
                
                self.user_table.setItem(i, 5, QTableWidgetItem(f"{u['base_salary']:,.0f}"))
                
                # Password Column logic
                username = u['username']
                if self.show_passwords and username in self.password_store:
                    password_display = self.password_store[username]
                    pass_item = QTableWidgetItem(password_display)
                    pass_item.setForeground(QColor("#e67e22")) # Orange for visible
                else:
                    if self.show_passwords:
                        pass_item = QTableWidgetItem("🔒 Encrypted") # Explicitly show it's encrypted
                    else:
                        pass_item = QTableWidgetItem("••••••••")
                    pass_item.setForeground(QColor("#95a5a6"))
                self.user_table.setItem(i, 6, pass_item)
                
                # Actions
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(5, 5, 5, 5) # Add padding
                btn_layout.setSpacing(5)
                
                edit_btn = QPushButton("Edit")
                style_button(edit_btn, variant="info", size="small")
                edit_btn.clicked.connect(lambda checked, uid=u['id']: self.edit_user(uid))
                btn_layout.addWidget(edit_btn)
                
                pass_btn = QPushButton("Reset Pass")
                style_button(pass_btn, variant="outline", size="small")
                pass_btn.clicked.connect(lambda checked, uid=u['id']: self.reset_password(uid))
                btn_layout.addWidget(pass_btn)
                
                toggle_btn = QPushButton("Deactivate" if u['is_active'] else "Activate")
                color = "#e74c3c" if u['is_active'] else "#2ecc71"
                toggle_btn.setStyleSheet(f"background-color: {color}; color: white; border-radius: 4px; padding: 4px;")
                toggle_btn.clicked.connect(lambda checked, uid=u['id'], s=u['is_active']: self.toggle_user(uid, s))
                btn_layout.addWidget(toggle_btn)
                
                self.user_table.setCellWidget(i, 7, btn_widget)

    def edit_user(self, user_id):
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, r.name as role 
                FROM users u 
                JOIN roles r ON u.role_id = r.id 
                WHERE u.id = ?
            """, (user_id,))
            user = cursor.fetchone()
            
            if user:
                user_data = dict(user)
                # Ensure permissions is a string
                if not user_data['permissions']: user_data['permissions'] = ''
                
                dialog = CreateUserDialog(self, user_data=user_data)
                if dialog.exec():
                    new_data = dialog.get_user_data()
                    # Store plaintext password if changed
                    if new_data.get('password'):
                        self.password_store[new_data['username']] = new_data['password']
                    self.update_existing_user(user_id, new_data)

    def update_existing_user(self, user_id, data):
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM roles WHERE name = ?", (data['role'],))
                role_id = cursor.fetchone()['id']
                
                base_query = "UPDATE users SET username=?, role_id=?, title=?, permissions=?, base_salary=?"
                params = [data['username'], role_id, data['title'], data['permissions'], data.get('base_salary', 0)]
                
                if data['password']:
                    new_hash = Auth.hash_password(data['password'])
                    base_query += ", password_hash=?"
                    params.append(new_hash)
                    
                if data.get('valid_until'): # Only update if present (SuperAdmin)
                    base_query += ", valid_until=?"
                    params.append(data['valid_until'])
                
                base_query += " WHERE id=?"
                params.append(user_id)
                
                cursor.execute(base_query, tuple(params))
                conn.commit()
            QMessageBox.information(self, "Success", "User updated successfully")
            self.load_users()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update user: {e}")

    def reset_password(self, uid):
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        new_pass, ok = QInputDialog.getText(self, "Reset Password", "Enter new password:", QLineEdit.EchoMode.Password)
        if ok and new_pass:
            new_hash = Auth.hash_password(new_pass)
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE id = ?", (uid,))
                uname = cursor.fetchone()['username']
                
                conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, uid))
                conn.commit()
                
                # Update store for "Show Password"
                self.password_store[uname] = new_pass
                
            QMessageBox.information(self, "Success", "Password updated")

    def toggle_user(self, uid, current_status):
        new_status = 0 if current_status else 1
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, uid))
            conn.commit()
        self.load_users()
