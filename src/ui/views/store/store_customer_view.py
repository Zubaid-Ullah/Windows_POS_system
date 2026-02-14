import os
import uuid

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDialog, QFormLayout, QComboBox, QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
import qtawesome as qta

from src.core.localization import lang_manager
from src.database.db_manager import db_manager
from src.core.auth import Auth
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button


class CustomerDialog(QDialog):
    def __init__(self, customer=None):
        super().__init__()
        self.customer = customer
        self.setWindowTitle("Customer Details & KYC")
        self.setMinimumWidth(500)
        self.photo_path = None
        self.id_photo_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel("Customer Information & KYC")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1b2559; margin-bottom: 10px;")
        layout.addWidget(header)

        basic_group = QFrame()
        basic_group.setObjectName("customer_basic_group")
        basic_group.setStyleSheet("""
            QFrame#customer_basic_group {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e0e5f2;
            }
        """)
        basic_layout = QVBoxLayout(basic_group)
        basic_layout.setContentsMargins(15, 15, 15, 15)

        basic_title = QLabel("Basic Information")
        basic_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4318ff; margin-bottom: 10px;")
        basic_layout.addWidget(basic_title)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_en = QLineEdit()
        self.name_en.setPlaceholderText("Enter customer's full name")
        self.name_en.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Enter phone number")
        self.phone.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")

        self.address = QTextEdit()
        self.address.setFixedHeight(80)
        self.address.setPlaceholderText("Enter customer's home address")
        self.address.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; font-size: 13px; padding: 4px;")

        form.addRow("Full Name:", self.name_en)
        form.addRow("Contact Number:", self.phone)
        form.addRow("Home Address:", self.address)

        basic_layout.addLayout(form)
        layout.addWidget(basic_group)

        loan_group = QFrame()
        loan_group.setObjectName("customer_loan_group")
        loan_group.setStyleSheet("""
            QFrame#customer_loan_group {
                background-color: #fff8f0;
                border-radius: 8px;
                border: 1px solid #ffe4c4;
            }
        """)
        loan_layout = QVBoxLayout(loan_group)
        loan_layout.setContentsMargins(15, 15, 15, 15)

        loan_title = QLabel("Credit & Loan Settings")
        loan_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff9800; margin-bottom: 10px;")
        loan_layout.addWidget(loan_title)

        loan_form = QFormLayout()
        loan_form.setSpacing(12)

        self.loan_enabled = QComboBox()
        self.loan_enabled.setMinimumWidth(100)
        self.loan_enabled.addItems(["No", "Yes"])
        self.loan_enabled.setStyleSheet("padding: 6px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")

        self.loan_limit = QLineEdit()
        self.loan_limit.setPlaceholderText("Maximum loan amount")
        self.loan_limit.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")

        loan_form.addRow("Allow Credit Sales:", self.loan_enabled)
        loan_form.addRow("Credit Limit (AFN):", self.loan_limit)

        loan_layout.addLayout(loan_form)
        layout.addWidget(loan_group)

        if self.customer:
            self.name_en.setText(self.customer['name_en'])
            self.phone.setText(self.customer['phone'] or "")
            self.address.setPlainText(self.customer.get('home_address', ""))
            self.loan_enabled.setCurrentIndex(1 if self.customer['loan_enabled'] else 0)
            self.loan_limit.setText(str(self.customer['loan_limit'] or 0))
            self.photo_path = self.customer.get('photo')
            self.id_photo_path = self.customer.get('id_card_photo')

        layout.addWidget(QLabel("<b>Security Verification (KYC)</b>"))
        kyc_box = QVBoxLayout()
        
        # Row 1: Profile Photo
        p_row = QHBoxLayout()
        self.photo_preview = QLabel("No Photo")
        self.photo_preview.setFixedSize(100, 100)
        self.photo_preview.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        p_btns = QVBoxLayout()
        self.photo_status = QLabel("Profile Photo: " + ("Registered" if self.photo_path else "Pending"))
        take_photo_btn = QPushButton("Take Photo")
        style_button(take_photo_btn, variant="outline")
        take_photo_btn.clicked.connect(self.take_photo)
        p_btns.addWidget(self.photo_status)
        p_btns.addWidget(take_photo_btn)
        
        p_row.addWidget(self.photo_preview)
        p_row.addLayout(p_btns)
        p_row.addStretch()
        kyc_box.addLayout(p_row)
        
        kyc_box.addSpacing(10)
        
        # Row 2: ID Photo
        id_row = QHBoxLayout()
        self.id_preview = QLabel("No ID")
        self.id_preview.setFixedSize(100, 100)
        self.id_preview.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
        self.id_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        id_btns = QVBoxLayout()
        self.id_status = QLabel("ID Card: " + ("Registered" if self.id_photo_path else "Pending"))
        take_id_btn = QPushButton("Take ID Photo")
        style_button(take_id_btn, variant="outline")
        take_id_btn.clicked.connect(self.take_id_photo)
        id_btns.addWidget(self.id_status)
        id_btns.addWidget(take_id_btn)
        
        id_row.addWidget(self.id_preview)
        id_row.addLayout(id_btns)
        id_row.addStretch()
        kyc_box.addLayout(id_row)
        
        layout.addLayout(kyc_box)

        # Pre-load existing photos if any
        from PyQt6.QtGui import QPixmap
        if self.photo_path and os.path.exists(self.photo_path):
             self.photo_preview.setPixmap(QPixmap(self.photo_path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
        if self.id_photo_path and os.path.exists(self.id_photo_path):
             self.id_preview.setPixmap(QPixmap(self.id_photo_path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))

        btns = QHBoxLayout()
        save_btn = QPushButton("Save Customer")
        style_button(save_btn, variant="success")
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn = QPushButton("Cancel")
        style_button(cancel_btn, variant="secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def take_photo(self):
        from src.utils.camera import capture_image
        from PyQt6.QtGui import QPixmap
        path = os.path.join("data", "kyc", f"cust_{uuid.uuid4()}.jpg")
        success, msg = capture_image(path, self)
        if success:
            self.photo_path = path
            self.photo_status.setText("Profile Photo: Captured ✓")
            self.photo_status.setStyleSheet("color: #05cd99; font-weight: bold;")
            self.photo_preview.setPixmap(QPixmap(path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            if msg:
                QMessageBox.warning(self, "Camera Error", msg)

    def take_id_photo(self):
        from src.utils.camera import capture_image
        from PyQt6.QtGui import QPixmap
        path = os.path.join("data", "kyc", f"id_{uuid.uuid4()}.jpg")
        success, msg = capture_image(path, self)
        if success:
            self.id_photo_path = path
            self.id_status.setText("ID Card: Captured ✓")
            self.id_status.setStyleSheet("color: #05cd99; font-weight: bold;")
            self.id_preview.setPixmap(QPixmap(path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            if msg:
                QMessageBox.warning(self, "Camera Error", msg)

    def validate_and_accept(self):
        if not self.name_en.text() or not self.phone.text():
            QMessageBox.warning(self, "Required Fields", "Name and Contact Number are mandatory.")
            return
        
        # Mandatory Photo (Requirement 4)
        if not self.photo_path or not os.path.exists(self.photo_path):
             QMessageBox.warning(self, "Required Field", "Customer Profile Photo is mandatory for KYC.")
             return
             
        self.accept()

    def get_data(self):
        try:
            val = float(self.loan_limit.text() or 0)
        except Exception:
            val = 0
        return {
            'name_en': self.name_en.text(),
            'phone': self.phone.text(),
            'address': self.address.toPlainText(),
            'loan_enabled': self.loan_enabled.currentIndex(),
            'loan_limit': val,
            'photo': self.photo_path,
            'id_card_photo': self.id_photo_path
        }


class StoreCustomerView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = Auth.get_current_user()
        perms = Auth.get_user_permissions(self.current_user)
        self.is_admin = '*' in perms or 'customers' in perms or 'customers_edit' in perms
        self.current_page = 1
        self.page_size = 50
        self.total_pages = 1
        self.is_loading = False

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(500)
        self.refresh_timer.timeout.connect(self._do_load_customers)

        self.init_ui()
        if hasattr(self, 'table'):
            self.table.viewport().installEventFilter(self)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_customers()

    def hideEvent(self, event):
        self.refresh_timer.stop()
        super().hideEvent(event)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame()
        self.container.setObjectName("card")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        header = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customer by name or phone...")
        self.search_input.setFixedHeight(35)
        self.search_input.textChanged.connect(self.load_customers)
        header.addWidget(self.search_input)

        self.add_btn = QPushButton(" Add New Customer")
        style_button(self.add_btn, variant="primary")
        self.add_btn.setIcon(qta.icon("fa5s.user-plus", color="white"))
        self.add_btn.clicked.connect(self.add_customer)
        if not self.is_admin:
            self.add_btn.hide()
        header.addWidget(self.add_btn)

        layout.addLayout(header)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Photo", "Full Name", "Contact", "Balance", "Actions"
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 60) # Photo col
        self.table.setColumnWidth(5, 200) # Actions col
        
        # Hover Preview Setup
        self.table.setMouseTracking(True)
        self.hover_preview = QLabel(self)
        self.hover_preview.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.hover_preview.setStyleSheet("border: 2px solid #4318ff; background: white; padding: 2px;")
        self.hover_preview.hide()
        
        # Debounce timer for hover
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.setInterval(150) # 150ms delay
        self.hover_timer.timeout.connect(self._do_show_hover)
        self._pending_hover_path = None
        self._pending_hover_pos = None

        layout.addWidget(self.table)

        pag_layout = QHBoxLayout()
        pag_layout.addStretch()

        self.prev_btn = QPushButton("Previous")
        style_button(self.prev_btn, variant="outline", size="small")
        self.prev_btn.clicked.connect(self.prev_page)

        self.page_label = QLabel("Page 1")
        self.page_label.setStyleSheet("font-weight: bold; color: #555;")

        self.next_btn = QPushButton("Next")
        style_button(self.next_btn, variant="outline", size="small")
        self.next_btn.clicked.connect(self.next_page)

        pag_layout.addWidget(self.prev_btn)
        pag_layout.addWidget(self.page_label)
        pag_layout.addWidget(self.next_btn)
        pag_layout.addStretch()

        layout.addLayout(pag_layout)
        main_layout.addWidget(self.container)

    def load_customers(self):
        self.refresh_timer.start()

    def _do_load_customers(self):
        from PyQt6.QtWidgets import QApplication
        if QApplication.applicationState() != Qt.ApplicationState.ApplicationActive or not self.isVisible():
            self.is_loading = False
            return
        if self.is_loading:
            return
        self.is_loading = True

        search = self.search_input.text().strip()
        from src.core.blocking_task_manager import task_manager

        def fetch_data():
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                base_query = "FROM customers WHERE is_active = 1"
                params = []
                if search:
                    base_query += " AND (name_en LIKE ? OR phone LIKE ?)"
                    params.extend([f"%{search}%", f"%{search}%"])

                cursor.execute(f"SELECT COUNT(*) {base_query}", params)
                total_count = cursor.fetchone()[0]

                offset = (self.current_page - 1) * self.page_size
                query = f"SELECT * {base_query} ORDER BY id DESC LIMIT ? OFFSET ?"
                params.extend([self.page_size, offset])
                cursor.execute(query, params)
                rows = [dict(row) for row in cursor.fetchall()]
                return {"rows": rows, "total": total_count}

        def on_loaded(result):
            self.is_loading = False
            customers = result["rows"]
            total_count = result["total"]

            self.total_pages = (total_count + self.page_size - 1) // self.page_size
            self.page_label.setText(f"Page {self.current_page} of {max(1, self.total_pages)}")
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < max(1, self.total_pages))

            self.table.setRowCount(0)
            for i, c in enumerate(customers):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(c['id'])))
                
                # Photo Thumbnail (Requirement 4)
                photo_item = QLabel()
                photo_item.setFixedSize(45, 45)
                photo_item.setAlignment(Qt.AlignmentFlag.AlignCenter)
                photo_path = c.get('photo')
                if photo_path and os.path.exists(photo_path):
                    photo_item.full_photo_path = photo_path # Custom property for hover
                    self.load_thumbnail_async(photo_path, photo_item)
                else:
                    photo_item.setText("N/A")
                    photo_item.full_photo_path = None
                self.table.setCellWidget(i, 1, photo_item)

                self.table.setItem(i, 2, QTableWidgetItem(c['name_en']))
                self.table.setItem(i, 3, QTableWidgetItem(c['phone'] or ""))
                self.table.setItem(i, 4, QTableWidgetItem(f"{float(c['balance'] or 0):,.2f}"))
                
                # Actions... (rest of the row)
                actions = QWidget()
                act_layout = QHBoxLayout(actions)
                act_layout.setContentsMargins(2, 2, 2, 2)

                pay_btn = QPushButton("Pay")
                style_button(pay_btn, variant="success", size="small")
                pay_btn.clicked.connect(lambda checked, cid=c['id']: self.make_payment(cid))
                act_layout.addWidget(pay_btn)

                if self.is_admin:
                    edit_btn = QPushButton()
                    style_button(edit_btn, variant="info", size="icon")
                    edit_btn.setIcon(qta.icon("fa5s.edit", color="white"))
                    edit_btn.clicked.connect(lambda checked, cust=c: self.edit_customer(cust))

                    del_btn = QPushButton()
                    style_button(del_btn, variant="danger", size="icon")
                    del_btn.setIcon(qta.icon("fa5s.trash", color="white"))
                    del_btn.clicked.connect(lambda checked, cid=c['id']: self.delete_customer(cid))

                    act_layout.addWidget(edit_btn)
                    act_layout.addWidget(del_btn)

                self.table.setCellWidget(i, 5, actions)

            self.table.resizeColumnsToContents()
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            self.table.setColumnWidth(5, 200)

        task_manager.run_task(fetch_data, on_finished=on_loaded)

    def load_thumbnail_async(self, path, label):
        from src.core.blocking_task_manager import task_manager
        from PyQt6.QtGui import QImage, QPixmap

        def scale_image():
            try:
                img = QImage(path)
                if img.isNull(): return None
                scaled = img.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                return scaled
            except: return None

        def on_finished(scaled_img):
            if scaled_img:
                label.setPixmap(QPixmap.fromImage(scaled_img))

        task_manager.run_task(scale_image, on_finished=on_finished)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_customers()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_customers()

    def eventFilter(self, source, event):
        if source is self.table.viewport() and event.type() == event.Type.MouseMove:
            self.handle_table_hover(event)
        return super().eventFilter(source, event)

    def handle_table_hover(self, event):
        index = self.table.indexAt(event.pos())
        if index.isValid() and index.column() == 1:
            row = index.row()
            cell_widget = self.table.cellWidget(row, 1)
            if cell_widget and hasattr(cell_widget, 'full_photo_path'):
                path = cell_widget.full_photo_path
                if path:
                    from PyQt6.QtGui import QCursor
                    self._pending_hover_path = path
                    self._pending_hover_pos = QCursor.pos()
                    self.hover_timer.start()
                    return
        self._pending_hover_path = None
        self.hover_timer.stop()
        self.hover_preview.hide()

    def _do_show_hover(self):
        path = self._pending_hover_path
        pos = self._pending_hover_pos
        if not path or not os.path.exists(path):
            self.hover_preview.hide()
            return

        from src.core.blocking_task_manager import task_manager
        from PyQt6.QtGui import QImage, QPixmap

        def scale_hover():
            try:
                img = QImage(path)
                if img.isNull(): return None
                return img.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            except: return None

        def on_finished(scaled):
            if scaled and self._pending_hover_path == path: # Ensure we still want this image
                self.hover_preview.setPixmap(QPixmap.fromImage(scaled))
                self.hover_preview.move(pos.x() + 20, pos.y() + 20)
                self.hover_preview.show()

        task_manager.run_task(scale_hover, on_finished=on_finished)

    def add_customer(self):
        dialog = CustomerDialog()
        if dialog.exec():
            data = dialog.get_data()
            if not data:
                return
            from src.core.blocking_task_manager import task_manager

            def do_add():
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO customers (name_en, phone, loan_enabled, loan_limit, home_address, photo, id_card_photo)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (data['name_en'], data['phone'], data['loan_enabled'], data['loan_limit'], data['address'], data['photo'], data['id_card_photo']))
                    customer_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO audit_logs (user_id, action, table_name, record_id, details) VALUES (?, ?, ?, ?, ?)",
                        (self.current_user['id'], 'ADD_CUSTOMER', 'customers', customer_id, f"Added customer {data['name_en']}")
                    )
                    conn.commit()
                return True

            task_manager.run_task(do_add, on_finished=lambda _: self.load_customers())

    def edit_customer(self, customer):
        dialog = CustomerDialog(customer)
        if dialog.exec():
            data = dialog.get_data()
            if not data:
                return
            from src.core.blocking_task_manager import task_manager

            def do_edit():
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE customers SET name_en=?, phone=?, loan_enabled=?, loan_limit=?, home_address=?, photo=?, id_card_photo=?
                        WHERE id=?
                    """, (data['name_en'], data['phone'], data['loan_enabled'], data['loan_limit'],
                          data['address'], data['photo'], data['id_card_photo'], customer['id']))
                    conn.commit()
                return True

            task_manager.run_task(do_edit, on_finished=lambda _: self.load_customers())

    def delete_customer(self, cid):
        if cid == 1:
            QMessageBox.warning(self, "Reserved", "Default walking customer cannot be deleted.")
            return
        reply = QMessageBox.question(
            self, 'Confirm Delete', "Deactivate this customer?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from src.core.blocking_task_manager import task_manager

            def do_delete():
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE customers SET is_active = 0 WHERE id = ?", (cid,))
                    conn.commit()
                return True

            task_manager.run_task(do_delete, on_finished=lambda _: self.load_customers())

    def make_payment(self, cid):
        from PyQt6.QtWidgets import QInputDialog
        amount, ok = QInputDialog.getDouble(self, "Payment", "Enter amount received:", 0, 0, 1000000, 2)
        if ok and amount > 0:
            from src.core.blocking_task_manager import task_manager
            from datetime import datetime

            def do_payment():
                try:
                    with db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE customers SET balance = MAX(0, balance - ?) WHERE id = ?", (amount, cid))
                        cursor.execute(
                            "INSERT INTO customer_payments (customer_id, amount, payment_method, reference_number) VALUES (?, ?, 'CASH', ?)",
                            (cid, amount, f"Settle-{datetime.now().strftime('%Y%m%d%H%M')}")
                        )
                        conn.commit()
                    return {"success": True}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            def on_finished(result):
                if result["success"]:
                    QMessageBox.information(self, "Success", "Payment recorded.")
                    self.load_customers()
                else:
                    QMessageBox.critical(self, "Error", result["error"])

            task_manager.run_task(do_payment, on_finished=on_finished)
