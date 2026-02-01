from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QFrame, QComboBox, QMessageBox, QFileDialog, QGridLayout,
                             QTabWidget, QGroupBox, QFormLayout, QTextEdit, QScrollArea, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
import qtawesome as qta
import qrcode
from src.core.localization import lang_manager
from src.utils.backup import BackupManager
from src.ui.theme_manager import theme_manager
from src.database.db_manager import db_manager
from src.ui.button_styles import style_button
from src.core.local_config import local_config
import os

class PharmacySettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

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

        tabs.addTab(self.create_company_tab(), "Pharmacy Info")
        tabs.addTab(self.create_maintenance_tab(), "Maintenance")
        tabs.addTab(self.create_backup_tab(), "Backup")

        main_layout.addWidget(tabs)

    def create_company_tab(self):
        """Create pharmacy information tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Pharmacy Information Group
        company_group = QGroupBox("Pharmacy Information")
        company_form = QFormLayout(company_group)

        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Enter pharmacy name")

        self.company_address = QTextEdit()
        self.company_address.setMaximumHeight(80)
        self.company_address.setPlaceholderText("Enter pharmacy address")

        self.company_phone = QLineEdit()
        self.company_phone.setPlaceholderText("Enter phone number")

        self.company_email = QLineEdit()
        self.company_email.setPlaceholderText("Enter email address")

        company_form.addRow("Pharmacy Name:", self.company_name)
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

        # System Maintenance Section
        conn_card, conn_layout = self.create_card("Connectivity Settings", "fa5s.wifi")
        
        self.offline_mode_cb = QCheckBox("Enable Offline Mode")
        self.offline_mode_cb.setStyleSheet("font-size: 14px; font-weight: bold; color: #374151;")
        self.offline_mode_cb.setChecked(local_config.get("offline_mode"))
        self.offline_mode_cb.toggled.connect(self.toggle_offline_mode)
        conn_layout.addWidget(self.offline_mode_cb)
        
        note_lbl = QLabel("Note: Enabling Offline Mode will disable daily cloud sync.\nMandatory contract validation will still occur upon expiry.")
        note_lbl.setStyleSheet("color: #6b7280; font-style: italic; font-size: 12px;")
        conn_layout.addWidget(note_lbl)
        
        layout.addWidget(conn_card)

        maint_card, maint_layout = self.create_card("Pharmacy System Maintenance", "fa5s.tools")

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
        backup_card, backup_layout = self.create_card("Pharmacy Database Management", "fa5s.database")

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
        """Load pharmacy settings from database"""
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # Load Pharmacy Info from pharmacy_info table
                try:
                    row = conn.execute("SELECT * FROM pharmacy_info WHERE id=1").fetchone()
                    if row:
                        self.company_name.setText(row['name'] or "")
                        self.company_address.setPlainText(row['address'] or "")
                        self.company_phone.setText(row['phone'] or "")
                        self.company_email.setText(row['email'] or "")
                except Exception as e:
                    print(f"Error loading pharmacy_info: {e}")

                # Load WhatsApp from app_settings
                try:
                    row = conn.execute("SELECT value FROM app_settings WHERE key='whatsapp_number'").fetchone()
                    if row:
                        self.whatsapp_number.setText(row['value'] or "")
                except: pass

        except Exception as e:
            print(f"Error loading pharmacy settings: {e}")

    def save_settings(self):
        """Save pharmacy settings to database"""
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # Save to pharmacy_info
                conn.execute("""
                    INSERT OR REPLACE INTO pharmacy_info (id, name, address, phone, email)
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

            # Auto-update QR
            self.generate_whatsapp_qr(auto=True)

            QMessageBox.information(self, "Success", "Pharmacy settings saved successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def generate_whatsapp_qr(self, auto=False):
        """Generate WhatsApp QR code"""
        number = self.whatsapp_number.text().strip()
        if not number:
            if not auto:
                QMessageBox.warning(self, "Error", "Please enter a WhatsApp number first")
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
                self, "Save QR Code", "pharmacy_whatsapp_qr.png",
                "PNG files (*.png);;All files (*)"
            )

            if file_path:
                self.generated_qr_data.save(file_path)
                QMessageBox.information(self, "Success", "QR code saved successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save QR code: {str(e)}")

    def run_vacuum(self):
        with db_manager.get_pharmacy_connection() as conn:
            conn.execute("VACUUM")
        QMessageBox.information(self, "Success", "Pharmacy database optimized.")

    def clear_logs(self):
        if QMessageBox.question(self, "Confirm", "Clear all pharmacy audit logs?") == QMessageBox.StandardButton.Yes:
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    conn.execute("DELETE FROM audit_logs")
                    conn.commit()
                QMessageBox.information(self, "Success", "Logs cleared.")
            except Exception as e:
                QMessageBox.warning(self, "Info", "Audit logs table may not exist yet.")

    def run_backup(self):
        path = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if path:
            try:
                # Backup pharmacy database
                import shutil
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                source = "afex_pharmacy.db"
                dest = os.path.join(path, f"pharmacy_backup_{timestamp}.db")
                shutil.copy2(source, dest)
                QMessageBox.information(self, "Success", f"Pharmacy backup created at:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Backup failed: {str(e)}")

    def run_restore(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Backup File", "", "Database Files (*.db)")
        if file:
            reply = QMessageBox.question(self, 'Confirm Restore', 
                                       'This will overwrite current pharmacy data. Continue?',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    import shutil
                    shutil.copy2(file, "afex_pharmacy.db")
                    QMessageBox.information(self, "Success", "Pharmacy database restored. Please restart the app.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Restore failed: {str(e)}")

    def toggle_offline_mode(self, checked):
        local_config.set("offline_mode", checked)
        status = "Offline Mode Enabled" if checked else "Offline Mode Disabled"
        mode = "OFFLINE" if checked else "ONLINE"
        QMessageBox.information(self, "Connectivity", f"{status}\nRestart may be required for full effect.")
