# Super Admin Information

## 🔑 Super Admin Credentials

### General Store (Main System)
- **Username**: `superadmin`
- **Password**: `secure_Sys_2026!`

### Pharmacy Module
- **Username**: `psuper`
- **Password**: `secure_Sys_2026!`

---

## 📝 Important Notes

### Password Security
- Passwords in the database are **hashed** using bcrypt for security
- **You cannot see the original passwords** from the database directly
- The hashed values you see (starting with `$2b$12$...`) are one-way encrypted

### Password Visibility Feature ✨ NEW
As of this update, both systems now have a **Password Visibility Toggle**:

#### For General Store:
1. Login as `superadmin`
2. Go to **Super Admin** → **User Management**
3. Click the **"👁️ Show Passwords"** button
4. Passwords will be displayed **ONLY** for users that were created/edited during this session
5. Click **"🙈 Hide Passwords"** to mask them again

#### For Pharmacy:
1. Login to Pharmacy as `psuper`
2. Go to **Ph-Users** (User Management)
3. Click the **"👁️ Show Passwords"** button  
4. Passwords will be displayed **ONLY** for users that were created/edited during this session
5. Click **"🙈 Hide Passwords"** to mask them again

### How It Works
- When you create a new user or update an existing user's password, the system stores the **plaintext password** in memory
- This allows the super admin to view passwords for recently created/modified users
- Old users (created before this feature) will show as masked `••••••••` since their plaintext passwords are not stored
- This is a **session-based** feature - closing and reopening will clear the stored passwords

---

## 🆕 Recent Updates Summary

### 1. Password Visibility Feature
- ✅ Added password toggle in **General Store User Management**
- ✅ Added password toggle in **Pharmacy User Management**
- ✅ Passwords display in **blue** when visible, **gray** when hidden
- ✅ Only shows plaintext for users created/updated in current session

### 2. General Store Finance View
- ✅ Made the entire Finance window **scrollable**
- ✅ Wrapped tabs in a scroll area for better usability

### 3. General Store Inventory View
- ✅ Added **"Tools"** button with comprehensive inventory options:
  - 📤 **Export to CSV** - Export inventory data
  - 🏷️ **Print Labels** - Barcode label generation guidance
  - 📊 **Stock Adjustments** - View low stock items
  
### 4. Inventory Management Tools
New features accessible via the **Tools** button:
- **Export Inventory**: Creates a CSV file with all product data
- **Low Stock Alert**: Shows items at or below minimum stock levels
- **Barcode Labels**: Provides guidance for printing labels

---

## 🔐 Security Best Practices

1. **Change default passwords** immediately after first login
2. **Never share** super admin credentials  
3. Super admin accounts have **full system access** - use responsibly
4. The password visibility feature is for **administrative purposes only**
5. Passwords are still **encrypted in the database** - this feature only shows them in the UI

---

## 📞 Support

If you need to reset the superadmin password:
1. Access the database directly using SQLite
2. Run the database initialization script to recreate default users
3. Or contact your system administrator

**Database Locations:**
- General Store: `afex_store.db`
- Pharmacy: `afex_pharmacy.db`

---

**Last Updated**: 2026-01-21
**System Version**: 2.0
