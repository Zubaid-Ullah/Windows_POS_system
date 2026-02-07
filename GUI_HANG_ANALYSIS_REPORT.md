# GUI Hang Analysis Report — FaqiriTech POS

**Scope:** Deep scan from `main.py` to identify causes of GUI freezes (after a few seconds or a few minutes).  
**Date:** 2026-02-07

---

## Executive Summary

The freezes are consistently explained by **work running on the main (UI) thread** that should be on background workers. The most impactful sources are:

1. **Synchronous network calls on the UI thread** (Supabase checks/verification).
2. **Synchronous DB access on the UI thread** (startup checks, login/contract flows, settings save, view loads).
3. **Blocking camera capture loops** (OpenCV while-loops run on the UI thread).
4. **Large UI table population on the UI thread** (thousands of rows + widgets per row).
5. A **pharmacy DB init bug** (cursor used after connection closes) that can cause locks/errors.
6. **Printing + QR generation on the UI thread** (printer I/O can block for seconds or more).

The app already includes a **GUI Watchdog** (`src/core/app_watchdog.py`) that reports main-thread stalls. The items below explain why those stalls occur.

---

## 1. Blocking network calls on the UI thread (high impact)

### 1.1 LoginView (contract check + contract update)

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/login_view.py` | `check_contract()` | Calls `supabase_manager.check_connection()` and `supabase_manager.get_installation_status()` directly on the UI thread. Both use `requests.get(..., timeout=3..10)` and can freeze the GUI while waiting. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/login_view.py` | `show_contract_update()` | Uses `supabase_manager.check_connection()` and `supabase_manager.verify_installer()` directly on the UI thread. |

### 1.2 Super admin + credentials screens

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/super_admin_view.py` | `update_validity()`, `toggle_system_status()` | Calls `supabase_manager.verify_secret_key()` on the UI thread. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/credentials_view.py` | `abort_shutdown()`, `remote_shutdown()`, `extend_contract()`, `toggle_status()` | Calls `supabase_manager.verify_secret_key()` on the UI thread before launching workers. |

**Impact:** Any slow network, DNS issue, or transient TLS stall freezes the UI for several seconds, which matches the “hang after a few seconds” symptom.

---

## 2. Blocking database access on the UI thread (high impact)

### 2.1 Startup checks in main.py

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/main.py` | `check_contract_validity()` | Uses `db_manager.get_connection()` on the main thread. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/main.py` | `verify_local_data_integrity()` | Uses `db_manager.get_connection()` on the main thread. |

### 2.2 Theme and settings

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/theme_manager.py` | `init_theme()` | Reads DB on the main thread during app startup. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/theme_manager.py` | `set_theme_mode()` | Writes DB on the main thread when toggling theme. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/settings_view.py` | `save_settings()` | Writes DB on the UI thread; a timer calls this every 30s (`sync_timer`). |

### 2.3 View constructors and handlers

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/finance_view.py` | `__init__()` | Calls `load_data()` and `load_payroll_data()` on the UI thread. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/reports_view.py` | `update_search_suggestions()` | Runs a DB query on every `textChanged` (main thread). |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/inventory_view.py` | `load_categories()`, `load_suppliers()` | DB work in constructors and dialog flows on UI thread. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/super_admin_view.py` | `load_system_settings()` | DB access on main thread. |

**Impact:** Any long query or DB lock (WAL contention, slow disk, etc.) will stall the UI. The `db_manager` warns about this exact pattern in `_check_thread_safety()`.

---

## 3. OpenCV camera capture loops block the UI (high impact)

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/utils/camera.py` | `capture_image()` | `while True` + `cv2.waitKey(1)` runs on the caller thread. If called from UI, Qt event loop freezes until user exits. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/pharmacy/pharmacy_customer_view.py` | `capture_photo_from_camera()` | Same: blocking OpenCV loop on the UI thread. |

**Impact:** When camera is open, the GUI appears frozen. This is a definite hang source when camera features are used.

---

## 4. Large UI table population on the UI thread (medium to high impact)

Even when DB fetch is done in a worker, the UI **populates tables on the main thread** and creates per-row widgets. With thousands of rows, this can cause multi‑second stalls.

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/inventory_view.py` | `load_products()` → `on_loaded()` | Inserts rows + creates buttons for each row on the UI thread. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/customer_view.py` | `load_customers()` → `on_loaded()` | Same: heavy UI work on the main thread. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/reports_view.py` | Table refresh handlers | Large table rebuilds are done on main thread. |

**Impact:** UI appears frozen during table rebuilds. This explains “hang after a few minutes” if the dataset grows large.

---

## 5. Pharmacy DB init bug (high risk for locks/errors)

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/database/db_manager.py` | `_create_pharmacy_tables()` | The `with self.get_pharmacy_connection() as conn:` block ends **before** the `cursor.execute(...)` calls. The cursor is used after the connection is closed, which can cause DB errors or lock contention. |

**Impact:** DB initialization or first pharmacy use can fail or hang unexpectedly.

---

## 6. Printing and QR generation on the UI thread (medium to high impact)

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/utils/thermal_bill_printer.py` | `generate_sales_bill()` + `_send_to_printer()` | DB queries + QR generation + printer I/O on the UI thread. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/sales_view.py` | `print_sale_bill()` | Calls thermal printer functions on UI thread. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/ui/views/pharmacy/pharmacy_sales_view.py` | receipt/print flows | Same pattern. |

**Impact:** Printer delays can freeze the GUI for seconds or more.

---

## 7. Heavy startup work on the UI thread (startup stalls)

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/database/db_manager.py` | `DatabaseManager.__init__()` | Creates tables, enables WAL, and performs auto-backups on the main thread at import time. |
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/database/db_manager.py` | `db_manager = DatabaseManager()` | Executes the above at import time (startup). |

**Impact:** Cold start can appear frozen, especially on slow disks or large DB files.

---

## 8. Supporting evidence: main-thread DB warning

| File (full path) | Location | Issue |
|---|---|---|
| `/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system/src/database/db_manager.py` | `_check_thread_safety()` | Logs a warning whenever DB is accessed on the main thread. This warning will appear frequently based on the above patterns. |

---

## Priority fix list (pragmatic)

1. **Move all Supabase calls off the UI thread** (wrap `check_connection()`, `verify_*`, `get_installation_status()` in `task_manager` or QThread).
2. **Fix `_create_pharmacy_tables()`** to keep all `cursor.execute()` inside the `with` block.
3. **Move camera capture to a worker thread or separate process** (or use a Qt video widget).
4. **Batch UI table updates** (e.g., model/view with `QAbstractTableModel`, or chunked insert with `QTimer`).
5. **Move printing/QR generation to a worker**.
6. **Audit remaining DB calls on UI thread** and migrate to background tasks.

---

If you want, I can patch the highest-risk paths first (Supabase calls + pharmacy DB init bug) and provide targeted fixes.
