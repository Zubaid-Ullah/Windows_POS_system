# Superadmin Offline Fallback - Implementation Plan

## Overview
Add an offline fallback mechanism for superadmin authentication, allowing login even when internet is unavailable.

## Current Behavior
- Superadmin login REQUIRES internet connection
- Authenticates against Supabase `authorized_persons` table
- Shows error if offline: "Internet connection required for Super Admin login"

## Proposed Solution
Add a fallback to check local database when cloud authentication fails or is unavailable.

## Implementation

### 1. Add Offline Superadmin Password to Local DB

**File**: `src/database/db_manager.py`

Add a new setting to store the offline superadmin password hash:

```python
# In ensure_schema() method, add to app_settings:
cursor.execute("""
    INSERT OR IGNORE INTO app_settings (key, value) 
    VALUES ('superadmin_offline_key', ?)
""", (Auth.hash_password('your_offline_password_here'),))
```

### 2. Modify Login View to Support Offline Fallback

**File**: `src/ui/views/login_view.py`

Update the `verify_super_admin` method (lines 288-318):

```python
def verify_super_admin(self, username, password, mode):
    # Try online verification first
    if supabase_manager.check_connection():
        QMessageBox.information(self, "Verifying", 
                              "Verifying Super Admin credentials online...")
        
        if supabase_manager.verify_installer(username, password):
            # Online success - proceed
            self._grant_superadmin_access(username, mode)
            return
        else:
            # Online verification failed
            reply = QMessageBox.question(
                self, 
                "Cloud Verification Failed",
                "Cloud verification failed. Try offline fallback?\\n\\n"
                "Note: Offline mode has limited verification.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                QMessageBox.warning(self, "Login Failed", 
                                  "Invalid Super Admin credentials.")
                return
            # Fall through to offline check
    
    # Offline verification
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM app_settings WHERE key = 'superadmin_offline_key'"
            )
            row = cursor.fetchone()
            
            if row and Auth.verify_password(password, row['value']):
                QMessageBox.information(
                    self, 
                    "Offline Mode",
                    "Authenticated via offline fallback.\\n"
                    "Some features may be limited."
                )
                self._grant_superadmin_access(username, mode)
            else:
                QMessageBox.warning(
                    self, 
                    "Login Failed", 
                    "Invalid Super Admin credentials (offline)."
                )
    except Exception as e:
        print(f"Offline verification error: {e}")
        QMessageBox.critical(
            self, 
            "Error", 
            f"Authentication failed: {e}"
        )

def _grant_superadmin_access(self, username, mode):
    """Helper to grant superadmin access after verification"""
    mock_user = {
        'username': username,
        'role_name': 'SuperAdmin',
        'id': 9999,
        'full_name': 'System Super Admin',
        'permissions': '*',
        'is_super_admin': True
    }
    
    if mode == "PHARMACY":
        PharmacyAuth.set_current_user(mock_user)
    else:
        Auth.set_current_user(mock_user)
    
    self.login_success.emit(mode, "superadmin")
```

### 3. Add Offline Password Management

**File**: `src/ui/views/user_management_view.py` or create new dialog

Add UI to set/change the offline superadmin password:

```python
def update_offline_superadmin_password(self):
    """Allow changing the offline superadmin password"""
    from PyQt6.QtWidgets import QInputDialog, QLineEdit
    
    # Verify current password first
    current, ok = QInputDialog.getText(
        self, 
        "Verify Identity",
        "Enter current superadmin password:",
        QLineEdit.EchoMode.Password
    )
    
    if not ok or not current:
        return
    
    # Verify against cloud OR offline
    verified = False
    if supabase_manager.check_connection():
        verified = supabase_manager.verify_installer("superadmin", current)
    
    if not verified:
        # Try offline
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM app_settings WHERE key = 'superadmin_offline_key'"
            )
            row = cursor.fetchone()
            if row and Auth.verify_password(current, row['value']):
                verified = True
    
    if not verified:
        QMessageBox.warning(self, "Error", "Current password incorrect")
        return
    
    # Get new password
    new_pass, ok = QInputDialog.getText(
        self,
        "Set Offline Password",
        "Enter new offline superadmin password:",
        QLineEdit.EchoMode.Password
    )
    
    if ok and new_pass:
        hashed = Auth.hash_password(new_pass)
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE app_settings SET value = ? WHERE key = 'superadmin_offline_key'",
                (hashed,)
            )
            conn.commit()
        
        QMessageBox.information(
            self,
            "Success",
            "Offline superadmin password updated successfully!"
        )
```

### 4. Security Considerations

**Pros:**
- Allows superadmin access even when offline
- Uses bcrypt hashing (same as regular users)
- Requires verification before changing

**Cons:**
- Two passwords to manage (cloud + offline)
- Offline password is less secure than cloud verification
- Could be compromised if database is accessed

**Recommendation:**
- Keep cloud verification as primary method
- Use offline only as emergency fallback
- Require strong password for offline mode
- Log all offline superadmin logins

## Alternative: Sync Cloud Password to Local

Instead of separate passwords, sync the cloud password to local DB:

```python
def sync_superadmin_password_to_local(password):
    """Store cloud superadmin password locally (encrypted)"""
    hashed = Auth.hash_password(password)
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            ('superadmin_offline_key', hashed)
        )
        conn.commit()
```

Call this after successful cloud authentication to cache the password locally.

## Files to Modify

1. `src/ui/views/login_view.py` - Add offline fallback logic
2. `src/database/db_manager.py` - Add offline password setting
3. `src/ui/views/user_management_view.py` - Add password management UI (optional)

## Testing Plan

1. Test online authentication (should work as before)
2. Test offline authentication with correct password
3. Test offline authentication with wrong password
4. Test transition from online to offline
5. Test password change functionality

Would you like me to implement this offline fallback solution?
