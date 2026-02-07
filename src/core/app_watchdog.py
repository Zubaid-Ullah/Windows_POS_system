from PyQt6.QtCore import QThread, QTimer, QObject, pyqtSignal, QDateTime
import time
import os

class AppWatchdog(QThread):
    """
    Background service that monitors the responsiveness of the main GUI thread.
    If the GUI hangs for more than X seconds, it logs the event.
    """
    ui_hang_detected = pyqtSignal(float) # Hang duration in seconds

    def __init__(self, timeout=2.0):
        super().__init__()
        self.timeout = timeout # seconds
        self.last_heartbeat = time.time()
        self._running = True
        self.daemon = True # Ensure it closes with the app

    def run(self):
        print("[Watchdog] UI Responsiveness Monitor Started.")
        while self._running:
            # Check how long since last heartbeat
            elapsed = time.time() - self.last_heartbeat
            if elapsed > self.timeout:
                print(f"[CRITICAL] GUI HANG DETECTED! Thread blocked for {elapsed:.2f} seconds.")
                self.ui_hang_detected.emit(elapsed)
                
            # Sleep for a bit to avoid CPU hogging
            time.sleep(0.5)

    def heartbeat(self):
        """Called from the main thread to prove it's still alive."""
        self.last_heartbeat = time.time()

    def stop(self):
        self._running = False

class WatchdogHelper(QObject):
    """
    Helper to bridge the Main Thread and the Watchdog Thread.
    """
    def __init__(self, watchdog):
        super().__init__()
        self.watchdog = watchdog
        
        # Ping the watchdog every 1 second from the main thread
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.ping)
        self.timer.start(1000)

    def ping(self):
        self.watchdog.heartbeat()

# Initialization logic to be called in main.py
watchdog_instance = None
helper_instance = None

def start_watchdog():
    global watchdog_instance, helper_instance
    if watchdog_instance is None:
        watchdog_instance = AppWatchdog()
        helper_instance = WatchdogHelper(watchdog_instance)
        watchdog_instance.start()
        return watchdog_instance
    return watchdog_instance
