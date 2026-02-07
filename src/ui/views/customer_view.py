import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QComboBox, QMessageBox, QInputDialog, QTextEdit)
from PyQt6.QtCore import Qt
import qtawesome as qta
import uuid
from src.core.localization import lang_manager
from src.database.db_manager import db_manager
from src.core.auth import Auth
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button

class CustomerDialog(QDialog):
    def __init__(self, customer=None):
        super().__init__()
        self.customer = customer
        self.setWindowTitle("Customer Details & KYC")
        self.setMinimumWidth(500)
        self.photo_path = None
        self.id_photo_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("Customer Information & KYC")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1b2559; margin-bottom: 10px;")
        layout.addWidget(header)

        # Basic Information Group
        basic_group = QFrame()
        basic_group.setObjectName("customer_basic_group")
        basic_group.setStyleSheet("""
            QFrame#customer_basic_group {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e0e5f2;
            }
        """)
        basic_layout = QVBoxLayout(basic_group)
        basic_layout.setContentsMargins(15, 15, 15, 15)

        basic_title = QLabel("Basic Information")
        basic_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4318ff; margin-bottom: 10px;")
        basic_layout.addWidget(basic_title)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_en = QLineEdit()
        self.name_en.setPlaceholderText("Enter customer's full name")
        self.name_en.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Enter phone number")
        self.phone.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")

        self.address = QTextEdit()
        self.address.setFixedHeight(80)
        self.address.setPlaceholderText("Enter customer's home address")
        self.address.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; font-size: 13px; padding: 4px;")

        form.addRow("Full Name:", self.name_en)
        form.addRow("Contact Number:", self.phone)
        form.addRow("Home Address:", self.address)

        basic_layout.addLayout(form)
        layout.addWidget(basic_group)

        # Loan Information Group
        loan_group = QFrame()
        loan_group.setObjectName("customer_loan_group")
        loan_group.setStyleSheet("""
            QFrame#customer_loan_group {
                background-color: #fff8f0;
                border-radius: 8px;
                border: 1px solid #ffe4c4;
            }
        """)
        loan_layout = QVBoxLayout(loan_group)
        loan_layout.setContentsMargins(15, 15, 15, 15)

        loan_title = QLabel("Credit & Loan Settings")
        loan_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff9800; margin-bottom: 10px;")
        loan_layout.addWidget(loan_title)

        loan_form = QFormLayout()
        loan_form.setSpacing(12)

        self.loan_enabled = QComboBox()
        self.loan_enabled.setMinimumWidth(100)
        self.loan_enabled.addItems(["No", "Yes"])
        self.loan_enabled.setStyleSheet("padding: 6px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")

        self.loan_limit = QLineEdit()
        self.loan_limit.setPlaceholderText("Maximum loan amount")
        self.loan_limit.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")

        loan_form.addRow("Allow Credit Sales:", self.loan_enabled)
        loan_form.addRow("Credit Limit (AFN):", self.loan_limit)

        loan_layout.addLayout(loan_form)
        layout.addWidget(loan_group)

        if self.customer:
            self.name_en.setText(self.customer['name_en'])
            self.phone.setText(self.customer['phone'] or "")
            self.address.setPlainText(self.customer.get('home_address', ""))
            self.loan_enabled.setCurrentIndex(1 if self.customer['loan_enabled'] else 0)
            self.loan_limit.setText(str(self.customer['loan_limit'] or 0))
            self.photo_path = self.customer.get('photo')
            self.id_photo_path = self.customer.get('id_card_photo')
        
        # Security/KYC Section
        layout.addWidget(QLabel("<b>Security Verification (KYC)</b>"))
        kyc_box = QHBoxLayout()
        
        self.photo_status = QLabel("Photo: " + ("Registered" if self.photo_path else "Pending"))
        self.id_status = QLabel("ID Card: " + ("Registered" if self.id_photo_path else "Pending"))
        
        take_photo_btn = QPushButton("Take Photo")
        take_photo_btn.clicked.connect(self.take_photo)
        
        take_id_btn = QPushButton("Take ID Photo")
        take_id_btn.clicked.connect(self.take_id_photo)
        
        kyc_box.addWidget(self.photo_status)
        kyc_box.addWidget(take_photo_btn)
        kyc_box.addSpacing(20)
        kyc_box.addWidget(self.id_status)
        kyc_box.addWidget(take_id_btn)
        layout.addLayout(kyc_box)
        
        btns = QHBoxLayout()
        save_btn = QPushButton("Save Customer")
        style_button(save_btn, variant="success")
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn = QPushButton("Cancel")
        style_button(cancel_btn, variant="secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def take_photo(self):
        print("DEBUG: take_photo button clicked")
        from src.utils.camera import capture_image
        path = os.path.join("data", "kyc", f"cust_{uuid.uuid4()}.jpg")
        success, msg = capture_image(path)
        if success:
            self.photo_path = path
            self.photo_status.setText("Photo: Captured ✓")
            self.photo_status.setStyleSheet("color: #05cd99; font-weight: bold;")
        else:
            if msg: QMessageBox.warning(self, "Camera Error", msg)

    def take_id_photo(self):
        from src.utils.camera import capture_image
        path = os.path.join("data", "kyc", f"id_{uuid.uuid4()}.jpg")
        success, msg = capture_image(path)
        if success:
            self.id_photo_path = path
            self.id_status.setText("ID Card: Captured ✓")
            self.id_status.setStyleSheet("color: #05cd99; font-weight: bold;")
        else:
            if msg: QMessageBox.warning(self, "Camera Error", msg)

    def validate_and_accept(self):
        if not self.name_en.text() or not self.phone.text():
            QMessageBox.warning(self, "Required Fields", "Name and Contact Number are mandatory.")
            return
        self.accept()

    def get_data(self):
        try:
            val = float(self.loan_limit.text() or 0)
        except: val = 0
        return {
            'name_en': self.name_en.text(),
            'phone': self.phone.text(),
            'address': self.address.toPlainText(),
            'loan_enabled': self.loan_enabled.currentIndex(),
            'loan_limit': val,
            'photo': self.photo_path,
            'id_card_photo': self.id_photo_path
        }

class CustomerView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = Auth.get_current_user()
        self.is_admin = self.current_user['role_name'] in ['Admin', 'Manager', 'SuperAdmin']
        self.init_ui()
        self.load_customers()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QFrame()
        self.container.setObjectName("card")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customer by name or phone...")
        self.search_input.setFixedHeight(35)
        self.search_input.textChanged.connect(self.load_customers)
        header.addWidget(self.search_input)
        
        self.add_btn = QPushButton(" Add New Customer")
        style_button(self.add_btn, variant="primary")
        self.add_btn.setIcon(qta.icon("fa5s.user-plus", color="white"))
        self.add_btn.clicked.connect(self.add_customer)
        if not self.is_admin:
            self.add_btn.hide()
        header.addWidget(self.add_btn)
        
        layout.addLayout(header)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Full Name", "Contact", "Balance", "Actions"
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Name stretches
        self.table.setColumnWidth(4, 200) # Actions fixed
        layout.addWidget(self.table)
        
        main_layout.addWidget(self.container)

    def load_customers(self):
        from src.core.blocking_task_manager import task_manager
        search = self.search_input.text().strip()
        
        def fetch_data():
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM customers WHERE is_active = 1"
                params = []
                if search:
                    query += " AND (name_en LIKE ? OR phone LIKE ?)"
                    params = [f"%{search}%", f"%{search}%"]
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

        def on_loaded(customers):
            self.table.setRowCount(0)
            for i, c in enumerate(customers):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(c['id'])))
                self.table.setItem(i, 1, QTableWidgetItem(c['name_en']))
                self.table.setItem(i, 2, QTableWidgetItem(c['phone'] or ""))
                
                bal_item = QTableWidgetItem(f"{c['balance']:.2f}")
                if c['balance'] > 0:
                    bal_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(i, 3, bal_item)
                
                actions = QWidget()
                act_layout = QHBoxLayout(actions)
                act_layout.setContentsMargins(2, 2, 2, 2)
                
                pay_btn = QPushButton()
                style_button(pay_btn, variant="success", size="icon")
                pay_btn.setIcon(qta.icon("fa5s.money-bill-wave", color="white"))
                pay_btn.clicked.connect(lambda checked, cid=c['id']: self.make_payment(cid))
                
                if self.is_admin:
                    edit_btn = QPushButton()
                    style_button(edit_btn, variant="info", size="icon")
                    edit_btn.setIcon(qta.icon("fa5s.edit", color="white"))
                    edit_btn.clicked.connect(lambda checked, cust=c: self.edit_customer(cust))
                    
                    del_btn = QPushButton()
                    style_button(del_btn, variant="danger", size="icon")
                    del_btn.setIcon(qta.icon("fa5s.trash", color="white"))
                    del_btn.clicked.connect(lambda checked, cid=c['id']: self.delete_customer(cid))
                    
                    act_layout.addWidget(pay_btn)
                    act_layout.addWidget(edit_btn)
                    act_layout.addWidget(del_btn)
                else:
                    act_layout.addWidget(pay_btn)
                
                self.table.setCellWidget(i, 4, actions)
            
            # Auto-fit columns to content once the table is populated
            self.table.resizeColumnsToContents()
            # Restore stretch and fixed action column
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.table.setColumnWidth(4, 200)

        task_manager.run_task(fetch_data, on_finished=on_loaded)

    def add_customer(self):
        dialog = CustomerDialog()
        if dialog.exec():
            data = dialog.get_data()
            if not data: return
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO customers (name_en, phone, loan_enabled, loan_limit, home_address, photo, id_card_photo)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data['name_en'], data['phone'], data['loan_enabled'], data['loan_limit'], data['address'], data['photo'], data['id_card_photo']))
                customer_id = cursor.lastrowid
                cursor.execute("INSERT INTO audit_logs (user_id, action, table_name, record_id, details) VALUES (?, ?, ?, ?, ?)",
                             (self.current_user['id'], 'ADD_CUSTOMER', 'customers', customer_id, f"Added customer {data['name_en']}"))
                conn.commit()
            self.load_customers()
            # If SalesView exists, refresh its customer list
            # Usually handled by a global refresh signal or in main_window

    def edit_customer(self, customer):
        dialog = CustomerDialog(customer)
        if dialog.exec():
            data = dialog.get_data()
            if not data: return
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE customers SET name_en=?, phone=?, loan_enabled=?, loan_limit=?, home_address=?, photo=?, id_card_photo=?
                    WHERE id=?
                """, (data['name_en'], data['phone'], data['loan_enabled'], data['loan_limit'], data['address'], data['photo'], data['id_card_photo'], customer['id']))
                conn.commit()
            self.load_customers()

    def delete_customer(self, cid):
        if cid == 1:
            QMessageBox.warning(self, "Reserved", "Default walking customer cannot be deleted.")
            return
        reply = QMessageBox.question(self, 'Confirm Delete', "Deactivate this customer?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE customers SET is_active = 0 WHERE id = ?", (cid,))
                conn.commit()
            self.load_customers()

    def make_payment(self, cid):
        amount, ok = QInputDialog.getDouble(self, "Payment", "Enter amount received:", 0, 0, 1000000, 2)
        if ok and amount > 0:
            try:
                from datetime import datetime
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE customers SET balance = MAX(0, balance - ?) WHERE id = ?", (amount, cid))
                    cursor.execute("INSERT INTO customer_payments (customer_id, amount, payment_method, reference_number) VALUES (?, ?, 'CASH', ?)",
                                 (cid, amount, f"Settle-{datetime.now().strftime('%Y%m%d%H%M')}"))
                    conn.commit()
                QMessageBox.information(self, "Success", "Payment recorded.")
                self.load_customers()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
