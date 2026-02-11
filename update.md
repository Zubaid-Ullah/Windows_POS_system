# Store Application – Update Requirements

**Prepared By:** Zubaid Ullah  
**Platform:** Desktop (PyQt6)  
**Charts:** QtCharts (QChart)  
**Camera:** OpenCV  
**Print Format:** A4  
**Export:** PDF, Excel  
**Target UI:** Desktop (Vertical scrolling only)

---

## Priority Legend
- **P0** – Critical (financial risk / data integrity / workflow blocker)
- **P1** – Important (UX / usability / clarity)
- **P2** – Enhancement (nice to have)

---

## 1. Dashboard

### REQ-DASH-01 (P1): Scrollable Dashboard
- Dashboard must be **vertically scrollable**
- Desktop layout only
- Cards should wrap correctly and never overlap

**Done when:**
- Mouse wheel scroll works
- No UI freeze or layout break

---

### REQ-DASH-02 (P1): Donut Chart with Progress Colors

Donut chart should support metrics:
- Sales
- Expenses
- Profit

**Progress → Color Mapping**

| Progress Range | Color |
|---------------|-------|
| 0–25% | Red |
| 25–50% | Orange |
| 50–75% | Yellow |
| 75–100% | Green |

**Done when:**
- Chart updates dynamically
- Correct color is applied per range

---

## 2. Finance Window

### 2.1 Overview Tab

#### REQ-FIN-01 (P0): Improve “New Expense” Entry
- Category and Date fields are too small
- Make form easier and keyboard friendly

**Done when:**
- Inputs are clearly visible
- Tab navigation works properly

---

#### REQ-FIN-02 (P0): Remove Salary from Expense
- Salary must NOT appear in expense categories
- Salary is already handled in Payroll tab

**Done when:**
- Salary option removed from expense list
- Salary calculations occur only in payroll

---

### 2.2 Payroll Tab

#### REQ-PAY-01 (P0): Salary Payment Table
When salary is paid, show:



(Table columns: Days | Amount Paid)

---

#### REQ-PAY-02 (P0): Prevent Duplicate Salary Payment
**Definition of duplicate:**
- Same employee + same month

**Rules:**
- Second payment must be blocked
- Either disable Pay button OR prevent DB insert

**Done when:**
- Employee cannot be paid twice for the same month

---

#### REQ-PAY-03 (P1): Salary Status by Month
Status must show:
- Paid
- Not Paid

**Month logic:**
- Based on selected/current month dropdown

---

#### REQ-PAY-04 (P1): Advance Display
- If advance taken → show amount
- If not taken → show blank / clean

**Advance source:**
- Payroll record field/table

---

### 2.3 Summary Tab (Missing)

#### REQ-SUM-01 (P0): Financial Summary Totals
Add:
- Total Gross Sale
- Total Costs (COGS)
- Total Expense
- Total Profit

**Done when:**
- Values match report data and filters

---

### 2.4 Report Tab

#### REQ-RPT-01 (P1): Scrollable Reports
Report sections:
- All
- Salaries
- Expenses
- Profit

---

#### REQ-RPT-02 (P0): Authorizer Information
Each payment must show **who paid**:
- Admin
- Manager
- Cashier

**DB Note:**  
Add `authorized_by / paid_by` field if required.

---

#### REQ-RPT-03 (P0): Custom Date Range Filter
- If **Salaries** selected → show only salaries
- If **All** selected → show salaries + expenses + profit
- Date range: From — To

---

#### REQ-RPT-04 (P0): Print & Export
- Print format: **A4**
- Export: **PDF & Excel**

**Header/Footer must include:**
- Store Name
- Report Period
- Generated Date/Time
- User/Authorizer

**If no data:**
- Show message: `No record for today`

---

## 3. Customer Window

### REQ-CUST-01 (P1): Camera Detection
- Detect all cameras via OpenCV
- Avoid macOS confusion:
  - Index 0 may be iPhone camera
  - Index 1 may be Mac internal camera

**Done when:**
- Camera list is clear and selectable

---

### REQ-KYC-01 (P1): KYC Picture Preview
- After capture, show image in QLabel preview

---

## 4. Sale Window

### REQ-SALE-01 (P1): Quantity Input
- Replace double-click quantity editing
- Use `QSpinBox`
- Must be tab-focusable

---

## 5. Loans Window

### REQ-LOAN-01 (P0): Loan Limit Missing in KYC Popup
- Loan limit is set during customer registration by store owner
- Loan limit must appear in KYC popup

---

### REQ-LOAN-02 (P1): Auto Balance Selection
- When Pay button clicked:
  - Balance should be auto-picked

---

## 6. Return Window

### REQ-RET-01 (P0): Prevent Multiple Returns
- Item returned once must NOT be returnable again
- Rule based on:
  - Invoice + Item (+ Serial if available)

---

### REQ-RET-02 (P1): Daily Pie Chart Update
- Pie chart updates based on daily sale
- If no credit → show full green chart

---

## 7. Settings Window

### REQ-REC-01 (P1): Receipt Types
Add two receipt formats:
- Walk-in Customer
- Trusty Customer

Receipt message must change accordingly.

---

## 8. Price Check Window

### REQ-PRC-01 (P0): Always Autofocus
Autofocus must work:
- On window open
- After scan
- After result display

---

## Notes
- DB migration may be required for:
  - Authorizer tracking
  - Payroll uniqueness (employee + month)
  - Return lock
