from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QPushButton, QLabel, QHeaderView, QGroupBox, 
                             QFormLayout, QLineEdit, QComboBox, QMessageBox, QTableWidgetItem, QDoubleSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.database.db_manager import db_manager

class PharmacyReturnsView(QWidget):
    return_processed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Search Invoice
        search_layout = QHBoxLayout()
        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText("Enter Invoice/Sale ID...")
        self.invoice_input.setFixedHeight(55)
        self.search_btn = QPushButton("Load Invoice")
        style_button(self.search_btn, variant="info")
        self.search_btn.clicked.connect(self.load_invoice)
        search_layout.addWidget(self.invoice_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        # Sale Info
        self.sale_info_lbl = QLabel("No invoice loaded")
        self.sale_info_lbl.setStyleSheet("font-size: 16px; color: #64748b; font-weight: 500;")
        layout.addWidget(self.sale_info_lbl)

        # Items Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Product", "Sold Qty", "Price", "Return Qty", "Action", "Confirm"])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_invoice(self):
        sale_id = self.invoice_input.text().strip()
        if not sale_id: return
        
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # Search by invoice_number OR id
                sale = conn.execute("""
                    SELECT s.*, c.name as customer_name 
                    FROM pharmacy_sales s
                    LEFT JOIN pharmacy_customers c ON s.customer_id = c.id
                    WHERE s.invoice_number = ? OR s.id = ?
                """, (sale_id, sale_id)).fetchone()
                
                if not sale:
                    QMessageBox.warning(self, "Not Found", "Invoice not found.")
                    return
                
                self.sale_info_lbl.setText(f"Invoice #{sale['invoice_number']} | Customer: {sale['customer_name'] or 'Walk-in'} | Total: ${sale['total_amount']:,.2f}")
                
                items = conn.execute("""
                    SELECT si.*, p.name_en
                    FROM pharmacy_sale_items si
                    JOIN pharmacy_products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                """, (sale['id'],)).fetchall()
                
                self.table.setRowCount(0)
                for i, item in enumerate(items):
                    self.table.insertRow(i)
                    self.table.setItem(i, 0, QTableWidgetItem(item['name_en']))
                    self.table.setItem(i, 1, QTableWidgetItem(str(item['quantity'])))
                    self.table.setItem(i, 2, QTableWidgetItem(f"{item['unit_price']:.2f}"))
                    
                    qty_input = QDoubleSpinBox()
                    qty_input.setRange(0, item['quantity'])
                    qty_input.setValue(0)
                    self.table.setCellWidget(i, 3, qty_input)
                    
                    action_combo = QComboBox()
                    action_combo.addItems(["RETURN", "REPLACE"])
                    self.table.setCellWidget(i, 4, action_combo)
                    
                    btn = QPushButton("Process")
                    style_button(btn, variant="warning", size="small")
                    btn.clicked.connect(lambda ch, it=item, r=i: self.process_return(it, r))
                    self.table.setCellWidget(i, 5, btn)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def process_return(self, sale_item, row_idx):
        qty_widget = self.table.cellWidget(row_idx, 3)
        action_widget = self.table.cellWidget(row_idx, 4)
        
        qty = qty_widget.value()
        action = action_widget.currentText()
        
        if qty <= 0:
            QMessageBox.warning(self, "Error", "Quantity must be greater than 0")
            return
            
        ok = QMessageBox.question(self, "Confirm", f"Process {action} for {qty} units?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ok != QMessageBox.StandardButton.Yes: return
        
        # Reason dialog
        from PyQt6.QtWidgets import QInputDialog
        reason_text, ok = QInputDialog.getText(self, "Reason", "Enter reason for return/replacement:")
        if not ok: return

        from src.core.pharmacy_auth import PharmacyAuth
        user = PharmacyAuth.get_current_user()
        user_id = user['id'] if user else 1
        
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # 1. Create Return Record
                conn.execute("""
                    INSERT INTO pharmacy_returns (original_sale_id, refund_amount, reason, user_id) 
                    VALUES (?, ?, ?, ?)
                """, (sale_item['sale_id'], qty * sale_item['unit_price'], reason_text, user_id))
                return_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                
                # 2. Add Return Item
                conn.execute("""
                    INSERT INTO pharmacy_return_items (return_id, product_id, quantity, unit_price, action)
                    VALUES (?, ?, ?, ?, ?)
                """, (return_id, sale_item['product_id'], qty, sale_item['unit_price'], action))
                
                # 3. Update Stock (If Return, add back to stock? Or just record?)
                # Requirement says "Update Stock"
                # We need to find which batch to put it back into or just increase general qty if not batch tracked here
                # Better: increase quantity in pharmacy_inventory for the latest batch or same batch?
                # For simplicity, let's find the batch if we had it. Since sale_items doesn't store batch currently (assumption),
                # we might need to add it to some batch.
                
                # Update general logic: increment quantity of the product in a batch
                batch = conn.execute("SELECT batch_number FROM pharmacy_inventory WHERE product_id=? ORDER BY created_at DESC LIMIT 1", (sale_item['product_id'],)).fetchone()
                if batch:
                    conn.execute("UPDATE pharmacy_inventory SET quantity = quantity + ? WHERE product_id=? AND batch_number=?", 
                                 (qty, sale_item['product_id'], batch['batch_number']))
                
                # 4. Update Customer Balance (if it was a credit sale)
                sale = conn.execute("SELECT customer_id, payment_type FROM pharmacy_sales WHERE id=?", (sale_item['sale_id'],)).fetchone()
                if sale and sale['customer_id'] and sale['payment_type'] == 'CREDIT':
                     refund_amt = qty * sale_item['unit_price']
                     conn.execute("UPDATE pharmacy_customers SET balance = balance - ? WHERE id=?", (refund_amt, sale['customer_id']))
                     # Also update loan balance if exists
                     conn.execute("UPDATE pharmacy_loans SET balance = balance - ? WHERE sale_id=?", (refund_amt, sale_item['sale_id']))

                conn.commit()
            
            QMessageBox.information(self, "Success", f"Item {action} processed successfully.")
            self.load_invoice()
            self.return_processed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
