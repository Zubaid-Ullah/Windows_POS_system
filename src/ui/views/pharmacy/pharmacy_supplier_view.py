from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QPushButton, QLabel, QHeaderView, QGroupBox, 
                             QFormLayout, QLineEdit, QMessageBox, QTableWidgetItem, QDialog)
from PyQt6.QtCore import Qt
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.database.db_manager import db_manager
from src.core.localization import lang_manager

class AddPharmacySupplierDialog(QDialog):
    def __init__(self, parent=None, supplier_data=None):
        super().__init__(parent)
        self.supplier_data = supplier_data
        self.setWindowTitle(lang_manager.get("add_edit_supplier"))
        self.setFixedWidth(450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(lang_manager.get("name") + "*")
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText(lang_manager.get("company"))
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText(lang_manager.get("contact"))
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText(lang_manager.get("address"))
        
        if self.supplier_data:
            self.name_input.setText(self.supplier_data['name'])
            self.company_input.setText(self.supplier_data['company_name'] or "")
            self.contact_input.setText(self.supplier_data['contact'] or "")
            self.address_input.setText(self.supplier_data['address'] or "")
            
        form.addRow(lang_manager.get("name") + ":", self.name_input)
        form.addRow(lang_manager.get("company") + ":", self.company_input)
        form.addRow(lang_manager.get("contact") + ":", self.contact_input)
        form.addRow(lang_manager.get("address") + ":", self.address_input)
        
        layout.addLayout(form)
        
        btns = QHBoxLayout()
        self.save_btn = QPushButton(lang_manager.get("save"))
        style_button(self.save_btn, variant="success")
        self.save_btn.clicked.connect(self.save)
        
        cancel = QPushButton(lang_manager.get("cancel"))
        style_button(cancel, variant="outline")
        cancel.clicked.connect(self.reject)
        
        btns.addWidget(self.save_btn)
        btns.addWidget(cancel)
        layout.addLayout(btns)

    def save(self):
        name = self.name_input.text().strip()
        company = self.company_input.text().strip()
        contact = self.contact_input.text().strip()
        address = self.address_input.text().strip()
        
        if not name or not contact:
            QMessageBox.warning(self, lang_manager.get("error"), lang_manager.get("name_contact_required"))
            return
            
        try:
            with db_manager.get_pharmacy_connection() as conn:
                if self.supplier_data:
                    conn.execute("UPDATE pharmacy_suppliers SET name=?, company_name=?, contact=?, address=? WHERE id=?", 
                                 (name, company, contact, address, self.supplier_data['id']))
                else:
                    conn.execute("INSERT INTO pharmacy_suppliers (name, company_name, contact, address) VALUES (?, ?, ?, ?)",
                                 (name, company, contact, address))
                conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, lang_manager.get("error"), str(e))


class PharmacySupplierView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        header_layout = QHBoxLayout()
        title = QLabel(lang_manager.get("suppliers"))
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("+ " + lang_manager.get("add_supplier"))
        style_button(add_btn, variant="success")
        add_btn.clicked.connect(lambda: self.open_dialog())
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "ID", lang_manager.get("name"), lang_manager.get("company"), 
            lang_manager.get("contact"), lang_manager.get("actions")
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_suppliers()

    def load_suppliers(self):
        from src.core.blocking_task_manager import task_manager
        
        def do_load():
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    return {"success": True, "rows": [dict(r) for r in conn.execute("SELECT * FROM pharmacy_suppliers WHERE is_active=1").fetchall()]}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(result):
            if not result["success"]:
                print(f"Error loading suppliers: {result['error']}")
                return

            self.table.setRowCount(0)
            for i, row in enumerate(result["rows"]):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                self.table.setItem(i, 1, QTableWidgetItem(row['name']))
                self.table.setItem(i, 2, QTableWidgetItem(row['company_name'] or ""))
                self.table.setItem(i, 3, QTableWidgetItem(row['contact'] or ""))
                
                actions = QWidget()
                act_layout = QHBoxLayout(actions)
                act_layout.setContentsMargins(2,2,2,2)
                
                edit_btn = QPushButton(lang_manager.get("edit"))
                style_button(edit_btn, variant="info", size="small")
                edit_btn.clicked.connect(lambda ch, s=row: self.open_dialog(s))
                
                del_btn = QPushButton(lang_manager.get("delete"))
                style_button(del_btn, variant="danger", size="small")
                del_btn.clicked.connect(lambda ch, sid=row['id']: self.delete_supplier(cid=sid))
                
                act_layout.addWidget(edit_btn)
                act_layout.addWidget(del_btn)
                self.table.setCellWidget(i, 4, actions)

        task_manager.run_task(do_load, on_finished=on_finished)

    def open_dialog(self, supplier_data=None):
        dialog = AddPharmacySupplierDialog(self, supplier_data)
        if dialog.exec():
            self.load_suppliers()

    def delete_supplier(self, sid):
        if QMessageBox.question(self, lang_manager.get("confirm"), lang_manager.get("confirm_delete_supplier")) == QMessageBox.StandardButton.Yes:
            with db_manager.get_pharmacy_connection() as conn:
                conn.execute("UPDATE pharmacy_suppliers SET is_active=0 WHERE id=?", (sid,))
                conn.commit()
            self.load_suppliers()
