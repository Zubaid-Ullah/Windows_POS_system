from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from src.core.supabase_manager import supabase_manager
from src.core.local_config import local_config
from datetime import datetime
import sys

class LicenseGuard(QObject):
    system_deactivated = pyqtSignal(dict) # info dictionary

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sid = local_config.get("system_id")
        
        # Periodic check timer (every 10 minutes)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_status)
        self.timer.start(600000) # 10 mins

    def check_status(self):
        # 1. Check Contract Expiry
        expiry_str = local_config.get("contract_expiry")
        is_expired = False
        try:
            expiry_date = datetime.fromisoformat(expiry_str)
            if datetime.now() > expiry_date:
                is_expired = True
                print(f"⚠️ Contract Expired on {expiry_str}")
        except Exception as e:
            print(f"Error parsing expiry: {e}")
            is_expired = True # Fail safe

        # 2. Handle Expiry (Force Online Check)
        if is_expired:
            print("⏳ Contract expired. Forcing online check...")
            try:
                status_data = supabase_manager.get_installation_status(self.sid)
                if not status_data:
                    print("❌ Failed to fetch online status during expiry check.")
                    # In a real strict system, we might block here. 
                    # For now, let's emit deactivated if we can't verify renewal.
                    self.system_deactivated.emit({'message': 'Contract Expired. Internet required to renew.'})
                    return False
                
                # Check if cloud has new date
                cloud_expiry = status_data.get('contract_expiry')
                if cloud_expiry and cloud_expiry != expiry_str:
                    print(f"✅ Contract renewed! New expiry: {cloud_expiry}")
                    local_config.set("contract_expiry", cloud_expiry)
                    # Also update other fields if needed
                    if status_data.get('company_name'): local_config.set("company_name", status_data.get('company_name'))
                    if status_data.get('uuid'): local_config.set("uuid", status_data.get('uuid'))
                    
                    # Re-check locally
                    new_expiry = datetime.fromisoformat(cloud_expiry)
                    if datetime.now() < new_expiry:
                        print("🎉 System reactivated.")
                        return True
                
                if status_data.get('status') == 'deactivated':
                    self.system_deactivated.emit(status_data)
                    return False
                
                # If we are here, it means we connected but expiry is still old
                print("❌ Contract is still expired in cloud.")
                self.system_deactivated.emit({'message': 'Contract Expired. Please contact support.'})
                return False

            except Exception as e:
                print(f"❌ Error during expiry check: {e}")
                self.system_deactivated.emit({'message': f'Contract Expired. Connection Error: {e}'})
                return False

        # 3. If Valid Duration, Check Offline Mode
        if local_config.get("offline_mode"):
            # print("📡 Offline Mode Active - Skipping periodic cloud check.")
            return True

        # 4. Standard Online Check (if not offline mode)
        try:
            status_data = supabase_manager.get_installation_status(self.sid)
            if status_data:
                # Sync expiry just in case it changed silently
                if status_data.get('contract_expiry'):
                    if status_data.get('contract_expiry') != expiry_str:
                         local_config.set("contract_expiry", status_data.get('contract_expiry'))
                         
                if status_data.get('status') == 'deactivated':
                    self.system_deactivated.emit(status_data)
                    return False
        except Exception as e:
            print(f"Periodic check failed: {e}")
            # If standard check fails, we don't block unless expired (handled above)
            return True

        return True

    def boot_check(self):
        # Quick check for bootstrap
        return self.check_status()
