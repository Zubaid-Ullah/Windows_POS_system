import os
import socket
import subprocess
import sys
from datetime import datetime, timedelta

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QComboBox, QFrame, 
                             QStackedWidget, QFormLayout, QGraphicsOpacityEffect,
                             QMessageBox, QDateEdit, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QDate
import qtawesome as qta
from src.core.supabase_manager import supabase_manager
from src.core.local_config import local_config
from src.database.db_manager import db_manager
from src.ui.button_styles import style_button
import qrcode
from PIL import Image as PILImage

class StepIndicator(QFrame):
    def __init__(self, step_num, title, active=False):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.circle = QLabel(str(step_num))
        self.set_active(active)
        self.layout.addWidget(self.circle, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.label = QLabel(title)
        self.label.setStyleSheet("font-size: 11px; font-weight: bold; color: #a3aed0;")
        self.layout.addWidget(self.label, 0, Qt.AlignmentFlag.AlignCenter)

    def set_active(self, active):
        bg = "#4318ff" if active else "#e0e5f2"
        fg = "white" if active else "#a3aed0"
        self.circle.setFixedSize(30, 30)
        self.circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.circle.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border-radius: 15px;
            font-weight: bold;
        """)

class CreateAccountWindow(QWidget):
    account_created = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Activate your POS")
        self.setFixedSize(700, 800)
        self.current_step = 0
        
        # Set Window Icon explicitly to FaqiriTech Logo
        import sys, os
        from PyQt6.QtGui import QIcon
        if getattr(sys, 'frozen', False):
            base = getattr(sys, '_MEIPASS', os.path.join(os.path.dirname(sys.executable), "..", "Resources"))
            icon_path = os.path.join(base, "Logo", "logo.ico")
        else:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "Logo", "logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.init_ui()
        
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)
        
        # Header
        self.title_lbl = QLabel("Activate your POS in minutes")
        self.title_lbl.setStyleSheet("font-size: 32px; font-weight: bold; color: #1b2559;")
        self.main_layout.addWidget(self.title_lbl)
        
        # Stepper Header
        self.stepper_header = QHBoxLayout()
        self.step_widgets = [
            StepIndicator(1, "Company", True),
            StepIndicator(2, "Authorization"),
            StepIndicator(3, "Summary")
        ]
        for i, w in enumerate(self.step_widgets):
            self.stepper_header.addWidget(w)
            if i < 2:
                line = QFrame()
                line.setFixedHeight(2)
                line.setStyleSheet("background-color: #e0e5f2;")
                line.setSizePolicy(line.sizePolicy().Expanding, line.sizePolicy().Fixed)
                self.stepper_header.addWidget(line)
        self.main_layout.addLayout(self.stepper_header)
        
        # Stacked Steps
        self.stack = QStackedWidget()
        self.init_step1()
        self.init_step2()
        self.init_step3()
        self.main_layout.addWidget(self.stack)
        
        # Navigation
        self.nav_layout = QHBoxLayout()
        self.back_btn = QPushButton(" Back")
        style_button(self.back_btn, variant="outline")
        self.back_btn.hide()
        self.back_btn.clicked.connect(self.go_back)
        
        self.next_btn = QPushButton("Next ")
        style_button(self.next_btn, variant="primary")
        self.next_btn.clicked.connect(self.go_next)
        
        self.nav_layout.addWidget(self.back_btn)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.next_btn)
        self.main_layout.addLayout(self.nav_layout)

    def init_step1(self):
        page = QWidget()
        lay = QFormLayout(page)
        lay.setSpacing(12)
        lay.setContentsMargins(0, 15, 0, 0)
        style = "border: 1px solid #e0e5f2; border-radius: 8px; padding: 5px;"
        self.comp_name = QLineEdit()
        self.comp_name.setFont(QFont("Inter", 18))
        self.comp_name.setPlaceholderText("e.g. FaqiriTech Tech Solutions")
        self.comp_name.setMinimumWidth(400)
        self.comp_name.setFixedHeight(35)
        self.comp_name.setStyleSheet(style)
        lay.addRow("Company Name *", self.comp_name)
        
        # WhatsApp with Country Code
        wa_lay = QHBoxLayout()
        self.wa_code = QComboBox()
        country_codes = [
            "+1","+7","+20","+27","+30","+31","+32","+33","+34","+36","+39","+40","+41","+43","+44","+45","+46",
            "+47","+48","+49","+51","+52","+53","+54","+55","+56","+57","+58","+60","+61","+62","+63","+64","+65",
            "+66","+81","+82","+84","+86","+90","+91","+92","+93","+94","+95","+98","+212","+213","+216","+218",
            "+220","+221","+222","+223","+224","+225","+226","+227","+228","+229","+230","+231","+232","+233","+234",
            "+235","+236","+237","+238","+239","+240","+241","+242","+243","+244","+245","+246","+248","+249","+250",
            "+251","+252","+253","+254","+255","+256","+257","+258","+260","+261","+262","+263","+264","+265","+266",
            "+267","+268","+269","+297","+298","+299","+350","+351","+352","+353","+354","+355","+356","+357","+358",
            "+359","+370","+371","+372","+373","+374","+375","+376","+377","+378","+380","+381","+382","+383","+385",
            "+386","+387","+389","+420","+421","+423","+500","+501","+502","+503","+504","+505","+506","+507","+508",
            "+509","+590","+591","+592","+593","+594","+595","+596","+597","+598","+599","+670","+672","+673","+674",
            "+675","+676","+677","+678","+679","+680","+681","+682","+683","+685","+686","+687","+688","+689","+690",
            "+691","+692","+850","+852","+853","+855","+856","+880","+886","+960","+961","+962","+963","+964","+965",
            "+966","+967","+968","+970","+971","+972","+973","+974","+975","+976","+977","+992","+993","+994","+995",
            "+996","+998",
        ]

        self.wa_code.addItems(country_codes)
        self.wa_code.setFixedWidth(95)
        self.wa_code.setFixedHeight(35)
        self.wa_code.setStyleSheet(style)
        self.wa_code.setFont(QFont("Inter", 18))
        wa_lay.addWidget(self.wa_code)
        self.wa_num = QLineEdit()
        self.wa_num.setFont(QFont("Inter", 18))
        self.wa_num.setPlaceholderText("WhatsApp Number")
        self.wa_num.setMinimumWidth(300)
        self.wa_num.setFixedHeight(35)
        self.wa_num.setStyleSheet(style)
        wa_lay.addWidget(self.wa_num)
        lay.addRow("WhatsApp *", wa_lay)
        
        self.phone = QLineEdit()
        self.phone.setFont(QFont("Inter", 18))
        self.phone.setPlaceholderText("Phone Number")
        self.phone.setMinimumWidth(400)
        self.phone.setFixedHeight(35)
        self.phone.setStyleSheet(style)
        lay.addRow("Phone", self.phone)
        
        self.email = QLineEdit()
        self.email.setFont(QFont("Inter", 18))
        self.email.setPlaceholderText("Email Address")
        self.email.setMinimumWidth(400)
        self.email.setFixedHeight(35)
        self.email.setStyleSheet(style)
        lay.addRow("Email Address", self.email)
        
        self.license = QLineEdit()
        self.license.setFont(QFont("Inter", 18))
        self.license.setPlaceholderText("Business License")
        self.license.setMinimumWidth(400)
        self.license.setFixedHeight(35)
        self.license.setStyleSheet(style)
        lay.addRow("Business License", self.license)
        
        self.address = QLineEdit()
        self.address.setFont(QFont("Inter", 18))
        self.address.setPlaceholderText("Full Address")
        self.address.setMinimumWidth(400)
        self.address.setFixedHeight(35)
        self.address.setStyleSheet(style)
        lay.addRow("Full Address", self.address)
        
        self.stack.addWidget(page)

    def init_step2(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(15)
        
        info = QLabel("Installer Authorization & Client Account Setup")
        info.setStyleSheet("color: #1b2559; font-size: 16px; font-weight: bold;")
        lay.addWidget(info)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        # Installer Info
        self.installer_user = QComboBox()
        self.installer_user.addItem("Loading online users...")
        self.installer_user.setEnabled(False)
        form.addRow("Authorized Person", self.installer_user)
        
        self.installer_pass = QLineEdit()
        self.installer_pass.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Auth Password", self.installer_pass)
        
        # Trigger refresh immediately so it's ready by the time they click Next
        QTimer.singleShot(500, self.refresh_installers)
        
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #e0e5f2;")
        form.addRow(line)
        
        # Client Account Setup
        sub_info = QLabel("Create the main system user account")
        sub_info.setStyleSheet("color: #707eae; font-size: 12px; margin-top: 10px;")
        form.addRow(sub_info)
        
        self.client_user = QLineEdit()
        self.client_user.setPlaceholderText("New system username")
        form.addRow("Client Username *", self.client_user)
        
        self.client_pass = QLineEdit()
        self.client_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_pass.setPlaceholderText("New system password")
        form.addRow("Client Password *", self.client_pass)
        
        lay.addLayout(form)
        
        self.verify_lbl = QLabel("")
        self.verify_lbl.setStyleSheet("color: #ee5d50; font-size: 12px;")
        lay.addWidget(self.verify_lbl)
        
        self.verify_btn = QPushButton("Verify & Authorize")
        style_button(self.verify_btn, variant="info")
        self.verify_btn.clicked.connect(self.verify_auth)
        lay.addWidget(self.verify_btn)
        
        self.auth_verified = False
        self.stack.addWidget(page)

    def init_step3(self):
        page = QWidget()
        lay = QFormLayout(page)
        lay.setSpacing(10)
        
        # Auto-picked values
        now = datetime.now()
        sid = local_config.get("system_id")
        pc = socket.gethostname()
        
        def add_summary_row(label, val):
            l = QLabel(val)
            l.setStyleSheet("font-weight: bold; color: #1b2559;")
            lay.addRow(QLabel(label), l)

        add_summary_row("System ID", sid)
        add_summary_row("PC Name", pc)
        add_summary_row("Account Creation", now.strftime("%Y-%m-%d %H:%M"))
        
        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDate(QDate.currentDate().addYears(1))
        self.expiry_date.setMinimumDate(QDate.currentDate())
        lay.addRow("Contract Expiry *", self.expiry_date)
        
        self.sys_info_lbl = QLabel(f"({pc})-{sid}-({now.strftime('%Y-%m-%d')})")
        self.sys_info_lbl.setWordWrap(True)
        self.sys_info_lbl.setStyleSheet("font-size: 10px; color: #a3aed0; font-family: 'Courier New';")
        lay.addRow("Serial Info", self.sys_info_lbl)
        
        self.registration_choice = QComboBox()
        self.registration_choice.addItems(["Login Each Time"])
        self.registration_choice.setEnabled(False) # Force this for now for security
        lay.addRow("Login Preference", self.registration_choice)
        
        self.shortcut_chk = QCheckBox("Create Desktop Shortcut")
        self.shortcut_chk.setChecked(True)
        self.shortcut_chk.setStyleSheet("font-size: 14px; color: #1b2559;")
        lay.addRow("", self.shortcut_chk)
        
        self.stack.addWidget(page)

    def verify_auth(self):
        user = self.installer_user.currentText()
        pw = self.installer_pass.text()
        if not pw:
            QMessageBox.warning(self, "Required", "Please enter the authorization password.")
            return

        self.verify_lbl.setText("Verifying with server...")
        self.verify_lbl.setStyleSheet("color: #4318ff;")
        self.verify_btn.setEnabled(False)
        
        from src.core.blocking_task_manager import task_manager
        
        def run_verify():
            return supabase_manager.verify_installer(user, pw)
            
        def on_finished(verified):
            self.verify_btn.setEnabled(True)
            if verified:
                self.auth_verified = True
                self.verify_lbl.setText("✅ Verified successfully")
                self.verify_lbl.setStyleSheet("color: #10b981;")
            else:
                self.verify_lbl.setText("❌ Username or password is incorrect")
                self.verify_lbl.setStyleSheet("color: #ee5d50;")
                
        task_manager.run_task(run_verify, on_finished=on_finished)

    def go_next(self):
        if self.current_step == 0:
            if not self.comp_name.text() or not self.wa_num.text():
                QMessageBox.warning(self, "Validation", "Company Name and WhatsApp are required.")
                return
            self.switch_step(1)
        elif self.current_step == 1:
            if not self.auth_verified:
                QMessageBox.warning(self, "Authorization", "Please verify authorization before proceeding.")
                return
            self.switch_step(2)
        else:
            self.finish_creation()

    def go_back(self):
        if self.current_step > 0:
            self.switch_step(self.current_step - 1)

    def switch_step(self, step_idx):
        self.current_step = step_idx
        self.stack.setCurrentIndex(step_idx)
        
        # Update indicators
        for i, w in enumerate(self.step_widgets):
            w.set_active(i == step_idx)
            
        self.back_btn.setVisible(step_idx > 0)
        self.next_btn.setText("Create my account" if step_idx == 2 else "Next ")
        style_button(self.next_btn, variant="success" if step_idx == 2 else "primary")

        # Refresh installers from Supabase if we enter Step 2
        if step_idx == 1:
            self.refresh_installers()

    def refresh_installers(self):
        self.installer_user.clear()
        self.installer_user.addItem("Loading online users...")
        self.installer_user.setEnabled(False)
        
        # Quick timer to allow UI to render 'Loading'
        QTimer.singleShot(100, self._do_refresh_installers)

    def _do_refresh_installers(self):
        try:
            users = supabase_manager.get_installers()
            self.installer_user.clear()
            
            # Always ensure SuperAdmin is an option for activation
            all_users = ["SuperAdmin"]
            if users:
                all_users.extend(users)
            
            self.installer_user.addItems(all_users)
            print(f"[SUCCESS] Loaded {len(all_users)} installers (including SuperAdmin)")
            self.installer_user.setEnabled(True)
        except Exception as e:
            print(f"[ERROR] Cloud Error: {e}")
            self.installer_user.addItem("SuperAdmin") # Fallback to just SuperAdmin if cloud offline
            self.installer_user.setEnabled(True)
            QMessageBox.warning(self, "Cloud Warning", "Could not fetch installer list. You can still activate using SuperAdmin Secret Key if you have one.")

    def get_system_serial(self):
        """Find OS and run appropriate command to read the system serial number without sudo."""
        os_type = sys.platform.lower()

        try:
            if "win" in os_type:
                # Command for Windows
                command = "wmic bios get serialnumber"
                result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                serial = result.decode().replace("SerialNumber", "").replace("\n", "").replace("\r", "").strip()
                return serial if serial else "WIN-UNKNOWN"

            elif "darwin" in os_type:
                # macOS: Try ioreg without sudo first (IOPlatformExpertDevice usually works)
                try:
                    command = "ioreg -d2 -c IOPlatformExpertDevice | grep IOPlatformSerialNumber"
                    result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE).decode().strip()
                    # Expected: "IOPlatformSerialNumber" = "C02..."
                    if "=" in result:
                        return result.split("=")[1].strip().replace('"', '')
                except:
                    pass
                
                # Fallback: system_profiler
                try:
                    command = "system_profiler SPHardwareDataType | grep 'Serial Number'"
                    result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE).decode().strip()
                    # Expected: Serial Number (system): C02...
                    if ":" in result:
                        return result.split(":")[1].strip()
                except:
                    pass
                    
                return "MAC-UNKNOWN"

            elif "linux" in os_type:
                # Linux: Try reading DMI file directly (no sudo needed usually)
                try:
                    with open("/sys/class/dmi/id/product_serial", "r") as f:
                        return f.read().strip()
                except:
                    pass
                
                # Fallback: machine-id
                try:
                    with open("/etc/machine-id", "r") as f:
                        return f.read().strip()
                except:
                    pass
                
                return "LINUX-UNKNOWN"
                
            else:
                return "UNSUPPORTED-OS"

        except Exception as e:
            print(f"[WARNING] Serial Key Error: {e}")
            return "ERROR-FETCH-SERIAL"

    def finish_creation(self):
        if not self.client_user.text() or not self.client_pass.text():
            QMessageBox.warning(self, "Required", "Please provide a client username and password.")
            return

        # Prepare payload
        sid = local_config.get("system_id")
        now = datetime.now()
        expiry_qdate = self.expiry_date.date()
        expiry_dt = datetime(expiry_qdate.year(), expiry_qdate.month(), expiry_qdate.day())
        duration = (expiry_dt - now).days
        serial = self.get_system_serial()
        
        payload = {
            "system_id": sid,
            "pc_name": socket.gethostname(),
            "serial_key": serial,
            "company_name": self.comp_name.text(),
            "company_whatsapp_url": f"https://wa.me/{self.wa_code.currentText().replace('+', '')}{self.wa_num.text()}",
            "phone": self.phone.text(),
            "email": self.email.text(),
            "address": self.address.text(),
            "location": self.address.text(),
            "license": self.license.text(),
            "status": "active",
            "installation_time": now.isoformat(),
            "installed_by": self.installer_user.currentText(),
            "contract_duration_days": duration if duration > 0 else 1,
            "contract_expiry": expiry_dt.date().isoformat(),
            "needs_renewal_notification": False
        }

        # Prevent double clicks
        self.next_btn.setEnabled(False)
        self.back_btn.setEnabled(False)
        self.next_btn.setText("Registering...")
        
        from src.core.blocking_task_manager import task_manager
        
        def run_registration():
            print("[INFO] Registering system and client online...")
            # 1. Register Installation
            if not supabase_manager.upsert_installation(payload):
                return False, "Failed to register system online."

            # 1b. Save company details to local database
            try:
                with db_manager.get_connection() as conn:
                    settings_data = [
                        ('company_name', payload["company_name"]),
                        ('company_address', payload["address"]),
                        ('company_phone', payload["phone"]),
                        ('company_email', payload["email"]),
                        ('whatsapp_number', self.wa_num.text()),
                        ('system_id', sid),
                        ('pc_name', payload["pc_name"]),
                        ('serial_key', payload["serial_key"]),
                        ('contract_end', payload["contract_expiry"])
                    ]
                    for key, value in settings_data:
                        conn.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, value))
                        try:
                            conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", (key, value))
                        except: pass
                    conn.commit()
            except Exception as e:
                print(f"[WARNING] Failed to sync to local DB: {e}")

            # 1c. Generate and save QR Code
            try:
                qr_data = f"Company: {payload['company_name']}\nSID: {sid}\nSerial: {serial}\nWhatsApp: {payload['company_whatsapp_url']}"
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(qr_data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                qr_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "credentials")
                if not os.path.exists(qr_dir): os.makedirs(qr_dir)
                qr_path = os.path.join(qr_dir, "company_qr.png")
                img.save(qr_path)
                local_config.set("company_qr_path", qr_path)
            except Exception as e:
                print(f"[WARNING] Failed to generate QR Code: {e}")

            # 2. Register Client Credentials
            if not supabase_manager.register_client(self.client_user.text(), self.client_pass.text(), sid):
                return False, "Successfully registered system, but failed to create client account online."
            
            # Save local preferences
            local_config.set("account_created", True)
            local_config.set("company_name", payload["company_name"])
            local_config.set("login_mode", "once" if "Once" in self.registration_choice.currentText() else "each_time")
            local_config.set("installed_by", payload["installed_by"])
            local_config.set("client_username", self.client_user.text())
            local_config.save()
            return True, None

        def on_finished(result):
            success, error_msg = result
            if success:
                QMessageBox.information(self, "Success", "Account created successfully 🎉\nYour system is now activated.")
                if self.shortcut_chk.isChecked():
                    self.create_desktop_shortcut()
                self.account_created.emit()
                self.close()
            else:
                self.next_btn.setEnabled(True)
                self.back_btn.setEnabled(True)
                self.next_btn.setText("Create my account")
                QMessageBox.critical(self, "Registration Error", error_msg)

        task_manager.run_task(run_registration, on_finished=on_finished)

    def create_desktop_shortcut(self):
        try:
            import sys
            import os
            # Determine path to the executable
            exe_path = os.path.abspath(sys.argv[0])
            
            # Helper for Windows
            if sys.platform == "win32":
                import winshell
                from win32com.client import Dispatch
                
                desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
                path = os.path.join(desktop, "FaqiriTech POS System.lnk")
                
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortcut(path)
                shortcut.TargetPath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.IconLocation = exe_path
                shortcut.save()
                print("[SUCCESS] Shortcut created via WScript")

            # Fallback for Windows if win32com not available (using temporary VBS)
            elif sys.platform == "win32": # Redundant check but logic flow
                 pass 

        except ImportError:
            # If libraries missing, use subprocess VBS approach which requires no deps
            if sys.platform == "win32":
                self._create_shortcut_vbs(sys.argv[0])
        except Exception as e:
            print(f"[WARNING] Failed to create shortcut: {e}")

    def _create_shortcut_vbs(self, exe_path):
        try:
            exe_path = os.path.abspath(exe_path)
            work_dir = os.path.dirname(exe_path)
            vbs_content = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = oWS.ExpandEnvironmentStrings("%USERPROFILE%\\Desktop\\FaqiriTech POS System.lnk")
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{exe_path}"
            oLink.WorkingDirectory = "{work_dir}"
            oLink.IconLocation = "{exe_path},0"
            oLink.Save
            """
            vbs_path = os.path.join(work_dir, "create_shortcut.vbs")
            with open(vbs_path, "w") as f:
                f.write(vbs_content)
            
            subprocess.call(["cscript", "//Nologo", vbs_path], shell=True)
            os.remove(vbs_path)
            print("[SUCCESS] Shortcut created via embedded VBS")
        except Exception as e:
            print(f"[ERROR] VBS Shortcut Error: {e}")
