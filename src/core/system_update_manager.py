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
        self.update_timer.setInterval(30000)  # Check for updates every 30 seconds
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start()

        self.last_update_check = 0
        self.module_cache = {}

    def check_for_updates(self):
        """Check for system updates and apply them"""
        try:
            # Check database for new configurations
            self.refresh_database_cache()

            # Check for UI theme updates
            self.refresh_theme_settings()

            # Check for localization updates
            self.refresh_localization()

            # Check for user permissions updates
            self.refresh_user_permissions()

        except Exception as e:
            self.update_failed.emit(f"Update check failed: {str(e)}")

    def refresh_database_cache(self):
        """Refresh database connections and cached data"""
        try:
            # Test database connection
            with db_manager.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()

            # Refresh any cached data if needed
            self.update_completed.emit("Database cache refreshed")

        except Exception as e:
            self.update_failed.emit(f"Database refresh failed: {str(e)}")

    def refresh_theme_settings(self):
        """Refresh theme settings without restart"""
        try:
            from src.ui.theme_manager import theme_manager
            # Reload theme settings from database or config
            theme_manager.apply_theme()
            self.update_completed.emit("Theme settings refreshed")

        except Exception as e:
            self.update_failed.emit(f"Theme refresh failed: {str(e)}")

    def refresh_localization(self):
        """Refresh localization settings"""
        try:
            from src.core.localization import lang_manager
            # Reapply current language settings
            lang_manager.apply_language()
            self.update_completed.emit("Localization refreshed")

        except Exception as e:
            self.update_failed.emit(f"Localization refresh failed: {str(e)}")

    def refresh_user_permissions(self):
        """Refresh user permissions cache"""
        try:
            from src.core.auth import Auth
            from src.core.pharmacy_auth import PharmacyAuth

            # Clear any cached permissions
            if hasattr(Auth, '_permission_cache'):
                Auth._permission_cache.clear()

            if hasattr(PharmacyAuth, '_permission_cache'):
                PharmacyAuth._permission_cache.clear()

            self.update_completed.emit("User permissions refreshed")

        except Exception as e:
            self.update_failed.emit(f"Permissions refresh failed: {str(e)}")

    def reload_module(self, module_name):
        """Reload a specific Python module"""
        try:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                self.update_completed.emit(f"Module {module_name} reloaded")
                return True
            else:
                self.update_failed.emit(f"Module {module_name} not found")
                return False

        except Exception as e:
            self.update_failed.emit(f"Module reload failed: {str(e)}")
            return False

    def force_full_refresh(self):
        """Force a complete system refresh"""
        try:
            # Refresh all components
            self.refresh_database_cache()
            self.refresh_theme_settings()
            self.refresh_localization()
            self.refresh_user_permissions()

            # Reload critical UI modules
            critical_modules = [
                'src.ui.theme_manager',
                'src.core.localization',
                'src.core.auth',
                'src.core.pharmacy_auth'
            ]

            for module in critical_modules:
                self.reload_module(module)

            self.update_completed.emit("Full system refresh completed")

        except Exception as e:
            self.update_failed.emit(f"Full refresh failed: {str(e)}")

    def stop_auto_updates(self):
        """Stop automatic update checks"""
        self.update_timer.stop()

    def start_auto_updates(self):
        """Start automatic update checks"""
        self.update_timer.start()

# Global instance
system_update_manager = SystemUpdateManager()