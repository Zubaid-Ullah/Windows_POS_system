import os
import sqlite3
import shutil
from datetime import datetime

class SystemMaintainer:
    @staticmethod
    def cleanup_old_backups(backup_dir, keep_days=30):
        # Implementation to delete backups older than keep_days
        pass

    @staticmethod
    def check_db_integrity(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            return result == "ok"
        except Exception:
            return False

    @staticmethod
    def rotate_logs(log_file, max_size_mb=10):
        if os.path.exists(log_file) and os.path.getsize(log_file) > max_size_mb * 1024 * 1024:
            shutil.move(log_file, f"{log_file}.{datetime.now().strftime('%Y%m%d')}")
            return True
        return False
