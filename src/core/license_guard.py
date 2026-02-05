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
