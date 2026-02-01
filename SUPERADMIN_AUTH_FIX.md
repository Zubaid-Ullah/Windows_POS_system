# Superadmin Authentication Issue - Fix Guide

## Problem
The superadmin password has been changed in the Supabase cloud `authorized_persons` table, but the app is not accepting it during login.

## Root Cause
The app authenticates superadmin by checking the `authorized_persons` table in Supabase:
- **Username**: Must be exactly "superadmin" (case-insensitive in app, but stored as-is in cloud)
- **Password**: Must match EXACTLY what's stored in the cloud table

## How Superadmin Authentication Works

### 1. Login Flow (`src/ui/views/login_view.py`)
```python
# Line 264-265 (Store Login) or 277-278 (Pharmacy Login)
if username.lower() == "superadmin":
    self.verify_super_admin(username, password, mode)
```

### 2. Verification (`src/ui/views/login_view.py`, line 299)
```python
if supabase_manager.verify_installer(username, password):
    # Login successful
```

### 3. Cloud Check (`src/core/supabase_manager.py`, lines 220-227)
```python
def verify_installer(self, username, password) -> bool:
    params = {
        "names": f"eq.{username.strip()}",
        "passwords": f"eq.{password.strip()}",
        "select": "id"
    }
    r = requests.get(self._url(self.USERS_TABLE), params=params, headers=self._headers())
    return r.status_code == 200 and len(r.json() or []) > 0
```

## Solutions

### Option 1: Update Cloud Password via Supabase Dashboard (RECOMMENDED)
1. Go to your Supabase Dashboard: https://app.supabase.com
2. Select your project: `gwmtlvquhlqtkyynuexf`
3. Navigate to: **Table Editor** → **authorized_persons**
4. Find the row where `names = "superadmin"`
5. Edit the `passwords` column to your desired password
6. Save changes
7. Try logging in with the new password

### Option 2: Use the Debug Script (When Internet is Available)
Run the diagnostic script I created:
```bash
cd /Users/apple/Documents/GitHub/POS_system
source .venv/bin/activate
python3 debug_superadmin_auth.py
```

Then:
1. Choose option **2** (Add/Update superadmin credentials)
2. Enter username: `superadmin`
3. Enter your new password
4. The script will update the cloud and test the credentials

### Option 3: Direct SQL Update in Supabase
1. Go to Supabase Dashboard → **SQL Editor**
2. Run this query to check current credentials:
```sql
SELECT names, passwords, role, created_at 
FROM authorized_persons 
WHERE names = 'superadmin';
```

3. Update the password:
```sql
UPDATE authorized_persons 
SET passwords = 'YOUR_NEW_PASSWORD_HERE'
WHERE names = 'superadmin';
```

4. If no superadmin exists, create one:
```sql
INSERT INTO authorized_persons (names, passwords, role)
VALUES ('superadmin', 'YOUR_PASSWORD_HERE', 'superadmin')
ON CONFLICT (names) DO UPDATE SET passwords = EXCLUDED.passwords;
```

### Option 4: Add Offline Fallback (Code Modification)
If you want to allow superadmin login even when offline, we can modify the code to check the local database as a fallback.

## Important Notes

### Password Requirements
- **No hashing**: Passwords are stored in plain text in the cloud (security consideration!)
- **Case sensitive**: Password must match exactly
- **No spaces**: Leading/trailing spaces are trimmed by `.strip()`

### Current Setup
- **Supabase URL**: `https://gwmtlvquhlqtkyynuexf.supabase.co`
- **Table**: `authorized_persons`
- **Username column**: `names`
- **Password column**: `passwords`
- **Service Key**: Stored in `/Users/apple/Documents/GitHub/POS_system/credentials/.env`

### Local Superadmin (Different from Cloud)
There's also a LOCAL superadmin in the SQLite database (`afex_store.db`):
- **Username**: `superadmin`
- **Password**: `secure_Sys_2026!` (hashed in DB)
- **Purpose**: For regular user login (NOT cloud authentication)

The cloud superadmin is ONLY used for:
1. Bypassing contract checks
2. Updating contract dates
3. Full system access

## Troubleshooting

### "Invalid Cloud Secret Key" Error
- The password in cloud doesn't match what you entered
- Check the exact password in Supabase Dashboard
- Ensure no extra spaces or special characters

### "Internet connection required" Error
- Superadmin login REQUIRES internet connection
- The app must verify against Supabase cloud
- Cannot login as superadmin offline

### Network Issues
- Check if you can access: https://gwmtlvquhlqtkyynuexf.supabase.co
- Verify your internet connection
- Check firewall settings

## Next Steps

**What would you like to do?**

1. **Tell me the password you want to use**, and I'll help you update it in the cloud
2. **Check what password is currently in the cloud** (requires running the debug script)
3. **Add offline fallback** so superadmin can login without internet
4. **Reset to default password** and tell you what it is

Let me know which option you prefer!
