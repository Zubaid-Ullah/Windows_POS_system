import os
import subprocess
import platform
from collections import namedtuple
import uuid
import socket
from datetime import datetime, timedelta

class LocalConfig:
    _instance = None
    _data = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalConfig, cls).__new__(cls)
            cls._instance._init_path()
            cls._instance.load()
        return cls._instance

    def get_serial_key(self):
        # Define a structure to allow the .serial_key access
        Result = namedtuple('SystemInfo', ['serial_key'])
        os_type = platform.system()
        serial = "Not Found"

        try:
            if os_type == "Windows":
                # Command to get Hardware Serial Number
                cmd = "wmic bios get serialnumber"
                output = subprocess.check_output(cmd, shell=True, text=True)
                serial = output.split("\n")[1].strip()

            elif os_type == "Darwin":  # macOS
                cmd = "ioreg -l | grep IOPlatformSerialNumber"
                output = subprocess.check_output(cmd, shell=True, text=True)
                serial = output.split('"')[-2]

            elif os_type == "Linux":
                # Common path for system serial
                with open("/sys/class/dmi/id/product_serial", "r") as f:
                    serial = f.read().strip()

        except Exception:
            serial = "Permission Denied / Error"

        # Return as an object so you can call .serial_key
        return Result(serial_key=serial)
    @staticmethod
    def get_data_dir():
        import platform
        import sys
        
        # Define the app name for the data folder
        app_name = "FaqiriTechPOS"
        
        if platform.system() == "Darwin":
            # macOS: ~/Library/Application Support/FaqiriTechPOS
            base = os.path.expanduser("~/Library/Application Support")
            data_dir = os.path.join(base, app_name)
        elif platform.system() == "Windows":
            # Windows: %APPDATA%/FaqiriTechPOS
            base = os.environ.get("APPDATA") or os.path.expanduser("~/AppData/Roaming")
            data_dir = os.path.join(base, app_name)
        else:
            # Linux: ~/.local/share/FaqiriTechPOS
            base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
            data_dir = os.path.join(base, app_name)
            
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except:
                # Fallback to current directory if OS-standard path is unwritable
                return os.getcwd()
        return data_dir

    def _init_path(self):
        import sys
        # Writable data goes to the system-standard data directory
        self.base_data_dir = self.get_data_dir()
        
        # Asset directory (Read-only icons, etc.)
        if getattr(sys, 'frozen', False):
            # Bundled resources (Contents/Resources or MEIPASS)
            self.assets_dir = getattr(sys, '_MEIPASS', os.path.join(os.path.dirname(sys.executable), "..", "Resources"))
        else:
            # Dev mode
            self.assets_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
        cred_dir = os.path.join(self.base_data_dir, "credentials")
        if not os.path.exists(cred_dir):
            try:
                os.makedirs(cred_dir, exist_ok=True)
            except: pass
            
        self.config_path = os.path.join(cred_dir, "useraccount.txt")

    def load(self):
        # Default data
        self._data = {
            "system_id": self._generate_system_id(),
            "pc_name": socket.gethostname(),
            "serial_key": f"{self.get_serial_key().serial_key}",
            "installation_time": datetime.now().isoformat(),
            "contract_duration_days": 365,
            "contract_expiry": "2023-01-01T00:00:00",
            "login_mode": "each_time",
            "account_created": "False",
            "status": "active",
            "offline_mode": "False",
            "installed_by": ""
        }

        if os.path.exists(self.config_path):
            try:
                content = ""
                with open(self.config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if "--- DATA ---" in content:
                    data_part = content.split("--- DATA ---")[1]
                    for line in data_part.strip().split("\n"):
                        if ":" in line:
                            k, v = line.split(":", 1)
                            self._data[k.strip()] = v.strip()
            except Exception as e:
                print(f"Error loading useraccount.txt: {e}")
        else:
            # Create the file with requirements + default data
            self.save()

    def save(self):
        try:
            # Read requirements part
            requirements = ""
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "--- DATA ---" in content:
                        requirements = content.split("--- DATA ---")[0]
                    else:
                        requirements = content

            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(requirements.strip())
                f.write("\n\n--- DATA ---\n")
                for k, v in self._data.items():
                    f.write(f"{k}: {v}\n")
        except Exception as e:
            print(f"Error saving useraccount.txt: {e}")

    def _generate_system_id(self):
        return "SYS-" + uuid.uuid4().hex[:12].upper()

    def get(self, key, default=None):
        val = self._data.get(key, default)
        # Convert string booleans back
        if val == "True": return True
        if val == "False": return False
        return val

    def set(self, key, value):
        self._data[key] = str(value)
        self.save()

    def is_registered(self):
        return self.get("account_created") == True

local_config = LocalConfig()
