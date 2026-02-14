from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from src.database.db_manager import db_manager
from src.core.localization import lang_manager
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button

class PharmacyInventoryView(QWidget):
    def __init__(self):
        super().__init__()
        self.is_loading = False
        self.current_page = 1
        self.page_size = 50
        self.total_count = 0
        
        # Debounce timer for loading
        self.load_timer = QTimer(self)
        self.load_timer.setSingleShot(True)
        self.load_timer.setInterval(300)
        self.load_timer.timeout.connect(self._do_load_inventory)
        
        self.init_ui()
        
        # Refresh timer (e.g. every 5 mins)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(300000)
        self.refresh_timer.timeout.connect(self.load_inventory)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_timer.start()
        self.load_inventory()

    def hideEvent(self, event):
        self.refresh_timer.stop()
        super().hideEvent(event)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(lang_manager.get("search") + " " + lang_manager.get("medicine") + "...")
        self.search_input.setMinimumHeight(55)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.returnPressed.connect(self.handle_barcode_scan)
        header.addWidget(self.search_input)
        
        self.refresh_btn = QPushButton(lang_manager.get("refresh"))
        style_button(self.refresh_btn, variant="info")
        self.refresh_btn.clicked.connect(self.load_inventory)
        header.addWidget(self.refresh_btn)
        
        # New Add Button
        self.add_btn = QPushButton("+ " + lang_manager.get("add_product"))
        style_button(self.add_btn, variant="success")
        self.add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(self.add_btn)
        
        main_layout.addLayout(header)
        
        # Columns: Barcode, Name, Rank/Shelf, Size, Expiry, Price, Qty, Total Val, Cost, Brand, Company, Vendor, Contact, Actions
        self.table = QTableWidget(0, 14)
        self.table.setHorizontalHeaderLabels([
            lang_manager.get("barcode"), lang_manager.get("name"), 
            lang_manager.get("rack") or "Rack",
            lang_manager.get("size"), lang_manager.get("expiry_date"), 
            lang_manager.get("price"), lang_manager.get("quantity"), 
            lang_manager.get("total_val"), lang_manager.get("cost"), 
            lang_manager.get("brand"), lang_manager.get("company"), 
            lang_manager.get("vendor"), lang_manager.get("contact"), 
            lang_manager.get("actions")
        ])
        style_table(self.table, variant="premium")
        # Global ResizeToContents will handle most, but let's stretch the Name column
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # Fix width for Actions to make it bigger
        self.table.setColumnWidth(13, 220) 
        main_layout.addWidget(self.table)

        # Pagination Footer (Requirement 5)
        pag_layout = QHBoxLayout()
        pag_layout.addStretch()
        
        self.btn_prev = QPushButton(lang_manager.get("previous") or "Previous")
        self.btn_next = QPushButton(lang_manager.get("next") or "Next")
        self.page_label = QLabel("Page 1")
        
        style_button(self.btn_prev, variant="outline", size="small")
        style_button(self.btn_next, variant="outline", size="small")
        
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)
        
        pag_layout.addWidget(self.btn_prev)
        pag_layout.addWidget(self.page_label)
        pag_layout.addWidget(self.btn_next)
        pag_layout.addStretch()
        main_layout.addLayout(pag_layout)
        
        # Ensure scroll bar is always visible if content overflows
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def on_search_changed(self):
        self.current_page = 1
        self.load_inventory()

    def load_inventory(self):
        """Trigger debounced load"""
        self.load_timer.start()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_inventory()

    def next_page(self):
        self.current_page += 1
        self.load_inventory()

    def _do_load_inventory(self):
        """Actual data loading logic after debounce"""
        if self.is_loading:
            self.load_timer.start(500)
            return
            
        # Skip if app is not active to prevent background hangs
        from PyQt6.QtWidgets import QApplication
        if QApplication.applicationState() != Qt.ApplicationState.ApplicationActive:
            return
        
        search_term = self.search_input.text().strip()
        self.is_loading = True
        
        from src.core.blocking_task_manager import task_manager
        
        def do_load():
            try:
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
                    if search_term:
                        query += " AND (p.name_en LIKE ? OR p.barcode LIKE ?)"
                        params = [f"%{search_term}%", f"%{search_term}%"]
                    
                    offset = (self.current_page - 1) * self.page_size
                    
                    query += " GROUP BY p.id ORDER BY p.id DESC LIMIT ? OFFSET ?"
                    params.extend([self.page_size, offset])
                    
                    cursor.execute(query, params)
                    rows = [dict(row) for row in cursor.fetchall()]

                    # Get total count for page label
                    count_q = "SELECT COUNT(*) FROM pharmacy_products WHERE is_active = 1"
                    if search_term:
                        count_q += " AND (name_en LIKE ? OR barcode LIKE ?)"
                        cursor.execute(count_q, [f"%{search_term}%", f"%{search_term}%"])
                    else:
                        cursor.execute(count_q)
                    total = cursor.fetchone()[0]
                    
                    return {"success": True, "rows": rows, "total": total}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(result):
            self.is_loading = False
            if not result["success"]:
                print(f"Inventory Load Error: {result['error']}")
                return

            self.total_count = result["total"]
            total_pages = (self.total_count + self.page_size - 1) // self.page_size
            self.page_label.setText(f"Page {self.current_page} of {max(1, total_pages)}")
            self.btn_prev.setEnabled(self.current_page > 1)
            self.btn_next.setEnabled(self.current_page < total_pages)

            from PyQt6.QtGui import QColor

            self.table.setRowCount(0)
            for i, p in enumerate(result["rows"]):
                self.table.insertRow(i)
                qty = p['quantity'] or 0
                price = p['sale_price'] or 0
                pack_size = p.get('pack_size', 1) or 1
                
                # Calculate Total Value (Approx based on pack price if sold as packs)
                # If quantity is total units, and price is Pack Price:
                # Value = (qty / pack_size) * price
                if pack_size > 0:
                    total_val = (qty / pack_size) * price
                else:
                    total_val = 0
                
                self.table.setItem(i, 0, QTableWidgetItem(str(p['barcode'] or '')))
                self.table.setItem(i, 1, QTableWidgetItem(str(p['name_en'] or '')))
                
                # Rack Column
                self.table.setItem(i, 2, QTableWidgetItem(str(p['shelf_location'] or '')))

                self.table.setItem(i, 3, QTableWidgetItem(str(p['size'] or 'N/A')))
                self.table.setItem(i, 4, QTableWidgetItem(str(p['expiry_date'] or 'N/A')))
                self.table.setItem(i, 5, QTableWidgetItem(f"{price:.2f}"))
                
                # Quantity with Packs + Units Display
                if pack_size > 1:
                    packs = int(qty // pack_size)
                    units = int(qty % pack_size)
                    qty_str = f"{packs} Packs + {units} Units"
                else:
                    qty_str = f"{qty} Units"
                
                qty_item = QTableWidgetItem(qty_str)
                qty_item.setData(Qt.ItemDataRole.UserRole, qty) # Store raw qty for sorting/logic
                
                min_stock = p.get('min_stock', 10) # Default to 10 if not set
                if min_stock is None: min_stock = 10
                
                # Check low stock in base units? checking min_stock (usually packs?)
                # If min_stock is packs, compare with qty/pack_size
                # Let's assume min_stock is in Packs for now as that's intuitive
                current_packs = qty / pack_size if pack_size else 0
                
                if current_packs < min_stock:
                     qty_item.setForeground(QColor("red"))
                     font = qty_item.font()
                     font.setBold(True)
                     qty_item.setFont(font)
                
                self.table.setItem(i, 6, qty_item)

                self.table.setItem(i, 7, QTableWidgetItem(f"{total_val:.2f}"))
                self.table.setItem(i, 8, QTableWidgetItem(f"{p['cost_price']:.2f}"))
                self.table.setItem(i, 9, QTableWidgetItem(str(p['brand'] or 'N/A')))
                self.table.setItem(i, 10, QTableWidgetItem(str(p['company_name'] or 'N/A')))
                self.table.setItem(i, 11, QTableWidgetItem(str(p['supplier_name'] or 'N/A')))
                self.table.setItem(i, 12, QTableWidgetItem(str(p['supplier_contact'] or 'N/A')))
                
                actions = QWidget()
                act_layout = QHBoxLayout(actions)
                act_layout.setContentsMargins(0,0,0,0)
                act_layout.setSpacing(5)
                
                import qtawesome as qta
                
                edit_btn = QPushButton(" " + lang_manager.get("edit"))
                edit_btn.setIcon(qta.icon("fa5s.edit", color="white"))
                style_button(edit_btn, variant="info")
                edit_btn.setMinimumHeight(40)
                edit_btn.clicked.connect(lambda checked, p_id=p['id']: self.edit_product(p_id))
                
                delete_btn = QPushButton(" " + lang_manager.get("delete"))
                delete_btn.setIcon(qta.icon("fa5s.trash", color="white"))
                style_button(delete_btn, variant="danger")
                delete_btn.setMinimumHeight(40)
                delete_btn.clicked.connect(lambda checked, p_id=p['id']: self.delete_product(p_id))
                
                act_layout.addWidget(edit_btn)
                act_layout.addWidget(delete_btn)
                self.table.setCellWidget(i, 13, actions)
            
            self.table.resizeRowsToContents()

        task_manager.run_task(do_load, on_finished=on_finished)

    def handle_barcode_scan(self):
        barcode = self.search_input.text().strip()
        if not barcode: return
        
        from src.core.blocking_task_manager import task_manager
        
        def do_scan():
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    res = conn.execute("SELECT id FROM pharmacy_products WHERE barcode = ? AND is_active=1", (barcode,)).fetchone()
                    return {"success": True, "id": res['id'] if res else None}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(result):
            if not result["success"]:
                print(f"Scan error: {result['error']}")
                return
                
            if result["id"]:
                self.edit_product(result["id"])
            else:
                self.open_add_dialog(barcode=barcode)

        task_manager.run_task(do_scan, on_finished=on_finished)

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
        confirm = QMessageBox.question(
            self, lang_manager.get("confirm_delete"), 
            lang_manager.get("confirm_delete") + "?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if confirm == QMessageBox.StandardButton.Yes:
            from src.core.blocking_task_manager import task_manager
            
            def do_delete():
                try:
                    with db_manager.get_pharmacy_connection() as conn:
                        conn.execute("UPDATE pharmacy_products SET is_active=0 WHERE id=?", (product_id,))
                        conn.commit()
                    return True
                except:
                    return False

            def on_finished(success):
                if success:
                    self.load_inventory()
                else:
                    QMessageBox.critical(self, "Error", "Could not delete product")

            task_manager.run_task(do_delete, on_finished=on_finished)

