from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QMessageBox, QDialog, QFormLayout,
                             QComboBox, QDateEdit, QFileDialog, QInputDialog, QTabWidget,
                             QCheckBox, QPlainTextEdit, QDateTimeEdit, QSizePolicy, QGroupBox)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta
from src.core.localization import lang_manager
from src.database.db_manager import db_manager
from src.utils.barcode_util import BarcodeGenerator
from src.core.auth import Auth
from datetime import datetime
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button

class CategoryManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.setFixedWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Category Name", "Actions"])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        add_layout = QHBoxLayout()
        self.new_cat = QLineEdit()
        self.new_cat.setPlaceholderText("New Category Name...")
        self.add_btn = QPushButton("Add")
        style_button(self.add_btn, variant="success")
        self.add_btn.clicked.connect(self.add_category)
        add_layout.addWidget(self.new_cat)
        add_layout.addWidget(self.add_btn)
        layout.addLayout(add_layout)
        
        self.load_categories()

    def load_categories(self):
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories")
            rows = cursor.fetchall()
            self.table.setRowCount(0)
            for i, row in enumerate(rows):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(row['name_en']))
                
                del_btn = QPushButton("Delete")
                style_button(del_btn, variant="danger", size="icon")
                del_btn.setIcon(qta.icon("fa5s.trash", color="white"))
                del_btn.clicked.connect(lambda checked, rid=row['id']: self.delete_category(rid))
                self.table.setCellWidget(i, 1, del_btn)

    def add_category(self):
        name = self.new_cat.text().strip()
        if not name: return
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categories (name_en) VALUES (?)", (name,))
            conn.commit()
        self.new_cat.clear()
        self.load_categories()

    def delete_category(self, rid):
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM categories WHERE id=?", (rid,))
                conn.commit()
            self.load_categories()
        except:
            QMessageBox.warning(self, "Error", "Cannot delete category linked to products.")

class ProductDialog(QDialog):
    def __init__(self, product=None, initial_barcode=None):
        super().__init__()
        self.product = product
        self.initial_barcode = initial_barcode
        self.setWindowTitle("🛒 Enterprise Product Registry")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Tabs for better organization
        self.tabs = QTabWidget()
        
        # --- TAB 1: GENERAL INFO ---
        general_tab = QWidget()
        gen_layout = QFormLayout(general_tab)
        
        self.name_en = QLineEdit()
        self.name_ps = QLineEdit()
        self.name_dr = QLineEdit()
        self.barcode = QLineEdit()
        self.sku = QLineEdit()
        self.brand = QLineEdit()
        
        cat_layout = QHBoxLayout()
        self.category_cb = QComboBox()
        self.category_cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.load_categories()
        
        add_cat_btn = QPushButton("+")
        add_cat_btn.setFixedWidth(30)
        add_cat_btn.clicked.connect(self.manage_categories)
        cat_layout.addWidget(self.category_cb)
        cat_layout.addWidget(add_cat_btn)
        
        self.prod_type = QComboBox()
        self.prod_type.addItems(["Simple", "Variant", "Bundle", "Service"])
        
        self.unit = QComboBox()
        self.unit.addItems(["pcs", "kg", "gram", "liter", "box", "packet", "dozen", "meter"])
        self.unit.setEditable(True)

        gen_layout.addRow("Product Name (EN) *:", self.name_en)
        gen_layout.addRow("Product Name (PS):", self.name_ps)
        gen_layout.addRow("Product Name (DR):", self.name_dr)
        gen_layout.addRow("Barcode / QR *:", self.barcode)
        gen_layout.addRow("SKU Code:", self.sku)
        gen_layout.addRow("Brand / Company *:", self.brand)
        gen_layout.addRow("Category:", cat_layout)
        gen_layout.addRow("Product Type:", self.prod_type)
        gen_layout.addRow("Unit of Measure:", self.unit)
        
        # --- TAB 2: PRICING ---
        pricing_tab = QWidget()
        prc_layout = QFormLayout(pricing_tab)
        
        self.cost_price = QLineEdit("0")
        self.sale_price = QLineEdit("0")
        self.wholesale_price = QLineEdit("0")
        self.tax_rate = QLineEdit("0")
        
        self.allow_zero_price = QCheckBox("Allow Sale at Zero Price")
        self.allow_price_change = QCheckBox("Allow Manual Price Change at POS")

        prc_layout.addRow("Cost Price (Purchase) *:", self.cost_price)
        prc_layout.addRow("Standard Sale Price *:", self.sale_price)
        prc_layout.addRow("Wholesale Price:", self.wholesale_price)
        prc_layout.addRow("Tax Rate (%):", self.tax_rate)
        prc_layout.addRow(self.allow_zero_price)
        prc_layout.addRow(self.allow_price_change)

        # --- TAB 3: INVENTORY CONTROLS ---
        inv_tab = QWidget()
        inv_layout = QFormLayout(inv_tab)
        
        from PyQt6.QtGui import QDoubleValidator
        self.quantity = QLineEdit("0")
        self.quantity.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        self.min_stock = QLineEdit("5")
        self.min_stock.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        self.max_stock = QLineEdit("100")
        self.max_stock.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        
        self.track_inv = QCheckBox("Track Inventory for this item")
        self.track_inv.setChecked(True)
        self.allow_negative = QCheckBox("Allow Negative Stock (Over-selling)")
        self.returnable = QCheckBox("Item is Returnable")
        self.returnable.setChecked(True)

        inv_layout.addRow("Current Stock Quantity *:", self.quantity)
        inv_layout.addRow("Minimum Alert Level *:", self.min_stock)
        inv_layout.addRow("Maximum Stock Level:", self.max_stock)
        inv_layout.addRow(self.track_inv)
        inv_layout.addRow(self.allow_negative)
        inv_layout.addRow(self.returnable)

        # --- TAB 4: TRACKING (BATCH/EXPIRY/SERIAL) ---
        track_tab = QWidget()
        trk_layout = QFormLayout(track_tab)
        
        self.batch_num = QLineEdit()
        self.serial_num = QLineEdit()
        
        self.mfg_date = QDateEdit()
        self.mfg_date.setCalendarPopup(True)
        self.mfg_date.setDate(QDate.currentDate())
        
        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDate(QDate.currentDate().addYears(1))

        trk_layout.addRow("Batch Number:", self.batch_num)
        trk_layout.addRow("Serial Number / IMEI:", self.serial_num)
        trk_layout.addRow("Manufacturing Date:", self.mfg_date)
        trk_layout.addRow("Expiry Date:", self.expiry_date)

        # --- TAB 5: SUPPLIER & LOCATION ---
        sl_tab = QWidget()
        sl_layout = QFormLayout(sl_tab)
        
        self.supplier_cb = QComboBox()
        self.load_suppliers()
        
        self.supplier_sku = QLineEdit()
        self.shelf_loc = QLineEdit()
        self.notes = QPlainTextEdit()
        self.notes.setMaximumHeight(100)

        sl_layout.addRow("Default Supplier / Vendor *:", self.supplier_cb)
        sl_layout.addRow("Supplier SKU:", self.supplier_sku)
        sl_layout.addRow("Shelf / Rack Location:", self.shelf_loc)
        sl_layout.addRow("Internal Notes:", self.notes)

        # Add all tabs
        self.tabs.addTab(general_tab, qta.icon("fa5s.info-circle"), " General")
        self.tabs.addTab(pricing_tab, qta.icon("fa5s.money-bill-wave"), " Pricing")
        self.tabs.addTab(inv_tab, qta.icon("fa5s.boxes"), " Inventory")
        self.tabs.addTab(track_tab, qta.icon("fa5s.history"), " Tracking")
        self.tabs.addTab(sl_tab, qta.icon("fa5s.truck"), " Logistics")
        
        main_layout.addWidget(self.tabs)
        
        # Populate data if editing
        if self.product:
            self.populate_data()
        elif self.initial_barcode:
            self.barcode.setText(self.initial_barcode)
            self.name_en.setFocus()

        # Buttons
        btns = QHBoxLayout()
        save_btn = QPushButton(" Register Product ")
        save_btn.clicked.connect(self.validate_and_accept)
        
        cancel_btn = QPushButton(" Cancel ")
        cancel_btn.clicked.connect(self.reject)
        
        btns.addStretch()
        style_button(cancel_btn, variant="secondary")
        style_button(save_btn, variant="success", size="large")
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        main_layout.addLayout(btns)

    def load_categories(self):
        self.category_cb.addItem("None (Uncategorized)", None)
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_en FROM categories")
            for row in cursor.fetchall():
                self.category_cb.addItem(row['name_en'], row['id'])

    def load_suppliers(self):
        self.supplier_cb.clear()
        self.supplier_cb.addItem("None (No Supplier)", None)
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM suppliers")
            for row in cursor.fetchall():
                self.supplier_cb.addItem(row['name'], row['id'])

    def manage_categories(self):
        dialog = CategoryManagerDialog(self)
        dialog.exec()
        self.load_categories()
        
    def load_categories(self):
        prev_data = self.category_cb.currentData()
        self.category_cb.clear()
        self.category_cb.addItem("None (Uncategorized)", None)
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_en FROM categories")
            for row in cursor.fetchall():
                self.category_cb.addItem(row['name_en'], row['id'])
        
        idx = self.category_cb.findData(prev_data)
        if idx >= 0: self.category_cb.setCurrentIndex(idx)

    def populate_data(self):
        p = self.product
        self.name_en.setText(str(p['name_en'] or ""))
        self.name_ps.setText(str(p['name_ps'] or ""))
        self.name_dr.setText(str(p['name_dr'] or ""))
        self.barcode.setText(str(p['barcode'] or ""))
        self.sku.setText(str(p.get('sku', '')))
        self.brand.setText(str(p.get('brand', '')))
        
        idx_cat = self.category_cb.findData(p.get('category_id'))
        if idx_cat >= 0: self.category_cb.setCurrentIndex(idx_cat)
        
        self.cost_price.setText(str(p['cost_price']))
        self.sale_price.setText(str(p['sale_price']))
        self.wholesale_price.setText(str(p.get('wholesale_price', 0)))
        self.tax_rate.setText(str(p.get('tax_rate', 0)))
        
        self.quantity.setText(str(p.get('quantity', 0)))
        self.min_stock.setText(str(p['min_stock']))
        self.max_stock.setText(str(p.get('max_stock', 100)))
        
        self.track_inv.setChecked(bool(p.get('track_inventory', 1)))
        self.allow_negative.setChecked(bool(p.get('allow_negative_stock', 0)))
        self.returnable.setChecked(bool(p.get('returnable', 1)))
        self.allow_zero_price.setChecked(bool(p.get('allow_zero_price', 0)))
        self.allow_price_change.setChecked(bool(p.get('allow_pos_price_change', 0)))
        
        self.batch_num.setText(str(p.get('batch_number', '')))
        self.serial_num.setText(str(p.get('serial_number', '')))
        
        if p.get('mfg_date'): self.mfg_date.setDate(QDate.fromString(p['mfg_date'], "yyyy-MM-dd"))
        if p.get('expiry_date'): self.expiry_date.setDate(QDate.fromString(p['expiry_date'], "yyyy-MM-dd"))
        
        idx_sup = self.supplier_cb.findData(p.get('supplier_id'))
        if idx_sup >= 0: self.supplier_cb.setCurrentIndex(idx_sup)
        
        self.shelf_loc.setText(str(p.get('shelf_location', '')))
        self.notes.setPlainText(str(p.get('internal_notes', '')))

    def validate_and_accept(self):
        if not self.name_en.text() or not self.barcode.text() or not self.brand.text():
            QMessageBox.warning(self, "Missing Fields", "Product Name, Barcode, and Brand/Company are mandatory!")
            return
        self.accept()

    def get_data(self):
        try:
            return {
                'name_en': self.name_en.text(),
                'name_ps': self.name_ps.text(),
                'name_dr': self.name_dr.text(),
                'barcode': self.barcode.text(),
                'sku': self.sku.text(),
                'brand': self.brand.text(),
                'category_id': self.category_cb.currentData(),
                'product_type': self.prod_type.currentText(),
                'unit': self.unit.currentText(),
                'cost_price': float(self.cost_price.text() or 0),
                'sale_price': float(self.sale_price.text() or 0),
                'wholesale_price': float(self.wholesale_price.text() or 0),
                'tax_rate': float(self.tax_rate.text() or 0),
                'allow_zero_price': 1 if self.allow_zero_price.isChecked() else 0,
                'allow_pos_price_change': 1 if self.allow_price_change.isChecked() else 0,
                'quantity': float(self.quantity.text() or 0),
                'min_stock': float(self.min_stock.text() or 0),
                'max_stock': float(self.max_stock.text() or 100),
                'track_inventory': 1 if self.track_inv.isChecked() else 0,
                'allow_negative_stock': 1 if self.allow_negative.isChecked() else 0,
                'returnable': 1 if self.returnable.isChecked() else 0,
                'batch_number': self.batch_num.text(),
                'serial_number': self.serial_num.text(),
                'mfg_date': self.mfg_date.date().toString("yyyy-MM-dd"),
                'expiry_date': self.expiry_date.date().toString("yyyy-MM-dd"),
                'supplier_id': self.supplier_cb.currentData(),
                'supplier_sku': self.supplier_sku.text(),
                'shelf_location': self.shelf_loc.text(),
                'internal_notes': self.notes.toPlainText()
            }
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values for prices and quantities.")
            return None

class InventoryView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = Auth.get_current_user()
        self.can_edit = self.current_user['role_name'] in ['Admin', 'Manager']
        self.init_ui()
        self.load_products()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Card Wrapper
        self.container = QFrame()
        self.container.setObjectName("card")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        header.setSpacing(15)
        
        # Barcode Scanner for Stock Intake
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Scan barcode to update stock...")
        self.scan_input.setFixedWidth(400)
        self.scan_input.returnPressed.connect(self.handle_barcode_scan)
        header.addWidget(self.scan_input)
        
        header.addStretch()
        
        # Inventory Tools/Options Menu
        self.tools_btn = QPushButton(" Tools")
        style_button(self.tools_btn, variant="outline")
        self.tools_btn.setIcon(qta.icon("fa5s.cog", color="#4318ff"))
        self.tools_btn.clicked.connect(self.show_inventory_tools)
        
        self.cat_btn = QPushButton(" Categories")
        style_button(self.cat_btn, variant="secondary")
        self.cat_btn.setIcon(qta.icon("fa5s.th-list", color="#4318ff"))
        self.cat_btn.clicked.connect(self.manage_categories)
        
        self.add_btn = QPushButton(" Register New Product")
        style_button(self.add_btn, variant="primary")
        self.add_btn.setIcon(qta.icon("fa5s.plus", color="white"))
        self.add_btn.clicked.connect(lambda: self.add_product())
        
        if not self.can_edit:
            self.add_btn.hide()
            self.cat_btn.hide()
            self.tools_btn.hide()
            self.scan_input.hide()
        
        header.addWidget(self.tools_btn)
        header.addWidget(self.cat_btn)
        header.addWidget(self.add_btn)
        
        layout.addLayout(header)
        
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Barcode", "Product Name", "Brand", "Cost", "Price", "Qty", "Actions"
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(7, 180)
        layout.addWidget(self.table)
        
        main_layout.addWidget(self.container)

    def load_products(self):
        from src.core.blocking_task_manager import task_manager
        
        def fetch_data():
            lang_col = f'name_{lang_manager.current_lang}'
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT p.*, i.quantity 
                    FROM products p 
                    LEFT JOIN inventory i ON p.id = i.product_id
                    WHERE p.is_active = 1
                    ORDER BY p.id DESC
                """)
                return [dict(row) for row in cursor.fetchall()], lang_col

        def on_loaded(result):
            products, lang_col = result
            self.table.setRowCount(0)
            for i, p in enumerate(products):
                name = p.get(lang_col) or p.get('name_en')
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(lang_manager.localize_digits(str(p['id']))))
                self.table.setItem(i, 1, QTableWidgetItem(p['barcode']))
                self.table.setItem(i, 2, QTableWidgetItem(name))
                self.table.setItem(i, 3, QTableWidgetItem(str(p['brand'] or 'N/A')))
                self.table.setItem(i, 4, QTableWidgetItem(lang_manager.localize_digits(f"{p['cost_price']:.2f}")))
                self.table.setItem(i, 5, QTableWidgetItem(lang_manager.localize_digits(f"{p['sale_price']:.2f}")))
                
                qty_val = p['quantity'] or 0
                qty_item = QTableWidgetItem(lang_manager.localize_digits(str(qty_val)))
                if qty_val <= (p['min_stock'] or 0):
                    qty_item.setForeground(Qt.GlobalColor.red)
                    font = qty_item.font()
                    font.setBold(True)
                    qty_item.setFont(font)
                self.table.setItem(i, 6, qty_item)
                
                # Actions
                actions = QWidget()
                act_layout = QHBoxLayout(actions)
                act_layout.setContentsMargins(2, 2, 2, 2)
                
                barcode_btn = QPushButton()
                style_button(barcode_btn, variant="success", size="icon")
                barcode_btn.setIcon(qta.icon("fa5s.barcode", color="white"))
                barcode_btn.setToolTip("Generate Barcode Image")
                barcode_btn.clicked.connect(lambda checked, b=p['barcode']: self.generate_barcode_img(b))
                act_layout.addWidget(barcode_btn)

                if self.can_edit:
                    edit_btn = QPushButton()
                    style_button(edit_btn, variant="info", size="icon")
                    edit_btn.setIcon(qta.icon("fa5s.edit", color="white"))
                    edit_btn.setToolTip("Edit Full Details")
                    edit_btn.clicked.connect(lambda checked, prod=p: self.edit_product(prod))
                    
                    del_btn = QPushButton()
                    style_button(del_btn, variant="danger", size="icon")
                    del_btn.setIcon(qta.icon("fa5s.trash", color="white"))
                    del_btn.setToolTip("Delete Product")
                    del_btn.clicked.connect(lambda checked, pid=p['id']: self.delete_product(pid))
                    
                    act_layout.addWidget(edit_btn)
                    act_layout.addWidget(del_btn)
                
                self.table.setCellWidget(i, 7, actions)

        task_manager.run_task(fetch_data, on_finished=on_loaded)

    def generate_barcode_img(self, code):
        if not code: return
        path, _ = QFileDialog.getSaveFileName(self, "Save Barcode", f"barcode_{code}.png", "Images (*.png)")
        if path:
            BarcodeGenerator.generate(code, path.replace(".png", ""))
            QMessageBox.information(self, "Success", "Barcode saved")

    def handle_barcode_scan(self):
        barcode = self.scan_input.text().strip()
        if not barcode: return
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, i.quantity 
                FROM products p 
                LEFT JOIN inventory i ON p.id = i.product_id 
                WHERE (p.barcode = ? OR p.sku = ?) AND p.is_active = 1
            """, (barcode, barcode))
            product = cursor.fetchone()
            
            if product:
                # Update existing quantity
                qty_add, ok = QInputDialog.getDouble(self, "Update Stock", 
                                                    f"Product: {product['name_en']} ({product['brand']})\nStock: {product['quantity'] or 0}\n\nEnter Quantity to ADD:", 
                                                    1, 0, 1000000)
                if ok and qty_add > 0:
                    cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE product_id = ?", 
                                 (qty_add, product['id']))
                    cursor.execute("INSERT INTO audit_logs (user_id, action, table_name, record_id, details) VALUES (?, ?, ?, ?, ?)",
                                 (self.current_user['id'], 'STOCK_IN', 'inventory', product['id'], f'Added {qty_add} via scan'))
                    conn.commit()
                    QMessageBox.information(self, "Success", "Stock updated")
                    print('\a', end='', flush=True) # Beep
                    self.load_products()
            else:
                # AUTOMATED REGISTRY POPUP (Point 13.1)
                reply = QMessageBox.question(self, "Not Found", 
                                           f"Barcode '{barcode}' is not registered.\nWould you like to register this new product now?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    self.add_product(barcode)
        
        self.scan_input.clear()
        self.scan_input.setFocus()

    def add_product(self, barcode=None):
        dialog = ProductDialog(initial_barcode=barcode)
        if dialog.exec():
            data = dialog.get_data()
            if not data: return
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO products (
                            barcode, sku, name_en, name_ps, name_dr, brand, category_id, 
                            product_type, cost_price, sale_price, wholesale_price, tax_rate, 
                            unit, min_stock, max_stock, expiry_date, mfg_date, batch_number, 
                            serial_number, supplier_id, supplier_sku, shelf_location, 
                            allow_negative_stock, returnable, track_inventory, 
                            allow_pos_price_change, allow_zero_price, internal_notes, created_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data['barcode'], data['sku'], data['name_en'], data['name_ps'], data['name_dr'],
                        data['brand'], data['category_id'], data['product_type'], data['cost_price'],
                        data['sale_price'], data['wholesale_price'], data['tax_rate'], data['unit'],
                        data['min_stock'], data['max_stock'], data['expiry_date'], data['mfg_date'],
                        data['batch_number'], data['serial_number'], data['supplier_id'], 
                        data['supplier_sku'], data['shelf_location'], data['allow_negative_stock'],
                        data['returnable'], data['track_inventory'], data['allow_pos_price_change'],
                        data['allow_zero_price'], data['internal_notes'], self.current_user['id']
                    ))
                    product_id = cursor.lastrowid
                    cursor.execute("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)", (product_id, data['quantity']))
                    conn.commit()
                self.load_products()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add product: {e}")

    def edit_product(self, product):
        dialog = ProductDialog(product)
        if dialog.exec():
            data = dialog.get_data()
            if not data: return
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE products SET 
                            barcode=?, sku=?, name_en=?, name_ps=?, name_dr=?, brand=?, 
                            category_id=?, product_type=?, cost_price=?, sale_price=?, 
                            wholesale_price=?, tax_rate=?, unit=?, min_stock=?, max_stock=?, 
                            expiry_date=?, mfg_date=?, batch_number=?, serial_number=?, 
                            supplier_id=?, supplier_sku=?, shelf_location=?, allow_negative_stock=?, 
                            returnable=?, track_inventory=?, allow_pos_price_change=?, 
                            allow_zero_price=?, internal_notes=?, last_updated_by=?, updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                    """, (
                        data['barcode'], data['sku'], data['name_en'], data['name_ps'], data['name_dr'],
                        data['brand'], data['category_id'], data['product_type'], data['cost_price'],
                        data['sale_price'], data['wholesale_price'], data['tax_rate'], data['unit'],
                        data['min_stock'], data['max_stock'], data['expiry_date'], data['mfg_date'],
                        data['batch_number'], data['serial_number'], data['supplier_id'], 
                        data['supplier_sku'], data['shelf_location'], data['allow_negative_stock'],
                        data['returnable'], data['track_inventory'], data['allow_pos_price_change'],
                        data['allow_zero_price'], data['internal_notes'], self.current_user['id'], product['id']
                    ))
                    cursor.execute("INSERT OR REPLACE INTO inventory (product_id, quantity) VALUES (?, ?)", (product['id'], data['quantity']))
                    conn.commit()
                self.load_products()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not edit product: {e}")

    def manage_categories(self):
        CategoryManagerDialog(self).exec()
        self.load_products()
    
    def show_inventory_tools(self):
        """Show inventory management tools dialog"""
        tools_dialog = QDialog(self)
        tools_dialog.setWindowTitle("Inventory Management Tools")
        tools_dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(tools_dialog)
        
        title = QLabel("<b>Inventory Management Tools</b>")
        title.setStyleSheet("font-size: 18px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Export Inventory
        export_group = QGroupBox("📤 Export Inventory")
        export_layout = QVBoxLayout(export_group)
        
        export_info = QLabel("Export current inventory data to CSV format")
        export_info.setStyleSheet("color: #666; font-size: 12px;")
        export_layout.addWidget(export_info)
        
        export_btn = QPushButton("Export to CSV")
        style_button(export_btn, variant="success")
        export_btn.clicked.connect(self.export_inventory)
        export_layout.addWidget(export_btn)
        
        layout.addWidget(export_group)
        
        # Print Labels
        labels_group = QGroupBox("🏷️ Print Labels")
        labels_layout = QVBoxLayout(labels_group)
        
        labels_info = QLabel("Generate printable barcode labels for products")
        labels_info.setStyleSheet("color: #666; font-size: 12px;")
        labels_layout.addWidget(labels_info)
        
        labels_btn = QPushButton("Generate Barcode Labels")
        style_button(labels_btn, variant="info")
        labels_btn.clicked.connect(self.print_labels)
        labels_layout.addWidget(labels_btn)
        
        layout.addWidget(labels_group)
        
        # Stock Adjustment
        adjust_group = QGroupBox("📊 Stock Adjustments")
        adjust_layout = QVBoxLayout(adjust_group)
        
        adjust_info = QLabel("View low stock items and perform bulk adjustments")
        adjust_info.setStyleSheet("color: #666; font-size: 12px;")
        adjust_layout.addWidget(adjust_info)
        
        low_stock_btn = QPushButton("View Low Stock Items")
        style_button(low_stock_btn, variant="warning")
        low_stock_btn.clicked.connect(self.show_low_stock)
        adjust_layout.addWidget(low_stock_btn)
        
        layout.addWidget(adjust_group)
        
        # Close button
        close_btn = QPushButton("Close")
        style_button(close_btn, variant="secondary")
        close_btn.clicked.connect(tools_dialog.close)
        layout.addWidget(close_btn)
        
        tools_dialog.exec()
    
    def export_inventory(self):
        """Export inventory to CSV"""
        import csv
        from datetime import datetime
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Inventory", 
            f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT p.id, p.barcode, p.name_en, p.brand, p.category_id, 
                               p.cost_price, p.sale_price, i.quantity, p.min_stock, p.unit
                        FROM products p
                        LEFT JOIN inventory i ON p.id = i.product_id
                        WHERE p.is_active = 1
                        ORDER BY p.name_en
                    """)
                    products = cursor.fetchall()
                
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Barcode', 'Product Name', 'Brand', 'Cost Price', 
                                   'Sale Price', 'Quantity', 'Min Stock', 'Unit'])
                    
                    for p in products:
                        writer.writerow([
                            p['id'], p['barcode'], p['name_en'], p['brand'] or '',
                            p['cost_price'], p['sale_price'], p['quantity'] or 0, 
                            p['min_stock'], p['unit'] or 'pcs'
                        ])
                
                QMessageBox.information(self, "Success", f"Inventory exported successfully to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export inventory: {str(e)}")
    
    def print_labels(self):
        """Generate printable barcode labels"""
        QMessageBox.information(self, "Print Labels", 
            "Barcode label printing feature:\n\n"
            "• Use the 'Barcode' button in the Actions column to generate individual labels\n"
            "• For bulk label printing, export inventory and use dedicated label software\n"
            "• Recommended: Use brother Label Printer or similar thermal printer")
    
    def show_low_stock(self):
        """Show low stock items"""
        low_stock_dialog = QDialog(self)
        low_stock_dialog.setWindowTitle("Low Stock Alert")
        low_stock_dialog.setMinimumSize(800, 500)
        
        layout = QVBoxLayout(low_stock_dialog)
        
        title = QLabel("<b>⚠️ Low Stock Items</b>")
        title.setStyleSheet("font-size: 18px; color: #e74c3c; margin-bottom: 10px;")
        layout.addWidget(title)
        
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["Product", "Brand", "Current Stock", "Min Stock", "Status"])
        style_table(table, variant="compact")
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.name_en, p.brand, i.quantity, p.min_stock
                FROM products p
                LEFT JOIN inventory i ON p.id = i.product_id
                WHERE p.is_active = 1 AND (i.quantity IS NULL OR i.quantity <= p.min_stock)
                ORDER BY i.quantity ASC
            """)
            low_stock_items = cursor.fetchall()
        
        for i, item in enumerate(low_stock_items):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(item['name_en']))
            table.setItem(i, 1, QTableWidgetItem(item['brand'] or 'N/A'))
            
            qty = item['quantity'] or 0
            qty_item = QTableWidgetItem(str(qty))
            qty_item.setForeground(Qt.GlobalColor.red)
            table.setItem(i, 2, qty_item)
            
            table.setItem(i, 3, QTableWidgetItem(str(item['min_stock'])))
            
            status = "⚠️ OUT OF STOCK" if qty == 0 else "⚠️ LOW STOCK"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(Qt.GlobalColor.red)
            table.setItem(i, 4, status_item)
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Close")
        style_button(close_btn, variant="secondary")
        close_btn.clicked.connect(low_stock_dialog.close)
        layout.addWidget(close_btn)
        
        low_stock_dialog.exec()
        
    def delete_product(self, pid):
        if QMessageBox.question(self, 'Delete', 'Are you sure?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET is_active = 0 WHERE id=?", (pid,))
                conn.commit()
            self.load_products()
