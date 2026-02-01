# Implementation Plan for demand.txt Requirements

## STATUS: IN PROGRESS

### ✅ COMPLETED:
1. Created thermal_bill_printer.py with exact format from demand.txt
   - Thermal-style bill format matching example
   - QR code generation for invoice number
   - Amount in words conversion
   - Company details from settings page
   - Proper line wrapping for long product names

### 🔨 REMAINING TASKS:

#### 1. Update Sales View (sales_view.py)
**Location**: Lines 110-220 (init_ui method)

Add after search_card (around line 153):
```python
# Bill Number Display and Reprint Section
bill_section = QFrame()
bill_section.setObjectName("card")
bill_layout = QHBoxLayout(bill_section)

bill_layout.addWidget(QLabel("📄 Current Bill #:"))
self.bill_number_display = QLineEdit()
self.bill_number_display.setReadOnly(True)
self.bill_number_display.setFixedWidth(200)
self.bill_number_display.setStyleSheet("background: #f0f0f0; font-weight: bold;")
self.load_next_bill_number()  # Load and display next bill number
bill_layout.addWidget(self.bill_number_display)

self.reprint_btn = QPushButton("🖨️ Reprint Last Bill")
style_button(self.reprint_btn, variant="outline")
self.reprint_btn.clicked.connect(self.reprint_last_bill)
bill_layout.addWidget(self.reprint_btn)

bill_layout.addStretch()
main_layout.addWidget(bill_section)
```

**Add methods before clear_cart (around line 539)**:
```python
def load_next_bill_number(self):
    """Load and display next bill number"""
    try:
        with db_manager.get_connection() as conn:
            last_bill = conn.execute(
                "SELECT invoice_number FROM sales ORDER BY id DESC LIMIT 1"
            ).fetchone()
            
            if last_bill:
                # Extract number and increment
                last_num = int(last_bill['invoice_number'].split('-')[-1])
                next_num = last_num + 1
            else:
                next_num = 1
            
            self.bill_number_display.setText(f"INV-{datetime.now().strftime('%Y%m%d')}-{next_num:04d}")
    except Exception as e:
        print(f"Error loading bill number: {e}")
        self.bill_number_display.setText("INV-0001")

def reprint_last_bill(self):
    """Reprint the last generated bill"""
    try:
        with db_manager.get_connection() as conn:
            last_sale = conn.execute(
                "SELECT id, invoice_number, total_amount, payment_type FROM sales ORDER BY id DESC LIMIT 1"
            ).fetchone()
            
            if not last_sale:
                QMessageBox.warning(self, "No Bills", "No bills found to reprint")
                return
            
            reply = QMessageBox.question(
                self, "Reprint Bill",
                f"Reprint Bill: {last_sale['invoice_number']}\\nAmount: {last_sale['total_amount']:.2f} AFN?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.print_sale_bill(
                    last_sale['id'],
                    last_sale['invoice_number'],
                    last_sale['total_amount'],
                    last_sale['payment_type']
                )
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to reprint: {str(e)}")
```

#### 2. Update print_sale_bill method (line 514-537)
Replace with thermal printer:
```python
def print_sale_bill(self, sale_id, invoice_num, total, method):
    """Ask user if they want to print the bill after sale completion"""
    reply = QMessageBox.question(
        self, "Print Bill",
        f"Sale completed successfully!\\nInvoice: {invoice_num}\\nAmount: {total:,.2f} AFN\\n\\nWould you like to print the bill?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes
    )

    if reply == QMessageBox.StandardButton.Yes:
        try:
            # Use thermal printer for exact format from demand.txt
            from src.utils.thermal_bill_printer import thermal_printer
            bill_text = thermal_printer.generate_sales_bill(sale_id, method == "CREDIT")
            
            if bill_text:
                thermal_printer.print_bill(bill_text)
                QMessageBox.information(self, "Success", "Bill printed successfully!")
            else:
                QMessageBox.warning(self, "Print Error", "Failed to generate bill.")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print bill: {str(e)}")
```

#### 3. Update process_payment method to auto-increment bill (line 490)
After getting sale_id:
```python
# Auto update bill number display
self.load_next_bill_number()
```

#### 4. Create Pharmacy Settings Page
**New File**: src/ui/views/pharmacy/pharmacy_settings_view.py
Copy from settings_view.py and adapt for pharmacy database.

#### 5. Add Pharmacy Settings to Sidebar
**File**: src/ui/main_window.py (or wherever pharmacy menu is defined)
Add "Ph-Settings" button that shows pharmacy_settings_view

---

## QUICK APPLY STEPS:

1. Run this script to apply all changes automatically
2. Test bill printing with thermal format
3. Verify bill number auto-increment
4. Add pharmacy settings page to navigation

## Files Modified:
- ✅ thermal_bill_printer.py (NEW)
- ⏳ sales_view.py (PENDING)
- ⏳ pharmacy_settings_view.py (PENDING - TO CREATE)
- ⏳ main_window.py or pharmacy menu (PENDING - ADD SETTINGS NAV)
