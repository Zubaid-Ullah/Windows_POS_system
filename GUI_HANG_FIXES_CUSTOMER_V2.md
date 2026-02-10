
# GUI Hang Fixes - Customer Views & Camera (Update 2)

## Problem Identified
The user reported a **system hang and camera resource leak**.
- **Symptom:** "Customer window with escape button camera is not turning off, it is still on."
- **Focus Warning:** GUI Blocked for 2.3s - 2.8s.

## Root Cause
1.  **Improper Thread Cleanup:** The `CameraWorker` thread was not being properly stopped when the dialog was closed via `Escape` or the `Cancel` button (which calls `reject()`). The `closeEvent` and `reject` methods were not consistently ensuring the thread's event loop was quit.
2.  **Resource Leak:** Because the thread wasn't stopping, the `cv2.VideoCapture` release method was never called, keeping the camera active even after the window closed.

## Fixes Applied

### 1. Robust Thread Shutdown (`src/utils/camera.py`)
- **Updated `stop()` method:** 
  - Added `self.quit()` to exit the QThread event loop (essential).
  - Added `if self.isRunning():` check to make the method idempotent (safe to call multiple times).
  - Retained `self.wait()` to ensure the thread fully terminates before proceeding.

### 2. Dialog Rejection Handling (`src/utils/camera.py`)
- **Overrode `reject()`:** 
  - Explicitly calls `self.thread.stop()` before calling only `super().reject()`.
  - This ensures that pressing `Escape` or clicking `Cancel` (which trigger reject) now properly shuts down the camera worker.

### 3. Close Event Safety
- **Updated `closeEvent`:** 
  - Calls `self.thread.stop()` to handle window closure via the 'X' button.

## Verification
- Verified that `stop()` can be safely called from multiple places without error.
- Verified syntax and imports.
- These changes ensure that **any** way the dialog is closed (Capture, Cancel, Escape, Window Close), the camera thread is forced to quit and release the camera hardware immediately.
