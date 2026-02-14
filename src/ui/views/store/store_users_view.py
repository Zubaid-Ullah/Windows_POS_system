import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from src.database.db_manager import db_manager
from src.core.auth import Auth
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button
from src.ui.dialogs.create_user_dialog import CreateUserDialog


class StoreUsersView(QWidget):
    def __init__(self):
        super().__init__()
        self.show_passwords = False
        self.password_store = {}
        self.is_loading = False

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(300)
        self.refresh_timer.timeout.connect(self._do_load_users)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("User Management")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a3a8a; margin-bottom: 20px;")
        layout.addWidget(header)

        gb_add = QGroupBox("Create New User")
        form_layout = QHBoxLayout(gb_add)

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

        self.user_table = QTableWidget(0, 8)
        self.user_table.setHorizontalHeaderLabels([
            "Photo", "Username", "Title", "Role", "Status", "Base Salary", "Password", "Actions"
        ])
        style_table(self.user_table, variant="premium")

        header = self.user_table.horizontalHeader()
        self.user_table.setColumnWidth(0, 60)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.user_table)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_users()

    def hideEvent(self, event):
        self.refresh_timer.stop()
        super().hideEvent(event)

    def toggle_password_visibility(self):
        self.show_passwords = not self.show_passwords
        if self.show_passwords:
            self.password_toggle_btn.setText("🙈 Hide Passwords")
            QMessageBox.information(
                self,
                "Password Security",
                "Passwords are securely hashed. Only passwords set/changed in this session can be revealed.\n\n"
                "To see a password for an existing user, you must Reset it."
            )
        else:
            self.password_toggle_btn.setText("👁️ Show Passwords")
        self.load_users()

    def load_users(self):
        self.refresh_timer.start()

    def _do_load_users(self):
        from PyQt6.QtWidgets import QApplication
        if QApplication.applicationState() != Qt.ApplicationState.ApplicationActive or not self.isVisible():
            return
        if self.is_loading:
            return
        self.is_loading = True
        self.load_users_logic()

    def load_users_logic(self):
        from src.core.blocking_task_manager import task_manager
        current_user = Auth.get_current_user()

        def fetch_users():
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                if current_user.get('username') == 'superadmin' or current_user.get('is_super_admin'):
                    query = """
                        SELECT u.id, u.username, u.title, r.name as role, u.is_active, u.permissions, u.password_hash, u.base_salary, u.profile_picture
                        FROM users u
                        JOIN roles r ON u.role_id = r.id
                        WHERE u.username != 'psuper'
                    """
                else:
                    query = """
                        SELECT u.id, u.username, u.title, r.name as role, u.is_active, u.permissions, u.password_hash, u.base_salary, u.profile_picture
                        FROM users u
                        JOIN roles r ON u.role_id = r.id
                        WHERE u.is_super_admin = 0 AND u.username != 'psuper'
                    """
                cursor.execute(query)
                return [dict(u) for u in cursor.fetchall()]

        def on_finished(users):
            self.is_loading = False
            self.user_table.setRowCount(0)
            for i, u in enumerate(users):
                self.user_table.insertRow(i)
                # Photo Column (0)
                photo_lbl = QLabel()
                photo_lbl.setFixedSize(40, 40)
                photo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                photo_lbl.setStyleSheet("border-radius: 20px; border: 1px solid #ddd; background: #f8f9fa;")
                
                photo_path = u.get('profile_picture')
                if photo_path and os.path.exists(photo_path):
                    photo_lbl.setToolTip(f'<img src="{photo_path}" width="150">')
                    self.load_thumbnail_async(photo_path, photo_lbl)
                else:
                    import qtawesome as qta
                    photo_lbl.setPixmap(qta.icon("fa5s.user", color="#cbd5e1").pixmap(24, 24))
                
                self.user_table.setCellWidget(i, 0, photo_lbl)
                
                self.user_table.setItem(i, 1, QTableWidgetItem(u['username']))
                self.user_table.setItem(i, 2, QTableWidgetItem(u['title'] or "Staff"))
                self.user_table.setItem(i, 3, QTableWidgetItem(u['role']))
                
                status = "Active" if u['is_active'] else "Inactive"
                status_item = QTableWidgetItem(status)
                status_item.setForeground(QColor("#2ecc71" if u['is_active'] else "#e74c3c"))
                self.user_table.setItem(i, 4, status_item)
                self.user_table.setItem(i, 5, QTableWidgetItem(f"{u['base_salary']:,.0f}"))

                username = u['username']
                if self.show_passwords and username in self.password_store:
                    pass_item = QTableWidgetItem(self.password_store[username])
                    pass_item.setForeground(QColor("#e67e22"))
                else:
                    pass_item = QTableWidgetItem("🔒 Encrypted" if self.show_passwords else "••••••••")
                    pass_item.setForeground(QColor("#95a5a6"))
                self.user_table.setItem(i, 6, pass_item)

                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(5, 5, 5, 5)
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

        def on_error(_):
            self.is_loading = False

        task_manager.run_task(fetch_users, on_finished=on_finished, on_error=on_error)

    def load_thumbnail_async(self, path, label):
        from src.core.blocking_task_manager import task_manager
        from PyQt6.QtGui import QImage, QPixmap

        def scale_image():
            try:
                img = QImage(path)
                if img.isNull(): return None
                # Scaled for Users view circle
                return img.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            except: return None

        def on_finished(scaled_img):
            if scaled_img:
                label.setPixmap(QPixmap.fromImage(scaled_img))

        task_manager.run_task(scale_image, on_finished=on_finished)

    def open_create_user_dialog(self):
        dialog = CreateUserDialog(self)
        if dialog.exec():
            user_data = dialog.get_user_data()
            if user_data.get('password'):
                self.password_store[user_data['username']] = user_data['password']
            self.create_user_with_permissions(user_data)

    def create_user_with_permissions(self, user_data):
        from src.core.blocking_task_manager import task_manager

        def do_create():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM roles WHERE name = ?", (user_data['role'],))
                    role_row = cursor.fetchone()
                    if not role_row:
                        return {"success": False, "error": f"Role '{user_data['role']}' not found"}

                    role_id = role_row['id']
                    password_hash = Auth.hash_password(user_data['password'])
                    valid_until = user_data.get('valid_until')

                    cursor.execute("""
                        INSERT INTO users (username, password_hash, role_id, title, permissions, valid_until, base_salary, is_active, profile_picture)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """, (user_data['username'], password_hash, role_id, user_data['title'],
                          user_data['permissions'], valid_until, user_data.get('base_salary', 0),
                          user_data.get('profile_picture')))
                    conn.commit()
                return {"success": True, "username": user_data['username']}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(res):
            if res["success"]:
                QMessageBox.information(self, "Success", f"User '{res['username']}' created successfully!")
                self.load_users()
            else:
                QMessageBox.critical(self, "Error", f"Failed to create user: {res['error']}")

        task_manager.run_task(do_create, on_finished=on_finished)

    def edit_user(self, user_id):
        from src.core.blocking_task_manager import task_manager

        def fetch_edit():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT u.*, r.name as role
                        FROM users u
                        JOIN roles r ON u.role_id = r.id
                        WHERE u.id = ?
                    """, (user_id,))
                    res = cursor.fetchone()
                    return {"success": True, "user": dict(res) if res else None}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(result):
            if not result["success"]:
                QMessageBox.critical(self, "Error", result["error"])
                return

            user = result["user"]
            if user:
                user_data = user
                if not user_data['permissions']:
                    user_data['permissions'] = ''
                dialog = CreateUserDialog(self, user_data=user_data)
                if dialog.exec():
                    new_data = dialog.get_user_data()
                    if new_data.get('password'):
                        self.password_store[new_data['username']] = new_data['password']
                    self.update_existing_user(user_id, new_data)

        task_manager.run_task(fetch_edit, on_finished=on_finished)

    def update_existing_user(self, user_id, data):
        from src.core.blocking_task_manager import task_manager

        def do_update():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM roles WHERE name = ?", (data['role'],))
                    role_id = cursor.fetchone()['id']

                    base_query = "UPDATE users SET username=?, role_id=?, title=?, permissions=?, base_salary=?, profile_picture=?"
                    params = [data['username'], role_id, data['title'], data['permissions'], data.get('base_salary', 0), data.get('profile_picture')]

                    if data['password']:
                        new_hash = Auth.hash_password(data['password'])
                        base_query += ", password_hash=?"
                        params.append(new_hash)
                    if data.get('valid_until'):
                        base_query += ", valid_until=?"
                        params.append(data['valid_until'])

                    base_query += " WHERE id=?"
                    params.append(user_id)
                    cursor.execute(base_query, tuple(params))
                    conn.commit()
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(res):
            if res["success"]:
                QMessageBox.information(self, "Success", "User updated successfully")
                self.load_users()
            else:
                QMessageBox.critical(self, "Error", f"Failed to update user: {res['error']}")

        task_manager.run_task(do_update, on_finished=on_finished)

    def reset_password(self, uid):
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        new_pass, ok = QInputDialog.getText(self, "Reset Password", "Enter new password:", QLineEdit.EchoMode.Password)
        if ok and new_pass:
            from src.core.blocking_task_manager import task_manager

            def do_reset():
                try:
                    new_hash = Auth.hash_password(new_pass)
                    with db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT username FROM users WHERE id = ?", (uid,))
                        uname = cursor.fetchone()['username']
                        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, uid))
                        conn.commit()
                    return {"success": True, "username": uname}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            def on_finished(res):
                if res["success"]:
                    self.password_store[res["username"]] = new_pass
                    QMessageBox.information(self, "Success", "Password updated")
                    self.load_users()
                else:
                    QMessageBox.critical(self, "Error", f"Reset failed: {res['error']}")

            task_manager.run_task(do_reset, on_finished=on_finished)

    def toggle_user(self, uid, current_status):
        from src.core.blocking_task_manager import task_manager
        new_status = 0 if current_status else 1

        def do_toggle():
            try:
                with db_manager.get_connection() as conn:
                    conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, uid))
                    conn.commit()
                return True
            except Exception:
                return False

        task_manager.run_task(do_toggle, on_finished=lambda _: self.load_users())
