from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QMessageBox, QInputDialog, QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QColor
import os
import qtawesome as qta
from src.core.auth import Auth
from src.core.pharmacy_auth import PharmacyAuth
from src.core.localization import lang_manager
from src.database.db_manager import db_manager
from src.ui.button_styles import style_button
from src.ui.theme_manager import theme_manager
from datetime import datetime
from src.core.supabase_manager import supabase_manager
from src.core.local_config import local_config

class BusinessCard(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, title, icon_name, color):
        super().__init__()
        self.title_text = title
        self.icon_name = icon_name
        self.color = color
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(220, 260)
        self.setObjectName("business_card")
        self.apply_styles()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(80, 80))
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("background:none;")
        layout.addWidget(self.icon_lbl)
        
        self.text_lbl = QLabel(title)
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text_lbl)
        self.update_theme()

    def apply_styles(self):
        bg = "#ffffff" if not theme_manager.is_dark else "#111c44"
        border = "#e0e5f2" if not theme_manager.is_dark else "#1b2559"
        self.setStyleSheet(f"""
            QFrame#business_card {{
                background-color: {bg};
                border-radius: 20px;
                border: 2px solid {border};
                padding: 20px;
            }}
            QFrame#business_card:hover {{
                border: 2px solid {self.color};
                background-color: {self.color}10;
            }}
        """)

    def update_theme(self):
        self.apply_styles()
        color = "#1b2559" if not theme_manager.is_dark else "#ffffff"
        self.text_lbl.setStyleSheet(f"background:none; font-size: 18px; font-weight: bold; color: {color};")

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class LoginView(QWidget):
    login_success = pyqtSignal(str, str) # "STORE" or "PHARMACY", Role ("user" or "superadmin")

    def __init__(self):
        super().__init__()
        self.selected_mode = "STORE"
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # 1. Choice View
        self.init_choice_view()
        # 2. Store Login View
        self.init_store_login_view()
        # 3. Pharmacy Login View
        self.init_pharm_login_view()
        
        self.apply_theme()

    def apply_theme(self):
        bg = "#f4f7fe" if not theme_manager.is_dark else "#0b1437"
        self.setStyleSheet(f"background-color: {bg};")
        
        # Update choice view texts
        text_color = "#1b2559" if not theme_manager.is_dark else "#ffffff"
        sub_color = "#a3aed0" if not theme_manager.is_dark else "#707eae"
        
        self.main_title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {text_color}; margin-bottom: 10px;")
        self.main_subtitle.setStyleSheet(f"font-size: 16px; color: {sub_color}; margin-bottom: 40px;")
        
        self.store_card.update_theme()
        self.pharmacy_card.update_theme()
        
        # Update Login Cards
        self.update_login_card_theme(self.store_login_card, "#4318ff")
        self.update_login_card_theme(self.pharmacy_login_card, "#10b981")

    def update_login_card_theme(self, card, brand_color):
        bg = "#ffffff" if not theme_manager.is_dark else "#111c44"
        border = "#e0e5f2" if not theme_manager.is_dark else "#1b2559"
        card.setStyleSheet(f"QFrame {{ background: {bg}; border-radius: 30px; border: 1px solid {border}; }}")
        
        # Find labels inside card
        for lbl in card.findChildren(QLabel):
            if lbl.objectName() == "card_title":
                color = "#1b2559" if not theme_manager.is_dark else "#ffffff"
                lbl.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color}; border: none;")
        
        # Update inputs
        input_bg = "#f4f7fe" if not theme_manager.is_dark else "#0b1437"
        input_text = "#1b2559" if not theme_manager.is_dark else "#ffffff"
        input_style = f"""
            QLineEdit {{
                padding: 12px;
                border: 2px solid {border};
                border-radius: 12px;
                background-color: {input_bg};
                color: {input_text};
                font-size: 15px;
            }}
            QLineEdit:focus {{ border: 2px solid {brand_color}; background: {bg}; }}
        """
        for edit in card.findChildren(QLineEdit):
            edit.setStyleSheet(input_style)

    def init_choice_view(self):
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.main_title = QLabel(lang_manager.get("welcome_title") or "Welcome to Affex POS")
        layout.addWidget(self.main_title, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.main_subtitle = QLabel(lang_manager.get("select_business") or "Please select a business to continue")
        layout.addWidget(self.main_subtitle, 0, Qt.AlignmentFlag.AlignCenter)
        
        card_layout = QHBoxLayout()
        card_layout.setSpacing(30)
        
        self.store_card = BusinessCard("General Store", "fa5s.store", "#4318ff")
        self.store_card.clicked.connect(lambda: self.switch_to_login("STORE"))
        
        self.pharmacy_card = BusinessCard("Pharmacy", "fa5s.prescription-bottle-alt", "#10b981")
        self.pharmacy_card.clicked.connect(lambda: self.switch_to_login("PHARMACY"))
        
        card_layout.addWidget(self.store_card)
        card_layout.addWidget(self.pharmacy_card)
        layout.addLayout(card_layout)
        
        # Language at bottom
        lang_layout = QHBoxLayout()
        for lang, name in [("en", "EN"), ("ps", "PS"), ("dr", "DR")]:
            btn = QPushButton(name)
            btn.setStyleSheet("border: none; color: #4318ff; font-weight: bold; font-size: 15px;")
            btn.clicked.connect(lambda checked, l=lang: self.change_language(l))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            lang_layout.addWidget(btn)
        layout.addSpacing(50)
        layout.addLayout(lang_layout)
        
        self.stack.addWidget(view)

    def init_store_login_view(self):
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.store_login_card = self.create_login_card("General Store", "fa5s.store", "#4318ff", self.handle_store_login)
        layout.addWidget(self.store_login_card)
        self.stack.addWidget(view)

    def init_pharm_login_view(self):
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pharmacy_login_card = self.create_login_card("Pharmacy", "fa5s.prescription-bottle-alt", "#10b981", self.handle_pharmacy_login)
        layout.addWidget(self.pharmacy_login_card)
        self.stack.addWidget(view)

    def create_login_card(self, title_text, icon_name, color, login_handler):
        card = QFrame()
        card.setFixedSize(450, 620)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(10)
        
        # Back Button
        back_btn = QPushButton(qta.icon("fa5s.arrow-left", color="#a3aed0"), "")
        back_btn.setStyleSheet("border: none; background: transparent;")
        back_btn.setFixedSize(30, 30)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        # Ensure focus returns to nothing specific on back
        layout.addWidget(back_btn)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(50, 50))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("border: none;")
        layout.addWidget(icon_lbl)
        
        title = QLabel(title_text)
        title.setObjectName("card_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        uname = QLineEdit()
        uname.setPlaceholderText(lang_manager.get("username") or "Username")
        uname.returnPressed.connect(lambda: pword.setFocus())
        layout.addWidget(uname)
        
        pword = QLineEdit()
        pword.setPlaceholderText(lang_manager.get("password") or "Password")
        pword.setEchoMode(QLineEdit.EchoMode.Password)
        pword.returnPressed.connect(lambda: login_handler(uname.text(), pword.text()))
        layout.addWidget(pword)
        
        login_btn = QPushButton(lang_manager.get("login") or "Login")
        style_button(login_btn, variant="primary" if title_text=="General Store" else "success")
        login_btn.setFixedHeight(50)
        login_btn.clicked.connect(lambda: login_handler(uname.text(), pword.text()))
        layout.addWidget(login_btn)
        
        # Update Contract Button
        update_cnt_btn = QPushButton(lang_manager.get("update_contract") or "Update Contract")
        update_cnt_btn.setStyleSheet("color: #a3aed0; font-size: 12px; border: none; background: transparent;")
        update_cnt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        update_cnt_btn.clicked.connect(self.show_contract_update)
        layout.addWidget(update_cnt_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        if title_text == "General Store":
            self.store_uname = uname
            self.store_pword = pword
        else:
            self.pharm_uname = uname
            self.pharm_pword = pword
            
        return card

    def switch_to_login(self, mode):
        self.selected_mode = mode
        if mode == "STORE":
            self.stack.setCurrentIndex(1)
            self.store_uname.setFocus()
        else:
            self.stack.setCurrentIndex(2)
            self.pharm_uname.setFocus()

    def handle_store_login(self, username, password):
        # Super Admin Check - Bypass Contract Check
        if username.lower() == "superadmin":
            self.verify_super_admin(username, password, "STORE")
            return

        if not self.check_contract(): return
        
        Auth.ensure_defaults()
        if Auth.login(username, password):
            self.store_uname.clear()
            self.store_pword.clear()
            self.login_success.emit("STORE", "user")
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials")

    def handle_pharmacy_login(self, username, password):
        # Super Admin Check - Bypass Contract Check
        if username.lower() == "superadmin":
            self.verify_super_admin(username, password, "PHARMACY")
            return

        if not self.check_contract(): return
        
        PharmacyAuth.ensure_defaults()
        if PharmacyAuth.login(username, password):
            self.pharm_uname.clear()
            self.pharm_pword.clear()
            self.login_success.emit("PHARMACY", "user")
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials")

    def verify_super_admin(self, username, password, mode):
        # 3b. Super Admin Login
        if not supabase_manager.check_connection():
            QMessageBox.critical(self, "Connection Required", 
                                 "Internet connection required for Super Admin login.")
            return

        # Show loading feedback
        QMessageBox.information(self, "Verifying", "Verifying Super Admin credentials online...")

        from src.core.blocking_task_manager import task_manager
        
        def run_verify():
            return supabase_manager.verify_installer(username, password)
            
        def on_finished(verified):
            if verified:
                 # Set a temporary virtual session for Super Admin
                 mock_user = {
                     'username': username,
                     'role_name': 'SuperAdmin',
                     'id': 9999, # Virtual ID
                     'full_name': 'System Super Admin',
                     'permissions': '*',
                     'is_super_admin': True # For pharmacy check
                 }
                 
                 if mode == "PHARMACY":
                      PharmacyAuth.set_current_user(mock_user)
                      self.pharm_uname.clear()
                      self.pharm_pword.clear()
                 else:
                      Auth.set_current_user(mock_user)
                      self.store_uname.clear()
                      self.store_pword.clear()
                      
                 self.login_success.emit(mode, "superadmin")
            else:
                 QMessageBox.warning(self, "Login Failed", "Invalid Super Admin credentials or unauthorized.")
                 
        task_manager.run_task(run_verify, on_finished=on_finished)

    def check_contract(self):
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM app_settings WHERE key = 'contract_end'")
                row = cursor.fetchone()
                
                if not row:
                    QMessageBox.critical(self, "System Error", 
                                       "Contract data missing. Please contact support or run setup again.")
                    return False

                contract_end_str = row['value']
                try:
                    contract_end = datetime.strptime(contract_end_str, '%Y-%m-%d')
                except ValueError:
                    # Fallback for ISO format if needed
                    contract_end = datetime.fromisoformat(contract_end_str)

                # Check if expired
                if datetime.now() > contract_end:
                    # 3a. Contract Expiration - Try Online Renewal Check
                    print("⌛ Contract expired locally. Checking online for renewal...")
                    
                    try:
                        renewed = False
                        if supabase_manager.check_connection():
                            sid = local_config.get("system_id")
                            status = supabase_manager.get_installation_status(sid)
                            
                            if status:
                                online_expiry_str = status.get('contract_expiry')
                                if online_expiry_str:
                                    # Parse online date (usually YYYY-MM-DD)
                                    online_expiry = datetime.strptime(online_expiry_str, '%Y-%m-%d')
                                    if online_expiry > datetime.now():
                                        # Contract IS renewed! Update local DB.
                                        cursor.execute("UPDATE app_settings SET value = ? WHERE key = 'contract_end'", 
                                                     (online_expiry_str,))
                                        conn.commit()
                                        
                                        # Update local config too
                                        local_config.set("contract_expiry", online_expiry_str)
                                        
                                        QMessageBox.information(self, "Contract Renewed", 
                                            f"Your contract has been successfully renewed until {online_expiry_str}. \nThank you!")
                                        return True
                    except Exception as e:
                        print(f"⚠️ Online renewal check failed: {e}")

                    # If still expired after check
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("Contract Expired")
                    # msg_box.setIcon(QMessageBox.Icon.Critical)
                    msg_box.setText(
                        "<h2 style='color:#ee5d50; margin-bottom:6px;'>🚫 Contract Completed</h2>"
                        "<p style='margin-top:4px;'>Thank you for using our service 🙏</p>"
                        "<p>Your contract has <b>expired</b>. To continue using the system, "
                        "please <b>renew your contract</b>.</p>"
                        "<p>If you have any questions regarding renewal, feel free to contact us.</p>"
                        "<hr>"
                        "<p><b>OR DEVELOPER</b></p>"
                        "<p>📱 WhatsApp: <b>+93 796 776 436</b></p>"
                        "<p>📞 Mobile: <b>+93 796 776 436</b></p>"
                        "<p>📧 Email: <b>zubaidullah.khan1437@gmail.com</b></p>"
                        "<p style='font-size:11px; color:#777;'>We’re happy to assist you anytime 🚀</p>"
                    )
                    msg_box.setTextFormat(Qt.TextFormat.RichText)
                    t = theme_manager.DARK if theme_manager.is_dark else theme_manager.QUICKMART
                    msg_box.setStyleSheet(f"QMessageBox {{ background-color: {t['bg_card']}; }} QLabel {{ color: {t['text_main']}; }}")
                    msg_box.exec()
                    return False
                    
            return True
        except Exception as e:
            print(f"❌ Contract Check Error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to verify contract: {e}")
            return False

    def change_language(self, lang):
        lang_manager.set_language(lang)
        self.update_ui_text()

    def update_ui_text(self):
        # Update Main View
        self.main_title.setText(lang_manager.get("welcome_title") or "Welcome to Affex POS")
        self.main_subtitle.setText(lang_manager.get("select_business") or "Please select a business to continue")
        
        # Update Inputs
        for uname in [self.store_uname, self.pharm_uname]:
            uname.setPlaceholderText(lang_manager.get("username") or "Username")
        for pword in [self.store_pword, self.pharm_pword]:
            pword.setPlaceholderText(lang_manager.get("password") or "Password")
            
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft if lang_manager.is_rtl() else Qt.LayoutDirection.LeftToRight)

    def show_contract_update(self):
        # Hybrid Security Check
        # Check connection silently first
        is_online = False
        try:
             is_online = supabase_manager.check_connection()
        except:
             pass
        
        if is_online:
            # -----------------------------------------------------
            # ONLINE MODE: Verify against Cloud (Super Admin)
            # -----------------------------------------------------
            from PyQt6.QtWidgets import QInputDialog, QLineEdit, QMessageBox
            
            key, ok = QInputDialog.getText(self, "Cloud Verification (Online)", 
                                           "System is Online.\nEnter Cloud Secret Key (Super Admin):", 
                                           QLineEdit.EchoMode.Password)
            if not ok or not key: return
            
            # Verify against Supabase
            if not supabase_manager.verify_installer("superadmin", key):
                 QMessageBox.critical(self, "Access Denied", "Invalid Cloud Secret Key.")
                 return
                 
        else:
            # -----------------------------------------------------
            # OFFLINE MODE: Verify against Local DB
            # -----------------------------------------------------
            from PyQt6.QtWidgets import QInputDialog, QLineEdit, QMessageBox
            
            key, ok = QInputDialog.getText(self, "Security Verification (Offline)", 
                                           "System is Offline.\nEnter Local Security Key:", 
                                           QLineEdit.EchoMode.Password)
            if not ok or not key: return
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM app_settings WHERE key = 'security_key'")
                row = cursor.fetchone()
                if not row or key != row['value']:
                    QMessageBox.warning(self, "Access Denied", "Invalid Security Key")
                    return

        # ---------------------------------------------------------
        # PROCEED TO UPDATE
        # ---------------------------------------------------------
        from PyQt6.QtWidgets import QDialog, QDateEdit, QFormLayout
        from PyQt6.QtCore import QDate
        diag = QDialog(self)
        diag.setWindowTitle("Update System Contract")
        diag.setFixedWidth(350)
        d_layout = QFormLayout(diag)
        target_date = QDateEdit(QDate.currentDate().addYears(1))
        target_date.setCalendarPopup(True)
        d_layout.addRow("New Expiry Date:", target_date)
        update_btn = QPushButton("Confirm Update")
        style_button(update_btn, variant="success")
        
        def do_update():
            # Final key check (Local or re-verify? User said check online. 
            # We already checked online above. We can do a quick re-confirm or just proceed.)
            # Let's just confirm locally to avoid annoyance, or strictly re-check?
            # User wants "check secret key online". We did that. 
            # Let's just ask for confirmation.
            
            confirm = QMessageBox.question(diag, "Confirm", 
                                         f"Extend contract until {target_date.date().toString('yyyy-MM-dd')}?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if confirm == QMessageBox.StandardButton.Yes:
                new_date_str = target_date.date().toString("yyyy-MM-dd")
                
                # Update Local DB
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE app_settings SET value = ? WHERE key = 'contract_end'", 
                                 (new_date_str,))
                    conn.commit()
                
                # Try to Sync to Cloud (Best Effort)
                try:
                    sid = local_config.get("system_id")
                    supabase_manager.update_company_details(sid, {"contract_expiry": new_date_str})
                    QMessageBox.information(diag, "Success", "Contract updated locally and synced to cloud.")
                except:
                    QMessageBox.information(diag, "Success", "Contract updated locally. Cloud sync failed (check connection later).")
                
                diag.accept()
                
        update_btn.clicked.connect(do_update)
        d_layout.addRow(update_btn)
        diag.exec()
