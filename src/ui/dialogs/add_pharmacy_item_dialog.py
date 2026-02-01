from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QFormLayout, 
                             QDateEdit, QMessageBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate
from src.database.db_manager import db_manager
from src.ui.button_styles import style_button
from src.ui.theme_manager import theme_manager

class AddPharmacyItemDialog(QDialog):
    def __init__(self, parent=None, product_id=None, barcode=None):
        super().__init__(parent)
        self.product_id = product_id
        self.barcode_param = barcode
        self.setWindowTitle("Edit Pharmacy Item" if product_id else "Add New Pharmacy Item")
        self.setMinimumWidth(500)
        self.init_ui()
        if self.product_id:
            self.preload_data()
        elif self.barcode_param:
            self.barcode.setText(self.barcode_param)
            self.name.setFocus()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(15)
        
        # Core Info
        self.barcode = QLineEdit()
        self.barcode.setPlaceholderText("Scan or Enter Barcode")
        self.name = QLineEdit()
        self.name.setPlaceholderText("Medicine Name")
        self.generic = QLineEdit()
        self.generic.setPlaceholderText("Generic Name (Optional)")
        self.brand = QLineEdit()
        self.size = QLineEdit()
        self.size.setPlaceholderText("e.g. 500mg, 100ml")
        
        # Pricing
        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 100000)
        self.cost.setDecimals(2)
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 100000)
        self.price.setDecimals(2)
        
        # Initial Stock
        self.qty = QDoubleSpinBox()
        self.qty.setRange(0, 10000)
        self.batch = QLineEdit()
        self.batch.setPlaceholderText("Batch #")
        self.expiry = QDateEdit()
        self.expiry.setDisplayFormat("yyyy-MM-dd")
        self.expiry.setCalendarPopup(True)
        self.expiry.setDate(QDate.currentDate().addYears(1))
        
        self.supplier = QComboBox()
        self.load_suppliers()
        
        form.addRow("Barcode *:", self.barcode)
        form.addRow("Name *:", self.name)
        form.addRow("Generic Name:", self.generic)
        form.addRow("Brand:", self.brand)
        form.addRow("Size/Strength:", self.size)
        form.addRow("Supplier:", self.supplier)
        form.addRow("Cost Price:", self.cost)
        form.addRow("Sale Price *:", self.price)
        
        layout.addLayout(form)
        
        # Initial Stock Section
        layout.addWidget(QLabel("<b>Initial Stock Entry</b>"))
        stock_form = QFormLayout()
        stock_form.addRow("Quantity:", self.qty)
        stock_form.addRow("Batch Number *:", self.batch)
        stock_form.addRow("Expiry Date *:", self.expiry)
        layout.addLayout(stock_form)
        
        # Buttons
        btns = QHBoxLayout()
        save = QPushButton("Save Item")
        style_button(save, variant="success")
        save.clicked.connect(self.save)
        cancel = QPushButton("Cancel")
        style_button(cancel, variant="outline")
        cancel.clicked.connect(self.reject)
        btns.addWidget(save)
        btns.addWidget(cancel)
        
        layout.addLayout(btns)
        
    def load_suppliers(self):
        self.supplier.addItem("None", None)
        with db_manager.get_pharmacy_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM pharmacy_suppliers WHERE is_active = 1")
            for row in cursor.fetchall():
                self.supplier.addItem(row['name'], row['id'])
                
    def preload_data(self):
        try:
            with db_manager.get_pharmacy_connection() as conn:
                row = conn.execute("SELECT * FROM pharmacy_products WHERE id = ?", (self.product_id,)).fetchone()
                if row:
                    self.barcode.setText(row['barcode'])
                    self.name.setText(row['name_en'])
                    self.generic.setText(row['generic_name'] or "")
                    self.brand.setText(row['brand'] or "")
                    self.size.setText(row['size'] or "")
                    self.cost.setValue(row['cost_price'] or 0)
                    self.price.setValue(row['sale_price'] or 0)
                    
                    idx = self.supplier.findData(row['supplier_id'])
                    if idx >= 0: self.supplier.setCurrentIndex(idx)
        except Exception as e:
            print(f"Preload error: {e}")

    def save(self):
        barcode = self.barcode.text().strip()
        name = self.name.text().strip()
        price = self.price.value()
        batch = self.batch.text().strip()
        
        if not barcode or not name:
            QMessageBox.warning(self, "Required", "Barcode and Name are required.")
            return
            
        if self.qty.value() > 0 and not batch:
             QMessageBox.warning(self, "Required", "Batch number is required for stock entry.")
             return
             
        try:
            with db_manager.get_pharmacy_connection() as conn:
                cursor = conn.cursor()
                
                if self.product_id:
                    # Update Existing
                    if self.qty.value() > 0:
                        curr_qty_row = cursor.execute("SELECT SUM(quantity) FROM pharmacy_inventory WHERE product_id = ?", (self.product_id,)).fetchone()
                        curr_qty = curr_qty_row[0] or 0
                        old_cost = cursor.execute("SELECT cost_price FROM pharmacy_products WHERE id=?", (self.product_id,)).fetchone()['cost_price']
                        old_val = curr_qty * old_cost
                        new_val = self.qty.value() * self.cost.value()
                        total_qty = curr_qty + self.qty.value()
                        new_avg_cost = (old_val + new_val) / total_qty
                    else:
                        new_avg_cost = self.cost.value()

                    cursor.execute("""
                        UPDATE pharmacy_products SET
                        barcode=?, name_en=?, generic_name=?, brand=?, size=?, cost_price=?, sale_price=?, supplier_id=?
                        WHERE id=?
                    """, (barcode, name, self.generic.text(), self.brand.text(), self.size.text(),
                          new_avg_cost, price, self.supplier.currentData(), self.product_id))
                    prod_id = self.product_id
                else:
                    # Check if exists by barcode
                    existing = cursor.execute("SELECT id, cost_price FROM pharmacy_products WHERE barcode = ?", (barcode,)).fetchone()
                    if existing:
                        prod_id = existing['id']
                        if self.qty.value() > 0:
                            curr_qty_row = cursor.execute("SELECT SUM(quantity) FROM pharmacy_inventory WHERE product_id = ?", (prod_id,)).fetchone()
                            curr_qty = curr_qty_row[0] or 0
                            old_val = curr_qty * existing['cost_price']
                            new_val = self.qty.value() * self.cost.value()
                            total_qty = curr_qty + self.qty.value()
                            new_avg_cost = (old_val + new_val) / total_qty
                            cursor.execute("UPDATE pharmacy_products SET cost_price = ?, sale_price = ? WHERE id = ?", (new_avg_cost, price, prod_id))
                    else:
                        # 1. Insert Product
                        cursor.execute("""
                            INSERT INTO pharmacy_products 
                            (barcode, name_en, generic_name, brand, size, cost_price, sale_price, supplier_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (barcode, name, self.generic.text(), self.brand.text(), self.size.text(),
                              self.cost.value(), price, self.supplier.currentData()))
                        prod_id = cursor.lastrowid
                
                # 2. Insert/Update Inventory (if qty > 0)
                if self.qty.value() > 0:
                    # Check if this batch already exists for this product
                    existing_batch = cursor.execute("""
                        SELECT id, quantity FROM pharmacy_inventory
                        WHERE product_id = ? AND batch_number = ?
                    """, (prod_id, batch)).fetchone()

                    if existing_batch:
                        # Update existing batch quantity
                        new_quantity = existing_batch['quantity'] + self.qty.value()
                        cursor.execute("""
                            UPDATE pharmacy_inventory
                            SET quantity = ?, expiry_date = ?
                            WHERE id = ?
                        """, (new_quantity, self.expiry.date().toString("yyyy-MM-dd"), existing_batch['id']))
                    else:
                        # Insert new batch
                        cursor.execute("""
                            INSERT INTO pharmacy_inventory (product_id, batch_number, expiry_date, quantity)
                            VALUES (?, ?, ?, ?)
                        """, (prod_id, batch, self.expiry.date().toString("yyyy-MM-dd"), self.qty.value()))
                
                conn.commit()
                QMessageBox.information(self, "Success", "Pharmacy Item Updated/Added Successfully")
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database Error: {e}")

