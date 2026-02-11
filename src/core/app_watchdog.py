from PyQt6.QtCore import QThread, QTimer, QObject, pyqtSignal, QDateTime
import time
import os

class AppWatchdog(QThread):
    """
    Background service that monitors the responsiveness of the main GUI thread.
    If the GUI hangs for more than X seconds, it logs the event.
    """
    ui_hang_detected = pyqtSignal(float) # Hang duration in seconds

    def __init__(self, timeout=10.0):
        super().__init__()
        self.timeout = timeout # seconds (Increased to 10.0 for better tolerance)
        self.last_heartbeat = time.time()
        self.last_check_time = time.time()
        self._running = True
        self._paused = False
        self._grace_period_until = 0 # Timestamp until which we ignore hangs (e.g. right after focus)
        self.daemon = True # Ensure it closes with the app

    def run(self):
        print("[Watchdog] UI Responsiveness Monitor Started.")
        last_alive_print = time.time()
        self.last_check_time = time.time()
        
        while self._running:
            now = time.time()
            
            # 1. Detect system sleep or process suspension (App Nap)
            # If current loop took > 5s, the system likely slept.
            if now - self.last_check_time > 5.0:
                 print("[Watchdog] System sleep/wake detected. Resetting baseline.")
                 self.last_heartbeat = now
                 self.last_check_time = now
                 time.sleep(0.5)
                 continue

            if self._paused:
                time.sleep(1)
                self.last_heartbeat = time.time() # Keep baseline fresh
                self.last_check_time = time.time()
                continue

            # 2. Check how long since last heartbeat
            elapsed = now - self.last_heartbeat
            
            # 3. Only trigger if outside grace period
            if elapsed > self.timeout and now > self._grace_period_until:
                import sys
                import threading
                import traceback
                
                # Identify where main thread is stuck
                main_thread_id = threading.main_thread().ident
                frames = sys._current_frames()
                main_frame = frames.get(main_thread_id)
                # ... (rest of extraction logic stays same)
                location_info = "Unknown location"
                if main_frame:
                    stack = traceback.extract_stack(main_frame)
                    for filename, lineno, name, line in reversed(stack):
                        if "src" in filename or "main.py" in filename:
                            location_info = f"{os.path.basename(filename)}:{lineno} ({name})"
                            break
                    else:
                        if stack:
                            filename, lineno, name, line = stack[-1]
                            location_info = f"{os.path.basename(filename)}:{lineno} ({name})"

                print(f"[CRITICAL] GUI HANG DETECTED! Thread blocked for {elapsed:.2f} seconds.")
                print(f"📍 Stuck at: {location_info}")
                self.ui_hang_detected.emit(elapsed)
                
                # After triggering, give another grace period to avoid flood
                self._grace_period_until = now + 5.0
            
            # Periodic proof of life
            if now - last_alive_print > 60:
                print(f"[Watchdog] Monitor active. Last GUI heartbeat: {elapsed:.2f}s ago.")
                last_alive_print = now
            
            self.last_check_time = now
            time.sleep(0.5)

    def heartbeat(self):
        """Called from the main thread to prove it's still alive."""
        self.last_heartbeat = time.time()

    def stop(self):
        self._running = False

    def pause(self):
        """Temporarily suspend monitoring (e.g., during app nap)."""
        self._paused = True

    def resume(self):
        """Resume monitoring, resetting the heartbeat baseline."""
        self._paused = False
        now = time.time()
        self.last_heartbeat = now
        self.last_check_time = now
        # Add 3 second grace period after focus gain to allow UI to settle
        self._grace_period_until = now + 3.0

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
        if self.watchdog._paused:
            return
        self.watchdog.heartbeat()

    def pause_timer(self):
        self.timer.stop()

    def resume_timer(self):
        if not self.timer.isActive():
            self.timer.start(1000)
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
