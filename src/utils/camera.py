import cv2
import os
import time
import PyQt6
from PyQt6.QtWidgets import QInputDialog, QMessageBox

from PyQt6.QtWidgets import QInputDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap

class CameraWorker(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    error_signal = pyqtSignal(str)

    def __init__(self, camera_index):
        super().__init__()
        self.camera_index = camera_index
        self._run_flag = True

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self.error_signal.emit(f"Could not open camera {self.camera_index}")
            return

        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                # Convert to RGB
                rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.change_pixmap_signal.emit(qt_img)
            else:
                self.error_signal.emit("Failed to grab frame")
                break
            # Throttle to ~30 FPS to prevent GUI freeze
            self.msleep(33)
        cap.release()

    def stop(self):
        if self.isRunning():
            self._run_flag = False
            self.quit()
            self.wait()

class CameraDialog(QDialog):
    def __init__(self, camera_index, save_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Camera Capture")
        self.setFixedSize(660, 540)
        self.save_path = save_path
        self.captured = False
        self.current_frame = None
        
        layout = QVBoxLayout(self)
        self.label = QLabel("Loading camera...")
        self.label.setFixedSize(640, 480)
        self.label.setStyleSheet("background: black; border: 2px solid #ccc;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        btn_layout = QHBoxLayout()
        self.capture_btn = QPushButton("Capture (Space)")
        self.capture_btn.setFixedHeight(40)
        self.capture_btn.clicked.connect(self.capture)
        
        self.cancel_btn = QPushButton("Cancel (Esc)")
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.capture_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.thread = CameraWorker(camera_index)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.error_signal.connect(self.handle_error)
        self.thread.start()

    def accept(self):
        self.thread.stop()
        super().accept()

    def reject(self):
        self.thread.stop()
        super().reject()

    def update_image(self, qt_img):
        self.current_frame = qt_img
        pixmap = QPixmap.fromImage(qt_img)
        self.label.setPixmap(pixmap.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def handle_error(self, msg):
        QMessageBox.critical(self, "Camera Error", msg)
        self.reject()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.capture()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def capture(self):
        if self.current_frame:
            try:
                os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
                # Clone the image to avoid race conditions with the background thread
                copy = self.current_frame.copy()
                copy.save(self.save_path)
                self.captured = True
                self.accept()
            except Exception as e:
                self.handle_error(f"Failed to save image: {e}")

    def closeEvent(self, event):
        self.thread.stop()
        super().closeEvent(event)

def capture_image(save_path, parent=None, choose_camera=True):
    """
    Opens camera dialog, allows capture via spacebar.
    Returns (True, "") if captured, (False, error_msg) otherwise.
    """
    from src.core.blocking_task_manager import task_manager
    from PyQt6.QtWidgets import QProgressDialog
    
    # Use a progress dialog for probing since it can take seconds
    progress = QProgressDialog("Scanning for cameras...", "Cancel", 0, 0, parent)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.show()
    
    
    # Use a threading Event for cancellation to avoid cross-thread GUI access
    import threading
    cancel_event = threading.Event()
    
    # Handle cancellation safely on the main thread
    def check_cancel():
        try:
            # Check if progress dialog still exists and was canceled
            if progress and not progress.isHidden() and progress.wasCanceled():
                cancel_event.set()
            elif not cancel_event.is_set():
                # Check again in 100ms if not finished or canceled
                QTimer.singleShot(100, check_cancel)
        except (RuntimeError, AttributeError):
            # Object probably deleted, stop checking
            pass
            
    # Start the cancel checker
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(100, check_cancel)
    
    def probe_cameras(progress_callback=None):
        available = []
        # Probe up to 3 indices (usually enough for built-in + 1 external)
        for i in range(3):
            # Check thread-safe event
            if cancel_event.is_set():
                break
                
            if progress_callback: progress_callback()
            
            # Additional check before heavy operation
            if cancel_event.is_set(): break
            
            temp = cv2.VideoCapture(i)
            if temp.isOpened():
                available.append(i)
                temp.release()
            
            if progress_callback: progress_callback()
        
        # Return all available cameras for optional user selection
        if not available:
            return []
        print(f"[Camera] Detected cameras at indices: {available}")
        return available

    # We need a synchronous-looking execution but without blocking the event loop
    probe_result = {"indices": [], "done": False}
    
    def on_ready(indices):
        probe_result["indices"] = indices or []
        probe_result["done"] = True
        progress.accept()

    def force_timeout():
        if probe_result["done"]:
            return
        cancel_event.set()
        progress.cancel()

    task_manager.run_task(probe_cameras, on_finished=on_ready)
    QTimer.singleShot(10000, force_timeout)
    progress.exec() # This keeps local event loop running while task finishes
    
    if progress.wasCanceled() or cancel_event.is_set():
        return False, "Camera scan cancelled"
        
    indices = probe_result["indices"]
    if not indices:
        return False, "No cameras found"

    camera_index = indices[0]
    if choose_camera and len(indices) > 1:
        opts = [f"Camera {i}" for i in indices]
        selected, ok = QInputDialog.getItem(parent, "Select Camera", "Choose camera:", opts, 0, False)
        if not ok:
            return False, "Camera selection cancelled"
        try:
            camera_index = int(selected.split(" ")[1])
        except Exception:
            camera_index = indices[0]
    
    dialog = CameraDialog(camera_index, save_path, parent)
    result = dialog.exec()
    return bool(result), ""
