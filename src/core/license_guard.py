from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QThread
from src.core.supabase_manager import supabase_manager
from src.core.local_config import local_config
from datetime import datetime
import sys
import platform

class LicenseWorker(QObject):
    """Background worker to poll Supabase status without blocking UI."""
    status_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, sid):
        super().__init__()
        self.sid = sid

    def run(self):
        try:
            status_data = supabase_manager.get_installation_status(self.sid)
            if status_data:
                self.status_received.emit(status_data)
            else:
                self.error_occurred.emit("Empty status received")
        except Exception as e:
            self.error_occurred.emit(str(e))

class LicenseGuard(QObject):
    # Signals for UI to react immediately
    system_deactivated = pyqtSignal(dict)
    system_activated = pyqtSignal(dict) # Triggered when account is re-enabled remotely
    modules_updated = pyqtSignal(bool, bool) # store_active, pharmacy_active

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sid = local_config.get("system_id")
        self.last_status = None
        self.is_currently_locked = False
        self.store_active = True
        self.pharmacy_active = True
        
        # Periodic check timer: 60 seconds for "immediate" cloud response
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.start_async_check)
        self.poll_timer.start(60000) # 1 Minute

        # Keep reference to active thread to avoid GC and overwriting
        self._active_thread = None

    def start_async_check(self):
        """Launches a one-off thread for the network poll."""
        # Check if thread is valid AND running
        try:
            if self._active_thread and self._active_thread.isRunning():
                return
        except RuntimeError:
            # Object was deleted but reference exists
            self._active_thread = None

        self._active_thread = QThread()
        self.worker = LicenseWorker(self.sid)
        self.worker.moveToThread(self._active_thread)
        
        self._active_thread.started.connect(self.worker.run)
        self.worker.status_received.connect(self.handle_status)
        self.worker.error_occurred.connect(self.handle_error)
        
        # Cleanup
        self.worker.status_received.connect(self._active_thread.quit)
        self.worker.error_occurred.connect(self._active_thread.quit)
        self._active_thread.finished.connect(self.worker.deleteLater)
        self._active_thread.finished.connect(self._active_thread.deleteLater)
        self._active_thread.finished.connect(self._on_thread_finished)
        
        self._active_thread.start()

    def _on_thread_finished(self):
        """Nullify reference after QThread.deleteLater finishes."""
        self._active_thread = None

    def handle_status(self, status_data):
        self.last_status = status_data
        
        # 1. Modular Activation Flags (Admin can toggle Store/Pharmacy separately)
        store_active = status_data.get('store_active', True)
        pharmacy_active = status_data.get('pharmacy_active', True)
        self.modules_updated.emit(bool(store_active), bool(pharmacy_active))

        # 2. Critical Deactivation Check
        status = status_data.get('status', 'active')
        if status == 'deactivated':
            if not self.is_currently_locked:
                self.is_currently_locked = True
                self.system_deactivated.emit(status_data)
        else:
            if self.is_currently_locked:
                self.is_currently_locked = False
                self.system_activated.emit(status_data) # Auto-Unlock signal

        # 3. Sync Contract Expiry
        expiry_str = status_data.get('contract_expiry')
        if expiry_str:
            local_config.set("contract_expiry", expiry_str)

        # 4. Remote Shutdown Monitoring
        shutdown_time_str = status_data.get('shutdown_time')
        if shutdown_time_str:
            try:
                import os
                # Support both ISO and custom formats
                try:
                    shutdown_time = datetime.fromisoformat(shutdown_time_str.replace("Z", "+00:00"))
                except:
                    shutdown_time = datetime.strptime(shutdown_time_str[:19], "%Y-%m-%dT%H:%M:%S")

                now = datetime.now()
                # If target time is in the past (but was set recently), trigger shutdown
                # We use a 10 minute window to prevent old shutdown requests from triggering on reboot
                time_diff = (now - shutdown_time).total_seconds()
                
                if time_diff >= 0 and time_diff < 600: # Range: reached but less than 10 mins old
                    import platform
                    from src.database.db_manager import db_manager
                    
                    print(f"⚠️ REMOTE SHUTDOWN TRIGGERED! Target was: {shutdown_time_str}")
                    
                    # 1. Log event before dying
                    pc_name = platform.node()
                    supabase_manager.log_activation_attempt("SYSTEM_AUTO_SHUTDOWN", self.sid, pc_name)
                    
                    # 2. Safety Grace: Pre-close Database to prevent corruption
                    try:
                        db_manager.close_all_connections()
                    except: pass

                    # 3. Cross-platform shutdown with 2-minute warning
                    if platform.system() == "Windows":
                        # /t 120 gives 2 minutes for apps to close gracefully
                        os.system("shutdown /s /t 120 /c \"Remotely triggered by SuperAdmin. System will shutdown in 2 minutes. Please save your work immediately.\"")
                    else:
                        # For macOS/Linux, we use a delayed shutdown if possible, or immediate
                        os.system("sudo shutdown -h +2 \"SuperAdmin shutdown trigger. Save work.\"") 
                    
                    # 4. Exit the POS app immediately so the UI doesn't interfere with the OS shutdown
                    sys.exit(0)
            except Exception as e:
                print(f"Shutdown check error: {e}")

    def handle_error(self, err):
        # We don't block on transient network errors unless contract is locally expired
        # print(f"License poll failed (expected silently in background): {err}")
        pass

    def log_activation_attempt(self, installer_name):
        """Helper to log installer activity to cloud."""
        pc_name = platform.node()
        supabase_manager.log_activation_attempt(installer_name, self.sid, pc_name)

    def boot_check(self):
        """Sync check used during app startup."""
        try:
            status_data = supabase_manager.get_installation_status(self.sid)
            if status_data:
                self.handle_status(status_data)
                return status_data.get('status') != 'deactivated'
        except: pass
        return True # Default to allow if offline at boot
