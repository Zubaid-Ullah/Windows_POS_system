from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QPushButton, QLabel, QHeaderView, QGroupBox, 
                             QFormLayout, QLineEdit, QComboBox, QMessageBox, QTableWidgetItem, QDoubleSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.database.db_manager import db_manager
from src.core.localization import lang_manager

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
        self.invoice_input.setPlaceholderText(lang_manager.get("search") + " Invoice/Sale ID...")
        self.invoice_input.setFixedHeight(55)
        self.search_btn = QPushButton(lang_manager.get("search"))
        style_button(self.search_btn, variant="info")
        self.search_btn.clicked.connect(self.load_invoice)
        search_layout.addWidget(self.invoice_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        # Sale Info
        self.sale_info_lbl = QLabel("No invoice loaded")
        self.sale_info_lbl.setStyleSheet("font-size: 16px; color: #64748b; font-weight: 500;")
        layout.addWidget(self.sale_info_lbl)

        # 2. Refund Mode Selection
        refund_layout = QHBoxLayout()
        refund_layout.addWidget(QLabel(lang_manager.get("refund_mode") + ":"))
        self.refund_mode_combo = QComboBox()
        self.refund_mode_combo.addItems([lang_manager.get("cash"), lang_manager.get("credit")])
        self.refund_mode_combo.setMinimumWidth(200)
        refund_layout.addWidget(self.refund_mode_combo)
        refund_layout.addStretch()
        layout.addLayout(refund_layout)

        # 3. Table for items in the invoice
        # Columns: Barcode, Name, Size, Sold Qty, Returned Qty, Price, Status, Return Action
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            lang_manager.get("product"), lang_manager.get("quantity") + " (Sold)", 
            lang_manager.get("already_returned"), lang_manager.get("price"), 
            lang_manager.get("remaining"), lang_manager.get("return_quantity"), 
            lang_manager.get("action"), lang_manager.get("confirm")
        ])
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
                    QMessageBox.warning(self, lang_manager.get("not_found"), lang_manager.get("invoice_not_found"))
                    return
                
                self.sale_info_lbl.setText(f"{lang_manager.get('invoice')} #{sale['invoice_number']} | {lang_manager.get('customer')}: {sale['customer_name'] or lang_manager.get('walk_in')} | {lang_manager.get('total')}: ${sale['total_amount']:,.2f}")
                
                items = conn.execute("""
                    SELECT si.*, p.name_en
                    FROM pharmacy_sale_items si
                    JOIN pharmacy_products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                """, (sale['id'],)).fetchall()
                
                self.table.setRowCount(0)
                for i, item in enumerate(items):
                    # Calculate already returned quantity for THIS specific invoice line
                    ret_row = conn.execute("""
                        SELECT SUM(quantity) as returned_qty 
                        FROM pharmacy_return_items 
                        WHERE sale_item_id = ?
                    """, (item['id'],)).fetchone()
                    
                    already_returned = ret_row['returned_qty'] or 0
                    remaining_qty = item['quantity'] - already_returned
                    
                    self.table.insertRow(i)
                    self.table.setItem(i, 0, QTableWidgetItem(item['name_en'])) # Product Name
                    self.table.setItem(i, 1, QTableWidgetItem(str(item['quantity']))) # Sold Qty
                    self.table.setItem(i, 2, QTableWidgetItem(str(already_returned))) # Already Ret
                    self.table.setItem(i, 3, QTableWidgetItem(f"{item['unit_price']:.2f}")) # Price
                    
                    rem_item = QTableWidgetItem(str(remaining_qty))
                    if remaining_qty <= 0:
                        rem_item.setForeground(Qt.GlobalColor.red)
                    self.table.setItem(i, 4, rem_item) # Remaining Qty
                    
                    qty_input = QDoubleSpinBox()
                    qty_input.setRange(0, remaining_qty)
                    qty_input.setValue(0)
                    self.table.setCellWidget(i, 5, qty_input) # Return Qty
                    
                    action_combo = QComboBox()
                    refund_mode_combo.addItems(["ACCOUNT", "CASH"])
                    # Default to ACCOUNT if it was a credit sale, otherwise CASH
                    if sale['payment_type'] == 'CREDIT':
                        refund_mode_combo.setCurrentText("ACCOUNT")
                    else:
                        refund_mode_combo.setCurrentText("CASH")
                    self.table.setCellWidget(i, 7, refund_mode_combo)
                    
                    btn = QPushButton("Process")
                    if remaining <= 0:
                        btn.setEnabled(False)
                        btn.setText("Fully Ret.")
                        style_button(btn, variant="secondary", size="small")
                    else:
                        style_button(btn, variant="warning", size="small")
                    
                    btn.clicked.connect(lambda ch, it=item, r=i: self.process_return(it, r))
                    self.table.setCellWidget(i, 8, btn)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def process_return(self, sale_item, row):
        qty = self.table.cellWidget(row, 5).value()
        action = self.table.cellWidget(row, 6).currentText()
        refund_mode = self.table.cellWidget(row, 7).currentText()
        
        if qty <= 0:
            QMessageBox.warning(self, "Error", "Please select a quantity to return.")
            return
            
        # Double check remaining one last time
        remaining = float(self.table.item(row, 3).text())
        if qty > remaining:
            QMessageBox.warning(self, "Error", f"Cannot return more than remaining quantity ({remaining}).")
            return
        
        ok = QMessageBox.question(self, "Confirm", f"Process {action} for {qty} units via {refund_mode}?", 
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                 QMessageBox.StandardButton.Yes)
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
                # Refund only if action is RETURN
                actual_refund = qty * sale_item['unit_price'] if action == 'RETURN' else 0
                
                conn.execute("""
                    INSERT INTO pharmacy_returns (original_sale_id, refund_amount, refund_type, reason, user_id) 
                    VALUES (?, ?, ?, ?, ?)
                """, (sale_item['sale_id'], actual_refund, refund_mode, reason_text, user_id))
                return_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                
                # 2. Add Return Item (Now with sale_item_id)
                conn.execute("""
                    INSERT INTO pharmacy_return_items (return_id, sale_item_id, product_id, quantity, unit_price, action)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (return_id, sale_item['id'], sale_item['product_id'], qty, sale_item['unit_price'], action))
                
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
                
                # 4. Update Customer Balance (if it was a credit sale AND refund is to ACCOUNT)
                sale = conn.execute("SELECT customer_id, payment_type FROM pharmacy_sales WHERE id=?", (sale_item['sale_id'],)).fetchone()
                if sale and sale['customer_id'] and sale['payment_type'] == 'CREDIT' and actual_refund > 0 and refund_mode == 'ACCOUNT':
                     # Update Customer Balance (Allow it to go negative/credit)
                     conn.execute("UPDATE pharmacy_customers SET balance = balance - ? WHERE id=?", (actual_refund, sale['customer_id']))
                     
                     # Also update loan balance if exists
                     conn.execute("UPDATE pharmacy_loans SET balance = balance - ? WHERE sale_id=?", (actual_refund, sale_item['sale_id']))
                     
                     # If loan balance is now <= 0, mark as COMPLETED
                     conn.execute("""
                        UPDATE pharmacy_loans 
                        SET status = 'COMPLETED' 
                        WHERE sale_id = ? AND balance <= 0
                     """, (sale_item['sale_id'],))

                conn.commit()
            
            QMessageBox.information(self, "Success", f"Item {action} processed successfully.")
            self.load_invoice()
            self.return_processed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
