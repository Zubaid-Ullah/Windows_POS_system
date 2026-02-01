from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
import qtawesome as qta
from src.database.db_manager import db_manager
from src.core.localization import lang_manager
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button

class PharmacyInventoryView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_inventory()
        
        # Auto-refresh timer (every 10 seconds)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(10000)  # 10 seconds
        self.refresh_timer.timeout.connect(self.load_inventory)
        self.refresh_timer.start()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Scan barcode or search medicine...")
        self.search_input.setMinimumHeight(55)
        self.search_input.textChanged.connect(self.load_inventory)
        self.search_input.returnPressed.connect(self.handle_barcode_scan)
        header.addWidget(self.search_input)
        
        self.refresh_btn = QPushButton("Refresh")
        style_button(self.refresh_btn, variant="info")
        self.refresh_btn.clicked.connect(self.load_inventory)
        header.addWidget(self.refresh_btn)
        
        # New Add Button
        self.add_btn = QPushButton("+ Add Medicine")
        style_button(self.add_btn, variant="success")
        self.add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(self.add_btn)
        
        main_layout.addLayout(header)
        
        # Columns: Barcode, Name, Size, Expiry, Price, Qty, Total Val, Cost, Brand, Company, Vendor, Contact, Actions
        self.table = QTableWidget(0, 13)
        self.table.setHorizontalHeaderLabels([
            "Barcode", "Name", "Size", "Expiry", "Price", "Qty", "Total Val", "Cost", "Brand", "Company", "Vendor", "Contact", "Actions"
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        main_layout.addWidget(self.table)

    def load_inventory(self):
        search = self.search_input.text().strip()
        with db_manager.get_pharmacy_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT p.*, SUM(i.quantity) as quantity, MIN(i.expiry_date) as expiry_date,
                       s.name as supplier_name, s.contact as supplier_contact, s.company_name
                FROM pharmacy_products p 
                LEFT JOIN pharmacy_inventory i ON p.id = i.product_id
                LEFT JOIN pharmacy_suppliers s ON p.supplier_id = s.id
                WHERE p.is_active = 1
            """
            params = []
            if search:
                query += " AND (p.name_en LIKE ? OR p.barcode LIKE ?)"
                params = [f"%{search}%", f"%{search}%"]
            
            query += " GROUP BY p.id"
            
            cursor.execute(query, params)
            products = [dict(row) for row in cursor.fetchall()]
            
            self.table.setRowCount(0)
            for i, p in enumerate(products):
                self.table.insertRow(i)
                qty = p['quantity'] or 0
                price = p['sale_price'] or 0
                total_val = qty * price
                
                self.table.setItem(i, 0, QTableWidgetItem(str(p['barcode'] or '')))
                self.table.setItem(i, 1, QTableWidgetItem(str(p['name_en'] or '')))
                self.table.setItem(i, 2, QTableWidgetItem(str(p['size'] or 'N/A')))
                self.table.setItem(i, 3, QTableWidgetItem(str(p['expiry_date'] or 'N/A')))
                self.table.setItem(i, 4, QTableWidgetItem(f"{price:.2f}"))
                self.table.setItem(i, 5, QTableWidgetItem(str(qty)))
                self.table.setItem(i, 6, QTableWidgetItem(f"{total_val:.2f}"))
                self.table.setItem(i, 7, QTableWidgetItem(f"{p['cost_price']:.2f}"))
                self.table.setItem(i, 8, QTableWidgetItem(str(p['brand'] or 'N/A')))
                self.table.setItem(i, 9, QTableWidgetItem(str(p['company_name'] or 'N/A')))
                self.table.setItem(i, 10, QTableWidgetItem(str(p['supplier_name'] or 'N/A')))
                self.table.setItem(i, 11, QTableWidgetItem(str(p['supplier_contact'] or 'N/A')))
                
                actions = QWidget()
                act_layout = QHBoxLayout(actions)
                act_layout.setContentsMargins(0,0,0,0)
                act_layout.setSpacing(5)
                
                edit_btn = QPushButton("Edit")
                style_button(edit_btn, variant="info", size="small")
                edit_btn.clicked.connect(lambda checked, p_id=p['id']: self.edit_product(p_id))
                
                delete_btn = QPushButton("Del")
                style_button(delete_btn, variant="danger", size="small")
                delete_btn.clicked.connect(lambda checked, p_id=p['id']: self.delete_product(p_id))
                
                act_layout.addWidget(edit_btn)
                act_layout.addWidget(delete_btn)
                self.table.setCellWidget(i, 12, actions)

    def handle_barcode_scan(self):
        barcode = self.search_input.text().strip()
        if not barcode: return
        
        try:
            with db_manager.get_pharmacy_connection() as conn:
                res = conn.execute("SELECT id FROM pharmacy_products WHERE barcode = ? AND is_active=1", (barcode,)).fetchone()
                if res:
                    self.edit_product(res['id'])
                else:
                    self.open_add_dialog(barcode=barcode)
        except Exception as e:
            print(f"Scan error: {e}")

    def open_add_dialog(self, barcode=None):
        from src.ui.dialogs.add_pharmacy_item_dialog import AddPharmacyItemDialog
        dialog = AddPharmacyItemDialog(self, barcode=barcode)
        if dialog.exec():
            self.load_inventory()

    def edit_product(self, product_id):
        from src.ui.dialogs.add_pharmacy_item_dialog import AddPharmacyItemDialog
        dialog = AddPharmacyItemDialog(self, product_id=product_id)
        if dialog.exec():
            self.load_inventory()

    def delete_product(self, product_id):
        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this product?")
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    conn.execute("UPDATE pharmacy_products SET is_active=0 WHERE id=?", (product_id,))
                    conn.commit()
                self.load_inventory()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete product: {e}")
