from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QPushButton, QLabel, QHeaderView, QGroupBox, 
                             QFormLayout, QLineEdit, QMessageBox, QTableWidgetItem, QDialog)
from PyQt6.QtCore import Qt
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.database.db_manager import db_manager

class AddPharmacySupplierDialog(QDialog):
    def __init__(self, parent=None, supplier_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add / Edit Pharmacy Supplier")
        self.setFixedWidth(400)
        self.supplier_data = supplier_data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.company_input = QLineEdit()
        self.contact_input = QLineEdit()
        
        if self.supplier_data:
            self.name_input.setText(self.supplier_data['name'])
            self.company_input.setText(self.supplier_data['company_name'] or "")
            self.contact_input.setText(self.supplier_data['contact'] or "")
            
        form.addRow("Supplier Name *:", self.name_input)
        form.addRow("Company Name:", self.company_input)
        form.addRow("Contact Number *:", self.contact_input)
        
        layout.addLayout(form)
        
        btns = QHBoxLayout()
        save = QPushButton("Save")
        style_button(save, variant="success")
        save.clicked.connect(self.save)
        
        cancel = QPushButton("Cancel")
        style_button(cancel, variant="outline")
        cancel.clicked.connect(self.reject)
        
        btns.addWidget(save)
        btns.addWidget(cancel)
        layout.addLayout(btns)

    def save(self):
        name = self.name_input.text().strip()
        company = self.company_input.text().strip()
        contact = self.contact_input.text().strip()
        
        if not name or not contact:
            QMessageBox.warning(self, "Error", "Name and Contact are required")
            return
            
        try:
            with db_manager.get_pharmacy_connection() as conn:
                if self.supplier_data:
                    conn.execute("UPDATE pharmacy_suppliers SET name=?, company_name=?, contact=? WHERE id=?", 
                                 (name, company, contact, self.supplier_data['id']))
                else:
                    conn.execute("INSERT INTO pharmacy_suppliers (name, company_name, contact) VALUES (?, ?, ?)",
                                 (name, company, contact))
                conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class PharmacySupplierView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        header_layout = QHBoxLayout()
        title = QLabel("Pharmacy Suppliers")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("+ Add Supplier")
        style_button(add_btn, variant="success")
        add_btn.clicked.connect(lambda: self.open_dialog())
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Full Name", "Company", "Contact", "Actions"])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_suppliers()

    def load_suppliers(self):
        self.table.setRowCount(0)
        try:
            with db_manager.get_pharmacy_connection() as conn:
                rows = conn.execute("SELECT * FROM pharmacy_suppliers WHERE is_active=1").fetchall()
                for i, row in enumerate(rows):
                    self.table.insertRow(i)
                    self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                    self.table.setItem(i, 1, QTableWidgetItem(row['name']))
                    self.table.setItem(i, 2, QTableWidgetItem(row['company_name'] or ""))
                    self.table.setItem(i, 3, QTableWidgetItem(row['contact'] or ""))
                    
                    actions = QWidget()
                    act_layout = QHBoxLayout(actions)
                    act_layout.setContentsMargins(2,2,2,2)
                    
                    edit_btn = QPushButton("Edit")
                    style_button(edit_btn, variant="success", size="small")
                    edit_btn.clicked.connect(lambda ch, r=row: self.open_dialog(r))
                    
                    del_btn = QPushButton("Del")
                    style_button(del_btn, variant="danger", size="small")
                    del_btn.clicked.connect(lambda ch, sid=row['id']: self.delete_supplier(sid))
                    
                    act_layout.addWidget(edit_btn)
                    act_layout.addWidget(del_btn)
                    self.table.setCellWidget(i, 4, actions)
        except Exception as e:
            print(f"Error loading suppliers: {e}")

    def open_dialog(self, supplier_data=None):
        dialog = AddPharmacySupplierDialog(self, supplier_data)
        if dialog.exec():
            self.load_suppliers()

    def delete_supplier(self, sid):
        if QMessageBox.question(self, "Confirm", "Delete this supplier?") == QMessageBox.StandardButton.Yes:
            with db_manager.get_pharmacy_connection() as conn:
                conn.execute("UPDATE pharmacy_suppliers SET is_active=0 WHERE id=?", (sid,))
                conn.commit()
            self.load_suppliers()
