from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QPushButton, QLabel, QHeaderView, QGroupBox, 
                             QFormLayout, QLineEdit, QComboBox, QMessageBox, QTableWidgetItem, 
                             QDoubleSpinBox, QDialog, QDialogButtonBox, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.database.db_manager import db_manager
from src.core.localization import lang_manager

class InvoiceLoadWorker(QObject):
    """Background worker to load invoice data"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, invoice_id):
        super().__init__()
        self.invoice_id = invoice_id

    def run(self):
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # Search by invoice_number OR id
                sale = conn.execute("""
                    SELECT s.*, c.name as customer_name 
                    FROM pharmacy_sales s
                    LEFT JOIN pharmacy_customers c ON s.customer_id = c.id
                    WHERE s.invoice_number = ? OR s.id = ?
                """, (self.invoice_id, self.invoice_id)).fetchone()
                
                if not sale:
                    self.error.emit("not_found")
                    return
                
                items = conn.execute("""
                    SELECT si.*, p.name_en
                    FROM pharmacy_sale_items si
                    JOIN pharmacy_products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                """, (sale['id'],)).fetchall()
                
                item_data = []
                for item in items:
                    # Calculate already returned quantity for THIS specific invoice line
                    ret_row = conn.execute("""
                        SELECT SUM(quantity) as returned_qty 
                        FROM pharmacy_return_items 
                        WHERE sale_item_id = ?
                    """, (item['id'],)).fetchone()
                    
                    already_returned = ret_row['returned_qty'] or 0
                    item_dict = dict(item)
                    item_dict['already_returned'] = already_returned
                    item_data.append(item_dict)
                
                result = {
                    'sale': dict(sale),
                    'items': item_data
                }
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ReplacementItemDialog(QDialog):
    """Dialog to select replacement items when action is REPLACEMENT"""
    def __init__(self, return_qty, unit_price, parent=None):
        super().__init__(parent)
        self.return_qty = return_qty
        self.unit_price = unit_price
        self.replacement_items = []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(lang_manager.get("select_replacement_items") or "Select Replacement Items")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel(f"{lang_manager.get('return_value')}: {self.return_qty * self.unit_price:.2f} AFN")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(info_label)
        
        # Search box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(lang_manager.get("search") + " " + lang_manager.get("product") + "...")
        self.search_input.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Products table
        self.products_table = QTableWidget(0, 5)
        self.products_table.setHorizontalHeaderLabels([
            lang_manager.get("product"), lang_manager.get("price"), 
            lang_manager.get("stock"), lang_manager.get("quantity"), 
            lang_manager.get("add")
        ])
        style_table(self.products_table, variant="premium")
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.products_table)
        
        # Selected items table
        selected_label = QLabel(f"<b>{lang_manager.get('selected_items') or 'Selected Items'}</b>")
        layout.addWidget(selected_label)
        
        self.selected_table = QTableWidget(0, 4)
        self.selected_table.setHorizontalHeaderLabels([
            lang_manager.get("product"), lang_manager.get("quantity"), 
            lang_manager.get("price"), lang_manager.get("remove")
        ])
        style_table(self.selected_table, variant="premium")
        self.selected_table.setMaximumHeight(200)
        layout.addWidget(self.selected_table)
        
        # Total label
        self.total_label = QLabel(f"{lang_manager.get('total')}: 0.00 AFN")
        self.total_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.total_label)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.load_products()
        
    def load_products(self):
        """Load available products in background to prevent freezing"""
        try:
            with db_manager.get_pharmacy_connection() as conn:
                products = conn.execute("""
                    SELECT p.id, p.name_en, p.sale_price, 
                           COALESCE(SUM(i.quantity), 0) as stock
                    FROM pharmacy_products p
                    LEFT JOIN pharmacy_inventory i ON p.id = i.product_id
                    WHERE p.is_active = 1
                    GROUP BY p.id
                    HAVING stock > 0
                    ORDER BY p.name_en
                """).fetchall()
                
                self.all_products = products
                self.display_products(products)
        except Exception as e:
            QMessageBox.critical(self, lang_manager.get("error"), str(e))
    
    def display_products(self, products):
        """Display products in table"""
        self.products_table.setRowCount(0)
        for i, product in enumerate(products):
            self.products_table.insertRow(i)
            self.products_table.setItem(i, 0, QTableWidgetItem(product['name_en']))
            self.products_table.setItem(i, 1, QTableWidgetItem(f"{product['sale_price']:.2f}"))
            self.products_table.setItem(i, 2, QTableWidgetItem(f"{product['stock']:.0f}"))
            
            qty_spin = QSpinBox()
            qty_spin.setRange(0, int(product['stock']))
            qty_spin.setValue(0)
            self.products_table.setCellWidget(i, 3, qty_spin)
            
            add_btn = QPushButton(lang_manager.get("add"))
            style_button(add_btn, variant="success", size="small")
            add_btn.clicked.connect(lambda ch, p=product, r=i: self.add_item(p, r))
            self.products_table.setCellWidget(i, 4, add_btn)
    
    def filter_products(self):
        """Filter products based on search text"""
        search_text = self.search_input.text().lower()
        if not search_text:
            self.display_products(self.all_products)
        else:
            filtered = [p for p in self.all_products if search_text in p['name_en'].lower()]
            self.display_products(filtered)
    
    def add_item(self, product, row):
        """Add selected item to replacement list"""
        qty_widget = self.products_table.cellWidget(row, 3)
        qty = qty_widget.value()
        
        if qty <= 0:
            QMessageBox.warning(self, lang_manager.get("error"), lang_manager.get("select_quantity"))
            return
        
        # Check if already added
        for item in self.replacement_items:
            if item['product_id'] == product['id']:
                item['quantity'] += qty
                self.update_selected_table()
                self.update_total()
                return
        
        # Add new item
        self.replacement_items.append({
            'product_id': product['id'],
            'product_name': product['name_en'],
            'quantity': qty,
            'unit_price': product['sale_price'],
            'total_price': qty * product['sale_price']
        })
        
        self.update_selected_table()
        self.update_total()
        qty_widget.setValue(0)
    
    def remove_item(self, index):
        """Remove item from replacement list"""
        del self.replacement_items[index]
        self.update_selected_table()
        self.update_total()
    
    def update_selected_table(self):
        """Update the selected items table"""
        self.selected_table.setRowCount(0)
        for i, item in enumerate(self.replacement_items):
            self.selected_table.insertRow(i)
            self.selected_table.setItem(i, 0, QTableWidgetItem(item['product_name']))
            self.selected_table.setItem(i, 1, QTableWidgetItem(str(item['quantity'])))
            self.selected_table.setItem(i, 2, QTableWidgetItem(f"{item['total_price']:.2f}"))
            
            remove_btn = QPushButton(lang_manager.get("remove"))
            style_button(remove_btn, variant="danger", size="small")
            remove_btn.clicked.connect(lambda ch, idx=i: self.remove_item(idx))
            self.selected_table.setCellWidget(i, 3, remove_btn)
    
    def update_total(self):
        """Update total price label"""
        total = sum(item['total_price'] for item in self.replacement_items)
        self.total_label.setText(f"{lang_manager.get('total')}: {total:.2f} AFN")
    
    def validate_and_accept(self):
        """Validate replacement items before accepting"""
        if not self.replacement_items:
            QMessageBox.warning(self, lang_manager.get("error"), 
                              lang_manager.get("select_replacement_items") or "Please select replacement items")
            return
        
        total = sum(item['total_price'] for item in self.replacement_items)
        return_value = self.return_qty * self.unit_price
        
        # Allow some tolerance for rounding
        if abs(total - return_value) > 0.01:
            reply = QMessageBox.question(
                self, 
                lang_manager.get("confirm"),
                f"{lang_manager.get('replacement_value_mismatch') or 'Replacement value does not match return value'}.\n"
                f"{lang_manager.get('return_value')}: {return_value:.2f} AFN\n"
                f"{lang_manager.get('replacement_value') or 'Replacement Value'}: {total:.2f} AFN\n\n"
                f"{lang_manager.get('continue') or 'Continue anyway'}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.accept()


class PharmacyReturnsView(QWidget):
    return_processed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None
        self.is_loading = False
        self.init_ui()
        self.destroyed.connect(self.cleanup_thread)

    def cleanup_thread(self):
        """Safely cleanup any running threads"""
        if hasattr(self, 'thread') and self.thread is not None:
            if self.thread.isRunning():
                self.thread.quit()
                self.thread.wait(1000)
            self.thread = None
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker = None

    def _reset_thread_refs(self):
        """Reset thread and worker references"""
        self.thread = None
        self.worker = None

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
        # Columns: Product, Sold, Already Ret, Price, Remaining, Ret Qty, Action, Refund Mode, Process
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            lang_manager.get("product"), lang_manager.get("quantity") + " (Sold)", 
            lang_manager.get("already_returned"), lang_manager.get("price"), 
            lang_manager.get("remaining"), lang_manager.get("return_quantity"), 
            lang_manager.get("action"), lang_manager.get("refund_mode"), lang_manager.get("confirm")
        ])
        style_table(self.table, variant="premium")
        # Initialize with Stretch, but load_invoice will adjust
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_invoice(self):
        """Search and load invoice in background thread"""
        sale_id = self.invoice_input.text().strip()
        if not sale_id: return
        
        if self.is_loading:
            return
        
        self.is_loading = True
        self.cleanup_thread()
        self.search_btn.setEnabled(False)
        self.search_btn.setText(lang_manager.get("loading") or "Loading...")
        
        self.thread = QThread(self)
        self.worker = InvoiceLoadWorker(sale_id)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_invoice_loaded)
        self.worker.error.connect(self.on_invoice_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.destroyed.connect(self._reset_thread_refs)
        
        self.thread.start()

    def on_invoice_loaded(self, result):
        """Handle loaded invoice data"""
        self.is_loading = False
        self.search_btn.setEnabled(True)
        self.search_btn.setText(lang_manager.get("search"))
        
        sale = result['sale']
        items = result['items']
        
        self.current_sale = sale
        self.sale_info_lbl.setText(f"{lang_manager.get('invoice')} #{sale['invoice_number']} | {lang_manager.get('customer')}: {sale['customer_name'] or lang_manager.get('walk_in')} | {lang_manager.get('total')}: Afg{sale['total_amount']:,.2f}")
        
        self.populate_table(items, sale)
        
        # Autofit
        self.table.resizeColumnsToContents()
        if self.table.horizontalHeader().length() < self.table.width():
             self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        else:
             self.table.horizontalHeader().setStretchLastSection(True)

    def on_invoice_error(self, error):
        """Handle invoice loading error"""
        self.is_loading = False
        self.search_btn.setEnabled(True)
        self.search_btn.setText(lang_manager.get("search"))
        
        if error == "not_found":
            QMessageBox.warning(self, lang_manager.get("not_found"), lang_manager.get("invoice_not_found"))
        else:
            QMessageBox.critical(self, lang_manager.get("error"), f"Error loading invoice: {error}")

    def populate_table(self, items, sale):
        """Populate items table with fetched data"""
        self.table.setRowCount(0)
        for i, item in enumerate(items):
            already_returned = item['already_returned']
            remaining_qty = item['quantity'] - already_returned
            
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(item['name_en']))
            self.table.setItem(i, 1, QTableWidgetItem(str(item['quantity'])))
            self.table.setItem(i, 2, QTableWidgetItem(str(already_returned)))
            self.table.setItem(i, 3, QTableWidgetItem(f"{item['unit_price']:.2f}"))
            
            rem_item = QTableWidgetItem(str(remaining_qty))
            if remaining_qty <= 0:
                rem_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(i, 4, rem_item)
            
            qty_input = QDoubleSpinBox()
            qty_input.setRange(0, remaining_qty)
            qty_input.setValue(0)
            self.table.setCellWidget(i, 5, qty_input)
            
            action_combo = QComboBox()
            action_combo.addItems(["RETURN", "REPLACEMENT"])
            self.table.setCellWidget(i, 6, action_combo)
            
            row_refund_combo = QComboBox()
            row_refund_combo.addItems([lang_manager.get("account"), lang_manager.get("cash")])
            row_refund_combo.setItemData(0, "ACCOUNT")
            row_refund_combo.setItemData(1, "CASH")
            
            if sale['payment_type'] == 'CREDIT':
                row_refund_combo.setCurrentIndex(0)
            else:
                row_refund_combo.setCurrentIndex(1)
            self.table.setCellWidget(i, 7, row_refund_combo)
            
            proc_btn = QPushButton(lang_manager.get("confirm"))
            style_button(proc_btn, variant="info", size="small")
            proc_btn.clicked.connect(lambda ch, it=item, r=i: self.process_return(it, r))
            self.table.setCellWidget(i, 8, proc_btn)


    def process_return(self, sale_item, row):
        qty = self.table.cellWidget(row, 5).value()
        action = self.table.cellWidget(row, 6).currentText()
        
        # Get DB-ready refund mode from item data
        refund_combo = self.table.cellWidget(row, 7)
        refund_mode = refund_combo.itemData(refund_combo.currentIndex())
        
        if qty <= 0:
            QMessageBox.warning(self, lang_manager.get("error"), lang_manager.get("select_quantity"))
            return
            
        # Double check remaining one last time - Remaining is column 4
        remaining_str = self.table.item(row, 4).text()
        remaining = float(remaining_str)
        if qty > remaining:
            QMessageBox.warning(self, lang_manager.get("error"), f"{lang_manager.get('error')}: {qty} > {remaining}")
            return
        
        # If REPLACEMENT, show item selection dialog
        replacement_items = []
        if action == 'REPLACEMENT':
            dialog = ReplacementItemDialog(qty, sale_item['unit_price'], self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                replacement_items = dialog.replacement_items
            else:
                return  # User cancelled
        
        ok = QMessageBox.question(self, lang_manager.get("confirm"), f"{lang_manager.get('process')} {action} {lang_manager.get('for')} {qty} {lang_manager.get('units')} via {refund_mode}?", 
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                 QMessageBox.StandardButton.Yes)
        if ok != QMessageBox.StandardButton.Yes: return
        
        # Reason dialog
        from PyQt6.QtWidgets import QInputDialog
        reason_text, ok = QInputDialog.getText(self, lang_manager.get("reason"), f"{lang_manager.get('enter_reason')}:")
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
                return_item_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                
                # 3. If REPLACEMENT, add replacement items
                if action == 'REPLACEMENT' and replacement_items:
                    for rep_item in replacement_items:
                        conn.execute("""
                            INSERT INTO pharmacy_replacement_items 
                            (return_item_id, product_id, product_name, quantity, unit_price, total_price)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (return_item_id, rep_item['product_id'], rep_item['product_name'], 
                              rep_item['quantity'], rep_item['unit_price'], rep_item['total_price']))
                        
                        # Deduct from inventory
                        batch = conn.execute(
                            "SELECT batch_number, quantity FROM pharmacy_inventory WHERE product_id=? AND quantity >= ? ORDER BY expiry_date ASC LIMIT 1", 
                            (rep_item['product_id'], rep_item['quantity'])
                        ).fetchone()
                        
                        if batch:
                            conn.execute(
                                "UPDATE pharmacy_inventory SET quantity = quantity - ? WHERE product_id=? AND batch_number=?", 
                                (rep_item['quantity'], rep_item['product_id'], batch['batch_number'])
                            )
                
                # 4. Update Stock (add back returned items)
                batch = conn.execute("SELECT batch_number FROM pharmacy_inventory WHERE product_id=? ORDER BY created_at DESC LIMIT 1", (sale_item['product_id'],)).fetchone()
                if batch:
                    conn.execute("UPDATE pharmacy_inventory SET quantity = quantity + ? WHERE product_id=? AND batch_number=?", 
                                 (qty, sale_item['product_id'], batch['batch_number']))
                
                # 5. Update Customer Balance (if it was a credit sale AND refund is to ACCOUNT)
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
            
            QMessageBox.information(self, lang_manager.get("success"), f"{lang_manager.get('success')}: {action}")
            self.load_invoice()
            self.return_processed.emit()
        except Exception as e:
            QMessageBox.critical(self, lang_manager.get("error"), str(e))
