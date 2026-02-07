import os
import sys
import subprocess
import platform

class AutoStartHelper:
    TASK_NAME = "FaqiriTechPOS"

    @staticmethod
    def is_windows():
        return platform.system() == "Windows"

    @classmethod
    def enable_autostart(cls):
        """Creates a scheduled task to run on logon for Windows"""
        if not cls.is_windows():
            return False
        
        try:
            exe_path = os.path.abspath(sys.argv[0])
            # If running as script, sys.argv[0] might be .py, but usually this is for EXE
            if exe_path.endswith(".py"):
                # Fallback for dev mode
                exe_path = f'"{sys.executable}" "{exe_path}"'
            else:
                exe_path = f'"{exe_path}"'

            # schtasks /Create /SC ONLOGON /TN "FaqiriTechPOS" /TR "<path>" /F
            command = f'schtasks /Create /SC ONLOGON /TN "{cls.TASK_NAME}" /TR {exe_path} /F'
            subprocess.run(command, shell=True, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"[AutoStart] Failed to enable: {e}")
            return False

    @classmethod
    def disable_autostart(cls):
        """Removes the scheduled task"""
        if not cls.is_windows():
            return False
        
        try:
            command = f'schtasks /Delete /TN "{cls.TASK_NAME}" /F'
            subprocess.run(command, shell=True, check=True, capture_output=True)
            return True
        except:
            return False

    @classmethod
    def is_enabled(cls):
        """Checks if the task exists"""
        if not cls.is_windows():
            return False
        
        try:
            command = f'schtasks /Query /TN "{cls.TASK_NAME}"'
            result = subprocess.run(command, shell=True, capture_output=True)
            return result.returncode == 0
        except:
            return False
