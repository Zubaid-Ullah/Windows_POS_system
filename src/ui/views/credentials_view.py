import os
import json
import socket
import qtawesome as qta
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button

# Suppress warnings if supabase is not installed, but it should be in requirements
try:
    from supabase import create_client
except ImportError:
    create_client = None

# Credentials from the provided files
SUPABASE_URL = "https://gwmtlvquhlqtkyynuexf.supabase.co"
SUPABASE_KEY = "sb_publishable_4KVNe1OfSa9BK7b5ALuQyQ_q4Igic6Z"
LOCAL_SYSTEM_ID_PATH = os.path.expanduser("~/.afex_pos_system_id.json")

class CredentialsView(QWidget):
    def __init__(self):
        super().__init__()
        self.supabase = None
        if create_client:
            try:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e:
                print(f"Supabase init error: {e}")
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Header Info Frame
        info_frame = QFrame()
        info_frame.setObjectName("header_info_frame")
        info_frame.setStyleSheet("""
            #header_info_frame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        info_lay = QHBoxLayout(info_frame)
        
        # Left side: Current System Info
        sys_info_lay = QVBoxLayout()
        header_title = QLabel("Installation Credentials")
        header_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e293b;")
        sys_info_lay.addWidget(header_title)
        
        self.system_id_lbl = QLabel("System ID: Loading...")
        self.system_id_lbl.setStyleSheet("font-size: 14px; color: #64748b; font-family: monospace;")
        sys_info_lay.addWidget(self.system_id_lbl)
        
        self.pc_name_lbl = QLabel(f"PC Name: {socket.gethostname()}")
        self.pc_name_lbl.setStyleSheet("font-size: 14px; color: #64748b;")
        sys_info_lay.addWidget(self.pc_name_lbl)
        
        info_lay.addLayout(sys_info_lay)
        info_lay.addStretch()
        
        # Right side: Actions
        actions_lay = QVBoxLayout()
        refresh_btn = QPushButton(" Refresh Data")
        refresh_btn.setIcon(qta.icon("fa5s.sync", color="white"))
        style_button(refresh_btn, variant="primary")
        refresh_btn.clicked.connect(self.load_data)
        actions_lay.addWidget(refresh_btn)
        
        info_lay.addLayout(actions_lay)
        layout.addWidget(info_frame)

        # Table Container
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "System ID", "PC Name", "Company", "Status", "Expiry", "Last Check-in", "Actions"
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        layout.addWidget(self.table)

        self.load_local_info()

    def load_local_info(self):
        if os.path.exists(LOCAL_SYSTEM_ID_PATH):
            try:
                with open(LOCAL_SYSTEM_ID_PATH, "r") as f:
                    data = json.load(f)
                    sid = data.get('system_id', 'Unknown')
                    self.system_id_lbl.setText(f"System ID: {sid}")
                    self.current_sid = sid
            except:
                self.system_id_lbl.setText("System ID: Error reading file")
                self.current_sid = None
        else:
            self.system_id_lbl.setText("System ID: Not registered on this PC")
            self.current_sid = None

    def load_data(self):
        if not self.supabase:
            QMessageBox.warning(self, "Supabase Error", "Supabase client not initialized. Check your connection or credentials.")
            return

        try:
            # According to register_installation.py order by installation_time DESC
            res = self.supabase.table("installations").select("*").order("installation_time", desc=True).execute()
            rows = res.data or []

            self.table.setRowCount(0)
            for i, r in enumerate(rows):
                self.table.insertRow(i)
                
                sid = r.get('system_id', '')
                sid_item = QTableWidgetItem(sid)
                if sid == getattr(self, 'current_sid', None):
                    sid_item.setText(f"{sid} (This PC)")
                    sid_item.setBackground(Qt.GlobalColor.yellow if sid else Qt.GlobalColor.transparent)
                
                self.table.setItem(i, 0, sid_item)
                self.table.setItem(i, 1, QTableWidgetItem(r.get('pc_name', '')))
                self.table.setItem(i, 2, QTableWidgetItem(r.get('company_name', '')))
                
                status = r.get('status', 'unknown')
                status_item = QTableWidgetItem(status.upper())
                if status == 'active':
                    status_item.setForeground(Qt.GlobalColor.green)
                else:
                    status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(i, 3, status_item)
                
                self.table.setItem(i, 4, QTableWidgetItem(r.get('contract_expiry', '')))
                self.table.setItem(i, 5, QTableWidgetItem(r.get('installation_time', '')))

                # Actions
                btn_widget = QWidget()
                btn_lay = QHBoxLayout(btn_widget)
                btn_lay.setContentsMargins(2, 2, 2, 2)
                
                toggle_btn = QPushButton("Deactivate" if status == 'active' else "Activate")
                style_button(toggle_btn, variant="danger" if status == 'active' else "success", size="small")
                toggle_btn.clicked.connect(lambda checked, s_id=sid, curr_s=status: self.toggle_status(s_id, curr_s))
                btn_lay.addWidget(toggle_btn)
                
                self.table.setCellWidget(i, 6, btn_widget)

            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()

        except Exception as e:
            print(f"Failed to fetch installations: {e}")
            # Don't show error dialog - this is likely a network issue and doesn't affect local operations

    def toggle_status(self, system_id, current_status):
        new_status = "deactivated" if current_status == "active" else "active"
        confirm = QMessageBox.question(self, "Confirm", f"Are you sure you want to {new_status} system {system_id}?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                res = self.supabase.table("installations").update({"status": new_status}).eq("system_id", system_id).execute()
                if res.data:
                    QMessageBox.information(self, "Success", f"System {system_id} is now {new_status}")
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", "Failed to update status.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Update failed: {e}")
