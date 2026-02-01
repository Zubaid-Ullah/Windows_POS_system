import cv2
import os
import time

from PyQt6.QtWidgets import QInputDialog, QMessageBox

def capture_image(save_path, parent=None):
    """
    Opens camera, waits for spacebar to capture, or 'q' to quit.
    Returns True if captured, False otherwise.
    """
    # Point: "first ask to choose camera"
    # Try common indices 0, 1, 2
    available = []
    for i in range(3):
        temp = cv2.VideoCapture(i)
        if temp.isOpened():
            available.append(str(i))
            temp.release()
    
    if not available:
        return False, "No cameras found"
        
    index_str, ok = QInputDialog.getItem(parent, "Select Camera", "Choose Camera Index:", available, 0, False)
    if not ok: return False, ""
    
    camera_index = int(index_str)
    print(f"DEBUG: Attempting to open camera {camera_index} for: {save_path}")
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"DEBUG: Camera {camera_index} failed to open")
        return False, f"Could not open camera {camera_index}"
    print(f"DEBUG: Camera {camera_index} opened successfully")

    captured = False
    error_msg = ""
    
    # Create directory if not exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            error_msg = "Failed to grab frame"
            break

        # Show preview
        cv2.imshow("Press SPACE to Capture, ESC to Cancel", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # Space
            print("DEBUG: SPACE pressed, capturing...")
            cv2.imwrite(save_path, frame)
            captured = True
            break
        elif key == 27 or key == ord('q'):  # ESC or Q
            print("DEBUG: ESC or Q pressed, cancelling...")
            break

    cap.release()
    cv2.destroyAllWindows()
    # On some systems (especially Mac), we need to pump events to close the window
    for _ in range(10): cv2.waitKey(1)
    
    print(f"DEBUG: Camera session ended. Captured: {captured}")
    return captured, error_msg
