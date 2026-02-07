from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QThread
from src.core.supabase_manager import supabase_manager
from src.core.local_config import local_config
from datetime import datetime, timedelta
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
        self.shutdown_window = None

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
                from datetime import timezone
                # Support relative shutdown marker (client time based)
                if isinstance(shutdown_time_str, str) and shutdown_time_str.startswith("IN_MINUTES:"):
                    try:
                        minutes = int(shutdown_time_str.split(":", 1)[1].strip())
                    except:
                        minutes = None

                    if minutes is not None:
                        now = datetime.now(timezone.utc)
                        shutdown_time = now + timedelta(minutes=minutes)
                        # Persist a fixed UTC timestamp so subsequent polls don't rebase.
                        try:
                            from src.core.blocking_task_manager import task_manager

                            def _persist_time():
                                iso = shutdown_time.isoformat().replace("+00:00", "Z")
                                supabase_manager.update_company_details(self.sid, {"shutdown_time": iso})
                                return iso

                            def _on_persisted(iso):
                                # Replace local var for immediate evaluation
                                nonlocal shutdown_time_str
                                shutdown_time_str = iso

                            task_manager.run_task(_persist_time, on_finished=_on_persisted)
                        except:
                            pass
                    else:
                        shutdown_time = None
                else:
                    # Parse the shutdown time (should be in ISO format with timezone)
                    try:
                        shutdown_time = datetime.fromisoformat(shutdown_time_str.replace("Z", "+00:00"))
                    except:
                        shutdown_time = datetime.strptime(shutdown_time_str[:19], "%Y-%m-%dT%H:%M:%S")
                        shutdown_time = shutdown_time.replace(tzinfo=timezone.utc)

                if shutdown_time:
                    now = datetime.now(timezone.utc)
                    if shutdown_time.tzinfo is None:
                        shutdown_time = shutdown_time.replace(tzinfo=timezone.utc)
                
                    remaining = (shutdown_time - now).total_seconds()
                    print(f"🔍 Shutdown check: Target={shutdown_time_str}, Now={now.isoformat()}, Remaining={remaining}s")

                    if remaining > 0 and remaining < 600: # Within 10 minutes in the future
                        self._show_shutdown_countdown(shutdown_time)
                    elif remaining <= 0 and remaining > -600: # Target reached (within last 10 mins)
                        self._execute_immediate_shutdown(status_data)
            except Exception as e:
                print(f"Shutdown check error: {e}")

    def _show_shutdown_countdown(self, target_time):
        """Displays a GUI countdown window for the remote shutdown."""
        if self.shutdown_window or self.is_currently_locked:
            return
            
        try:
            from src.ui.views.onboarding.shutdown_window import ShutdownCountdownWindow
            self.shutdown_window = ShutdownCountdownWindow(target_time)
            # Use a wrapper to pass data if needed
            self.shutdown_window.shutdown_now.connect(lambda: self._execute_immediate_shutdown(self.last_status))
            self.shutdown_window.show()
            self.shutdown_window.raise_()
            self.shutdown_window.activateWindow()
            print("🔔 Shutdown countdown window displayed.")
        except Exception as e:
            print(f"Error showing shutdown window: {e}")

    def _execute_immediate_shutdown(self, status_data):
        """Final execution of the system shutdown."""
        try:
            import os
            import platform
            from src.database.db_manager import db_manager
            
            # 1. Notify Cloud and Log
            pc_name = platform.node()
            print(f"⚠️ REMOTE SHUTDOWN EXECUTING! (PC: {pc_name})")
            
            try:
                # Update status to indicate execution started
                supabase_manager.log_activation_attempt("SHUTDOWN_EXECUTED", self.sid, pc_name)
                # Clear the command so it doesn't loop
                supabase_manager.update_company_details(self.sid, {"shutdown_time": None})
            except: pass
            
            # 2. Safety: Close DB
            try: db_manager.close_all_connections()
            except: pass

            # 3. Final OS Command
            if platform.system() == "Windows":
                # Shutdown in 15 seconds (last chance to save)
                os.system("shutdown /s /t 15 /c \"Finalizing remote shutdown command from SuperAdmin.\"")
            elif platform.system() == "Darwin":  # macOS
                os.system('osascript -e \"tell application \\"System Events\\" to shut down\"')
            else:  # Linux
                os.system("shutdown -h now")
            
            # Close app immediately
            sys.exit(0)
        except Exception as e:
            print(f"Critical shutdown execution error: {e}")
            sys.exit(1)
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
