from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QDialog, QFormLayout, QDoubleSpinBox)
from PyQt6.QtCore import Qt
import qtawesome as qta
from src.core.localization import lang_manager
from src.database.db_manager import db_manager
from src.core.auth import Auth
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button

class ReturnsView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = Auth.get_current_user()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Search Panel
        search_card = QFrame()
        search_card.setObjectName("card")
        search_layout = QHBoxLayout(search_card)
        
        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText("Enter Invoice Number (e.g. INV-...)")
        self.invoice_input.setFixedHeight(40)
        self.invoice_input.returnPressed.connect(self.find_invoice)
        
        search_btn = QPushButton(" Find Invoice")
        style_button(search_btn, variant="primary")
        search_btn.setIcon(qta.icon("fa5s.search", color="white"))
        search_btn.clicked.connect(self.find_invoice)
        
        search_layout.addWidget(self.invoice_input)
        search_layout.addWidget(search_btn)
        layout.addWidget(search_card)

        # Sale Details Area
        self.details_card = QFrame()
        self.details_card.setObjectName("card")
        self.details_card.hide()
        details_layout = QVBoxLayout(self.details_card)
        
        self.sale_info = QLabel("Sale Info")
        self.sale_info.setStyleSheet("font-weight: bold; font-size: 16px;")
        details_layout.addWidget(self.sale_info)
        
        self.items_table = QTableWidget(0, 5)
        self.items_table.setHorizontalHeaderLabels(["Product", "Sold Qty", "Price", "Returned", "Action"])
        style_table(self.items_table, variant="premium")
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        details_layout.addWidget(self.items_table)
        
        layout.addWidget(self.details_card)
        layout.addStretch()

        self.current_sale = None

    def find_invoice(self):
        inv_num = self.invoice_input.text().strip()
        if not inv_num: return
        
        from src.core.blocking_task_manager import task_manager
        
        def fetch_data():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT s.*, c.name_en as customer_name , c.id as cust_id
                        FROM sales s 
                        LEFT JOIN customers c ON s.customer_id = c.id 
                        WHERE s.invoice_number = ?
                    """, (inv_num,))
                    sale = cursor.fetchone()
                    
                    if not sale:
                        return None
                    
                    cursor.execute("""
                        SELECT si.*, 
                        IFNULL((SELECT SUM(ri.quantity) 
                         FROM return_items ri 
                         JOIN sales_returns sr ON ri.return_id = sr.id 
                         WHERE sr.sale_id = si.sale_id AND ri.product_id = si.product_id), 0) as already_returned
                        FROM sale_items si 
                        WHERE si.sale_id = ?
                    """, (sale['id'],))
                    
                    items = cursor.fetchall()
                    return {"sale": dict(sale), "items": [dict(it) for it in items]}
            except:
                return None

        def on_finished(result):
            if not result:
                QMessageBox.warning(self, lang_manager.get("not_found"), f"{lang_manager.get('no_sale_found_with_invoice')} {inv_num}")
                self.details_card.hide()
                return
            
            self.current_sale = result["sale"]
            sale = result["sale"]
            self.sale_info.setText(f"Invoice: {sale['invoice_number']} | Customer: {sale['customer_name']} | Date: {sale['created_at']}")
            
            items = result["items"]
            self.items_table.setRowCount(0)
            for i, item in enumerate(items):
                self.items_table.insertRow(i)
                self.items_table.setItem(i, 0, QTableWidgetItem(item['product_name']))
                self.items_table.setItem(i, 1, QTableWidgetItem(lang_manager.localize_digits(str(item['quantity']))))
                self.items_table.setItem(i, 2, QTableWidgetItem(lang_manager.localize_digits(f"{item['total_price']/item['quantity']:.2f}")))
                self.items_table.setItem(i, 3, QTableWidgetItem(lang_manager.localize_digits(str(item['already_returned']))))
                
                if item['already_returned'] < item['quantity']:
                    ret_btn = QPushButton("Return")
                    style_button(ret_btn, variant="warning", size="small")
                    ret_btn.clicked.connect(lambda checked, it=dict(item): self.process_item_return(it))
                    
                    container = QFrame()
                    container.setStyleSheet("background: none; border: none;")
                    c_layout = QHBoxLayout(container)
                    c_layout.setContentsMargins(2, 2, 2, 2)
                    c_layout.addWidget(ret_btn)
                    c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.items_table.setCellWidget(i, 4, container)
                else:
                    self.items_table.setItem(i, 4, QTableWidgetItem("Fully Returned"))
            
            self.details_card.show()

        task_manager.run_task(fetch_data, on_finished=on_finished)

    def process_item_return(self, item):
        max_ret = item['quantity'] - item['already_returned']
        
        # Proper Dialog for Return
        dialog = QDialog(self)
        dialog.setWindowTitle("Return Item")
        d_layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        sb = QDoubleSpinBox()
        sb.setRange(0.01, max_ret)
        sb.setValue(1.0)
        form.addRow(f"Return Qty (Max {max_ret}):", sb)
        
        reason = QLineEdit()
        form.addRow("Reason:", reason)
        
        d_layout.addLayout(form)
        
        btns = QHBoxLayout()
        confirm = QPushButton("Confirm Return")
        style_button(confirm, variant="success")
        confirm.clicked.connect(dialog.accept)
        cancel = QPushButton("Cancel")
        style_button(cancel, variant="secondary")
        cancel.clicked.connect(dialog.reject)
        btns.addWidget(cancel)
        btns.addWidget(confirm)
        d_layout.addLayout(btns)
        
        if dialog.exec():
            ret_qty = sb.value()
            ret_reason = reason.text()
            refund_unit = item['total_price'] / item['quantity']
            total_refund = ret_qty * refund_unit
            
            from src.core.blocking_task_manager import task_manager
            
            def run_return():
                try:
                    with db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        # 1. Create return header
                        cursor.execute("""
                            INSERT INTO sales_returns (sale_id, user_id, reason, refund_amount)
                            VALUES (?, ?, ?, ?)
                        """, (self.current_sale['id'], self.current_user['id'], ret_reason, total_refund))
                        return_id = cursor.lastrowid
                        
                        # 2. Create return item
                        cursor.execute("""
                            INSERT INTO return_items (return_id, product_id, quantity, refund_price)
                            VALUES (?, ?, ?, ?)
                        """, (return_id, item['product_id'], ret_qty, total_refund))
                        
                        # 3. Update Inventory
                        cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE product_id = ?", 
                                     (ret_qty, item['product_id']))
                        
                        # 4. If Credit sale, update customer balance
                        if self.current_sale['payment_type'] == 'CREDIT':
                            cursor.execute("UPDATE customers SET balance = MAX(0, balance - ?) WHERE id = ?",
                                         (total_refund, self.current_sale['cust_id']))
                        
                        # 5. Audit Log
                        cursor.execute("INSERT INTO audit_logs (user_id, action, table_name, record_id, details) VALUES (?, ?, ?, ?, ?)",
                                     (self.current_user['id'], 'RETURN_ITEM', 'sales_returns', return_id, 
                                      f"Returned {ret_qty} of {item['product_name']} from INV {self.current_sale['invoice_number']}"))
                        
                        conn.commit()
                    return {"success": True}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            def on_finished(result):
                if result["success"]:
                    msg = f"{lang_manager.get('successfully_returned')} {lang_manager.localize_digits(ret_qty)} {lang_manager.get('items')}. {lang_manager.get('refund')}: {lang_manager.localize_digits(f'{total_refund:.2f}')} AFN"
                    QMessageBox.information(self, lang_manager.get("success"), msg)
                    self.find_invoice()
                else:
                    QMessageBox.critical(self, lang_manager.get("error"), f"{lang_manager.get('error')}: {result['error']}")

            task_manager.run_task(run_return, on_finished=on_finished)
