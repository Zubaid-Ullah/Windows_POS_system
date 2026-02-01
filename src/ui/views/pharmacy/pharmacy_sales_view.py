from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QComboBox, QDialog, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import qtawesome as qta
from src.database.db_manager import db_manager
from src.core.localization import lang_manager
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button
from datetime import datetime

class PharmacySalesView(QWidget):
    sale_completed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.cart = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Search / Barcode Entry
        header = QHBoxLayout()
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan Barcode or Type Product Name...")
        self.barcode_input.setFixedHeight(55)
        self.barcode_input.returnPressed.connect(self.handle_search)
        header.addWidget(self.barcode_input, 4)
        
        self.add_btn = QPushButton("Add to Basket")
        style_button(self.add_btn, variant="primary")
        self.add_btn.clicked.connect(self.handle_search)
        header.addWidget(self.add_btn, 1)
        layout.addLayout(header)

        # Bill Number & Reprint Row
        bill_row = QHBoxLayout()
        bill_row.setSpacing(10)
        
        self.bill_number_display = QLabel("INV-0001")
        self.bill_number_display.setStyleSheet("""
            background-color: #f1f5f9;
            color: #475569;
            font-family: monospace;
            font-size: 16px;
            font-weight: bold;
            padding: 8px 15px;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
        """)
        bill_row.addWidget(QLabel("📄 Current Bill #:"))
        bill_row.addWidget(self.bill_number_display)
        
        self.reprint_btn = QPushButton(" 🖨️ Reprint Last Bill ")
        style_button(self.reprint_btn, variant="info", size="small")
        self.reprint_btn.clicked.connect(self.reprint_last_bill)
        bill_row.addWidget(self.reprint_btn)
        
        bill_row.addStretch()
        layout.addLayout(bill_row)
        
        self.load_next_bill_number()

        # Customer & Payment Method
        control_layout = QHBoxLayout()
        
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["CASH", "CREDIT"]) 
        # Default for Walk-in is CASH
        self.payment_combo.setCurrentText("CASH")
        
        self.customer_combo = QComboBox()
        self.load_customers()
        self.customer_combo.currentIndexChanged.connect(self.handle_customer_change)
        self.customer_combo.installEventFilter(self) # We'll refresh on focus
        
        control_layout.addWidget(QLabel("Customer:"))
        control_layout.addWidget(self.customer_combo, 2)
        control_layout.addWidget(QLabel("Method:"))
        control_layout.addWidget(self.payment_combo, 1)
        
        layout.addLayout(control_layout)
        
        # Cart Table
        # Columns: Barcode, Name, Size, Expiry, Price, Qty, Total, Remaining, Actions
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Barcode", "Name", "Size", "Expiry", "Price", "Qty", "Total", "Remaining", "Action"
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # Footer
        footer = QHBoxLayout()
        self.total_lbl = QLabel("Total: 0.00 AFN")
        self.total_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #1b2559;")
        footer.addWidget(self.total_lbl)
        
        footer.addStretch()
        
        # Requirement: Add credit button for loan purpose
        credit_btn = QPushButton(" Credit Sale (Loan) ")
        style_button(credit_btn, variant="warning", size="large")
        credit_btn.clicked.connect(lambda: self.process_checkout(force_credit=True))
        footer.addWidget(credit_btn)
        
        checkout_btn = QPushButton(" Process Checkout ")
        style_button(checkout_btn, variant="success", size="large")
        checkout_btn.clicked.connect(self.process_checkout)
        footer.addWidget(checkout_btn)
        
        layout.addLayout(footer)

    def load_customers(self):
        curr_text = self.customer_combo.currentText()
        self.customer_combo.clear()
        self.customer_combo.addItem("Walk-in Customer", None)
        try:
            with db_manager.get_pharmacy_connection() as conn:
                rows = conn.execute("SELECT id, name FROM pharmacy_customers WHERE is_active=1").fetchall()
                for r in rows:
                    self.customer_combo.addItem(r['name'], r['id'])
            
            # Restore selection if possible
            idx = self.customer_combo.findText(curr_text)
            if idx >= 0: self.customer_combo.setCurrentIndex(idx)
        except Exception as e:
            print(f"Error loading customers: {e}")

    def handle_customer_change(self, index):
        """Automatically set payment method based on customer selection"""
        if index == 0: # Walk-in Customer (always first item in load_customers)
            self.payment_combo.setCurrentText("CASH")
        elif index > 0:
            self.payment_combo.setCurrentText("CREDIT")

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj == self.customer_combo and event.type() == QEvent.Type.FocusIn:
            self.load_customers()
        return super().eventFilter(obj, event)

    def check_stock(self, product_id, batch, quantity):
        with db_manager.get_pharmacy_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT quantity, expiry_date FROM pharmacy_inventory 
                WHERE product_id = ? AND batch_number = ?
            """, (product_id, batch))
            row = cursor.fetchone()
            if not row: return False, "Batch not found"
            
            stock, expiry = row['quantity'], row['expiry_date']
            
            # Check Expiry
            if expiry:
                exp_date = datetime.strptime(expiry, "%Y-%m-%d")
                if exp_date < datetime.now():
                    return False, f"Batch Expired on {expiry}"
            
            if stock < quantity:
                return False, f"Insufficient Stock. Available: {stock}"
            
            return True, "OK"

    def handle_search(self):
        search_term = self.barcode_input.text().strip()
        if not search_term: return
        
        with db_manager.get_pharmacy_connection() as conn:
            cursor = conn.cursor()
            # Fetch product with earliest expiring batch (FIFO)
            cursor.execute("""
                SELECT p.*, i.quantity as stock, i.batch_number, i.expiry_date 
                FROM pharmacy_products p 
                JOIN pharmacy_inventory i ON p.id = i.product_id 
                WHERE (p.barcode = ? OR p.name_en LIKE ?) 
                AND p.is_active = 1 
                AND i.quantity > 0
                ORDER BY i.expiry_date ASC 
                LIMIT 1
            """, (search_term, f"%{search_term}%"))
            row = cursor.fetchone()
            
            if row:
                product = dict(row)
                self.add_to_cart(product)
                self.barcode_input.clear()
            else:
                QMessageBox.warning(self, "Not Found", "Product not found in system.")

    def add_to_cart(self, p):
        #1. Existing Item Logic
        for item in self.cart:
            if item['id'] == p['id'] and item.get('batch') == p.get('batch_number'):
                new_qty = item['qty'] + 1
                valid, msg = self.check_stock(item['id'], item['batch'], new_qty)
                if not valid:
                    QMessageBox.warning(self, "Stock Issue", msg)
                    return
                item['qty'] = new_qty
                self.refresh_table()
                return

        # 2. New Item Logic
        valid, msg = self.check_stock(p['id'], p.get('batch_number'), 1)
        if not valid:
             QMessageBox.warning(self, "Stock Issue", msg)
             return

        self.cart.append({
            'id': p['id'],
            'barcode': p['barcode'],
            'name': p['name_en'],
            'size': p.get('size', 'N/A'),
            'expiry': p.get('expiry_date', 'N/A'),
            'price': p['sale_price'],
            'batch': p.get('batch_number'),
            'qty': 1,
            'stock': p.get('stock', 0)  # Store available stock
        })
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        grant_total = 0
        for i, item in enumerate(self.cart):
            self.table.insertRow(i)
            total = item['price'] * item['qty']
            grant_total += total
            
            self.table.setItem(i, 0, QTableWidgetItem(item['barcode']))
            self.table.setItem(i, 1, QTableWidgetItem(item['name']))
            self.table.setItem(i, 2, QTableWidgetItem(item['size']))
            self.table.setItem(i, 3, QTableWidgetItem(item.get('expiry', '')))
            self.table.setItem(i, 4, QTableWidgetItem(f"{item['price']:.2f}"))
            
            # Editable Quantity with SpinBox
            qty_spinbox = QSpinBox()
            qty_spinbox.setMinimum(1)
            qty_spinbox.setMaximum(int(item.get('stock', 999)))  # Convert to int
            qty_spinbox.setValue(item['qty'])
            qty_spinbox.editingFinished.connect(lambda s=qty_spinbox, idx=i: self.update_qty(idx, s.value()))
            self.table.setCellWidget(i, 5, qty_spinbox)
            
            self.table.setItem(i, 6, QTableWidgetItem(f"{total:.2f}"))
            
            # Remaining stock display
            remaining = item.get('stock', 0) - item['qty']
            remaining_item = QTableWidgetItem(str(remaining))
            remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Color code: green if plenty, orange if low, red if very low
            if remaining > 10:
                remaining_item.setForeground(Qt.GlobalColor.darkGreen)
            elif remaining > 5:
                remaining_item.setForeground(QColor(255, 140, 0))  # Orange
            else:
                remaining_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(i, 7, remaining_item)
            
            remove_btn = QPushButton()
            remove_btn.setIcon(qta.icon("fa5s.times", color="white"))
            style_button(remove_btn, variant="danger", size="icon")
            remove_btn.clicked.connect(lambda checked, idx=i: self.remove_item(idx))
            self.table.setCellWidget(i, 8, remove_btn)
            
        self.total_lbl.setText(f"Total: {grant_total:.2f} AFN")
    
    def update_qty(self, idx, new_qty):
        """Update quantity when spinbox changes"""
        if idx < len(self.cart):
            item = self.cart[idx]
            valid, msg = self.check_stock(item['id'], item['batch'], new_qty)
            if not valid:
                QMessageBox.warning(self, "Stock Issue", msg)
                self.refresh_table()
                return
            item['qty'] = new_qty
            self.refresh_table()

    def remove_item(self, idx):
        self.cart.pop(idx)
        self.refresh_table()

    def process_checkout(self, force_credit=False):
        if not self.cart: return
        
        from src.core.pharmacy_auth import PharmacyAuth
        user = PharmacyAuth.get_current_user()
        user_id = user['id'] if user else 1
        
        total_amount = sum(item['price'] * item['qty'] for item in self.cart)
        invoice = f"PHARM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        customer_id = self.customer_combo.currentData()
        payment_method = "CREDIT" if force_credit else self.payment_combo.currentText()
        
        if payment_method == "CREDIT" and not customer_id:
            QMessageBox.warning(self, "Error", "Customer must be selected for Credit sales.")
            return

        # Check Loan Limit
        if payment_method == "CREDIT":
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    # Fetch customer limit and balance
                    cust = conn.execute("SELECT balance, loan_limit, loan_enabled FROM pharmacy_customers WHERE id=?", (customer_id,)).fetchone()
                    if cust:
                        if not cust['loan_enabled']:
                            QMessageBox.warning(self, "Loan Disabled", "Credit sales are disabled for this customer.")
                            return
                            
                        # If limit is 0, maybe it means unlimited? 
                        # User requirement: "if customer loan is set to a specific number then display a message if amount goes beyond loan limit"
                        # Usually 0 means no limit or no credit allowed. Let's assume >0 is the limit. 
                        # If the user specifically sets a number, we enforce it.
                        limit = cust['loan_limit']
                        if limit > 0:
                            current_bal = cust['balance']
                            if (current_bal + total_amount) > limit:
                                QMessageBox.warning(self, "Limit Exceeded", 
                                    f"Transaction denied. \nCustomer Loan Limit: {limit:,.2f}\nCurrent Balance: {current_bal:,.2f}\nNew Balance would be: {(current_bal+total_amount):,.2f}")
                                return
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to verify loan limit: {e}")
                return

        try:
            with db_manager.get_pharmacy_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Create Sale Header
                cursor.execute("""
                    INSERT INTO pharmacy_sales (invoice_number, user_id, total_amount, customer_id, payment_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (invoice, user_id, total_amount, customer_id, payment_method))
                sale_id = cursor.lastrowid
                
                # 2. Process Items and Inventory
                for item in self.cart:
                    # Record Item
                    cursor.execute("""
                        INSERT INTO pharmacy_sale_items 
                        (sale_id, product_id, product_name, batch_number, expiry_date, quantity, unit_price, total_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (sale_id, item['id'], item['name'], item.get('batch'), item.get('expiry'), 
                          item['qty'], item['price'], item['price']*item['qty']))
                    
                    # Update Inventory (Specific Batch)
                    cursor.execute("""
                        UPDATE pharmacy_inventory 
                        SET quantity = quantity - ? 
                        WHERE product_id = ? AND batch_number = ?
                    """, (item['qty'], item['id'], item.get('batch')))
                
                # 3. Handle Credit/Loan
                if payment_method == "CREDIT":
                    cursor.execute("""
                        INSERT INTO pharmacy_loans (customer_id, sale_id, total_amount, balance)
                        VALUES (?, ?, ?, ?)
                    """, (customer_id, sale_id, total_amount, total_amount))
                    
                    # Update customer balance
                    cursor.execute("UPDATE pharmacy_customers SET balance = balance + ? WHERE id = ?", (total_amount, customer_id))

                conn.commit()

                # Ask for bill printing after successful sale
                self.print_pharmacy_sale_bill(sale_id, invoice, total_amount, payment_method)

                # Auto update bill number display for next sale
                self.load_next_bill_number()

                QMessageBox.information(self, "Success", f"Pharmacy Sale Completed!\nInvoice: {invoice}")
                self.cart = []
                self.refresh_table()
                self.sale_completed.emit() # Notify reports
                self.barcode_input.setFocus()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Transaction Failed: {e}")

    def load_next_bill_number(self):
        """Load and display next pharmacy bill number"""
        try:
            with db_manager.get_pharmacy_connection() as conn:
                last_bill = conn.execute(
                    "SELECT invoice_number FROM pharmacy_sales ORDER BY id DESC LIMIT 1"
                ).fetchone()
                
                if last_bill:
                    try:
                        # Extract number from format PHARM-YYYYMMDDHHMMSS or similar
                        # But let's use a simpler incrementing number if we want to match general store style
                        # For now, just generate the next likely one
                        next_num = last_bill['id'] + 1 if 'id' in last_bill else 1
                    except:
                        next_num = 1
                else:
                    next_num = 1
                
                self.bill_number_display.setText(f"PHARM-{datetime.now().strftime('%Y%m%d')}-{next_num:04d}")
        except Exception as e:
            print(f"Error loading pharmacy bill number: {e}")
            self.bill_number_display.setText("PHARM-0001")

    def reprint_last_bill(self):
        """Reprint the last pharmacy bill"""
        try:
            with db_manager.get_pharmacy_connection() as conn:
                last_sale = conn.execute(
                    "SELECT id, invoice_number, total_amount, payment_type FROM pharmacy_sales ORDER BY id DESC LIMIT 1"
                ).fetchone()
                
                if not last_sale:
                    QMessageBox.warning(self, "No Sales", "No previous sales found to reprint.")
                    return
                
                sale_id = last_sale['id']
                invoice_num = last_sale['invoice_number']
                total = last_sale['total_amount']
                method = last_sale['payment_type']
                
                confirm = QMessageBox.question(
                    self, "Reprint Bill",
                    f"Reprint last pharmacy bill?\nInvoice: {invoice_num}\nAmount: {total:,.2f} AFN",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if confirm == QMessageBox.StandardButton.Yes:
                    from src.utils.thermal_bill_printer import thermal_printer
                    bill_text = thermal_printer.generate_sales_bill(sale_id, method == "CREDIT", is_pharmacy=True)
                    if bill_text:
                        thermal_printer.print_bill(bill_text)
                    else:
                        QMessageBox.warning(self, "Error", "Failed to generate bill.")
                        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Reprint failed: {e}")

    def print_pharmacy_sale_bill(self, sale_id, invoice_num, total, method):
        """Ask user if they want to print the pharmacy bill after sale completion"""
        reply = QMessageBox.question(
            self, "Print Pharmacy Bill",
            f"Pharmacy sale completed successfully!\nInvoice: {invoice_num}\nAmount: {total:,.2f} AFN\n\nWould you like to print the bill?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from src.utils.thermal_bill_printer import thermal_printer
                bill_text = thermal_printer.generate_sales_bill(sale_id, method == "CREDIT", is_pharmacy=True)
                
                if bill_text:
                    thermal_printer.print_bill(bill_text)
                else:
                    QMessageBox.warning(self, "Print Error", "Failed to generate bill.")
            except Exception as e:
                QMessageBox.critical(self, "Print Error", f"Failed to print bill: {str(e)}")

    def generate_pharmacy_bill_pdf(self, sale_id, invoice_num, total, method):
        """Generate PDF bill for pharmacy sales"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            import tempfile

            with db_manager.get_pharmacy_connection() as conn:
                cursor = conn.cursor()

                # Get sale details
                cursor.execute("""
                    SELECT ps.*, pc.name as customer_name
                    FROM pharmacy_sales ps
                    LEFT JOIN pharmacy_customers pc ON ps.customer_id = pc.id
                    WHERE ps.id = ?
                """, (sale_id,))
                sale = cursor.fetchone()

                # Get sale items
                cursor.execute("""
                    SELECT psi.*, pp.name_en as product_name
                    FROM pharmacy_sale_items psi
                    JOIN pharmacy_products pp ON psi.product_id = pp.id
                    WHERE psi.sale_id = ?
                """, (sale_id,))
                items = cursor.fetchall()

            # Create temporary PDF file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()

            doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
            elements = []

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('Title', fontSize=20, fontName='Helvetica-Bold', alignment=1, spaceAfter=20)

            elements.append(Paragraph("PHARMACY RECEIPT", title_style))
            elements.append(Paragraph(f"Invoice: {invoice_num}", styles['Normal']))
            elements.append(Paragraph(f"Date: {sale['created_at'][:10] if sale else 'N/A'}", styles['Normal']))
            if sale and sale['customer_name']:
                elements.append(Paragraph(f"Customer: {sale['customer_name']}", styles['Normal']))
            elements.append(Paragraph(f"Payment: {method}", styles['Normal']))
            elements.append(Spacer(1, 20))

            # Items table
            table_data = [['Product', 'Qty', 'Price', 'Total']]
            for item in items:
                table_data.append([
                    item['product_name'],
                    str(item['quantity']),
                    f"{item['unit_price']:.2f}",
                    f"{item['total_price']:.2f}"
                ])

            table_data.append(['', '', 'TOTAL:', f"{total:.2f}"])

            items_table = Table(table_data, colWidths=[200, 50, 70, 70])
            items_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))
            elements.append(items_table)
            elements.append(Spacer(1, 30))
            elements.append(Paragraph("Thank you for your business!", styles['Normal']))

            doc.build(elements)
            return temp_file.name

        except Exception as e:
            print(f"Error generating pharmacy bill: {e}")
            return None
