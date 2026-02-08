from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox, QLineEdit, QInputDialog, QDialog, QScrollArea, QFrame, QListWidget, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
import qtawesome as qta
import os
from src.core.localization import lang_manager
from src.database.db_manager import db_manager
from src.core.auth import Auth
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button

class LoanView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = Auth.get_current_user()
        self.search_result_customers = []
        self.init_ui()
        self.load_loans()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QFrame()
        self.container.setObjectName("card")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Search Bar (Point: "search bar should work with customer full name")
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customer by full name for loan details...")
        self.search_input.setFixedHeight(35)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Phone", "Balance", "History/Ledger", "KYC Docs", "Actions"
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        main_layout.addWidget(self.container)

    def on_search_text_changed(self, text):
        if not text.strip():
            self.load_loans()
            return
        
        from src.core.blocking_task_manager import task_manager
        
        def fetch_search():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM customers WHERE name_en LIKE ? AND balance > 0 AND is_active = 1", (f"%{text}%",))
                    return cursor.fetchall()
            except:
                return []

        def on_finished(results):
            self.search_result_customers = results
            self.populate_table(results)

        task_manager.run_task(fetch_search, on_finished=on_finished)

    def load_loans(self):
        from src.core.blocking_task_manager import task_manager
        
        def fetch_data():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM customers WHERE balance > 0 AND is_active = 1")
                    return cursor.fetchall()
            except:
                return []

        def on_finished(customers):
            self.populate_table(customers)

        task_manager.run_task(fetch_data, on_finished=on_finished)

    def populate_table(self, customers):
        self.table.setRowCount(0)
        lang_col = f'name_{lang_manager.current_lang}'
        for i, row in enumerate(customers):
            c = dict(row) if not isinstance(row, dict) else row
            name = c.get(lang_col) or c['name_en']
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(c['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(name))
            self.table.setItem(i, 2, QTableWidgetItem(c['phone'] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(f"{c['balance']:.2f}"))
            
            # Ledger Button
            ledger_btn = QPushButton("Ledger")
            style_button(ledger_btn, variant="info")
            ledger_btn.clicked.connect(lambda checked, cid=c['id'], nm=name: self.view_ledger(cid, nm))
            self.table.setCellWidget(i, 4, ledger_btn)

            # KYC Button
            kyc_btn = QPushButton("View KYC")
            style_button(kyc_btn, variant="secondary")
            kyc_btn.clicked.connect(lambda checked, cid=c['id']: self.view_kyc(cid))
            self.table.setCellWidget(i, 5, kyc_btn)

            # Pay Button
            pay_btn = QPushButton("Pay")
            style_button(pay_btn, variant="success")
            pay_btn.clicked.connect(lambda checked, cid=c['id']: self.make_payment(cid))
            self.table.setCellWidget(i, 6, pay_btn)

    def make_payment(self, cid):
        amount, ok = QInputDialog.getDouble(self, "Payment Received", "Enter amount to settle:", min=0.01)
        if ok and amount > 0:
            from src.core.blocking_task_manager import task_manager
            
            def run_payment():
                remaining = amount
                try:
                    from datetime import datetime
                    with db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # FIFO Loan Settlement Logic
                        cursor.execute("""
                            SELECT id, loan_amount, paid_amount 
                            FROM loans 
                            WHERE customer_id = ? AND status = 'PENDING' 
                            ORDER BY created_at ASC
                        """, (cid,))
                        pending_loans = cursor.fetchall()
                        
                        for loan in pending_loans:
                            if remaining <= 0: break
                            loan_id = loan['id']
                            loan_rem = loan['loan_amount'] - loan['paid_amount']
                            
                            if remaining >= loan_rem:
                                cursor.execute("UPDATE loans SET paid_amount = loan_amount, status = 'PAID' WHERE id = ?", (loan_id,))
                                remaining -= loan_rem
                            else:
                                cursor.execute("UPDATE loans SET paid_amount = paid_amount + ? WHERE id = ?", (remaining, loan_id))
                                remaining = 0

                        cursor.execute("UPDATE customers SET balance = MAX(0, balance - ?) WHERE id = ?", (amount, cid))
                        
                        cursor.execute("""
                            INSERT INTO customer_payments (customer_id, amount, payment_method, reference_number)
                            VALUES (?, ?, 'CASH', ?)
                        """, (cid, amount, f"Settle-{datetime.now().strftime('%Y%m%d%H%M')}") )

                        conn.commit()
                    return {"success": True}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            def on_finished(result):
                if result['success']:
                    QMessageBox.information(self, lang_manager.get("success"), lang_manager.get("payment_received"))
                    self.load_loans()
                else:
                    QMessageBox.critical(self, lang_manager.get("error"), f"{lang_manager.get('error')}: {result['error']}")

            task_manager.run_task(run_payment, on_finished=on_finished)

    def view_ledger(self, cid, name):
        from src.core.blocking_task_manager import task_manager
        
        def fetch_ledger():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 'SALE' as type, s.created_at, s.total_amount as debit, 0 as credit,
                        (SELECT GROUP_CONCAT(product_name, ', ') FROM sale_items WHERE sale_id = s.id) as details
                        FROM sales s WHERE customer_id = ? AND payment_type = 'CREDIT'
                        UNION ALL
                        SELECT 'PAYMENT' as type, created_at, 0 as debit, amount as credit, 'Cash Payment' as details
                        FROM customer_payments WHERE customer_id = ?
                        ORDER BY created_at ASC
                    """, (cid, cid))
                    return [dict(row) for row in cursor.fetchall()]
            except:
                return []

        def on_finished(transactions):
            dialog = CustomerLedgerDialog(name, transactions, self)
            dialog.exec()

        task_manager.run_task(fetch_ledger, on_finished=on_finished)

    def view_kyc(self, cid):
        from src.core.blocking_task_manager import task_manager
        
        def fetch_kyc():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM customers WHERE id = ?", (cid,))
                    row = cursor.fetchone()
                    return dict(row) if row else None
            except:
                return None

        def on_finished(cust):
            if not cust: return
            if not cust['photo'] and not cust['id_card_photo']:
                QMessageBox.warning(self, lang_manager.get("no_records"), lang_manager.get("no_kyc_found"))
                return
                
            dialog = KYCViewerDialog(cust, self)
            dialog.exec()

        task_manager.run_task(fetch_kyc, on_finished=on_finished)

class CustomerLedgerDialog(QDialog):
    def __init__(self, name, transactions, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Financial Ledger: {name}")
        self.setFixedSize(850, 550)
        self.transactions = transactions
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Date", "Action", "Details", "Debit (+)", "Credit (-)", "Balance"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        balance = 0
        for i, tx in enumerate(self.transactions):
            self.table.insertRow(i)
            debit = tx['debit'] or 0
            credit = tx['credit'] or 0
            balance += debit - credit
            
            self.table.setItem(i, 0, QTableWidgetItem(lang_manager.localize_digits(str(tx['created_at']))))
            self.table.setItem(i, 1, QTableWidgetItem(tx['type']))
            self.table.setItem(i, 2, QTableWidgetItem(tx['details'] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(lang_manager.localize_digits(f"{debit:.2f}") if debit > 0 else ""))
            self.table.setItem(i, 4, QTableWidgetItem(lang_manager.localize_digits(f"{credit:.2f}") if credit > 0 else ""))
            
            bal_item = QTableWidgetItem(lang_manager.localize_digits(f"{balance:.2f}"))
            bal_item.setForeground(Qt.GlobalColor.red if balance > 0 else Qt.GlobalColor.darkGreen)
            self.table.setItem(i, 5, bal_item)
            
        layout.addWidget(self.table)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

class KYCViewerDialog(QDialog):
    def __init__(self, customer, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"KYC Documents: {customer['name_en']}")
        self.setFixedSize(600, 500)
        self.customer = customer
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        info = QLabel(f"<b>Name:</b> {self.customer['name_en']}<br><b>Phone:</b> {self.customer['phone']}<br><b>Address:</b> {self.customer.get('home_address', 'N/A')}")
        layout.addWidget(info)
        
        img_layout = QHBoxLayout()
        # Photo
        p_box = QVBoxLayout()
        p_box.addWidget(QLabel("Customer Photo:"))
        p_lbl = QLabel("No Image")
        if self.customer['photo'] and os.path.exists(self.customer['photo']):
            p_lbl.setPixmap(QPixmap(self.customer['photo']).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        p_box.addWidget(p_lbl)
        img_layout.addLayout(p_box)
        
        # ID
        i_box = QVBoxLayout()
        i_box.addWidget(QLabel("ID Photo:"))
        i_lbl = QLabel("No Image")
        if self.customer['id_card_photo'] and os.path.exists(self.customer['id_card_photo']):
            i_lbl.setPixmap(QPixmap(self.customer['id_card_photo']).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        i_box.addWidget(i_lbl)
        img_layout.addLayout(i_box)
        
        layout.addLayout(img_layout)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
