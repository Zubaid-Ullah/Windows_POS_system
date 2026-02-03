import os
import sys
import requests
import subprocess
import tempfile
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from src.core.app_version import APP_VERSION
from src.core.local_config import local_config

class GitHubUpdateChecker(QObject):
    update_available = pyqtSignal(str, str)  # latest_version, release_notes
    download_progress = pyqtSignal(int)
    download_completed = pyqtSignal(str)     # path to installer
    download_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.repo_owner = "Zubaid-Ullah"
        self.repo_name = "Windows_POS_system"
        self.token = self._load_token()
        
        # Periodic check timer (12 hours)
        self.check_timer = QTimer(self)
        self.check_timer.setInterval(12 * 60 * 60 * 1000) 
        self.check_timer.timeout.connect(self.check_for_updates)
        self.check_timer.start()

    def _load_token(self):
        # 1. Check environment variable
        token = os.environ.get("AFEX_GITHUB_TOKEN")
        if token: return token
        
        # 2. Check github-token.txt
        try:
            # Try to find it in the root or next to main.py
            paths = [
                "github-token.txt",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "github-token.txt"),
                os.path.join(os.getcwd(), "github-token.txt")
            ]
            for p in paths:
                if os.path.exists(p):
                    with open(p, "r") as f:
                        return f.read().strip()
        except: pass
        return None

    def _headers(self):
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AfexPOS-Update-Checker"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def check_for_updates(self):
        """Calls GitHub API to check for the latest release"""
        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            response = requests.get(url, headers=self._headers(), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                latest_tag = data.get("tag_name", "v0.0.0").lower().replace("v", "")
                
                # Compare versions
                if self._is_newer(latest_tag, APP_VERSION):
                    release_notes = data.get("body", "No release notes provided.")
                    self.update_available.emit(latest_tag, release_notes)
                    return True
            else:
                print(f"[Update] GitHub API returned status: {response.status_code}")
        except Exception as e:
            print(f"[Update] Check failed: {e}")
        return False

    def _is_newer(self, latest, current):
        try:
            l_parts = [int(p) for p in latest.split(".")]
            c_parts = [int(p) for p in current.split(".")]
            return l_parts > c_parts
        except:
            return latest > current

    def download_update(self):
        """Downloads the first .exe asset from the latest release"""
        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            response = requests.get(url, headers=self._headers(), timeout=10)
            
            if response.status_code != 200:
                self.download_failed.emit("Could not fetch release data")
                return

            data = response.json()
            assets = data.get("assets", [])
            installer_asset = None
            
            # Find the first .exe asset
            for asset in assets:
                if asset.get("name", "").endswith(".exe"):
                    installer_asset = asset
                    break
            
            if not installer_asset:
                self.download_failed.emit("No installer (.exe) found in release assets")
                return

            download_url = installer_asset.get("url") # GitHub API asset URL
            asset_name = installer_asset.get("name")
            
            # Use specific asset download headers for private repos
            headers = self._headers()
            headers["Accept"] = "application/octet-stream"
            
            temp_dir = tempfile.gettempdir()
            save_path = os.path.join(temp_dir, asset_name)
            
            # Stream download
            with requests.get(download_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                bytes_downloaded = 0
                
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            bytes_downloaded += len(chunk)
                            if total_size > 0:
                                progress = int((bytes_downloaded / total_size) * 100)
                                self.download_progress.emit(progress)
            
            self.download_completed.emit(save_path)
            return save_path

        except Exception as e:
            self.download_failed.emit(str(e))
            return None

    def launch_installer(self, path):
        """Exits app and runs installer"""
        try:
            print(f"[Update] Launching installer: {path}")
            if sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.Popen(["open", path])
            
            # Force exit app
            sys.exit(0)
        except Exception as e:
            print(f"[Update] Failed to launch installer: {e}")

# Singleton
update_checker = GitHubUpdateChecker()
