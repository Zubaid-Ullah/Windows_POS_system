from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QPushButton, QLabel, QHeaderView, QGroupBox,
                             QFormLayout, QLineEdit, QComboBox, QMessageBox, QTableWidgetItem,
                             QCheckBox, QScrollArea, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt
import json
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.core.pharmacy_auth import PharmacyAuth as Auth
from src.database.db_manager import db_manager
from src.core.localization import lang_manager

class PharmacyUsersView(QWidget):
    def __init__(self):
        super().__init__()
        self.show_passwords = False
        self.password_store = {}  # Store plaintext passwords temporarily
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Main Splitter-like Layout
        content_layout = QHBoxLayout()
        
        
        # Left Side: Creation Form
        form_container = QFrame()
        form_container.setFixedWidth(400)
        from_v_layout = QVBoxLayout(form_container)
        
        # Add New User Header Button
        add_user_header = QHBoxLayout()
        header_label = QLabel(f"<b>{lang_manager.get('user_management')}</b>")
        header_label.setStyleSheet("font-size: 16px;")
        
        # Password Visibility Toggle
        self.password_toggle_btn = QPushButton(lang_manager.get("show_passwords_icon"))
        style_button(self.password_toggle_btn, variant="warning", size="small")
        self.password_toggle_btn.clicked.connect(self.toggle_password_visibility)
        
        add_user_btn = QPushButton(lang_manager.get("add_new_user_icon"))
        style_button(add_user_btn, variant="success", size="small")
        add_user_btn.clicked.connect(self.clear_form)
        add_user_header.addWidget(header_label)
        add_user_header.addStretch()
        add_user_header.addWidget(self.password_toggle_btn)
        add_user_header.addWidget(add_user_btn)
        from_v_layout.addLayout(add_user_header)
        
        gb = QGroupBox(lang_manager.get("user_details"))
        from_v_layout.addWidget(gb)
        form = QFormLayout(gb)
        form.setSpacing(15)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(lang_manager.get("enter_username"))
        self.username_input.setFixedHeight(55)
        self.username_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.username_input.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.username_input.setStyleSheet("border: 1px solid black;")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(lang_manager.get("enter_password"))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(55)
        self.password_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.password_input.setStyleSheet("border: 1px solid black;")
        
        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems([lang_manager.get("pharmacist"), lang_manager.get("manager")])
        self.role_combo.setFixedHeight(55)
        self.role_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.role_combo.setStyleSheet("border: 1px solid black;")
        form.addRow(f"{lang_manager.get('role')}:", self.role_combo)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(lang_manager.get("e.g._senior_pharmacist"))
        self.title_input.setFixedHeight(55)
        self.title_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.title_input.setStyleSheet("border: 1px solid black;")

        form.addRow(f"{lang_manager.get('username')} *:", self.username_input)
        form.addRow(f"{lang_manager.get('password')} *:", self.password_input)
        form.addRow(f"{lang_manager.get('title')}:", self.title_input)
        
        # Permissions Section
        perm_label = QLabel(f"<b>{lang_manager.get('assign_features_permissions')}</b>")
        form.addRow(perm_label)
        
        self.perm_area = QScrollArea()
        self.perm_area.setWidgetResizable(True)
        self.perm_area.setFixedHeight(250)
        perm_widget = QWidget()
        self.perm_layout = QVBoxLayout(perm_widget)
        
        self.features = [
            ("pharmacy_dashboard", lang_manager.get("pharmacy_dashboard")),
            ("pharmacy_sales", lang_manager.get("pharmacy_sales_pos")),
            ("pharmacy_inventory", lang_manager.get("pharmacy_inventory")),
            ("pharmacy_customers", lang_manager.get("pharmacy_customers")),
            ("pharmacy_suppliers", lang_manager.get("medicine_suppliers")),
            ("pharmacy_loans", lang_manager.get("credit_loan_control")),
            ("pharmacy_reports", lang_manager.get("pharmacy_reports")),
            ("pharmacy_finance", lang_manager.get("pharmacy_finance")),
            ("pharmacy_price_check", lang_manager.get("medicine_price_check")),
            ("pharmacy_returns", lang_manager.get("returns_replacements")),
            ("pharmacy_users", lang_manager.get("pharmacy_user_management")),
            ("pharmacy_settings", lang_manager.get("pharmacy_settings"))
        ]
        
        self.feature_checkboxes = {}
        for key, label in self.features:
            cb = QCheckBox(label)
            self.perm_layout.addWidget(cb)
            self.feature_checkboxes[key] = cb
            
        self.perm_area.setWidget(perm_widget)
        form.addRow(self.perm_area)
        
        save_btn = QPushButton(lang_manager.get("save"))
        style_button(save_btn, variant="success")
        save_btn.clicked.connect(self.save_user)
        form.addRow(save_btn)
        
        content_layout.addWidget(form_container)
        
        # Right Side: Table
        table_container = QFrame()
        table_layout = QVBoxLayout(table_container)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            lang_manager.get("id"),
            lang_manager.get("username"),
            lang_manager.get("password"),
            lang_manager.get("assigned_features"),
            lang_manager.get("actions")
        ])
        style_table(self.table, variant="premium")
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Username
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Password
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Features
        
        table_layout.addWidget(self.table)
        content_layout.addWidget(table_container)
        
        layout.addLayout(content_layout)
        
        self.load_users()

    def toggle_password_visibility(self):
        self.show_passwords = not self.show_passwords
        if self.show_passwords:
            self.password_toggle_btn.setText("🙈 Hide Passwords")
        else:
            self.password_toggle_btn.setText("👁️ Show Passwords")
        self.load_users()
    
    def save_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        title = self.title_input.text().strip()
        
        if not username:
             QMessageBox.warning(self, "Error", "Username is required")
             return
        
        # Store plaintext password if provided
        if password:
            self.password_store[username] = password
             
        # Collect permissions
        perms = [k for k, cb in self.feature_checkboxes.items() if cb.isChecked()]
        perms_json = json.dumps(perms)
        
        # Get role from combo
        role_name = self.role_combo.currentText()
        
        # Hash password if provided
        hashed_pw = Auth.hash_password(password) if password else None
        
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # Check if exists
                existing = conn.execute("SELECT id FROM pharmacy_users WHERE username = ?", (username,)).fetchone()
                
                if existing:
                    if hashed_pw:
                        conn.execute("""
                            UPDATE pharmacy_users SET password_hash=?, title=?, permissions=?, role=?
                            WHERE id=?
                        """, (hashed_pw, title, perms_json, role_name, existing['id']))
                    else:
                        conn.execute("""
                            UPDATE pharmacy_users SET title=?, permissions=?, role=?
                            WHERE id=?
                        """, (title, perms_json, role_name, existing['id']))
                else:
                    if not password:
                         QMessageBox.warning(self, "Error", "Password is required for new users")
                         return
                    # Create new user
                    conn.execute("""
                        INSERT INTO pharmacy_users (username, password_hash, title, permissions, role)
                        VALUES (?, ?, ?, ?, ?)
                    """, (username, hashed_pw, title, perms_json, role_name))
                
                conn.commit()
            
            QMessageBox.information(self, "Success", "Pharmacy User saved successfully")
            self.load_users()
            self.clear_form()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_users(self):
        self.table.setRowCount(0)
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # Show all pharmacy users except psuper
                rows = conn.execute("""
                    SELECT * FROM pharmacy_users
                    WHERE is_active = 1 AND username != 'psuper'
                    ORDER BY id DESC
                """).fetchall()
                
                for i, row in enumerate(rows):
                    self.table.insertRow(i)
                    self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                    self.table.setItem(i, 1, QTableWidgetItem(row['username']))
                    
                    # Password column - show actual password if available, otherwise show masked
                    username = row['username']
                    if self.show_passwords and username in self.password_store:
                        password_display = self.password_store[username]
                    else:
                        password_display = "••••••••"  # Masked by default
                    
                    password_item = QTableWidgetItem(password_display)
                    password_item.setForeground(Qt.GlobalColor.gray if not self.show_passwords else Qt.GlobalColor.blue)
                    self.table.setItem(i, 2, password_item)
                    
                    perms = []
                    if row['permissions']:
                        try:
                            perms = json.loads(row['permissions'])
                        except:
                            perms = [row['permissions']]
                    
                    self.table.setItem(i, 3, QTableWidgetItem(", ".join(perms)))
                    
                    actions = QWidget()
                    act_layout = QHBoxLayout(actions)
                    act_layout.setContentsMargins(0,0,0,0)
                    act_layout.setSpacing(5)
                    
                    edit_btn = QPushButton("Edit")
                    style_button(edit_btn, variant="info", size="small")
                    edit_btn.clicked.connect(lambda ch, r=row: self.edit_user(r))
                    
                    del_btn = QPushButton("Del")
                    style_button(del_btn, variant="danger", size="small")
                    del_btn.clicked.connect(lambda ch, uid=row['id']: self.delete_user(uid))
                    
                    act_layout.addWidget(edit_btn)
                    act_layout.addWidget(del_btn)
                    self.table.setCellWidget(i, 4, actions)
        except Exception as e:
            print(f"Error loading users: {e}")

    def edit_user(self, user_row):
        self.username_input.setText(user_row['username'])
        self.password_input.setText("") # Don't show hashed password
        self.title_input.setText(user_row['title'] or "")
        self.role_combo.setCurrentText(user_row['role'] or "Pharmacist")
        
        perms = []
        if user_row['permissions']:
            try:
                perms = json.loads(user_row['permissions'])
            except:
                perms = [user_row['permissions']]
        
        for key, cb in self.feature_checkboxes.items():
            cb.setChecked(key in perms)

    def delete_user(self, uid):
        if QMessageBox.question(self, "Confirm", "Deactivate this pharmacy user?") == QMessageBox.StandardButton.Yes:
            with db_manager.get_pharmacy_connection() as conn:
                conn.execute("UPDATE pharmacy_users SET is_active=0 WHERE id=?", (uid,))
                conn.commit()
            self.load_users()

    def clear_form(self):
        self.username_input.clear()
        self.password_input.clear()
        self.title_input.clear()
        for cb in self.feature_checkboxes.values():
            cb.setChecked(False)
