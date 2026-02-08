from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QGroupBox,
                             QPushButton, QLabel, QHeaderView, QMessageBox, QTableWidgetItem, QLineEdit, QDialog,
                             QInputDialog, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.database.db_manager import db_manager
from src.core.localization import lang_manager

class PharmacyLoanView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Search / Filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(lang_manager.get("search") + " " + lang_manager.get("customer") + "...")
        self.search_input.setMinimumHeight(55)
        self.search_input.textChanged.connect(self.load_loans)
        layout.addWidget(self.search_input)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID", lang_manager.get("customer"), lang_manager.get("total"), 
            lang_manager.get("balance"), lang_manager.get("status"), lang_manager.get("actions")
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        
        self.load_loans()

    def load_loans(self):
        search = self.search_input.text().strip()
        from src.core.blocking_task_manager import task_manager
        
        def do_load():
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
                    return {"success": True, "rows": [dict(r) for r in rows]}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(result):
            if not result["success"]:
                print(f"Error loading loans: {result['error']}")
                return
                
            self.table.setRowCount(0)
            rows = result["rows"]
            for i, row in enumerate(rows):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                self.table.setItem(i, 1, QTableWidgetItem(row['customer_name'] or lang_manager.get("walk_in_customer")))
                self.table.setItem(i, 2, QTableWidgetItem(f"{row['total_amount']:,.2f}"))
                
                bal_item = QTableWidgetItem(f"{row['balance']:,.2f}")
                if row['balance'] < 0:
                    bal_item.setForeground(Qt.GlobalColor.darkGreen)
                    bal_item.setToolTip(lang_manager.get("customer_has_credit_balance"))
                elif row['balance'] > 0:
                    bal_item.setForeground(Qt.GlobalColor.red)
                
                self.table.setItem(i, 3, bal_item)
                
                status = row['status']
                status_item = QTableWidgetItem(lang_manager.get(status.lower()))
                if status == 'PENDING': status_item.setForeground(Qt.GlobalColor.red)
                else: status_item.setForeground(Qt.GlobalColor.darkGreen)
                self.table.setItem(i, 4, status_item)
                
                actions = QWidget()
                act_layout = QHBoxLayout(actions)
                act_layout.setContentsMargins(0,0,0,0)
                act_layout.setSpacing(5)

                pay_btn = QPushButton(lang_manager.get("pay"))
                style_button(pay_btn, variant="success", size="small")
                pay_btn.clicked.connect(lambda ch, r=row: self.receive_payment(r))
                
                detail_btn = QPushButton(lang_manager.get("details"))
                style_button(detail_btn, variant="info", size="small")
                detail_btn.clicked.connect(lambda ch, cid=row['customer_id'], name=row['customer_name']: self.show_visual_details(cid, name))

                act_layout.addWidget(pay_btn)
                act_layout.addWidget(detail_btn)
                self.table.setCellWidget(i, 5, actions)
            
            # Autofit logic
            self.table.resizeColumnsToContents()
            if self.table.horizontalHeader().length() < self.table.width():
                self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            else:
                self.table.horizontalHeader().setStretchLastSection(True)

        task_manager.run_task(do_load, on_finished=on_finished)


    def show_visual_details(self, customer_id, name=None):
        try:
            with db_manager.get_pharmacy_connection() as conn:
                row = conn.execute("SELECT * FROM pharmacy_customers WHERE id=?", (customer_id,)).fetchone()
                if not row:
                    QMessageBox.warning(self, lang_manager.get("error"), lang_manager.get("customer_not_found"))
                    return
                
                display_name = name or row['name'] or "Unknown"
                dialog = QDialog(self)
                dialog.setWindowTitle(lang_manager.get("customer_info") + f" - {display_name}")
                dialog.setMinimumWidth(700)
                l = QVBoxLayout(dialog)

                # Data Section
                data_gb = QGroupBox(lang_manager.get("basic_info"))
                data_layout = QFormLayout(data_gb)
                data_layout.addRow(f"<b>{lang_manager.get('name')}:</b>", QLabel(row['name']))
                data_layout.addRow(f"<b>{lang_manager.get('phone')}:</b>", QLabel(row['phone']))
                data_layout.addRow(f"<b>{lang_manager.get('address')}:</b>", QLabel(row['address'] or "N/A"))
                
                balance_lbl = QLabel(f"<b>{row['balance']:,.2f} AFN</b>")
                balance_lbl.setStyleSheet("color: #ef4444; font-size: 16px;" if row['balance'] > 0 else "color: #10b981;")
                data_layout.addRow(f"<b>{lang_manager.get('balance')}:</b>", balance_lbl)
                
                loan_status = lang_manager.get("active") if row['loan_enabled'] else "Disabled"
                data_layout.addRow(f"<b>{lang_manager.get('loans')}:</b>", QLabel(loan_status))
                data_layout.addRow(f"<b>{lang_manager.get('reorder_level').split()[1] if ' ' in lang_manager.get('reorder_level') else 'Limit'}:</b>", QLabel(f"{row['loan_limit']:,.2f} AFN"))
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
                photo_v.addWidget(QLabel(f"<b>{lang_manager.get('customer_photo')}:</b>"))
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
                id_v.addWidget(QLabel(f"<b>{lang_manager.get('id_card_photo')}:</b>"))
                id_v.addWidget(id_img)
                img_layout.addLayout(id_v)
                
                l.addLayout(img_layout)
                close_btn = QPushButton(lang_manager.get("close"))
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
                                            loan_row['balance'] if loan_row['balance'] > 0 else 0, 0, 1000000, 2)
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
                
                QMessageBox.information(self, lang_manager.get("success"), f"{lang_manager.get('payment_received')}: {amount:,.2f} AFN")
                self.load_loans()
            except Exception as e:
                QMessageBox.critical(self, lang_manager.get("error"), str(e))
