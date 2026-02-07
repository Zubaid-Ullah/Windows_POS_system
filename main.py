# --- STARTUP LOGGING (CAPTURE EARLY CRASHES) ---
import sys
import os
import traceback
from datetime import datetime

# Logging removed for security as requested
def log_msg(msg):
    pass

try:
    print("--- FaqiriTech POS GUI Startup Session ---")
    print(f"Executable: {sys.executable}")
    print(f"CWD: {os.getcwd()}")
    
    # If we are in a .app bundle, let's fix CWD to Resources
    if getattr(sys, 'frozen', False) and "Contents/MacOS" in sys.executable:
        res_path = os.path.join(os.path.dirname(sys.executable), "..", "Resources")
        if os.path.exists(res_path):
            os.chdir(res_path)
            print(f"Changed CWD to Bundle Resources: {os.getcwd()}")
except Exception as e:
    pass

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtGui import QFont, QIcon
from src.ui.main_window import MainWindow
from credentials.bootstrap_installations_table import bootstrap_installations_table
from src.core.supabase_manager import supabase_manager
from src.core.local_config import local_config
from src.core.license_guard import LicenseGuard
from src.ui.views.onboarding.connectivity_gate import ConnectivityGateWindow
from src.ui.views.onboarding.create_account_stepper import CreateAccountWindow
from src.ui.views.onboarding.login_window import LoginWindow
from src.ui.views.onboarding.locked_window import LockedWindow
from src.database.db_manager import db_manager
from src.ui.views.login_view import LoginView 
from src.ui.theme_manager import theme_manager

def main():
    try:
        app = QApplication(sys.argv)
        print("QApplication initialized.")
        app.setFont(QFont("Arial"))
        app.setQuitOnLastWindowClosed(False)
        
        # Set Global App Icon
        if getattr(sys, 'frozen', False):
            # Try finding icon in multiple bundle locations
            base = getattr(sys, '_MEIPASS', os.path.join(os.path.dirname(sys.executable), "..", "Resources"))
            icon_path = os.path.join(base, "Logo", "logo.ico")
        else:
            icon_path = os.path.join(os.path.dirname(__file__), "Logo", "logo.ico")
        
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            print(f"Icon loaded from: {icon_path}")
        
        theme_manager.init_theme()
        
        # Background Bootstrap (Non-blocking)
        def bootstrap_db():
            try:
                from src.core.auth import Auth
                from src.core.pharmacy_auth import PharmacyAuth
                Auth.ensure_defaults()
                PharmacyAuth.ensure_defaults()
                print("[DEBUG] Background DB Bootstrap complete.")
            except Exception as e:
                print(f"[ERROR] Background Bootstrap Failed: {e}")

        from src.core.blocking_task_manager import task_manager
        task_manager.run_task(bootstrap_db)

        # Start GUI Watchdog (Background Monitor)
        from src.core.app_watchdog import start_watchdog
        watchdog = start_watchdog()
        watchdog.ui_hang_detected.connect(lambda d: print(f"⚠️ App focus warning: UI was frozen for {d:.1f}s. Check background tasks."))

        # Shared References to prevent garbage collection
        main_window = None
        onboarding_window = None
        installer_login_window = None
        app_login_window = None
        locked_screen = None # Track the active lock screen
        gate = ConnectivityGateWindow()
        
        # Security Guard Integration
        guard = LicenseGuard()

        def show_locked_screen(info):
            nonlocal locked_screen
            if not locked_screen:
                locked_screen = LockedWindow(contact_info=info)
                locked_screen.show()
            if main_window: main_window.hide()

        def hide_locked_screen():
            nonlocal locked_screen
            if locked_screen:
                locked_screen.close()
                locked_screen = None
            if main_window: main_window.show()

        def handle_modular_access(store_active, pharmacy_active):
            """Applies module-level permissions globally."""
            if main_window:
                main_window.set_modules_visibility(store_active, pharmacy_active)
            # Store these in local config for session persistence
            local_config.set("store_active", store_active)
            local_config.set("pharmacy_active", pharmacy_active)

        # Connect Real-time Security Signals
        guard.system_deactivated.connect(show_locked_screen)
        guard.system_activated.connect(hide_locked_screen)
        guard.modules_updated.connect(handle_modular_access)

        def start_main_app(mode="STORE", role="user"):
            if app_login_window: app_login_window.close()
            
            # Smart Module Selection: If default mode is deactivated, pick the other one
            store_on = local_config.get("store_active", True)
            pharmacy_on = local_config.get("pharmacy_active", True)
            
            if mode == "STORE" and not store_on:
                if pharmacy_on: mode = "PHARMACY"
            elif mode == "PHARMACY" and not pharmacy_on:
                if store_on: mode = "STORE"

            if role != "superadmin":
                if not check_contract_validity():
                    print("[WARNING] Contract expired. Auto-login disabled.")
                    show_app_login()
                    return
                
            nonlocal main_window
            print(f"[INFO] Launching Main POS Interface (Mode: {mode})...")
            main_window = MainWindow()
            main_window.set_modules_visibility(store_on, pharmacy_on)
            main_window.show_main_app(mode)
            main_window.show()

        def check_contract_validity():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT value FROM app_settings WHERE key = 'contract_end'")
                    row = cursor.fetchone()
                    if row:
                        contract_end_str = row['value']
                        try:
                            contract_end = datetime.strptime(contract_end_str, '%Y-%m-%d')
                            if datetime.now() > contract_end:
                                return False
                        except:
                            return False
                    else:
                        return False
                return True
            except Exception as e:
                print(f"Contract check warning: {e}")
                return False

        def verify_local_data_integrity():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT value FROM app_settings WHERE key = 'company_name'")
                    if not cursor.fetchone():
                        return False
                return True
            except Exception as e:
                print(f"[WARNING] DB Integrity Check Failed: {e}")
                return False
        def on_internet_gate_resolved(online):
            try:
                print("="*60)
                print(f"[DEBUG] Gate resolve sequence START: online={online}")
                print(f"[DEBUG] Checking local registration...")
                is_registered_local = local_config.is_registered() and verify_local_data_integrity()
                print(f"[DEBUG] is_registered_local={is_registered_local}")
                sid = local_config.get("system_id")
                print(f"[DEBUG] system_id={sid}")

                if not online:
                    print("[DEBUG] Offline mode detected")
                    if is_registered_local:
                        print("[DEBUG] Calling jump_to_app() for offline registered user")
                        jump_to_app()
                        return
                    else:
                        print("[DEBUG] No local registration, showing activation required message")
                        QMessageBox.critical(None, "Activation Required", "Internet required for first-time activation.")
                        sys.exit()

                def check_cloud():
                    try:
                        print(f"[DEBUG] Calling supabase_manager.get_installation_status({sid})")
                        return supabase_manager.get_installation_status(sid)
                    except Exception as e:
                        print(f"[DEBUG] Supabase check failed: {e}")
                        return None

                def on_cloud_check_finished(cloud_record):
                    if not cloud_record:
                        print("[DEBUG] No cloud record found")
                        if is_registered_local:
                            print("[DEBUG] Calling jump_to_app() for locally registered user")
                            jump_to_app()
                        else:
                            print("[DEBUG] Calling show_registration_stepper()")
                            show_registration_stepper()
                    else:
                        print("[DEBUG] Cloud record found, processing...")
                        status = cloud_record.get('status', 'active')
                        print(f"[DEBUG] Account status={status}")
                        if status == 'deactivated':
                            print("[DEBUG] Account deactivated, showing locked screen")
                            show_locked_screen(cloud_record)
                            return

                        print("[DEBUG] Setting local config...")
                        local_config.set("account_created", True)
                        local_config.set("status", status)
                        
                        # Store modular activation flags
                        store_active = cloud_record.get('store_active', True)
                        pharmacy_active = cloud_record.get('pharmacy_active', True)
                        local_config.set("store_active", store_active)
                        local_config.set("pharmacy_active", pharmacy_active)
                        
                        # Update guard state
                        if hasattr(guard, 'store_active'): guard.store_active = store_active
                        if hasattr(guard, 'pharmacy_active'): guard.pharmacy_active = pharmacy_active
                        
                        print("[DEBUG] Verifying local data integrity...")
                        if not verify_local_data_integrity():
                             print("[DEBUG] Data integrity failed, showing registration stepper")
                             local_config.set("account_created", False)
                             show_registration_stepper()
                             return

                        print("[DEBUG] All checks passed, calling jump_to_app()")
                        jump_to_app()
                    print("[DEBUG] on_internet_gate_resolved() task completed")

                from src.core.blocking_task_manager import task_manager
                task_manager.run_task(check_cloud, on_finished=on_cloud_check_finished)
                print("[DEBUG] on_internet_gate_resolved() completed")
                print("="*60)
            except Exception as e:
                print(f"[CRITICAL ERROR in on_internet_gate_resolved]: {e}")
                print(f"[DEBUG] Exception type: {type(e).__name__}")
                import traceback
                print(traceback.format_exc())

        def show_installer_login():
            nonlocal installer_login_window
            installer_login_window = LoginWindow()
            installer_login_window.login_success.connect(lambda: jump_to_app())
            app.setQuitOnLastWindowClosed(True)
            installer_login_window.show()
            gate.close()
            
        def show_app_login():
            try:
                print("\n" + "="*60)
                print("[DEBUG] show_app_login() START")
                nonlocal app_login_window
                
                print("[DEBUG] Creating LoginView instance...")
                app_login_window = LoginView()
                print("[DEBUG] LoginView created successfully")
                
                print("[DEBUG] Setting window title...")
                app_login_window.setWindowTitle("FaqiriTech POS Login")
                
                # Fix for Windows frozen executable - ensure window displays properly
                print("[DEBUG] Importing Qt...")
                from PyQt6.QtCore import Qt
                print("[DEBUG] Setting window flags...")
                app_login_window.setWindowFlags(Qt.WindowType.Window)
                print("[DEBUG] Setting WA_DeleteOnClose attribute...")
                app_login_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
                
                print("[DEBUG] Connecting login_success signal...")
                app_login_window.login_success.connect(start_main_app)
                app.setQuitOnLastWindowClosed(True)
                
                print("[DEBUG] Calling show()...")
                app_login_window.show()
                print("[DEBUG] Calling raise_()...")
                app_login_window.raise_()  # Bring to front
                print("[DEBUG] Calling activateWindow()...")
                app_login_window.activateWindow()  # Activate window
                
                print("[DEBUG] Closing gate...")
                gate.close()
                print("[DEBUG] Checking main_window...")
                if main_window:
                    print("[DEBUG] Closing main_window...")
                    main_window.close()
                
                print("[DEBUG] show_app_login() COMPLETED SUCCESSFULLY")
                print("="*60 + "\n")
            except Exception as e:
                print(f"[CRITICAL ERROR in show_app_login]: {e}")
                print(f"[DEBUG] Exception type: {type(e).__name__}")
                import traceback
                print(traceback.format_exc())

        def jump_to_app():
            try:
                print("\n" + "="*60)
                print("[DEBUG] jump_to_app() START")
                
                # Security Check: Even offline, respect last known cloud status
                if local_config.get("status") == "deactivated":
                     print("[DEBUG] Last known status is deactivated. Blocking.")
                     show_locked_screen({"status": "deactivated", "message": "System deactivated. Connect to internet to refresh status."})
                     return

                print("[DEBUG] Checking contract validity...")
                if not check_contract_validity():
                    print("[DEBUG] Contract invalid, showing app login")
                    show_app_login()
                    return
                
                print("[DEBUG] Showing login screen...")
                show_app_login()
                
                print("[DEBUG] jump_to_app() COMPLETED")
                print("="*60 + "\n")
            except Exception as e:
                print(f"[CRITICAL ERROR in jump_to_app]: {e}")
                print(f"[DEBUG] Exception type: {type(e).__name__}")
                import traceback
                print(traceback.format_exc())

        def show_registration_stepper():
            nonlocal onboarding_window
            try:
                onboarding_window = CreateAccountWindow()
                onboarding_window.account_created.connect(jump_to_app)
                app.setQuitOnLastWindowClosed(True)
                onboarding_window.show()
                gate.close()
            except Exception as e:
                print(f"[ERROR] Error opening registration window: {e}")
                start_main_app()

        def debug_gate_resolved(online):
            on_internet_gate_resolved(online)

        gate.connection_resolved.connect(debug_gate_resolved)
        gate.show()
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"CRITICAL STARTUP ERROR:\n{str(e)}")
        print(traceback.format_exc())
        raise e

if __name__ == "__main__":
    import threading
    threading.Thread(target=bootstrap_installations_table, daemon=True).start()
    main()