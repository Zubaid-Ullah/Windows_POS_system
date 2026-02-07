from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QFrame, QComboBox, QMessageBox, QFileDialog, QGridLayout,
                             QTabWidget, QGroupBox, QFormLayout, QTextEdit, QScrollArea, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
import qtawesome as qta
import qrcode
from src.core.localization import lang_manager
from src.utils.backup import BackupManager
from src.ui.theme_manager import theme_manager
from src.database.db_manager import db_manager
from src.ui.button_styles import style_button
from src.core.supabase_manager import supabase_manager
from src.core.local_config import local_config
from src.core.autostart_helper import AutoStartHelper
import os
import platform

class SettingsSyncWorker(QThread):
    finished = pyqtSignal(bool, dict) # success, data
    saved = pyqtSignal(bool)

    def __init__(self, task="load", sid=None, payload=None):
        super().__init__()
        self.task = task
        self.sid = sid
        self.payload = payload

    def run(self):
        try:
            if self.task == "load":
                if supabase_manager.check_connection():
                    data = supabase_manager.get_installation_status(self.sid)
                    self.finished.emit(True, data if data else {})
                else:
                    self.finished.emit(False, {})
            elif self.task == "sync":
                if supabase_manager.check_connection():
                    success = supabase_manager.update_company_details(self.sid, self.payload)
                    self.saved.emit(success)
                else:
                    self.saved.emit(False)
        except Exception as e:
            print(f"SettingsSyncWorker Error: {e}")
            self.finished.emit(False, {})

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.sync_thread = None
        self.is_syncing = False
        self.init_ui()
        
        # Background Sync Timer for offline changes
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.check_and_sync_online)
        self.sync_timer.start(30000) # Every 30 seconds

    def cleanup_thread(self):
        if self.sync_thread:
            try:
                if self.sync_thread.isRunning():
                    self.sync_thread.quit()
                    self.sync_thread.wait(500)
            except RuntimeError:
                pass
        self.sync_thread = None

    def create_card(self, title, icon_name):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color="#2196f3").pixmap(24, 24))
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #f0f0f0;")
        layout.addWidget(line)
        
        return card, layout

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(0)

        # Create tabs
        tabs = QTabWidget()
        tabs.setObjectName("settings_tabs")
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e5f2;
                background: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #f8f9fa;
                border: 1px solid #e0e5f2;
                padding: 12px 24px;
                margin-right: 2px;
                border-radius: 8px 8px 0 0;
                font-size: 14px;
                font-weight: 500;
                color: #666;
            }
            QTabBar::tab:selected {
                background: white;
                color: #4318ff;
                border-bottom: 3px solid #4318ff;
            }
            QTabBar::tab:hover {
                background: #e8f4fd;
                color: #4318ff;
            }
        """)

        tabs.addTab(self.create_appearance_tab(), "Appearance")
        tabs.addTab(self.create_company_tab(), "Company")
        tabs.addTab(self.create_maintenance_tab(), "Maintenance")
        tabs.addTab(self.create_backup_tab(), "Backup")

        main_layout.addWidget(tabs)

    def create_appearance_tab(self):
        """Create appearance settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)

        # Appearance Section
        app_card, app_layout = self.create_card("Appearance Settings", "fa5s.palette")

        app_layout.addWidget(QLabel("Interface Theme"))
        self.theme_box = QComboBox()
        self.theme_box.addItems(["Light Mode", "Night Mode", "System Default"])

        mode_idx = 0
        if theme_manager.theme_mode == "DARK": mode_idx = 1
        elif theme_manager.theme_mode == "SYSTEM": mode_idx = 2

        self.theme_box.setCurrentIndex(mode_idx)
        self.theme_box.setFixedHeight(40)
        self.theme_box.currentIndexChanged.connect(self.change_theme)
        app_layout.addWidget(self.theme_box)

        app_layout.addWidget(QLabel("System Language"))
        self.lang_box = QComboBox()
        self.lang_box.addItem("English", "en")
        self.lang_box.addItem("Pashto (پښتو)", "ps")
        self.lang_box.addItem("Dari (دری)", "dr")
        self.lang_box.setCurrentIndex(self.lang_box.findData(lang_manager.current_lang))
        self.lang_box.setFixedHeight(40)
        self.lang_box.currentIndexChanged.connect(self.change_language)
        app_layout.addWidget(self.lang_box)

        layout.addWidget(app_card)
        layout.addStretch()
        return tab

    def create_company_tab(self):
        """Create company information tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Company Information Group
        company_group = QGroupBox("Company Information")
        company_form = QFormLayout(company_group)

        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Enter company name")

        self.company_address = QTextEdit()
        self.company_address.setMaximumHeight(80)
        self.company_address.setPlaceholderText("Enter company address")

        self.company_phone = QLineEdit()
        self.company_phone.setPlaceholderText("Enter phone number")

        self.company_email = QLineEdit()
        self.company_email.setPlaceholderText("Enter email address")

        company_form.addRow("Company Name:", self.company_name)
        company_form.addRow("Address:", self.company_address)
        company_form.addRow("Phone:", self.company_phone)
        company_form.addRow("Email:", self.company_email)

        layout.addWidget(company_group)

        # WhatsApp QR Code Group
        whatsapp_group = QGroupBox("WhatsApp Integration")
        whatsapp_layout = QVBoxLayout(whatsapp_group)

        # WhatsApp number input
        whatsapp_form = QFormLayout()
        self.whatsapp_number = QLineEdit()
        self.whatsapp_number.setPlaceholderText("Enter WhatsApp number (e.g., +1234567890)")
        whatsapp_form.addRow("WhatsApp Number:", self.whatsapp_number)

        whatsapp_layout.addLayout(whatsapp_form)

        # QR Code display and generate button
        qr_layout = QHBoxLayout()

        self.qr_label = QLabel()
        self.qr_label.setFixedSize(200, 200)
        self.qr_label.setStyleSheet("border: 1px solid #ccc; background: white;")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        qr_layout.addWidget(self.qr_label)

        qr_controls = QVBoxLayout()
        self.generate_qr_btn = QPushButton("Generate QR Code")
        style_button(self.generate_qr_btn, variant="primary")
        self.generate_qr_btn.clicked.connect(self.generate_whatsapp_qr)

        self.save_qr_btn = QPushButton("Save QR Code")
        style_button(self.save_qr_btn, variant="success")
        self.save_qr_btn.clicked.connect(self.save_qr_code)

        qr_controls.addWidget(self.generate_qr_btn)
        qr_controls.addWidget(self.save_qr_btn)
        qr_controls.addStretch()

        qr_layout.addLayout(qr_controls)

        whatsapp_layout.addLayout(qr_layout)

        # Instructions
        instructions = QLabel("This QR code allows customers to quickly contact you via WhatsApp for support and inquiries.")
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-size: 12px; margin-top: 10px;")
        whatsapp_layout.addWidget(instructions)

        layout.addWidget(whatsapp_group)
        
        # System Identity QR Code Group (New)
        system_qr_group = QGroupBox("System Identity QR Code")
        system_qr_layout = QHBoxLayout(system_qr_group)
        
        self.sys_qr_label = QLabel()
        self.sys_qr_label.setFixedSize(200, 200)
        self.sys_qr_label.setStyleSheet("border: 1px solid #4318ff; background: white; border-radius: 8px;")
        self.sys_qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        system_qr_layout.addWidget(self.sys_qr_label)
        
        sys_info = QVBoxLayout()
        sys_info.addWidget(QLabel("<b>Official System Identity QR</b>"))
        sys_info.addWidget(QLabel("This QR code was generated during activation."))
        sys_info.addWidget(QLabel("It is used for official receipts and verification."))
        
        self.open_sys_qr_btn = QPushButton("Open File Location")
        style_button(self.open_sys_qr_btn, variant="outline")
        self.open_sys_qr_btn.clicked.connect(self.open_system_qr_folder)
        sys_info.addWidget(self.open_sys_qr_btn)
        sys_info.addStretch()
        system_qr_layout.addLayout(sys_info)
        
        layout.addWidget(system_qr_group)

        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        self.save_settings_btn = QPushButton("Save All Settings")
        style_button(self.save_settings_btn, variant="success", size="large")
        self.save_settings_btn.clicked.connect(self.save_settings)

        save_layout.addWidget(self.save_settings_btn)
        layout.addLayout(save_layout)

        self.load_company_settings()
        return scroll

    def create_maintenance_tab(self):
        """Create maintenance settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)

        layout.setSpacing(25)

        # Connectivity Section
        conn_card, conn_layout = self.create_card("Connectivity Settings", "fa5s.wifi")
        
        self.offline_mode_cb = QCheckBox("Enable Offline Mode")
        self.offline_mode_cb.setStyleSheet("font-size: 14px; font-weight: bold; color: #374151;")
        self.offline_mode_cb.setChecked(local_config.get("offline_mode"))
        self.offline_mode_cb.toggled.connect(self.toggle_offline_mode)
        conn_layout.addWidget(self.offline_mode_cb)
        
        self.update_check_cb = QCheckBox("Check for Updates Automatically")
        self.update_check_cb.setStyleSheet("font-size: 14px; font-weight: bold; color: #374151;")
        self.update_check_cb.setChecked(local_config.get("check_updates", True))
        self.update_check_cb.toggled.connect(self.toggle_update_checks)
        conn_layout.addWidget(self.update_check_cb)
        
        note_lbl = QLabel("Note: Enabling Offline Mode will disable daily cloud sync.\nMandatory contract validation will still occur upon expiry.")
        note_lbl.setStyleSheet("color: #6b7280; font-style: italic; font-size: 12px;")
        conn_layout.addWidget(note_lbl)
        
        layout.addWidget(conn_card)
        
        # Auto-Start Section (Windows Only)
        if AutoStartHelper.is_windows():
            autostart_card, autostart_layout = self.create_card("System Startup", "fa5s.clock")
            self.autostart_cb = QCheckBox("Launch on Startup")
            self.autostart_cb.setStyleSheet("font-size: 14px; font-weight: bold; color: #374151;")
            self.autostart_cb.setChecked(AutoStartHelper.is_enabled())
            self.autostart_cb.toggled.connect(self.toggle_autostart)
            autostart_layout.addWidget(self.autostart_cb)
            
            auto_note = QLabel("Note: This registers the application in Windows Task Scheduler to start automatically when you log in.")
            auto_note.setStyleSheet("color: #6b7280; font-style: italic; font-size: 12px;")
            autostart_layout.addWidget(auto_note)
            layout.addWidget(autostart_card)

        # System Maintenance Section
        maint_card, maint_layout = self.create_card("System Maintenance", "fa5s.tools")

        vacuum_btn = QPushButton(" Optimize Database")
        vacuum_btn.setIcon(qta.icon("fa5s.broom", color="white"))
        style_button(vacuum_btn, variant="primary")
        vacuum_btn.clicked.connect(self.run_vacuum)
        maint_layout.addWidget(vacuum_btn)

        clean_logs_btn = QPushButton(" Clear Activity Logs")
        clean_logs_btn.setIcon(qta.icon("fa5s.history", color="white"))
        style_button(clean_logs_btn, variant="warning")
        clean_logs_btn.clicked.connect(self.clear_logs)
        maint_layout.addWidget(clean_logs_btn)

        reset_btn = QPushButton(" Factory Data Reset")
        reset_btn.setIcon(qta.icon("fa5s.trash-alt", color="white"))
        style_button(reset_btn, variant="danger")
        reset_btn.clicked.connect(self.system_reset)
        maint_layout.addWidget(reset_btn)

        layout.addWidget(maint_card)
        layout.addStretch()
        return tab

    def create_backup_tab(self):
        """Create backup settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)

        # Backup Section
        backup_card, backup_layout = self.create_card("Database Management", "fa5s.database")

        backup_btn = QPushButton(" Create Full Backup")
        backup_btn.setIcon(qta.icon("fa5s.file-export", color="white"))
        style_button(backup_btn, variant="success")
        backup_btn.clicked.connect(self.run_backup)

        restore_btn = QPushButton(" Restore from Backup")
        restore_btn.setIcon(qta.icon("fa5s.file-import", color="white"))
        style_button(restore_btn, variant="info")
        restore_btn.clicked.connect(self.run_restore)

        backup_layout.addWidget(backup_btn)
        backup_layout.addWidget(restore_btn)

        layout.addWidget(backup_card)
        layout.addStretch()
        return tab

    def load_company_settings(self):
        """Load company settings from local database and sync with cloud"""
        try:
            with db_manager.get_connection() as conn:
                # Load Company Info from company_info table
                try:
                    row = conn.execute("SELECT * FROM company_info WHERE id=1").fetchone()
                    if row:
                        self.company_name.setText(row['name'] or "")
                        self.company_address.setPlainText(row['address'] or "")
                        self.company_phone.setText(row['phone'] or "")
                        self.company_email.setText(row['email'] or "")
                except Exception as e:
                    print(f"Error loading company_info: {e}")

                # Load WhatsApp from app_settings
                try:
                    row = conn.execute("SELECT value FROM app_settings WHERE key='whatsapp_number'").fetchone()
                    if row:
                        self.whatsapp_number.setText(row['value'] or "")
                except: pass

            # Load System QR Code
            qr_path = os.path.join("credentials", "company_qr.png")
            if os.path.exists(qr_path):
                pixmap = QPixmap(qr_path)
                self.sys_qr_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                self.sys_qr_label.setText("QR Not Found")

            # Cloud update logic (Asynchronous)
            sid = local_config.get("system_id")
            if sid:
                self.cleanup_thread()
                self.sync_thread = SettingsSyncWorker(task="load", sid=sid)
                self.sync_thread.finished.connect(self._on_online_settings_loaded)
                self.sync_thread.finished.connect(self.sync_thread.deleteLater)
                self.sync_thread.start()

        except Exception as e:
            print(f"Error loading company settings: {e}")

    def _on_online_settings_loaded(self, success, data):
        if success and data:
            self.company_name.setText(data.get('company_name', self.company_name.text()))
            self.company_phone.setText(data.get('phone', self.company_phone.text()))
            self.company_email.setText(data.get('email', self.company_email.text()))
            self.company_address.setPlainText(data.get('address', self.company_address.toPlainText()))
            self.generate_whatsapp_qr(auto=True)

    def check_and_sync_online(self):
        """Timer callback - triggered every 30s. Must be non-blocking."""
        if self.is_syncing: return
        self.save_settings(silent=True)

    def save_settings(self, silent=False):
        """Save company settings to database"""
        try:
            with db_manager.get_connection() as conn:
                # Save to company_info
                conn.execute("""
                    INSERT OR REPLACE INTO company_info (id, name, address, phone, email)
                    VALUES (1, ?, ?, ?, ?)
                """, (
                    self.company_name.text().strip(),
                    self.company_address.toPlainText().strip(),
                    self.company_phone.text().strip(),
                    self.company_email.text().strip()
                ))
                
                # Save WhatsApp to app_settings
                conn.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('whatsapp_number', ?)",
                            (self.whatsapp_number.text().strip(),))
                
                conn.commit()

            # Cloud Sync (Asynchronous)
            sid = local_config.get("system_id")
            if sid:
                payload = {
                    "company_name": self.company_name.text().strip(),
                    "address": self.company_address.toPlainText().strip(),
                    "phone": self.company_phone.text().strip(),
                    "email": self.company_email.text().strip(),
                    "company_whatsapp_url": f"https://wa.me/{self.whatsapp_number.text().strip().replace('+', '').replace(' ', '')}"
                }
                
                self.is_syncing = True
                self.cleanup_thread()
                self.sync_thread = SettingsSyncWorker(task="sync", sid=sid, payload=payload)
                self.sync_thread.saved.connect(lambda s: setattr(self, 'is_syncing', False))
                self.sync_thread.finished.connect(self.sync_thread.deleteLater)
                self.sync_thread.start()

            # Auto-update QR
            self.generate_whatsapp_qr(auto=True)

            if not silent:
                QMessageBox.information(self, "Success", "Settings saved and syncing in background.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def generate_whatsapp_qr(self, auto=False):
        """Generate WhatsApp QR code"""
        number = self.whatsapp_number.text().strip()
        if not number:
            if not auto: QMessageBox.warning(self, "Error", "Please enter a WhatsApp number first")
            return

        try:
            # Create WhatsApp link
            whatsapp_link = f"https://wa.me/{number.replace('+', '')}"

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(whatsapp_link)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.convert("RGBA")

            # Convert to QPixmap
            img_data = img.tobytes("raw", "RGBA")
            qimage = QImage(img_data, img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            # Scale to fit label
            scaled_pixmap = pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio)
            self.qr_label.setPixmap(scaled_pixmap)

            self.generated_qr_data = img  # Store for saving

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate QR code: {str(e)}")

    def save_qr_code(self):
        """Save QR code to file"""
        if not hasattr(self, 'generated_qr_data'):
            QMessageBox.warning(self, "Error", "Please generate a QR code first")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save QR Code", "whatsapp_qr.png",
                "PNG files (*.png);;All files (*)"
            )

            if file_path:
                self.generated_qr_data.save(file_path)
                QMessageBox.information(self, "Success", "QR code saved successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save QR code: {str(e)}")

    def change_theme(self, index):
        modes = ["LIGHT", "DARK", "SYSTEM"]
        theme_manager.set_theme_mode(modes[index])

    def change_language(self, index):
        lang = self.lang_box.itemData(index)
        lang_manager.set_language(lang)
        QMessageBox.information(self, "Language Changed", "Please restart the application for language changes to take full effect.")

    def run_vacuum(self):
        with db_manager.get_connection() as conn:
            conn.execute("VACUUM")
        QMessageBox.information(self, "Success", "Database optimized.")

    def system_reset(self):
        # Multiple confirmations as per spec safety
        reply1 = QMessageBox.critical(self, "SYSTEM RESET", 
                                    "WARNING: This will delete ALL sales, loans, and audit data. Products and Users will remain. Continue?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply1 == QMessageBox.StandardButton.Yes:
            reply2 = QMessageBox.warning(self, "FINAL CONFIRMATION", 
                                        "Are you absolutely sure? This action is irreversible.",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply2 == QMessageBox.StandardButton.Yes:
                try:
                    with db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM sales")
                        cursor.execute("DELETE FROM sale_items")
                        cursor.execute("DELETE FROM loans")
                        cursor.execute("DELETE FROM cash_transactions")
                        cursor.execute("DELETE FROM audit_logs")
                        cursor.execute("UPDATE customers SET balance = 0")
                        cursor.execute("UPDATE inventory SET quantity = 0")
                        conn.commit()
                    QMessageBox.information(self, "Success", "System has been reset to initial state.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Reset failed: {e}")

    def clear_logs(self):
        if QMessageBox.question(self, "Confirm", "Clear all audit logs?") == QMessageBox.StandardButton.Yes:
            with db_manager.get_connection() as conn:
                conn.execute("DELETE FROM audit_logs")
                conn.commit()
            QMessageBox.information(self, "Success", "Logs cleared.")

    def run_backup(self):
        path = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if path:
            success, msg = BackupManager.create_backup(path)
            if success:
                QMessageBox.information(self, "Success", f"Backup created at: {msg}")
            else:
                QMessageBox.critical(self, "Error", msg)

    def run_restore(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Backup File", "", "Database Files (*.db)")
        if file:
            reply = QMessageBox.question(self, 'Confirm Restore', 
                                       'This will overwrite current data. Continue?',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                success, msg = BackupManager.restore_backup(file)
                if success:
                    QMessageBox.information(self, "Success", "Database restored. Please restart the app.")
                else:
                    QMessageBox.critical(self, "Error", msg)
    def open_system_qr_folder(self):
        import subprocess
        import platform
        path = os.path.abspath("credentials")
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

    def toggle_offline_mode(self, checked):
        local_config.set("offline_mode", checked)
        status = "Offline Mode Enabled" if checked else "Offline Mode Disabled"
        mode = "OFFLINE" if checked else "ONLINE"
        print(f"📡 System switched to {mode} mode.")
        QMessageBox.information(self, "Connectivity", f"{status}\nRestart may be required for full effect.")

    def toggle_update_checks(self, checked):
        local_config.set("check_updates", checked)
        from src.core.github_update_checker import update_checker
        if checked:
            update_checker.start()
        else:
            if hasattr(update_checker, 'check_timer'):
                update_checker.check_timer.stop()
        msg = "Update checks enabled." if checked else "Update checks disabled."
        QMessageBox.information(self, "Updates", f"{msg}")

    def toggle_autostart(self, checked):
        if checked:
            success = AutoStartHelper.enable_autostart()
            if success:
                QMessageBox.information(self, "Success", "Launch on Startup enabled.")
            else:
                self.autostart_cb.setChecked(False)
                QMessageBox.critical(self, "Error", "Failed to enable Launch on Startup. You may need administrator privileges.")
        else:
            success = AutoStartHelper.disable_autostart()
            if success:
                QMessageBox.information(self, "Success", "Launch on Startup disabled.")
            else:
                self.autostart_cb.setChecked(True)
                QMessageBox.critical(self, "Error", "Failed to disable Launch on Startup.")
