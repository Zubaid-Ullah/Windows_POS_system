# System Update Implementation Plan

> ⚠ IMPORTANT  
> The existing UI layout, spacing, hover effects, card styles, and overall visual structure must NOT be disturbed.  
> All improvements should enhance functionality without redesigning the interface.

---

# 1️⃣ Repair Store Module Regressions

Restore missing functionalities and fix crashes introduced in previous updates.

---

## [Component: Store Finance]

**File:** `store_finance_view.py`

### Fixes:
- Ensure both functions exist:
  - `create_overview_tab()`
  - `create_expense_tab()`
- Update `init_ui()` to correctly call `create_expense_tab()` (do NOT rename or remove `create_overview_tab()`).
- Ensure Expense form includes:
  - Title
  - Amount
  - Date (QDateEdit)
  - Description
- Ensure salary calculations reflect correctly in Net Profit.
- Restructure Summary tab into:

### Summary Tab Layout

**Row 1 – Sales**
- Total Price Sale
- Total Return Price Sale
- Net Sale (Sale − Return)

**Row 2 – Cost**
- Total Cost Sale
- Total Return Cost Sale
- Net Cost (Cost − Return)

**Row 3 – Profit**
- Profit (Net Sale − Net Cost)
- Total Operational Expense
- Net Profit

---

## [Component: Store Reports]

**File:** `store_reports_view.py`

### Fixes:
- Implement `toggle_alert_mode()` method.
- Ensure `expiry_days_spin` works correctly.
- Verify imports: `QDateEdit`, `QSpinBox`, etc.
- Add Delete button in Reports table.

---

## [Component: Store Users]

**File:** `store_users_view.py`

### Fixes:
- Restore "Photo" column in user table.
- Enforce mandatory photo when creating user.
- Show 2x2 thumbnail in table.
- Implement hover popup preview:
  - Show larger image on hover.
  - Auto-close on mouse leave.

---

## [Component: Store Inventory]

**File:** `store_inventory_view.py`

### Fixes:
- Restore and ensure Actions column (Edit/Delete) is functional.
- Add Rack column.
- Implement pagination:
  - 50 rows per page.
  - Fetch only when page changes or search triggers.
- Avoid loading entire dataset at once.

---

## [Component: Store Customers]

**File:** `store_customer_view.py`

### Fixes:
- Enforce mandatory photo validation.
- Restore missing action buttons.
- Implement hover preview popup for photo.

---

## [Component: Store Suppliers]

**File:** `store_supplier_view.py`

### Fixes:
- Enforce mandatory Contact Number.
- Make picture optional.
- Restore missing action buttons if any.

---

## [Component: Sidebar / Main Window]

**File:** `main_window.py`

### Fixes:
- Restore Settings button.
- Ensure permission check uses:
  - `Auth.get_user_permissions()`
- Do NOT hardcode bypass.
- Ensure SuperAdmin/Admin roles include `settings` permission.

---

# 2️⃣ PDF Reports (URGENT)

## Goal:
Professional structured PDF generation.

## Implementation:

- Use **ReportLab** (`Table + PageBreak`) for structured reporting.
- Create new utility:
  - `src/utils/pdf_generator_v2.py`
- Do NOT render QTableWidget directly.

### Requirements:
- Fixed column widths.
- `repeatRows` for table headers.
- Proper pagination.
- Clean section separation.
- Branding and margins.
- Must handle large datasets.

---

# 3️⃣ Dashboard Improvements

## Goal:
Scrollable dashboard + analytics section.

## Implementation:

- Wrap `StoreDashboardView` inside `QScrollArea`.
- Keep existing card hover effects unchanged.
- Add Analytics section below main cards.

### Layout:
