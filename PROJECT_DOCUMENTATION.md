# POS System Project Documentation

This document provides a detailed overview of the Offline POS & Inventory Management System. It explains the project structure, core components, and the functionality of each module.

## 1. Project Overview

**Application Name:** Offline POS & Inventory Management  
**Platform:** Desktop (Cross-platform: Windows, macOS, Linux)  
**Frameworks:** 
- **Language:** Python 3.9+
- **GUI:** PyQt6
- **Database:** SQLite3
- **Icons:** QtAwesome

**Key Features:**
- Role-Based Access Control (Super Admin, Admin, Manager, Salesman).
- Complete Point of Sale (POS) interface.
- Inventory Management with Barcode and SKU support.
- Financial Management (Expenses, Payroll, Reporting).
- Dual-Mode System (Shop & Pharmacy Modules).
- Secure Login & Contract/License Management.
- Multi-language Support (English, Pashto, Dari).
- Dynamic Theming (Light/Dark Mode).

---

## 2. Directory Structure

```
POS_system/
├── main.py                     # Application Entry Point
├── data/                       # Data storage
│   ├── pos_system.db           # Main SQLite Database
│   ├── backups/                # Automated backups
│   └── kyc/                    # Customer KYC images
├── src/
│   ├── core/                   # Core business logic
│   │   ├── auth.py             # User authentication & permission logic
│   │   └── localization.py     # Language translation manager
│   ├── database/               # Database handling
│   │   └── db_manager.py       # Singleton Database Manager (CRUD operations)
│   ├── ui/                     # User Interface
│   │   ├── main_window.py      # Main application container & Navigation
│   │   ├── theme_manager.py    # Theme handling (Colors, Styles)
│   │   ├── components/         # Reusable UI widgets (cards, charts)
│   │   ├── dialogs/            # Pop-up dialogs (Create User, Checkout, etc.)
│   │   └── views/              # Main functional screens
│   │       ├── sales_view.py
│   │       ├── inventory_view.py
│   │       ├── finance_view.py
│   │       ├── user_management_view.py
│   │       ├── super_admin_view.py
│   │       ├── pharmacy/       # Dedicated Pharmacy Module
│   │       └── ... (others)
│   └── utils/                  # Helper utilities (Camera, Printer, Logger)
```

---

## 3. Core Components

### 3.1. Database Manager (`src/database/db_manager.py`)
The backbone of the application. It handles all SQLite interactions.
- **Initialization:** Automatically creates tables if they don't exist (`users`, `products`, `sales`, `expenses`, etc.).
- **Migrations:** Handles schema updates (e.g., adding `base_salary` to `users`).
- **Connection:** Uses `sqlite3` with `Row` factory for dict-like access.
- **Auto-Backup:** Creates a comprehensive backup on every startup in `data/backups/auto`.

### 3.2. Authentication (`src/core/auth.py`)
Manages user sessions and security.
- **Login:** Verifies username/password hash (PBKDF2/SHA256).
- **Session:** Stores the currently logged-in user in memory.
- **Permissions:** simple RBAC system augmented by granular permissions strings (e.g., "sales,finance" or "*").

### 3.3. Localization (`src/core/localization.py`)
Handles multi-language support (English, Dari, Pashto).
- Use `lang_manager.get('key')` to fetch translated strings.
- Supports RTL (Right-to-Left) layout switching.

### 3.4. Theme Manager (`src/ui/theme_manager.py`)
Centralized styling.
- Defines color palettes for Light and Dark modes.
- Emits signals when the theme changes so UI components can repaint themselves.

---

## 4. User Interface & Modules

### 4.1. Entry Point (`main.py`)
- Initializes `QApplication`.
- Sets up the global theme.
- Launches `MainWindow`.

### 4.2. Main Window (`src/ui/main_window.py`)
- **Container:** Uses `QStackedWidget` to switch between views (Login, Sales, Dashboard, etc.).
- **Sidebar:** Dynamic navigation menu based on user permissions.
- **Header:** Displays current view title, date, and search bar.
- **State Management:** Handles Logout and View Switching.

### 4.3. Login View (`src/ui/views/login_view.py`)
- **Security:** Password toggling (Show/Hide).
- **Language Switcher:** Toggle UI language before login.
- **Contract Check:** Validates if the system license is active.
- **Emergency Update:** Hidden button to update license/contract using a security key (for Super Admin support).

### 4.4. Finance View (`src/ui/views/finance_view.py`)
A comprehensive finance module.
- **Tabs:**
    1.  **Overview:** Graphical dashboard showing Total Income, Expenses, and Net Profit. Add miscellaneous expenses (Petty Cash, etc.).
    2.  **Payroll Management:** Table of staff with editable **Base Salary**.
        - **Run Payroll:** Calculate "Day-Wise" salary. Input `Days Worked` vs `Total Days` to auto-calculate net pay and record it as an expense.

### 4.5. User Management View (`src/ui/views/user_management_view.py`)
Dedicated user administration for Admins.
- **List:** Shows Users, Roles, Salaries, and Status.
- **CRUD:** Create, Edit, Deactivate Users.
- **Reset Password:** Admin can force-reset user passwords.
- **Permissions:** Assign specific module access (Sales, Finance, etc.) via the creation dialog.

### 4.6. Super Admin View (`src/ui/views/super_admin_view.py`)
Restricted to the `is_super_admin` flag.
- **User Management:** Embeds `UserManagementView` but gives Super Admin extra powers (e.g., setting Contract End Date for staff).
- **System Governance:**
    - **License Management:** Extend system validity date.
    - **Database Mode:** Toggle between Online (Cloud Sync) and Offline modes.
    - **System Kill Switch:** Remote/Local deactivation of the software.

### 4.7. Sales View (`src/ui/views/sales_view.py`)
The primary POS interface.
- **Cart:** Add items via Barcode scanner or Search.
- **Calculations:** Real-time total, tax, and discount.
- **Checkout:** Process payment (Cash, Card) and generate receipt.
- **Hold/Retrieve:** Park transactions.

### 4.8. Inventory View (`src/ui/views/inventory_view.py`)
- **Product List:** Filterable, sortable list of all items.
- **Stock Management:** Edit quantity, low stock alerts.
- **Add Product:** Form to add new items with Barcode, Cost/Sale Price, Category, etc.

### 4.9. Pharmacy Module (`src/ui/views/pharmacy/`)
A completely separate flow for Pharmacy operations.
- **Pharmacy Hub:** Central navigation for pharmacy.
- **Pharmacy Sales:** Specialized point of sale for drugs (expiry handling).
- **Pharmacy Inventory:** Batch number and Expiry date tracking for medicines.

### 4.10. Reports View (`src/ui/views/reports_view.py`)
Visual analytics.
- **Charts:** Sales trends (Bar/Pie charts) using `matplotlib` backend.
- **Tables:** Detailed transaction logs, top-selling items.
- **Export:** Export data to CSV/Excel.

### 4.11. Other Views
- **Customers (`customer_view.py`):** CRM, maintain customer debts/loans.
- **Suppliers (`supplier_view.py`):** Supplier database and contact info.
- **Loans (`loan_view.py`):** Track customer credit limits and repayments.
- **Settings (`settings_view.py`):** Application configuration (Printer selection, Backup settings).
- **Returns (`returns_view.py`):** Process product returns and refunds.
- **Price Check (`price_check_view.py`):** Simple kiosk mode for checking item prices.

---

## 5. Technical Workflows

### Payroll Calculation Logic
Located in `FinanceView`.
Formula: `Net Pay = (Base Salary / Total Days in Month) * Days Worked`
This allows precise salary distribution ensuring fairness for partial attendance.

### Database Schema
Key tables:
- `users`: Stores login, role, permissions, base_salary, and contract info (`valid_until`).
- `products`: Inventory items.
- `sales` / `sale_items`: Transaction headers and details.
- `expenses`: Records of all spending (Salary, Rent, Utilities).
- `customers` / `loans`: CRM and credit tracking.

### startup Sequence
1. `main.py` -> Init `QApplication`.
2. `db_manager` -> Run Migrations & Auto-Backup.
3. `MainWindow` -> Show `LoginView`.
4. User Logs in -> `Auth.login()` verifies credentials.
5. `MainWindow` -> Loads Sidebar menu based on `Auth.get_user_permissions()`.
6. User enters Dashboard.
