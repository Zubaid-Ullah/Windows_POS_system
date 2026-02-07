import os
import json
import socket
import qtawesome as qta
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QDate
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
LOCAL_SYSTEM_ID_PATH = os.path.expanduser("~/.faqiritech_pos_system_id.json")

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
        self.system_id_lbl.setStyleSheet("font-size: 14px; color: #64748b; font-family: 'Courier New';")
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

        # Prevent double fetch + safely handle deleted C++ objects
        try:
            if hasattr(self, 'fetch_worker') and self.fetch_worker and self.fetch_worker.isRunning():
                return
        except RuntimeError: self.fetch_worker = None

        # Show Loading Placeholder
        self.table.setRowCount(0)
        self.table.insertRow(0)
        loading_item = QTableWidgetItem("Fetching data from cloud... Please wait.")
        loading_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(0, 0, loading_item)
        self.table.setSpan(0, 0, 1, 7)

        from PyQt6.QtCore import QThread, pyqtSignal
        class FetchWorker(QThread):
            data_received = pyqtSignal(list)
            error_occurred = pyqtSignal(str)

            def __init__(self, supabase_client, parent=None):
                super().__init__(parent)
                self._supabase = supabase_client

            def run(self):
                try:
                    # According to register_installation.py order by installation_time DESC
                    res = self._supabase.table("installations").select("*").order("installation_time", desc=True).execute()
                    self.data_received.emit(res.data or [])
                except Exception as e:
                    self.error_occurred.emit(str(e))

        self.fetch_worker = FetchWorker(self.supabase)
        self.fetch_worker.data_received.connect(self._populate_table)
        self.fetch_worker.error_occurred.connect(lambda e: print(f"Fetch Error: {e}"))
        self.fetch_worker.finished.connect(self.fetch_worker.deleteLater)
        self.fetch_worker.start()

    def _populate_table(self, rows):
        from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
        self.table.setRowCount(0)
        for i, r in enumerate(rows):
            self.table.insertRow(i)
            
            sid = r.get('system_id', '')
            sid_item = QTableWidgetItem(sid)
            if sid == getattr(self, 'current_sid', None):
                sid_item.setText(f"{sid} (This PC)")
                sid_item.setBackground(Qt.GlobalColor.yellow)
            
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

            # Actions Layout
            btn_widget = QWidget()
            btn_lay = QHBoxLayout(btn_widget)
            btn_lay.setContentsMargins(2, 2, 2, 2)
            
            toggle_btn = QPushButton("Deactivate" if status == 'active' else "Activate")
            style_button(toggle_btn, variant="danger" if status == 'active' else "success", size="small")
            toggle_btn.clicked.connect(lambda checked, s_id=sid, curr_s=status: self.toggle_status(s_id, curr_s))
            btn_lay.addWidget(toggle_btn)
            
            extend_btn = QPushButton("Extend")
            style_button(extend_btn, variant="info", size="small")
            extend_btn.clicked.connect(lambda checked, s_id=sid: self.extend_contract(s_id))
            btn_lay.addWidget(extend_btn)

            shutdown_btn = QPushButton("Shutdown")
            style_button(shutdown_btn, variant="danger", size="small")
            shutdown_btn.setToolTip("Schedule or Cancel remote shutdown")
            shutdown_btn.clicked.connect(lambda checked, s_id=sid: self.remote_shutdown(s_id))
            btn_lay.addWidget(shutdown_btn)
            
            # Check for pending shutdown to show a "Abort" option
            if r.get('shutdown_time'):
                clear_btn = QPushButton("Abort")
                style_button(clear_btn, variant="warning", size="small")
                clear_btn.setToolTip("Clear pending shutdown request")
                clear_btn.clicked.connect(lambda checked, s_id=sid: self.abort_shutdown(s_id))
                btn_lay.addWidget(clear_btn)

            self.table.setCellWidget(i, 6, btn_widget)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def abort_shutdown(self, system_id):
        from src.core.supabase_manager import supabase_manager
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        
        key, ok = QInputDialog.getText(self, "Verification Required", 
                                     "Enter SuperAdmin SECRET KEY to ABORT shutdown:",
                                     QLineEdit.EchoMode.Password)
        if not ok or not key: return
        if not supabase_manager.verify_secret_key(key):
            QMessageBox.critical(self, "Access Denied", "Invalid Secret Key.")
            return

        # Move to background thread
        from PyQt6.QtCore import QThread, pyqtSignal
        class AbortWorker(QThread):
            success = pyqtSignal(str)
            error = pyqtSignal(str)
            
            def __init__(self, supabase_client, system_id):
                super().__init__()
                self.supabase = supabase_client
                self.system_id = system_id
            
            def run(self):
                try:
                    res = self.supabase.table("installations").update({"shutdown_time": None}).eq("system_id", self.system_id).execute()
                    if res.data:
                        self.success.emit(f"Remote shutdown for {self.system_id} has been cancelled.")
                    else:
                        self.error.emit("No data returned")
                except Exception as e:
                    self.error.emit(str(e))
        
        self.abort_thread = AbortWorker(self.supabase, system_id)
        self.abort_thread.success.connect(lambda msg: self._on_abort_success(msg))
        self.abort_thread.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Failed to abort: {err}"))
        self.abort_thread.finished.connect(self.abort_thread.deleteLater)
        self.abort_thread.start()
    
    def _on_abort_success(self, message):
        QMessageBox.information(self, "Cancelled", message)
        self.load_data()

    def remote_shutdown(self, system_id):
        from src.core.supabase_manager import supabase_manager
        from PyQt6.QtWidgets import QInputDialog, QLineEdit, QMessageBox
        from datetime import datetime, timedelta
        
        # 1. Verification
        key, ok = QInputDialog.getText(self, "Verification Required", 
                                     "Enter SuperAdmin SECRET KEY to schedule SHUTDOWN:",
                                     QLineEdit.EchoMode.Password)
        if not ok or not key: return
        if not supabase_manager.verify_secret_key(key):
            QMessageBox.critical(self, "Access Denied", "Invalid Secret Key.")
            return

        # 2. Pick Minutes Range
        minutes, ok = QInputDialog.getInt(self, "Schedule Shutdown", 
                                         f"Shut down system {system_id} in how many minutes?", 
                                         value=5, min=1, max=1440)
        if not ok: return

        confirm = QMessageBox.warning(self, "Confirm Remote Shutdown", 
                                     f"Are you sure you want to SHUT DOWN system {system_id} in {minutes} minutes?\n"
                                     "This will force a system shutdown on the client PC.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        
        if confirm == QMessageBox.StandardButton.Yes:
            target_time = (datetime.now() + timedelta(minutes=minutes)).isoformat()
            
            # Move Supabase update to background thread
            from PyQt6.QtCore import QThread, pyqtSignal
            class ShutdownScheduler(QThread):
                success = pyqtSignal(str)
                error = pyqtSignal(str)
                
                def __init__(self, supabase_client, system_id, target_time):
                    super().__init__()
                    self.supabase = supabase_client
                    self.system_id = system_id
                    self.target_time = target_time
                
                def run(self):
                    try:
                        res = self.supabase.table("installations").update({"shutdown_time": self.target_time}).eq("system_id", self.system_id).execute()
                        if res.data:
                            self.success.emit(f"Shutdown scheduled for {self.system_id} in {minutes} minutes.")
                        else:
                            self.error.emit("No data returned from update")
                    except Exception as e:
                        self.error.emit(str(e))
            
            self.shutdown_thread = ShutdownScheduler(self.supabase, system_id, target_time)
            self.shutdown_thread.success.connect(lambda msg: self._on_shutdown_scheduled(msg))
            self.shutdown_thread.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Update failed: {err}"))
            self.shutdown_thread.finished.connect(self.shutdown_thread.deleteLater)
            self.shutdown_thread.start()
    
    def _on_shutdown_scheduled(self, message):
        QMessageBox.information(self, "Success", message)
        self.load_data()

    def extend_contract(self, system_id):
        from src.core.supabase_manager import supabase_manager
        from PyQt6.QtWidgets import QInputDialog, QLineEdit, QCalendarWidget, QDialog, QVBoxLayout
        
        # 1. Verification
        key, ok = QInputDialog.getText(self, "Verification Required", 
                                     "Enter SuperAdmin SECRET KEY to extend contract:",
                                     QLineEdit.EchoMode.Password)
        if not ok or not key: return
        if not supabase_manager.verify_secret_key(key):
            QMessageBox.critical(self, "Access Denied", "Invalid Secret Key.")
            return

        # 2. Pick Date
        dialog = QDialog(self)
        dialog.setWindowTitle("Select New Expiry Date")
        vbox = QVBoxLayout(dialog)
        cal = QCalendarWidget()
        cal.setMinimumDate(QDate.currentDate())
        vbox.addWidget(cal)
        btn = QPushButton("Update Expiry Date")
        btn.clicked.connect(dialog.accept)
        vbox.addWidget(btn)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_date = cal.selectedDate().toString("yyyy-MM-dd")
            
            # Move to background thread
            from PyQt6.QtCore import QThread, pyqtSignal
            class ExtendWorker(QThread):
                success = pyqtSignal(str, str)
                error = pyqtSignal(str)
                
                def __init__(self, supabase_client, system_id, new_date):
                    super().__init__()
                    self.supabase = supabase_client
                    self.system_id = system_id
                    self.new_date = new_date
                
                def run(self):
                    try:
                        res = self.supabase.table("installations").update({"contract_expiry": self.new_date}).eq("system_id", self.system_id).execute()
                        if res.data:
                            self.success.emit(self.system_id, self.new_date)
                        else:
                            self.error.emit("No data returned")
                    except Exception as e:
                        self.error.emit(str(e))
            
            self.extend_thread = ExtendWorker(self.supabase, system_id, new_date)
            self.extend_thread.success.connect(lambda sid, date: self._on_extend_success(sid, date))
            self.extend_thread.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Update failed: {err}"))
            self.extend_thread.finished.connect(self.extend_thread.deleteLater)
            self.extend_thread.start()
    
    def _on_extend_success(self, system_id, new_date):
        QMessageBox.information(self, "Success", f"Contract for {system_id} extended to {new_date}")
        self.load_data()

    def toggle_status(self, system_id, current_status):
        from src.core.supabase_manager import supabase_manager
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        
        new_status = "deactivated" if current_status == "active" else "active"
        
        key, ok = QInputDialog.getText(self, "Verification Required", 
                                     f"Enter SuperAdmin SECRET KEY to {new_status} system {system_id}:",
                                     QLineEdit.EchoMode.Password)
        
        if not ok or not key:
            return

        if not supabase_manager.verify_secret_key(key):
            QMessageBox.critical(self, "Access Denied", "Invalid Secret Key. Action aborted.")
            return

        confirm = QMessageBox.question(self, "Confirm", f"Are you sure you want to {new_status} system {system_id}?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Move to background thread
            from PyQt6.QtCore import QThread, pyqtSignal
            class StatusToggleWorker(QThread):
                success = pyqtSignal(str, str)
                error = pyqtSignal(str)
                
                def __init__(self, supabase_client, system_id, new_status):
                    super().__init__()
                    self.supabase = supabase_client
                    self.system_id = system_id
                    self.new_status = new_status
                
                def run(self):
                    try:
                        res = self.supabase.table("installations").update({"status": self.new_status}).eq("system_id", self.system_id).execute()
                        if res.data:
                            self.success.emit(self.system_id, self.new_status)
                        else:
                            self.error.emit("Failed to update status")
                    except Exception as e:
                        self.error.emit(str(e))
            
            self.toggle_thread = StatusToggleWorker(self.supabase, system_id, new_status)
            self.toggle_thread.success.connect(lambda sid, status: self._on_toggle_success(sid, status))
            self.toggle_thread.error.connect(lambda err: QMessageBox.critical(self, "Error", f"Update failed: {err}"))
            self.toggle_thread.finished.connect(self.toggle_thread.deleteLater)
            self.toggle_thread.start()
    
    def _on_toggle_success(self, system_id, new_status):
        QMessageBox.information(self, "Success", f"System {system_id} is now {new_status}")
        self.load_data()
