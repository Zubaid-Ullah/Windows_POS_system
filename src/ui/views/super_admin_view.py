import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QLabel, QPushButton, QMessageBox, 
                             QDateEdit, QGroupBox, QRadioButton, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea)
from PyQt6.QtCore import Qt, QDate
from src.core.local_config import local_config
from src.core.supabase_manager import supabase_manager
from src.database.db_manager import db_manager
from src.ui.button_styles import style_button
from src.ui.views.user_management_view import UserManagementView

class SuperAdminView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("SUPER ADMIN CONTROL PANEL")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #c0392b; margin-bottom: 20px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #bdc3c7; }
            QTabBar::tab { background: #ecf0f1; padding: 10px 20px; font-weight: bold; }
            QTabBar::tab:selected { background: #3498db; color: white; }
        """)
        
        # User Management Tab using the shared component
        self.tabs.addTab(UserManagementView(), "User Management")
        
        # System Governance Tab
        self.tabs.addTab(self.create_system_tab(), "System Governance")

        # Credentials Tab (New)
        self.tabs.addTab(self.create_credentials_tab(), "System Credentials")
        
        layout.addWidget(self.tabs)

    def create_system_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System Activation
        gb_act = QGroupBox("System Activation & Time Period")
        layout_act = QVBoxLayout(gb_act)
        
        self.status_lbl = QLabel("System Status: UNKNOWN")
        self.status_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout_act.addWidget(self.status_lbl)
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Valid Until:"))
        self.valid_date = QDateEdit()
        self.valid_date.setDisplayFormat("yyyy-MM-dd")
        self.valid_date.setCalendarPopup(True)
        self.valid_date.setDate(QDate.currentDate().addYears(1))
        time_layout.addWidget(self.valid_date)
        
        update_time_btn = QPushButton("Extend License")
        update_time_btn.clicked.connect(self.update_validity)
        time_layout.addWidget(update_time_btn)
        layout_act.addLayout(time_layout)
        
        self.toggle_sys_btn = QPushButton("DEACTIVATE SYSTEM")
        style_button(self.toggle_sys_btn, variant="primary")
        self.toggle_sys_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; height: 40px;")
        self.toggle_sys_btn.clicked.connect(self.toggle_system_status)
        layout_act.addWidget(self.toggle_sys_btn)
        
        layout.addWidget(gb_act)
        
        # Database Mode
        gb_db = QGroupBox("Database Mode (Online/Offline)")
        layout_db = QHBoxLayout(gb_db)
        
        self.rb_offline = QRadioButton("Offline (Local Database)")
        self.rb_online = QRadioButton("Online (Cloud Sync)")
        
        layout_db.addWidget(self.rb_offline)
        layout_db.addWidget(self.rb_online)
        
        save_mode_btn = QPushButton("Save Mode")
        save_mode_btn.clicked.connect(self.save_db_mode)
        layout_db.addWidget(save_mode_btn)
        
        layout.addWidget(gb_db)
        
        self.load_system_settings()
        
        layout.addStretch()
        return tab

    def create_credentials_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info = QLabel("System Activation Credentials & Detailed Info")
        info.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(info)
        
        # Credentials Table
        self.cred_table = QTableWidget(0, 2)
        self.cred_table.setHorizontalHeaderLabels(["Field", "Value"])
        self.cred_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.cred_table.horizontalHeader().setStretchLastSection(True)
        self.cred_table.setAlternatingRowColors(True)
        self.cred_table.setStyleSheet("QTableWidget { gridline-color: #d1d1d1; }")
        
        layout.addWidget(self.cred_table)
        
        controls = QHBoxLayout()
        refresh_btn = QPushButton("Refresh from Cloud")
        style_button(refresh_btn, variant="info")
        refresh_btn.clicked.connect(self.load_credentials_data)
        controls.addWidget(refresh_btn)
        
        layout.addLayout(controls)
        
        self.load_credentials_data()
        return tab

    def load_credentials_data(self):
        data = []
        
        # 1. Load from local_config
        sid = local_config.get("system_id")
        data.append(("Local System ID", sid))
        data.append(("Registration Status", str(local_config.get("account_created"))))
        
        # 2. Load from useraccount.txt
        txt_path = os.path.join("credentials", "useraccount.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r") as f:
                    content = f.read()
                    data.append(("Local File Content", "--- useraccount.txt ---"))
                    for line in content.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            data.append((k.strip(), v.strip()))
            except: pass
            
        # 3. Load from Cloud (installations table)
        if sid:
            cloud_data = supabase_manager.get_installation_status(sid)
            if cloud_data:
                data.append(("--- CLOUD DATA ---", "--- (installations table) ---"))
                for k, v in cloud_data.items():
                    data.append((f"Cloud: {k}", str(v)))
        
        self.cred_table.setRowCount(0)
        for i, (k, v) in enumerate(data):
            self.cred_table.insertRow(i)
            self.cred_table.setItem(i, 0, QTableWidgetItem(k))
            self.cred_table.setItem(i, 1, QTableWidgetItem(v))
        
        self.cred_table.resizeRowsToContents()

    def load_system_settings(self):
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_settings WHERE id = 1")
            settings = cursor.fetchone()
            
            if settings:
                is_active = settings['is_active']
                mode = settings['mode']
                valid_until = settings['valid_until']
                
                if is_active:
                    self.status_lbl.setText("System Status: ACTIVE ✅")
                    self.status_lbl.setStyleSheet("color: green; font-size: 18px; font-weight: bold;")
                    self.toggle_sys_btn.setText("DEACTIVATE SYSTEM")
                else:
                    self.status_lbl.setText("System Status: INACTIVE ❌")
                    self.status_lbl.setStyleSheet("color: red; font-size: 18px; font-weight: bold;")
                    self.toggle_sys_btn.setText("ACTIVATE SYSTEM")
                
                if mode == 'ONLINE':
                    self.rb_online.setChecked(True)
                else:
                    self.rb_offline.setChecked(True)
                    
                if valid_until:
                    try:
                        qdate = QDate.fromString(valid_until[:10], "yyyy-MM-dd")
                        self.valid_date.setDate(qdate)
                    except: pass

    def update_validity(self):
        new_date = self.valid_date.date().toString("yyyy-MM-dd 23:59:59")
        # Update both databases for consistency
        for db_func in [db_manager.get_connection, db_manager.get_pharmacy_connection]:
            try:
                with db_func() as conn:
                    conn.execute("UPDATE system_settings SET valid_until = ? WHERE id = 1", (new_date,))
                    conn.commit()
            except: pass
        QMessageBox.information(self, "Success", f"System license extended until {new_date}")

    def toggle_system_status(self):
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_active FROM system_settings WHERE id = 1")
            current = cursor.fetchone()['is_active']
            new_status = 0 if current else 1
            
        # Apply to both
        for db_func in [db_manager.get_connection, db_manager.get_pharmacy_connection]:
            try:
                with db_func() as conn:
                    conn.execute("UPDATE system_settings SET is_active = ? WHERE id = 1", (new_status,))
                    conn.commit()
            except: pass
        self.load_system_settings()

    def save_db_mode(self):
        mode = 'ONLINE' if self.rb_online.isChecked() else 'OFFLINE'
        for db_func in [db_manager.get_connection, db_manager.get_pharmacy_connection]:
            try:
                with db_func() as conn:
                    conn.execute("UPDATE system_settings SET mode = ? WHERE id = 1", (mode,))
                    conn.commit()
            except: pass
        QMessageBox.information(self, "Saved", f"Database mode set to: {mode}")
