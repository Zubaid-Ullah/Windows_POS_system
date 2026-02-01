import shutil
import os
from datetime import datetime
from src.database.db_manager import db_manager

class BackupManager:
    @staticmethod
    def create_backup(destination_dir):
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"pos_backup_{timestamp}.db"
        dest_path = os.path.join(destination_dir, backup_name)
        
        try:
            shutil.copy2(db_manager.db_path, dest_path)
            return True, dest_path
        except Exception as e:
            return False, str(e)

    @staticmethod
    def restore_backup(backup_path):
        try:
            # Simple restore by copying back
            shutil.copy2(backup_path, db_manager.db_path)
            return True, "Database restored successfully"
        except Exception as e:
            return False, str(e)
