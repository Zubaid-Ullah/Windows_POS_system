from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QGroupBox,
                             QPushButton, QLabel, QHeaderView, QMessageBox, QTableWidgetItem, QLineEdit, QDialog,
                             QInputDialog, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.database.db_manager import db_manager

class PharmacyLoanView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Search / Filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customer name...")
        self.search_input.setMinimumHeight(55)
        self.search_input.textChanged.connect(self.load_loans)
        layout.addWidget(self.search_input)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Customer", "Total Loan", "Balance", "Status", "Actions"])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        
        self.load_loans()

    def load_loans(self):
        self.table.setRowCount(0)
        search = self.search_input.text().strip()
        try:
            with db_manager.get_pharmacy_connection() as conn:
                query = """
                    SELECT l.*, c.name as customer_name, c.phone
                    FROM pharmacy_loans l
                    JOIN pharmacy_customers c ON l.customer_id = c.id
                    WHERE l.status != 'COMPLETED'
                """
                params = []
                if search:
                    query += " AND c.name LIKE ?"
                    params = [f"%{search}%"]
                
                rows = conn.execute(query, params).fetchall()
                for i, row in enumerate(rows):
                    self.table.insertRow(i)
                    self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                    self.table.setItem(i, 1, QTableWidgetItem(f"{row['customer_name']} ({row['phone']})"))
                    self.table.setItem(i, 2, QTableWidgetItem(f"{row['total_amount']:,.2f} AFN"))
                    self.table.setItem(i, 3, QTableWidgetItem(f"{row['balance']:,.2f} AFN"))
                    self.table.setItem(i, 4, QTableWidgetItem(row['status']))
                    
                    actions = QWidget()
                    act_layout = QHBoxLayout(actions)
                    act_layout.setContentsMargins(0,0,0,0)
                    act_layout.setSpacing(5)

                    pay_btn = QPushButton("Pay")
                    style_button(pay_btn, variant="info", size="small")
                    pay_btn.clicked.connect(lambda ch, r=row: self.receive_payment(r))
                    
                    view_btn = QPushButton("Details")
                    style_button(view_btn, variant="outline", size="small")
                    view_btn.clicked.connect(lambda ch, cid=row['customer_id'], name=row['customer_name']: self.show_visual_details(cid, name))

                    act_layout.addWidget(pay_btn)
                    act_layout.addWidget(view_btn)
                    self.table.setCellWidget(i, 5, actions)
        except Exception as e:
            print(f"Error loading loans: {e}")

    def show_visual_details(self, customer_id, name):
        try:
            with db_manager.get_pharmacy_connection() as conn:
                row = conn.execute("SELECT * FROM pharmacy_customers WHERE id=?", (customer_id,)).fetchone()
                if not row:
                    QMessageBox.warning(self, "Error", "Customer details not found")
                    return
                
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Customer Information - {name}")
                dialog.setMinimumWidth(700)
                l = QVBoxLayout(dialog)

                # Data Section
                data_gb = QGroupBox("Basic Information")
                data_layout = QFormLayout(data_gb)
                data_layout.addRow("<b>Full Name:</b>", QLabel(row['name']))
                data_layout.addRow("<b>Phone:</b>", QLabel(row['phone']))
                data_layout.addRow("<b>Address:</b>", QLabel(row['address'] or "N/A"))
                
                balance_lbl = QLabel(f"<b>{row['balance']:,.2f} AFN</b>")
                balance_lbl.setStyleSheet("color: #ef4444; font-size: 16px;" if row['balance'] > 0 else "color: #10b981;")
                data_layout.addRow("<b>Current Balance:</b>", balance_lbl)
                
                loan_status = "Enabled" if row['loan_enabled'] else "Disabled"
                data_layout.addRow("<b>Loan Feature:</b>", QLabel(loan_status))
                data_layout.addRow("<b>Loan Limit:</b>", QLabel(f"{row['loan_limit']:,.2f} AFN"))
                l.addWidget(data_gb)

                img_layout = QHBoxLayout()
                
                # Photo
                photo_v = QVBoxLayout()
                photo_img = QLabel()
                photo_img.setFixedSize(300, 300)
                photo_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                photo_img.setStyleSheet("border: 2px solid #3b82f633; border-radius: 8px; background: #f8fafc;")
                if row['kyc_photo']:
                    pix = QPixmap(row['kyc_photo'])
                    if not pix.isNull(): photo_img.setPixmap(pix.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    else: photo_img.setText("Photo File Missing")
                else: photo_img.setText("No Photo")
                photo_v.addWidget(QLabel("<b>Customer Photo:</b>"))
                photo_v.addWidget(photo_img)
                img_layout.addLayout(photo_v)
                
                # ID
                id_v = QVBoxLayout()
                id_img = QLabel()
                id_img.setFixedSize(300, 300)
                id_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                id_img.setStyleSheet("border: 2px solid #3b82f633; border-radius: 8px; background: #f8fafc;")
                if row['kyc_id_card']:
                    pix_id = QPixmap(row['kyc_id_card'])
                    if not pix_id.isNull(): id_img.setPixmap(pix_id.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    else: id_img.setText("ID File Missing")
                else: id_img.setText("No ID")
                id_v.addWidget(QLabel("<b>ID Card / Document:</b>"))
                id_v.addWidget(id_img)
                img_layout.addLayout(id_v)
                
                l.addLayout(img_layout)
                close_btn = QPushButton("Close Details")
                style_button(close_btn, variant="outline")
                close_btn.clicked.connect(dialog.accept)
                l.addWidget(close_btn)
                dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def receive_payment(self, loan_row):
        # Use simple input dialog for payment amount
        
        amount, ok = QInputDialog.getDouble(self, "Receive Payment", 
                                            f"Enter amount received from {loan_row['customer_name']}:", 
                                            loan_row['balance'], 0, loan_row['balance'], 2)
        if ok and amount > 0:
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    # Update loan balance
                    new_balance = loan_row['balance'] - amount
                    status = 'PAID' if new_balance <= 0 else 'PARTIAL'
                    if new_balance <= 0: status = 'COMPLETED'
                    
                    conn.execute("UPDATE pharmacy_loans SET balance=?, status=? WHERE id=?", 
                                 (new_balance, status, loan_row['id']))
                    
                    # Update customer balance
                    conn.execute("UPDATE pharmacy_customers SET balance = balance - ? WHERE id=?", 
                                 (amount, loan_row['customer_id']))
                    
                    # Record payment in a history table if exists, or just log
                    conn.execute("""
                        INSERT INTO pharmacy_payments (loan_id, customer_id, amount, payment_method)
                        VALUES (?, ?, ?, ?)
                    """, (loan_row['id'], loan_row['customer_id'], amount, 'CASH'))
                    
                    conn.commit()
                
                QMessageBox.information(self, "Success", f"Payment of ${amount:,.2f} received.")
                self.load_loans()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
