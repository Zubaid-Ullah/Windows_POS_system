"""
System Update Manager - Handles runtime updates without restart
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from src.database.db_manager import db_manager
import sys
import importlib

class SystemUpdateManager(QObject):
    """Manages runtime system updates and refreshes"""

    update_completed = pyqtSignal(str)  # Signal when update is done
    update_failed = pyqtSignal(str)     # Signal when update fails

    def __init__(self):
        super().__init__()
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(60000)  # Check every 60 seconds (less frequent)
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start()

        self.last_theme_hash = None
        self.last_lang_hash = None
        self.is_checking = False

    def check_for_updates(self):
        """Check for system updates and apply them asynchronously"""
        if self.is_checking: return
        self.is_checking = True
        
        from src.core.blocking_task_manager import task_manager
        
        def background_check():
            try:
                # 1. Check DB connection
                with db_manager.get_connection() as conn:
                    conn.execute("SELECT 1").fetchone()
                
                # 2. Check for theme/config changes (stub for actual hash check if needed)
                # For now, let's just assume we only refresh if something truly changed
                # or provide a way to trigger it.
                return True
            except Exception as e:
                return str(e)

        def on_finished(result):
            self.is_checking = False
            if result is True:
                # Only perform UI refreshes if absolutely necessary 
                # (Removing the heavy 30s re-applications that hung the GUI)
                pass 
            else:
                self.update_failed.emit(f"Update background check failed: {result}")

        task_manager.run_task(background_check, on_finished=on_finished)

    def force_full_refresh(self):
        """Force a complete system refresh - only call when user explicitly requests or on critical change"""
        try:
            from src.ui.theme_manager import theme_manager
            from src.core.localization import lang_manager
            from src.core.auth import Auth
            from src.core.pharmacy_auth import PharmacyAuth

            theme_manager.apply_theme()
            lang_manager.apply_language()

            if hasattr(Auth, '_permission_cache'): Auth._permission_cache.clear()
            if hasattr(PharmacyAuth, '_permission_cache'): PharmacyAuth._permission_cache.clear()

            self.update_completed.emit("Full system refresh completed")

        except Exception as e:
            self.update_failed.emit(f"Full refresh failed: {str(e)}")

    def stop_auto_updates(self):
        self.update_timer.stop()

    def start_auto_updates(self):
        self.update_timer.start()

# Global instance
system_update_manager = SystemUpdateManager()