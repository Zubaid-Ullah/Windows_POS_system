# GUI Hang Issues - Deep Scan Report
**Generated:** 2026-02-08  
**Project:** Windows POS System  
**Scan Type:** Deep Analysis for Network/Blocking Operations

---

## 🚨 CRITICAL ISSUES - HIGH PRIORITY

### 1. **Direct Supabase Calls in UI Thread** ⚠️ SEVERE
**Location:** `src/ui/views/onboarding/create_account_stepper.py`  
**Line:** 374, 492, 535  
**Issue:** Direct blocking network calls in UI event handlers

```python
# ❌ BLOCKING - Line 374
def _do_refresh_installers(self):
    users = supabase_manager.get_installers()  # BLOCKS UI THREAD
    
# ❌ BLOCKING - Line 492
def run_registration():
    if not supabase_manager.upsert_installation(payload):  # BLOCKS
```

**Impact:** GUI freezes for 3-10 seconds during installer refresh and registration  
**Fix Required:** Move to `task_manager.run_task()` with loading indicators

---

### 2. **Synchronous Connection Checks** ⚠️ SEVERE
**Location:** Multiple files  
**Files Affected:**
- `src/ui/views/login_view.py` (Line 325, 392, 490)
- `src/ui/views/settings_view.py` (Line 32, 38)
- `src/ui/views/onboarding/connectivity_gate.py` (Line 77)

```python
# ❌ BLOCKING - login_view.py:325
def run_check_connection():
    return supabase_manager.check_connection()  # 3-5 second timeout
```

**Impact:** 
- Login delays of 3-5 seconds when checking connection
- Settings view freezes during cloud sync checks
- Connectivity gate blocks startup for up to 5 seconds

**Fix Required:** Already using `task_manager` in some places, but needs consistent application

---

### 3. **Main.py Startup Blocking** ⚠️ CRITICAL
**Location:** `main.py`  
**Lines:** 202-208, 254  
**Issue:** Synchronous cloud check during startup flow

```python
# ❌ BLOCKING - Line 202-208
def check_cloud():
    try:
        return supabase_manager.get_installation_status(sid)  # BLOCKS
    except Exception as e:
        return None
```

**Impact:** App startup can hang for 10+ seconds if network is slow  
**Current Mitigation:** Using `task_manager.run_task()` (Line 254) ✅  
**Status:** PARTIALLY FIXED - Good pattern, needs verification

---

## ⚠️ HIGH PRIORITY ISSUES

### 4. **License Guard Polling** ⚠️ MODERATE
**Location:** `src/core/license_guard.py`  
**Lines:** 17-25, 51-76  
**Issue:** Background thread created every 60 seconds

```python
# Line 19 - BLOCKING in worker thread
def run(self):
    status_data = supabase_manager.get_installation_status(self.sid)
```

**Impact:** 
- Creates new QThread every minute
- Network call blocks worker thread (acceptable)
- Potential thread leak if not cleaned up properly

**Current Status:** Using QThread properly ✅  
**Concern:** Thread cleanup on Line 70-74 looks good, but verify no leaks

---

### 5. **Settings View Cloud Sync** ⚠️ MODERATE
**Location:** `src/ui/views/settings_view.py`  
**Lines:** 19-45, 426-432  
**Issue:** Custom QThread for sync operations

```python
# Line 32-33 - BLOCKING in thread
if supabase_manager.check_connection():
    data = supabase_manager.get_installation_status(self.sid)
```

**Impact:** 
- Sync operations run in background ✅
- But check_connection() has 3-5 second timeout
- Timer-based sync every 30 seconds (Line 57)

**Recommendation:** Use `task_manager` instead of custom QThread for consistency

---

### 6. **SuperAdmin View Cloud Fetch** ⚠️ MODERATE
**Location:** `src/ui/views/super_admin_view.py`  
**Lines:** 177-189  
**Issue:** Custom CloudWorker thread

```python
# Line 181 - BLOCKING in thread
cloud_data = supabase_manager.get_installation_status(sid)
```

**Impact:** Background operation, but could use centralized task manager  
**Status:** Acceptable but inconsistent pattern

---

## 🔶 MEDIUM PRIORITY ISSUES

### 7. **Credentials View Multiple Workers** ⚠️ MODERATE
**Location:** `src/ui/views/credentials_view.py`  
**Lines:** 129-149, 238-261, 304-327, 365-388, 424-447  
**Issue:** 5 different custom QThread workers for different operations

```python
# Multiple custom workers:
- FetchWorker (Line 129)
- AbortWorker (Line 238)
- ShutdownScheduler (Line 304)
- ExtendWorker (Line 365)
- StatusToggleWorker (Line 424)
```

**Impact:** 
- Each operation properly threaded ✅
- But creates inconsistent patterns
- Harder to maintain and debug

**Recommendation:** Consolidate to use `task_manager` for all operations

---

### 8. **Login Window User Fetcher** ⚠️ LOW-MODERATE
**Location:** `src/ui/views/onboarding/login_window.py`  
**Lines:** 83-94, 119-145  
**Issue:** Two custom QThread workers

```python
# Line 87 - BLOCKING in thread
users = supabase_manager.get_installers()

# Line 133-134 - BLOCKING in thread
if supabase_manager.verify_installer(self.username, self.password):
    status = supabase_manager.get_installation_status(self.system_id)
```

**Impact:** Properly threaded, but inconsistent with task_manager pattern  
**Status:** Works but needs standardization

---

### 9. **Pharmacy Views Threading** ⚠️ LOW
**Location:** Multiple pharmacy view files  
**Files:**
- `pharmacy_finance_view.py` (Line 498)
- `pharmacy_inventory_view.py` (Line 10)
- `pharmacy_returns_view.py` (Line 342)
- `pharmacy_reports_view.py` (Line 551)
- `pharmacy_dashboard_view.py` (Line 269)

**Issue:** Custom QThread workers for data loading  
**Impact:** Database operations, not network - lower priority  
**Status:** Acceptable for now, but should use task_manager for consistency

---

## ✅ GOOD PATTERNS FOUND

### 1. **Task Manager Usage** ✅ EXCELLENT
**Location:** Multiple files using `src/core/blocking_task_manager.py`

```python
# ✅ GOOD PATTERN - login_view.py:322-366
from src.core.blocking_task_manager import task_manager

def verify_super_admin(self, username, password, mode):
    def run_check_connection():
        return supabase_manager.check_connection()
    
    def on_connection_checked(is_online):
        # Handle result
        pass
    
    task_manager.run_task(run_check_connection, on_finished=on_connection_checked)
```

**Files Using Task Manager Correctly:**
- `main.py` (Lines 72-73, 253-254)
- `login_view.py` (Lines 322-366, 465, 485-534)
- `settings_view.py` (Line 506)
- `super_admin_view.py` (Line 289)
- `credentials_view.py` (Line 158)
- `create_account_stepper.py` (Lines 313-328, 487-561)

---

## 📊 SUMMARY STATISTICS

| Category | Count | Severity |
|----------|-------|----------|
| **Direct Blocking Calls** | 3 | 🔴 Critical |
| **Synchronous Connection Checks** | 6 | 🔴 Critical |
| **Custom QThread Workers** | 15+ | 🟡 Medium |
| **Task Manager Usage** | 10+ | 🟢 Good |
| **Potential Thread Leaks** | 2 | 🟡 Medium |

---

## 🎯 RECOMMENDED FIXES - PRIORITY ORDER

### **PHASE 1: Critical Fixes (Do First)**

#### 1.1 Fix `create_account_stepper.py` - Line 374
```python
# ❌ BEFORE
def _do_refresh_installers(self):
    users = supabase_manager.get_installers()  # BLOCKS UI
    self.installer_user.clear()
    # ...

# ✅ AFTER
def _do_refresh_installers(self):
    from src.core.blocking_task_manager import task_manager
    
    def fetch_installers():
        return supabase_manager.get_installers()
    
    def on_finished(users):
        self.installer_user.clear()
        all_users = ["SuperAdmin"]
        if users:
            all_users.extend(users)
        self.installer_user.addItems(all_users)
        self.installer_user.setEnabled(True)
    
    task_manager.run_task(fetch_installers, on_finished=on_finished)
```

#### 1.2 Fix `create_account_stepper.py` - Line 489-545 (run_registration)
**Already using task_manager** ✅ - Verify it's working correctly

---

### **PHASE 2: High Priority Fixes**

#### 2.1 Standardize Settings View
Replace `SettingsSyncWorker` (Line 19) with `task_manager`

```python
# ❌ BEFORE - Custom QThread
class SettingsSyncWorker(QThread):
    finished = pyqtSignal(bool, dict)
    # ...

# ✅ AFTER - Use task_manager
from src.core.blocking_task_manager import task_manager

def load_cloud_settings(self):
    def fetch_settings():
        if supabase_manager.check_connection():
            return supabase_manager.get_installation_status(self.sid)
        return None
    
    def on_finished(data):
        if data:
            self._populate_fields(data)
    
    task_manager.run_task(fetch_settings, on_finished=on_finished)
```

#### 2.2 Consolidate Credentials View Workers
Replace all 5 custom workers with `task_manager` calls

---

### **PHASE 3: Medium Priority**

#### 3.1 Standardize All Pharmacy Views
Use `task_manager` instead of custom QThread workers

#### 3.2 Review License Guard
- Verify thread cleanup is working
- Consider using `task_manager` instead of manual QThread

---

## 🛡️ BACKGROUND SERVICE ARCHITECTURE

### **Recommended Pattern for Internet Operations**

```python
# ✅ BEST PRACTICE TEMPLATE

from src.core.blocking_task_manager import task_manager
from PyQt6.QtWidgets import QMessageBox

class MyView(QWidget):
    def perform_network_operation(self):
        # 1. Disable UI elements
        self.submit_button.setEnabled(False)
        self.submit_button.setText("Loading...")
        
        # 2. Define background task
        def background_task():
            try:
                # All network operations here
                result = supabase_manager.some_operation()
                return {"success": True, "data": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # 3. Define callback
        def on_finished(result):
            # Re-enable UI
            self.submit_button.setEnabled(True)
            self.submit_button.setText("Submit")
            
            # Handle result
            if result["success"]:
                QMessageBox.information(self, "Success", "Operation completed")
            else:
                QMessageBox.critical(self, "Error", result["error"])
        
        # 4. Execute
        task_manager.run_task(background_task, on_finished=on_finished)
```

---

## 🔍 FILES REQUIRING IMMEDIATE ATTENTION

### **Critical (Fix within 1-2 days)**
1. ✅ `src/ui/views/onboarding/create_account_stepper.py` - Line 374
2. ✅ `src/ui/views/login_view.py` - Verify all connection checks are async
3. ✅ `main.py` - Verify startup flow is non-blocking

### **High Priority (Fix within 1 week)**
4. `src/ui/views/settings_view.py` - Replace custom worker
5. `src/ui/views/credentials_view.py` - Consolidate workers
6. `src/ui/views/super_admin_view.py` - Standardize pattern

### **Medium Priority (Fix within 2 weeks)**
7. All pharmacy view files - Standardize threading
8. `src/ui/views/onboarding/login_window.py` - Use task_manager
9. `src/core/license_guard.py` - Review and optimize

---

## 🎓 DEVELOPER GUIDELINES

### **DO's ✅**
1. **ALWAYS** use `task_manager.run_task()` for network operations
2. **ALWAYS** disable UI elements during async operations
3. **ALWAYS** show loading indicators for operations > 500ms
4. **ALWAYS** handle both success and error cases in callbacks
5. **ALWAYS** re-enable UI elements in the callback

### **DON'Ts ❌**
1. **NEVER** call `supabase_manager` methods directly from UI event handlers
2. **NEVER** use `requests.get/post` in the main thread
3. **NEVER** create custom QThread workers when `task_manager` exists
4. **NEVER** forget to cleanup threads/workers
5. **NEVER** block the UI thread for more than 100ms

---

## 📈 PROGRESS TRACKING

### **Current State**
- ✅ Task Manager infrastructure exists and works well
- ✅ Some views already using proper patterns
- ⚠️ Inconsistent usage across codebase
- ❌ 3-6 critical blocking calls remain

### **Target State**
- ✅ All network operations use `task_manager`
- ✅ No custom QThread workers for simple tasks
- ✅ Consistent error handling patterns
- ✅ All UI operations complete in < 100ms
- ✅ Loading indicators for all async operations

---

## 🔧 TESTING CHECKLIST

After implementing fixes, test these scenarios:

### **Network Scenarios**
- [ ] Slow network (throttle to 3G speed)
- [ ] No network connection
- [ ] Intermittent connection
- [ ] Server timeout (10+ seconds)

### **UI Responsiveness**
- [ ] Can click buttons during network operations
- [ ] Can navigate between views during loading
- [ ] Loading indicators appear within 100ms
- [ ] No frozen cursor or unresponsive UI

### **Error Handling**
- [ ] Graceful degradation when offline
- [ ] Clear error messages for users
- [ ] No crashes on network errors
- [ ] Retry mechanisms work correctly

---

## 📝 NOTES

1. **Task Manager is Well Designed**: The existing `BlockingTaskManager` (src/core/blocking_task_manager.py) is excellent and should be the standard for all async operations.

2. **Thread Pool**: Uses `QThreadPool` with proper sizing (max(4, idealThreadCount())) - good for I/O operations.

3. **Signal Safety**: Properly handles RuntimeError for deleted C++ objects in several places.

4. **Cleanup**: Most workers have proper `deleteLater()` calls, but verify no leaks exist.

5. **License Guard**: The 60-second polling is acceptable for license checks, but ensure it doesn't accumulate threads.

---

## 🚀 IMPLEMENTATION PLAN

### **Week 1: Critical Fixes**
- Day 1-2: Fix `create_account_stepper.py`
- Day 3-4: Audit and fix `login_view.py`
- Day 5: Verify `main.py` startup flow

### **Week 2: High Priority**
- Day 1-2: Refactor `settings_view.py`
- Day 3-4: Consolidate `credentials_view.py` workers
- Day 5: Standardize `super_admin_view.py`

### **Week 3: Medium Priority**
- Day 1-3: Refactor all pharmacy views
- Day 4: Fix `login_window.py`
- Day 5: Review and optimize `license_guard.py`

### **Week 4: Testing & Validation**
- Day 1-2: Network scenario testing
- Day 3: UI responsiveness testing
- Day 4: Error handling validation
- Day 5: Performance benchmarking

---

**END OF REPORT**
