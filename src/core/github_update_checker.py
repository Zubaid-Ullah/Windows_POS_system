import os
import sys
import requests
import subprocess
import tempfile
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from src.core.app_version import APP_VERSION
from src.core.local_config import local_config

class UpdateWorker(QObject):
    finished = pyqtSignal(bool, dict) # success, data
    progress = pyqtSignal(int)
    download_finished = pyqtSignal(str) # path
    error = pyqtSignal(str)

    def __init__(self, task="check", context=None):
        super().__init__()
        self.task = task
        self.context = context or {}

    def run(self):
        try:
            if self.task == "check":
                data = self._fetch_latest()
                self.finished.emit(True, data)
            elif self.task == "download":
                path = self._download()
                if path:
                    self.download_finished.emit(path)
                else:
                    self.error.emit("Download failed (Unknown error)")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if self.task != "download": # Download has its own signals
                self.finished.emit(False, {})

    def _fetch_latest(self):
        owner = self.context.get('owner')
        name = self.context.get('name')
        headers = self.context.get('headers')
        url = f"https://api.github.com/repos/{owner}/{name}/releases/latest"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"GitHub API Error: {response.status_code}")

    def _download(self):
        # First fetch release metadata to find the asset
        data = self._fetch_latest()
        assets = data.get("assets", [])
        installer_asset = next((a for a in assets if a.get("name", "").endswith(".exe")), None)
        
        if not installer_asset:
            raise Exception("No installer (.exe) found in release assets")

        download_url = installer_asset.get("url")
        asset_name = installer_asset.get("name")
        headers = self.context.get('headers').copy()
        headers["Accept"] = "application/octet-stream"
        
        save_path = os.path.join(tempfile.gettempdir(), asset_name)
        
        with requests.get(download_url, headers=headers, stream=True, timeout=15) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            bytes_downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((bytes_downloaded / total_size) * 100)
                            self.progress.emit(progress)
        return save_path

class GitHubUpdateChecker(QObject):
    update_available = pyqtSignal(str, str)
    download_progress = pyqtSignal(int)
    download_completed = pyqtSignal(str)
    download_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.repo_owner = "Zubaid-Ullah"
        self.repo_name = "Windows_POS_system"
        self.token = self._load_token()
        self._active_thread = None
        
        self.check_timer = QTimer(self)
        self.check_timer.setInterval(12 * 60 * 60 * 1000) 
        self.check_timer.timeout.connect(self.check_for_updates)

    def start(self):
        if not self.check_timer.isActive():
            self.check_timer.start()
            # Delay first check after start to let UI settle
            QTimer.singleShot(10000, self.check_for_updates)

    def _load_token(self):
        token = os.environ.get("AFEX_GITHUB_TOKEN")
        if token: return token
        try:
            paths = ["github-token.txt", os.path.join(os.getcwd(), "github-token.txt")]
            for p in paths:
                if os.path.exists(p):
                    with open(p, "r") as f: return f.read().strip()
        except: pass
        return None

    def _headers(self):
        headers = {"Accept": "application/vnd.github.v3+json",
                   "User-Agent": "AfexPOS-Update-Checker"}
        if self.token: headers["Authorization"] = f"token {self.token}"
        return headers

    def check_for_updates(self):
        try:
            if self._active_thread and self._active_thread.isRunning(): return
        except RuntimeError: self._active_thread = None
        
        self._active_thread = QThread()
        ctx = {'owner': self.repo_owner, 'name': self.repo_name, 'headers': self._headers()}
        self.worker = UpdateWorker("check", ctx)
        self.worker.moveToThread(self._active_thread)
        
        self._active_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_check_finished)
        self.worker.error.connect(lambda e: print(f"[Update] Error: {e}"))
        
        # Cleanup
        self.worker.finished.connect(self._active_thread.quit)
        self.worker.error.connect(self._active_thread.quit)
        self._active_thread.finished.connect(self.worker.deleteLater)
        self._active_thread.finished.connect(self._active_thread.deleteLater)
        self._active_thread.start()

    def _on_check_finished(self, success, data):
        if not success or not data: return
        try:
            latest_tag = data.get("tag_name", "v0.0.0").lower().replace("v", "")
            if self._is_newer(latest_tag, APP_VERSION):
                self.update_available.emit(latest_tag, data.get("body", ""))
        except Exception as e:
            print(f"[Update] Parse error: {e}")

    def _is_newer(self, latest, current):
        try:
            l_parts = [int(p) for p in latest.split(".")]
            c_parts = [int(p) for p in current.split(".")]
            return l_parts > c_parts
        except: return latest > current

    def download_update(self):
        try:
            if self._active_thread and self._active_thread.isRunning(): return
        except RuntimeError: self._active_thread = None
        
        self._active_thread = QThread()
        ctx = {'owner': self.repo_owner, 'name': self.repo_name, 'headers': self._headers()}
        self.worker = UpdateWorker("download", ctx)
        self.worker.moveToThread(self._active_thread)
        
        self._active_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.download_progress.emit)
        self.worker.download_finished.connect(self.download_completed.emit)
        self.worker.error.connect(self.download_failed.emit)
        
        # Cleanup
        self.worker.download_finished.connect(self._active_thread.quit)
        self.worker.error.connect(self._active_thread.quit)
        self._active_thread.finished.connect(self.worker.deleteLater)
        self._active_thread.finished.connect(self._active_thread.deleteLater)
        self._active_thread.start()

    def launch_installer(self, path):
        try:
            if sys.platform == "win32": os.startfile(path)
            else: subprocess.Popen(["open", path])
            sys.exit(0)
        except Exception as e: print(f"[Update] Launch failed: {e}")

update_checker = GitHubUpdateChecker()
