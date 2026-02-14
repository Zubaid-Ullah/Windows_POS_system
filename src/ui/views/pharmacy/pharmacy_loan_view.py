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
        self._current_request_id = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Search / Filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(lang_manager.get("search") + " " + lang_manager.get("customer") + "...")
        self.search_input.setMinimumHeight(55)
        self.search_input.setMinimumHeight(55)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        layout.addWidget(self.search_input)

        from PyQt6.QtCore import QTimer
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300) # 300ms debounce
        self.search_timer.timeout.connect(self._do_load_loans)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID", lang_manager.get("customer"), lang_manager.get("total"), 
            lang_manager.get("balance"), lang_manager.get("status"), lang_manager.get("actions")
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_loans()

    def on_search_text_changed(self, text):
        self.search_timer.start()

    def load_loans(self):
        self._do_load_loans()

    def _do_load_loans(self):
        search = self.search_input.text().strip()
        from src.core.blocking_task_manager import task_manager
        
        # Request-id cancellation: discard stale results from fast typing
        self._current_request_id += 1
        request_id = self._current_request_id
        
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
                    return {"success": True, "rows": [dict(r) for r in rows], "request_id": request_id}
            except Exception as e:
                return {"success": False, "error": str(e), "request_id": request_id}

        def on_finished(result):
            # Discard stale result if a newer request was issued
            if result.get("request_id") != self._current_request_id:
                return
            if not result["success"]:
                print(f"Error loading loans: {result['error']}")
                return
            
            self.table.setUpdatesEnabled(False)
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
            
            self.table.setUpdatesEnabled(True)
            
            # Autofit logic
            self.table.resizeColumnsToContents()
            if self.table.horizontalHeader().length() < self.table.width():
                self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            else:
                self.table.horizontalHeader().setStretchLastSection(True)

        task_manager.run_task(do_load, on_finished=on_finished)


    def show_visual_details(self, customer_id, name=None):
        from src.core.blocking_task_manager import task_manager
        
        def do_fetch():
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    row = conn.execute("SELECT * FROM pharmacy_customers WHERE id=?", (customer_id,)).fetchone()
                    if row:
                        return {"success": True, "row": dict(row)}
                    else:
                        return {"success": False, "error": lang_manager.get("customer_not_found")}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(result):
            if not result["success"]:
                QMessageBox.warning(self, lang_manager.get("error"), result["error"])
                return
            
            row = result["row"]
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
            
            term_limit = lang_manager.get('reorder_level').split()[1] if ' ' in lang_manager.get('reorder_level') else 'Limit'
            data_layout.addRow(f"<b>{term_limit}:</b>", QLabel(f"{row['loan_limit']:,.2f} AFN"))
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

        task_manager.run_task(do_fetch, on_finished=on_finished)

    def receive_payment(self, loan_row):
        # Use simple input dialog for payment amount
        
        # UI Input on Main Thread
        current_balance = loan_row['balance']
        # Default to full payment if positive balance, else 0
        default_val = current_balance if current_balance > 0 else 0
        
        amount, ok = QInputDialog.getDouble(self, lang_manager.get("receive_payment"), 
                                            f"{lang_manager.get('amount')}:", 
                                            default_val, 0, 1000000, 2)
        if ok and amount > 0:
            from src.core.blocking_task_manager import task_manager
            
            # Capture data for thread
            loan_id = loan_row['id']
            customer_id = loan_row['customer_id']
            # We need the fresh balance in case it changed, but usually row is fresh enough. 
            # Ideally do read-modify-write in transaction or simple update decrement.
            
            def do_pay():
                try:
                    with db_manager.get_pharmacy_connection() as conn:
                        cursor = conn.cursor()
                        
                        # 1. Fetch latest balance AND sale_id to be safe
                        curr_loan = cursor.execute("SELECT balance, sale_id FROM pharmacy_loans WHERE id=?", (loan_id,)).fetchone()
                        if not curr_loan:
                            return {"success": False, "error": "Loan record not found"}
                        
                        linked_sale_id = curr_loan['sale_id']
                            
                        # 2. Update loan
                        latest_bal = curr_loan['balance']
                        new_balance = latest_bal - amount
                        status = 'PAID' if new_balance <= 0 else 'PARTIAL'
                        if new_balance <= 0: status = 'COMPLETED'
                        
                        cursor.execute("UPDATE pharmacy_loans SET balance=?, status=? WHERE id=?", 
                                     (new_balance, status, loan_id))
                        
                        # 3. Update customer balance
                        cursor.execute("UPDATE pharmacy_customers SET balance = balance - ? WHERE id=?", 
                                     (amount, customer_id))
                        
                        # 4. Record payment (include sale_id for Cash Realized Profit tracking)
                        cursor.execute("""
                            INSERT INTO pharmacy_payments (sale_id, loan_id, customer_id, amount, payment_method)
                            VALUES (?, ?, ?, ?, ?)
                        """, (linked_sale_id, loan_id, customer_id, amount, 'CASH'))
                        
                        conn.commit()
                        return {"success": True, "amount": amount}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            def on_finished(result):
                if result["success"]:
                    QMessageBox.information(self, lang_manager.get("success"), f"{lang_manager.get('payment_received')}: {result['amount']:,.2f} AFN")
                    self.load_loans()
                else:
                    QMessageBox.critical(self, lang_manager.get("error"), result["error"])

            task_manager.run_task(do_pay, on_finished=on_finished)
