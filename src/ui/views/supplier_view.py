from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt
import qtawesome as qta
from src.core.localization import lang_manager
from src.database.db_manager import db_manager
from src.core.auth import Auth
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button

class SupplierDialog(QDialog):
    def __init__(self, supplier=None):
        super().__init__()
        self.supplier = supplier
        self.setWindowTitle("Supplier Details")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.company = QLineEdit()
        self.contact = QLineEdit()
        
        if self.supplier:
            self.name.setText(self.supplier.get('name', ''))
            self.company.setText(self.supplier.get('company_name', ''))
            self.contact.setText(self.supplier.get('contact', ""))

        layout.addRow("Supplier Name:", self.name)
        layout.addRow("Company Name:", self.company)
        layout.addRow("Contact Number:", self.contact)
        
        btns = QHBoxLayout()
        save_btn = QPushButton("Save Supplier")
        style_button(save_btn, variant="success")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        style_button(cancel_btn, variant="secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addRow(btns)

    def get_data(self):
        return {
            'name': self.name.text(),
            'company_name': self.company.text(),
            'contact': self.contact.text()
        }

class SupplierView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = Auth.get_current_user()
        self.is_admin = self.current_user['role_name'] in ['Admin', 'Manager', 'SuperAdmin']
        self.init_ui()
        self.load_suppliers()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QFrame()
        self.container.setObjectName("card")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        header.addStretch()
        
        self.add_btn = QPushButton(" Register New Supplier")
        style_button(self.add_btn, variant="primary")
        self.add_btn.setIcon(qta.icon("fa5s.truck-loading", color="white"))
        self.add_btn.clicked.connect(self.add_supplier)
        if not self.is_admin:
            self.add_btn.hide()
        header.addWidget(self.add_btn)
        
        layout.addLayout(header)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Supplier Name", "Company", "Contact", "Actions"
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(4, 160)
        layout.addWidget(self.table)
        
        main_layout.addWidget(self.container)

    def load_suppliers(self):
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers")
            suppliers = [dict(row) for row in cursor.fetchall()]
            
            self.table.setRowCount(0)
            for i, s in enumerate(suppliers):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(s['id'])))
                self.table.setItem(i, 1, QTableWidgetItem(s['name']))
                self.table.setItem(i, 2, QTableWidgetItem(s['company_name'] or ''))
                self.table.setItem(i, 3, QTableWidgetItem(s['contact'] or ''))
                
                actions = QWidget()
                act_layout = QHBoxLayout(actions)
                act_layout.setContentsMargins(2, 2, 2, 2)
                
                if self.is_admin:
                    edit_btn = QPushButton()
                    style_button(edit_btn, variant="info", size="icon")
                    edit_btn.setIcon(qta.icon("fa5s.edit", color="white"))
                    edit_btn.clicked.connect(lambda checked, supp=dict(s): self.edit_supplier(supp))
                    
                    del_btn = QPushButton()
                    style_button(del_btn, variant="danger", size="icon")
                    del_btn.setIcon(qta.icon("fa5s.trash", color="white"))
                    del_btn.clicked.connect(lambda checked, sid=s['id']: self.delete_supplier(sid))
                    
                    act_layout.addWidget(edit_btn)
                    act_layout.addWidget(del_btn)
                
                self.table.setCellWidget(i, 4, actions)

    def add_supplier(self):
        dialog = SupplierDialog()
        if dialog.exec():
            data = dialog.get_data()
            if not data['name']: return
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO suppliers (name, company_name, contact) VALUES (?, ?, ?)", 
                             (data['name'], data['company_name'], data['contact']))
                conn.commit()
            self.load_suppliers()

    def edit_supplier(self, supplier):
        dialog = SupplierDialog(supplier)
        if dialog.exec():
            data = dialog.get_data()
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE suppliers SET name=?, company_name=?, contact=? WHERE id=?", 
                             (data['name'], data['company_name'], data['contact'], supplier['id']))
                conn.commit()
            self.load_suppliers()

    def delete_supplier(self, sid):
        reply = QMessageBox.question(self, 'Confirm Delete', "Delete this supplier?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM suppliers WHERE id=?", (sid,))
                conn.commit()
            self.load_suppliers()
