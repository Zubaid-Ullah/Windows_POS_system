from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QMessageBox, QDialog, QInputDialog, QCompleter, QTextEdit, QComboBox, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QStringListModel
from PyQt6.QtGui import QImage, QPixmap, QFont
from datetime import datetime
import qtawesome as qta
# import cv2 # Camera feature placeholder
import numpy as np
import os
import time
import uuid
from src.core.localization import lang_manager
from src.database.db_manager import db_manager
from src.core.auth import Auth
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table

class CreditKYCDialog(QDialog):
    def __init__(self, parent=None, customer_name=""):
        super().__init__(parent)
        self.setWindowTitle(f"Credit Security Registration - {customer_name}")
        self.setFixedWidth(400)
        self.photo_path = None
        self.id_photo_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.address_input = QLineEdit()
        self.phone_input = QLineEdit()
        
        form.addRow("Home Address:", self.address_input)
        form.addRow("Contact Number:", self.phone_input)
        
        layout.addLayout(form)
        
        # Photos
        self.photo_btn = QPushButton(" Take Customer Photo")
        self.photo_btn.setIcon(qta.icon("fa5s.camera"))
        self.photo_btn.clicked.connect(self.take_photo)
        layout.addWidget(self.photo_btn)
        
        self.id_btn = QPushButton(" Take ID Card Photo")
        self.id_btn.setIcon(qta.icon("fa5s.id-card"))
        self.id_btn.clicked.connect(self.take_id_photo)
        layout.addWidget(self.id_btn)
        
        btns = QHBoxLayout()
        save = QPushButton("Verify & Save")
        style_button(save, variant="success")
        save.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        style_button(cancel, variant="danger")
        cancel.clicked.connect(self.reject)
        btns.addWidget(save)
        btns.addWidget(cancel)
        layout.addLayout(btns)

    def take_photo(self):
        from src.utils.camera import capture_image
        path = os.path.join("data", "kyc", f"cust_{int(time.time())}.jpg")
        success, msg = capture_image(path)
        if success:
            self.photo_path = path
            self.photo_btn.setText(" Photo Captured ✓")
            self.photo_btn.setStyleSheet("background-color: #05cd99; color: white;")
        else:
            if msg: QMessageBox.warning(self, "Camera Error", msg)

    def take_id_photo(self):
        from src.utils.camera import capture_image
        path = os.path.join("data", "kyc", f"id_{int(time.time())}.jpg")
        success, msg = capture_image(path)
        if success:
            self.id_photo_path = path
            self.id_btn.setText(" ID Captured ✓")
            self.id_btn.setStyleSheet("background-color: #05cd99; color: white;")
        else:
            if msg: QMessageBox.warning(self, "Camera Error", msg)
    def get_data(self):
        return {
            "address": self.address_input.text(),
            "phone": self.phone_input.text(),
            "photo": self.photo_path,
            "id_photo": self.id_photo_path
        }

class SalesView(QWidget):
    def __init__(self):
        super().__init__()
        self.cart = []
        self.selected_customer_id = 1
        self.barcode_cache = {}
        self.last_scan_time = 0
        self.current_user = Auth.get_current_user()
        self.completion_map = {}
        
        # State for Price Check Hold
        self.is_price_check_mode = False
        self.held_cart_data = None
        
        self.load_barcode_cache()
        self.init_ui()
        self.load_customers()
        QTimer.singleShot(100, self.search_input.setFocus)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 1. Search Bar (Top)
        search_card = QFrame()
        search_card.setObjectName("card")
        search_layout = QHBoxLayout(search_card)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(lang_manager.get("barcode") + "...")
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px; 
                border: none; 
                padding: 0 10px; 
                background: transparent; 
            }
        """)
        
        # Live Suggestions
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.activated.connect(self.handle_completer_activation)
        self.search_input.setCompleter(self.completer)
        self.search_input.textChanged.connect(self.update_completer)
        self.search_input.returnPressed.connect(self.handle_barcode_scan)
        
        search_layout.addWidget(QLabel("🔍"))
        search_layout.addWidget(self.search_input)
        
        # Customer Selection (Point: "add a combobox where customer can be selected easily")
        self.cust_combo = QComboBox()
        self.cust_combo.setFixedWidth(250)
        self.cust_combo.setFixedHeight(35)
        # Styling handled by theme manager
        self.cust_combo.currentIndexChanged.connect(self.on_customer_changed)
        search_layout.addWidget(QLabel("👤"))
        search_layout.addWidget(self.cust_combo)
        
        main_layout.addWidget(search_card)
        
        # Bill Number Display and Reprint Section
        bill_section = QFrame()
        bill_section.setObjectName("card")
        bill_layout = QHBoxLayout(bill_section)
        bill_layout.setContentsMargins(10, 5, 10, 5)
        
        bill_layout.addWidget(QLabel("📄 Current Bill #:"))
        self.bill_number_display = QLineEdit()
        self.bill_number_display.setReadOnly(True)
        self.bill_number_display.setFixedWidth(250)
        self.bill_number_display.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        self.load_next_bill_number()  # Load and display next bill number
        bill_layout.addWidget(self.bill_number_display)
        
        self.reprint_btn = QPushButton("🖨️ Reprint Last Bill")
        style_button(self.reprint_btn, variant="outline")
        self.reprint_btn.clicked.connect(self.reprint_last_bill)
        bill_layout.addWidget(self.reprint_btn)
        
        bill_layout.addStretch()
        main_layout.addWidget(bill_section)
        
        # 2. Table (Point: "has action/clear button where a specific product can be removed")
        self.cart_table = QTableWidget(0, 8)
        self.cart_table.setHorizontalHeaderLabels([
            "ID", "Barcode", "Product Name", "Price", "Qty", "Stock", "Total", "Action"
        ])
        style_table(self.cart_table, variant="premium")
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.cart_table.cellChanged.connect(self.handle_qty_edit)
        main_layout.addWidget(self.cart_table)
        
        # Price Check Stats Card (Hidden by default)
        self.display_card = QFrame()
        self.display_card.setObjectName("card")
        self.display_card.setVisible(False)
        self.display_card.setMinimumHeight(200)
        card_layout = QVBoxLayout(self.display_card)
        
        self.product_name_lbl = QLabel("")
        self.product_name_lbl.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.product_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.price_lbl = QLabel("")
        self.price_lbl.setStyleSheet("font-size: 32px; font-weight: 800; color: #059669;")
        self.price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.quantity_lbl = QLabel("")
        self.quantity_lbl.setStyleSheet("font-size: 18px; color: #64748b;")
        self.quantity_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(self.product_name_lbl)
        card_layout.addWidget(self.price_lbl)
        card_layout.addWidget(self.quantity_lbl)
        main_layout.addWidget(self.display_card)
        
        # 3. Bottom Panel
        bottom_panel = QHBoxLayout()
        
        # Discount logic
        self.discount_container = QFrame()
        disc_layout = QHBoxLayout(self.discount_container)
        disc_layout.setContentsMargins(0, 0, 0, 0)
        disc_layout.addWidget(QLabel("Discount:"))
        self.discount_input = QLineEdit()
        self.discount_input.setFixedWidth(80)
        self.discount_input.setPlaceholderText("0.00")
        self.discount_input.textChanged.connect(self.update_totals)
        disc_layout.addWidget(self.discount_input)
        bottom_panel.addWidget(self.discount_container)
        
        bottom_panel.addStretch()
        
        self.total_label = QLabel("Total: 0.00 AFN")
        self.total_label.setObjectName("page_header")
        self.total_label.setStyleSheet("font-size: 24px;")
        bottom_panel.addWidget(self.total_label)
        
        main_layout.addLayout(bottom_panel)
        
        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton(" Clear Cart")
        style_button(clear_btn, variant="danger")
        clear_btn.setIcon(qta.icon("fa5s.trash", color="white"))
        clear_btn.clicked.connect(self.clear_cart)
        
        cash_btn = QPushButton(" Checkout (Cash)")
        style_button(cash_btn, variant="success")
        cash_btn.setIcon(qta.icon("fa5s.money-bill-wave", color="white"))
        cash_btn.clicked.connect(lambda: self.process_payment("CASH"))
        
        credit_btn = QPushButton(" Credit Sale")
        style_button(credit_btn, variant="info")
        credit_btn.setIcon(qta.icon("fa5s.credit-card", color="white"))
        credit_btn.clicked.connect(lambda: self.process_payment("CREDIT"))

        price_check_btn = QPushButton(" Price Check ")
        style_button(price_check_btn, variant="secondary")
        price_check_btn.setIcon(qta.icon("fa5s.tag", color="white"))
        price_check_btn.clicked.connect(self.activate_price_check)
        
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(price_check_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(credit_btn)
        btn_layout.addWidget(cash_btn)
        
        main_layout.addLayout(btn_layout)

    def activate_price_check(self):
        if self.is_price_check_mode:
            self.exit_price_check()
            return
            
        # 1. Hold current state
        self.held_cart_data = {
            'cart': list(self.cart),  # Deep copy not needed for simple dicts, list() is enough
            'customer_idx': self.cust_combo.currentIndex(),
            'discount': self.discount_input.text()
        }
        
        # 2. Clear UI for Price Check
        self.is_price_check_mode = True
        self.cart = []
        self.refresh_table()
        self.discount_input.clear()
        self.cart_table.setVisible(False)
        self.display_card.setVisible(True)
        self.product_name_lbl.setText("Scan product for price check")
        self.price_lbl.setText("")
        self.quantity_lbl.setText("")
        
        # 3. Visual feedback
        self.search_input.setPlaceholderText("🔴 PRICE CHECK MODE (Press ESC to Resume Sale)")
        self.search_input.setStyleSheet("font-size: 16px; border: 2px solid #ffb547; padding: 0 10px; background: #fff8e1; color: black;")
        self.search_input.setFocus()
        
    def exit_price_check(self):
        if not self.is_price_check_mode: return
        
        # Restore State
        if self.held_cart_data:
            self.cart = self.held_cart_data['cart']
            self.cust_combo.setCurrentIndex(self.held_cart_data['customer_idx'])
            self.discount_input.setText(self.held_cart_data['discount'])
            self.held_cart_data = None
        
        self.is_price_check_mode = False
        self.cart_table.setVisible(True)
        self.display_card.setVisible(False)
        self.refresh_table()
        self.reset_search_style()
        QMessageBox.information(self, "Resumed", "Sale transaction resumed.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.is_price_check_mode:
            self.exit_price_check()
        else:
            super().keyPressEvent(event)

    def reset_search_style(self):
        self.search_input.setPlaceholderText(lang_manager.get("barcode") + "...")
        self.search_input.setStyleSheet("font-size: 16px; border: none; padding: 0 10px;")

    def load_barcode_cache(self):
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT p.*, i.quantity as stock_qty FROM products p LEFT JOIN inventory i ON p.id = i.product_id WHERE p.is_active = 1")
            for row in cursor.fetchall():
                self.barcode_cache[row['barcode']] = dict(row)

    def load_customers(self):
        self.cust_combo.blockSignals(True)
        self.cust_combo.clear()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_en FROM customers WHERE is_active = 1")
            customers = cursor.fetchall()
            for c in customers:
                self.cust_combo.addItem(c['name_en'], c['id'])
        
        # Default to Walking Customer (ID 1)
        index = self.cust_combo.findData(1)
        if index >= 0:
            self.cust_combo.setCurrentIndex(index)
            self.selected_customer_id = 1
        self.cust_combo.blockSignals(False)

    def on_customer_changed(self, index):
        self.selected_customer_id = self.cust_combo.itemData(index)

    def handle_barcode_scan(self):
        barcode = self.search_input.text().strip()
        if not barcode: return
        
        if barcode in self.barcode_cache:
            product = self.barcode_cache[barcode]
            
            if self.is_price_check_mode:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name_en, name_fa, sale_price FROM products WHERE barcode = ?", (barcode,))
                    product_info = cursor.fetchone()
                    
                    if product_info:
                        name = product_info['name_en'] or product_info['name_fa']
                        price = product_info['sale_price']
                        
                        # Fetch stock
                        cursor.execute("SELECT quantity FROM inventory WHERE product_id = ?", (product['id'],))
                        s_row = cursor.fetchone()
                        stock = s_row['quantity'] if s_row else 0
                        
                        self.product_name_lbl.setText(name)
                        self.price_lbl.setText(f"{price:.2f} AFN")
                        self.quantity_lbl.setText(f"In Stock: {int(stock)}")
                        self.display_card.setStyleSheet("background-color: #e6f7ff; border: 2px solid #91d5ff; border-radius: 8px; padding: 15px;")
                    else:
                        self.product_name_lbl.setText("Product not found")
                        self.price_lbl.setText("")
                        self.quantity_lbl.setText("")
                        self.display_card.setStyleSheet("background-color: #fff1f0; border: 2px solid #ffccc7; border-radius: 8px; padding: 15px;")
                self.search_input.clear()
                return

            self.add_to_cart(product, product.get('stock_qty') or 0)
            print('\a', end='', flush=True)
        self.search_input.clear()

    def update_completer(self, text):
        if len(text) < 2: return
        suggestions = []
        new_map = {}
        for bc, p in self.barcode_cache.items():
            if text.lower() in p['name_en'].lower() or text in bc:
                display = f"{p['name_en']} ({bc})"
                suggestions.append(display)
                new_map[display] = bc
        self.completion_map = new_map
        self.completer.setModel(QStringListModel(suggestions))

    def handle_completer_activation(self, text):
        barcode = self.completion_map.get(text)
        if barcode:
            self.search_input.setText(barcode)
            self.handle_barcode_scan()

    def add_to_cart(self, product, stock_qty):
        for item in self.cart:
            if item['id'] == product['id']:
                if item['qty'] + 1 > stock_qty:
                    QMessageBox.warning(self, "Out of Stock", f"Only {stock_qty} available.")
                    return
                item['qty'] += 1
                self.refresh_table()
                return
        
        if stock_qty <= 0:
            QMessageBox.warning(self, "Out of Stock", "Product out of stock.")
            return

        self.cart.append({
            'id': product['id'],
            'barcode': product['barcode'],
            'name': product['name_en'],
            'price': product['sale_price'],
            'qty': 1,
            'max_qty': stock_qty
        })
        self.refresh_table()

    def handle_qty_edit(self, row, col):
        if col == 4:
            try:
                item = self.cart[row]
                new_qty = float(self.cart_table.item(row, col).text())
                
                # Point: "quantity goes into minus, it should not go to minus number"
                # Point: "and it should not go beyond current stock"
                if new_qty < 0:
                    QMessageBox.warning(self, "Invalid Qty", "Quantity cannot be negative.")
                    self.refresh_table()
                    return
                
                if new_qty > item['max_qty']:
                    # Point: "a popup window should be shown to tell that dash product available"
                    QMessageBox.warning(self, "Insufficient Stock", f"Only {item['max_qty']} {item['name']} available.")
                    self.refresh_table()
                    return
                
                item['qty'] = new_qty
                self.refresh_table()
            except:
                self.refresh_table()

    def refresh_table(self):
        self.cart_table.blockSignals(True)
        self.cart_table.setRowCount(0)
        for i, item in enumerate(self.cart):
            # Fetch current stock in real-time
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT quantity FROM inventory WHERE product_id = ?", (item['id'],))
                stock_row = cursor.fetchone()
                current_stock = stock_row['quantity'] if stock_row else 0
            
            self.cart_table.insertRow(i)
            self.cart_table.setItem(i, 0, QTableWidgetItem(str(item['id'])))
            self.cart_table.setItem(i, 1, QTableWidgetItem(item['barcode']))
            self.cart_table.setItem(i, 2, QTableWidgetItem(item['name']))
            self.cart_table.setItem(i, 3, QTableWidgetItem(lang_manager.localize_digits(f"{item['price']:.2f}")))
            qty_item = QTableWidgetItem(lang_manager.localize_digits(str(item['qty'])))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cart_table.setItem(i, 4, qty_item)
            
            stock_item = QTableWidgetItem(lang_manager.localize_digits(str(int(current_stock))))
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if current_stock > 10:
                stock_item.setForeground(Qt.GlobalColor.darkGreen)
            elif current_stock > 5:
                stock_item.setForeground(QColor(255, 140, 0))  # Orange
            else:
                stock_item.setForeground(Qt.GlobalColor.red)
            self.cart_table.setItem(i, 5, stock_item)
            
            total_item = QTableWidgetItem(lang_manager.localize_digits(f"{(item['price'] * item['qty']):.2f}"))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.cart_table.setItem(i, 6, total_item)
            
            remove_btn = QPushButton()
            remove_btn.setIcon(qta.icon("fa5s.times", color="white"))
            style_button(remove_btn, variant="danger", size="icon")
            remove_btn.clicked.connect(lambda checked, r=i: self.remove_cart_item(r))
            
            # Point: "in table in action buttons macke background white, not for buttons"
            container = QFrame()
            container.setStyleSheet("background: none; border: none;")
            c_layout = QHBoxLayout(container)
            c_layout.setContentsMargins(2, 2, 2, 2)
            c_layout.addWidget(remove_btn)
            c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cart_table.setCellWidget(i, 7, container)
            
        self.cart_table.resizeColumnsToContents()
        self.cart_table.resizeRowsToContents()
        self.cart_table.blockSignals(False)
        self.update_totals()

    def remove_cart_item(self, row):
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self.refresh_table()

    def update_totals(self):
        subtotal = sum(item['price'] * item['qty'] for item in self.cart)
        discount = 0
        try:
            discount = float(self.discount_input.text() or 0)
        except: pass
        
        total = max(0, subtotal - discount)
        self.total_label.setText(f"{lang_manager.get('total')}: {lang_manager.localize_digits(f'{total:,.2f}')} AFN")

    def process_payment(self, method):
        if not self.cart: return
        subtotal = sum(item['price'] * item['qty'] for item in self.cart)
        discount = 0
        try: discount = float(self.discount_input.text() or 0)
        except: pass
        total = max(0, subtotal - discount)
        
        if method == "CREDIT":
            # Point: "if default customer is selected as walking customer... with each refresh"
            # Point: "if id is selected in sale window it should be calculated into loan window without asking for security progress"
            # Point: "Credit sale... open a security window where it takes customer photo, ID card photo, and contact number, along with address"
            
            if self.selected_customer_id == 1:
                QMessageBox.warning(self, "Invalid", "Walking Customer cannot have credit sales.")
                return
            
            # Check Credit Limit and KYC
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name_en, home_address, photo, id_card_photo, loan_limit, balance, loan_enabled FROM customers WHERE id = ?", (self.selected_customer_id,))
                cust = cursor.fetchone()
                
                # Check Loan Limit
                new_balance = (cust['balance'] or 0) + total
                loan_limit = cust['loan_limit'] or 0
                if cust['loan_enabled'] and new_balance > loan_limit:
                    QMessageBox.warning(self, "Limit Exceeded", 
                        f"Customer {cust['name_en']} is not allowed to exceed the loan limit of {loan_limit:,.2f}.\n"
                        f"Current Balance: {cust['balance']:,.2f}\n"
                        f"Attempted Sale: {total:,.2f}\n"
                        f"New Balance would be: {new_balance:,.2f}")
                    return

                if not cust['home_address'] or not cust['photo'] or not cust['id_card_photo']:
                    # Security registration required
                    kyc = CreditKYCDialog(self, cust['name_en'])
                    if kyc.exec():
                        data = kyc.get_data()
                        # Update customer with KYC info
                        cursor.execute("""
                            UPDATE customers 
                            SET home_address = ?, photo = ?, id_card_photo = ?, phone = ? 
                            WHERE id = ?
                        """, (data['address'], data['photo'], data['id_photo'], data['phone'], self.selected_customer_id))
                        conn.commit()
                    else:
                        return # Cancelled sale

        invoice_num = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sales (invoice_number, user_id, customer_id, total_amount, payment_type, uuid)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (invoice_num, self.current_user['id'], self.selected_customer_id, total, method, str(uuid.uuid4())))
                sale_id = cursor.lastrowid
                
                for item in self.cart:
                    cursor.execute("""
                        INSERT INTO sale_items (sale_id, product_id, barcode, product_name, quantity, unit_price, total_price, uuid)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (sale_id, item['id'], item['barcode'], item['name'], item['qty'], item['price'], item['price']*item['qty'], str(uuid.uuid4())))
                    cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE product_id = ?", (item['qty'], item['id']))
                
                if method == "CREDIT":
                    cursor.execute("UPDATE customers SET balance = balance + ? WHERE id = ?", (total, self.selected_customer_id))
                    cursor.execute("INSERT INTO loans (customer_id, sale_id, loan_amount, status) VALUES (?, ?, ?, 'PENDING')",
                                 (self.selected_customer_id, sale_id, total))
                
                conn.commit()

            # Ask for bill printing after successful sale
            self.print_sale_bill(sale_id, invoice_num, total, method)
            
            # Auto update bill number display for next sale
            self.load_next_bill_number()

            QMessageBox.information(self, "Success", f"Sale completed: {invoice_num}")
            self.clear_cart()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def print_sale_bill(self, sale_id, invoice_num, total, method):
        """Ask user if they want to print the bill after sale completion"""
        reply = QMessageBox.question(
            self, "Print Bill",
            f"Sale completed successfully!\nInvoice: {invoice_num}\nAmount: {total:,.2f} AFN\n\nWould you like to print the bill?",
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
    
    def load_next_bill_number(self):
        """Load and display next bill number"""
        try:
            with db_manager.get_connection() as conn:
                last_bill = conn.execute(
                    "SELECT invoice_number FROM sales ORDER BY id DESC LIMIT 1"
                ).fetchone()
                
                if last_bill:
                    # Extract number and increment
                    try:
                        last_num = int(last_bill['invoice_number'].split('-')[-1])
                        next_num = last_num + 1
                    except:
                        next_num = 1
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
                    f"Reprint Bill: {last_sale['invoice_number']}\nAmount: {last_sale['total_amount']:.2f} AFN?",
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

    def clear_cart(self):
        self.cart = []
        self.discount_input.clear()
        self.refresh_table()
