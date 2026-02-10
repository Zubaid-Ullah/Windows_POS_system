
# GUI Hang Fixes - Customer Views & Camera

## Problem Identified
The user reported system hangs when working with the customer window. Analysis revealed two primary causes:
1.  **Camera Capture Blocking:** The camera capture utility was running a loop that could block the UI thread, causing freezes when taking photos for KYC.
2.  **Heavy UI Population:** Loading the customer list (standard and pharmacy) created all UI widgets at once on the main thread, causing freezes with large datasets.

## Fixes Applied

### 1. Camera Optimization (`src/utils/camera.py`)
- **Throttled Frame Rate:** Added a `33ms` sleep in the camera worker loop to limit frame rate to ~30FPS. This prevents the worker from flooding the main thread's event loop with high-frequency image updates, which was a major source of UI stuttering/freezing.
- **Optimized Discovery:** Modified the camera discovery logic to prioritize index 0 (default camera) and reduce the scanning range, making the camera startup faster.

### 2. Customer List  Pagination (`src/ui/views/customer_view.py`)
- **Implemented Pagination:** Added "Previous" and "Next" buttons to the customer list.
- **Optimized Query:** Updated the database query to use `LIMIT 50 OFFSET X`, fetching only the necessary records for the current page. This dramatically reduces the initial load time and memory usage.
- **UI Update:** Added page status label (e.g., "Page 1 of 5") and navigation controls.

### 3. Pharmacy Customer List Pagination (`src/ui/views/pharmacy/pharmacy_customer_view.py`)
- **Implemented Pagination:** Similar to the standard customer view, added pagination controls to the pharmacy customer list.
- **Optimized Query:** Updated the `load_customers` function to use `LIMIT 50 OFFSET X`.
- **Fixed Indentation:** Corrected a syntax error in the signal definition.

## Verification
- Verified syntax of modified files (`verify_fixes_syntax.py` passed).
- Confirmed that imports and logic are consistent with the codebase structure.

## Next Steps
- The user can now restart the application and verify that the customer windows load instantly and navigation is smooth.
- Test the camera feature to ensure the preview is fluid but not freezing the UI.
