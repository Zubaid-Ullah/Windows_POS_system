from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QPushButton, QLabel, QHeaderView, QGroupBox,
                             QFormLayout, QLineEdit, QComboBox, QMessageBox, QTableWidgetItem,
                             QCheckBox, QFileDialog, QDialog, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.database.db_manager import db_manager

class PharmacyCustomerView(QWidget):
    customers_updated = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("Pharmacy Customer Management & KYC")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #065f46; margin-bottom: 10px;")
        layout.addWidget(header)

        # Basic Information Group
        basic_group = QFrame()
        basic_group.setObjectName("pharmacy_customer_basic_group")
        basic_group.setStyleSheet("""
            QFrame#pharmacy_customer_basic_group {
                background-color: #f0fdf4;
                border-radius: 8px;
                border: 1px solid #bbf7d0;
            }
        """)
        basic_layout = QVBoxLayout(basic_group)
        basic_layout.setContentsMargins(15, 15, 15, 15)

        basic_title = QLabel("Basic Information")
        basic_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #166534; margin-bottom: 10px;")
        basic_layout.addWidget(basic_title)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter customer's full name")
        self.name_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")
        self.name_input.setMinimumWidth(500)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number")
        self.phone_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")
        self.phone_input.setMinimumWidth(500)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Enter customer address")
        self.address_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")
        self.address_input.setMinimumWidth(500)

        form.addRow("Full Name:", self.name_input)
        form.addRow("Contact Number:", self.phone_input)
        form.addRow("Address:", self.address_input)

        basic_layout.addLayout(form)
        layout.addWidget(basic_group)

        # Credit & Loan Group
        loan_group = QFrame()
        loan_group.setObjectName("pharmacy_customer_loan_group")
        loan_group.setStyleSheet("""
            QFrame#pharmacy_customer_loan_group {
                background-color: #fef3c7;
                border-radius: 8px;
                border: 1px solid #fcd34d;
            }
        """)
        loan_layout = QVBoxLayout(loan_group)
        loan_layout.setContentsMargins(15, 15, 15, 15)

        loan_title = QLabel("Credit & Loan Settings")
        loan_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #92400e; margin-bottom: 10px;")
        loan_layout.addWidget(loan_title)

        loan_form = QFormLayout()
        loan_form.setSpacing(12)

        self.loan_cb = QCheckBox("Allow Credit Sales")
        self.loan_cb.setStyleSheet("font-weight: 500; color: #92400e;")

        self.loan_limit = QLineEdit()
        self.loan_limit.setPlaceholderText("Maximum credit amount")
        self.loan_limit.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;")
        self.loan_limit.setEnabled(False)
        self.loan_limit.setMinimumWidth(500)
        self.loan_cb.toggled.connect(self.loan_limit.setEnabled)

        loan_form.addRow("Credit Sales:", self.loan_cb)
        loan_form.addRow("Credit Limit (AFN):", self.loan_limit)

        loan_layout.addLayout(loan_form)
        layout.addWidget(loan_group)

        # KYC Section
        kyc_group = QFrame()
        kyc_group.setObjectName("pharmacy_customer_kyc_group")
        kyc_group.setStyleSheet("""
            QFrame#pharmacy_customer_kyc_group {
                background-color: #f3f4f6;
                border-radius: 8px;
                border: 1px solid #d1d5db;
            }
        """)
        kyc_layout = QVBoxLayout(kyc_group)
        kyc_layout.setContentsMargins(15, 15, 15, 15)

        kyc_title = QLabel("KYC Documentation")
        kyc_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #374151; margin-bottom: 10px;")
        kyc_layout.addWidget(kyc_title)

        kyc_form = QFormLayout()
        kyc_form.setSpacing(12)

        self.photo_path = QLineEdit()
        self.photo_path.setReadOnly(True)
        self.photo_path.setPlaceholderText("No photo selected")
        self.photo_path.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; background: #f9fafb;")
        self.photo_path.setMinimumWidth(500)
        photo_btn = QPushButton("Browse Photo")
        photo_btn.setStyleSheet("padding: 6px 12px; background: #3b82f6; color: white; border: none; border-radius: 4px; font-size: 12px;")
        photo_btn.clicked.connect(lambda: self.browse_kyc("photo"))

        photo_layout = QHBoxLayout()
        photo_layout.addWidget(self.photo_path)
        photo_layout.addWidget(photo_btn)

        self.id_card_path = QLineEdit()
        self.id_card_path.setReadOnly(True)
        self.id_card_path.setPlaceholderText("No ID card selected")
        self.id_card_path.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; background: #f9fafb;")
        self.id_card_path.setMinimumWidth(500)
        id_card_btn = QPushButton("Browse ID Card")
        id_card_btn.setStyleSheet("padding: 6px 12px; background: #10b981; color: white; border: none; border-radius: 4px; font-size: 12px;")
        id_card_btn.clicked.connect(lambda: self.browse_kyc("id_card"))

        id_layout = QHBoxLayout()
        id_layout.addWidget(self.id_card_path)
        id_layout.addWidget(id_card_btn)

        kyc_form.addRow("Customer Photo:", photo_layout)
        kyc_form.addRow("ID Card Photo:", id_layout)

        kyc_layout.addLayout(kyc_form)
        layout.addWidget(kyc_group)
        
        save_btn = QPushButton("Save Customer")
        style_button(save_btn, variant="success")
        save_btn.clicked.connect(self.save_customer)
        layout.addWidget(save_btn)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Full Name", "Contact", "Balance", "Actions"])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_customers()

    def browse_kyc(self, k_type):
        """Ask user whether to upload from system or take photo"""
        # Create custom dialog with proper buttons
        msg = QMessageBox(self)
        msg.setWindowTitle("Upload Method")
        msg.setText(f"Choose how to upload {k_type.replace('_', ' ').title()}:")
        
        camera_btn = msg.addButton("Open Camera", QMessageBox.ButtonRole.ActionRole)
        upload_btn = msg.addButton("Upload Photo", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        clicked = msg.clickedButton()
        
        path = None
        if clicked == upload_btn:  # Upload from system
            path, _ = QFileDialog.getOpenFileName(
                self, 
                f"Select Customer {k_type.replace('_',' ').title()}", 
                "", 
                "Images (*.png *.jpg *.jpeg)"
            )
        elif clicked == camera_btn:  # Take photo with camera
            path = self.capture_photo_from_camera(k_type)
        else:
            return  # Cancelled
            
        if path:
            if k_type == "photo": 
                self.photo_path.setText(path)
            else: 
                self.id_card_path.setText(path)
    
    def capture_photo_from_camera(self, photo_type):
        """Capture photo using OpenCV"""
        try:
            import cv2
            import os
            from datetime import datetime
            
            # Detect available cameras
            available_cameras = []
            for i in range(5):  # Check first 5 camera indices
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    available_cameras.append(i)
                    cap.release()
            
            if not available_cameras:
                QMessageBox.warning(self, "No Camera", "No camera detected on this system.")
                return None
            
            # If multiple cameras, let user choose
            camera_index = 0
            if len(available_cameras) > 1:
                from PyQt6.QtWidgets import QInputDialog
                items = [f"Camera {i}" for i in available_cameras]
                item, ok = QInputDialog.getItem(
                    self, "Select Camera", 
                    "Multiple cameras detected. Choose one:", 
                    items, 0, False
                )
                if ok and item:
                    camera_index = available_cameras[items.index(item)]
                else:
                    return None
            else:
                camera_index = available_cameras[0]
            
            # Open camera
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                QMessageBox.warning(self, "Camera Error", "Could not open camera.")
                return None
            
            QMessageBox.information(
                self, "Camera Instructions", 
                "Position yourself in frame and press SPACE to capture.\nPress ESC to cancel."
            )
            
            captured_frame = None
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Add text overlay
                cv2.putText(frame, "Press SPACE to capture, ESC to cancel", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow(f'Capture {photo_type.replace("_", " ").title()}', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == 32:  # SPACE
                    captured_frame = frame
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            if captured_frame is not None:
                # Save the captured image
                save_dir = os.path.join("data", "kyc")
                os.makedirs(save_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{photo_type}_{timestamp}.jpg"
                filepath = os.path.join(save_dir, filename)
                
                cv2.imwrite(filepath, captured_frame)
                QMessageBox.information(self, "Success", f"Photo captured and saved!")
                return filepath
            
            return None
            
        except ImportError:
            QMessageBox.warning(
                self, "OpenCV Not Installed",
                "OpenCV (cv2) is not installed.\nInstall with: pip install opencv-python"
            )
            return None
        except Exception as e:
            QMessageBox.critical(self, "Camera Error", f"Error accessing camera: {e}")
            return None

    def save_customer(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()
        loan_enabled = 1 if self.loan_cb.isChecked() else 0
        limit = float(self.loan_limit.text() or 0)
        
        photo = self.photo_path.text()
        id_card = self.id_card_path.text()
        
        if not name or not phone:
             QMessageBox.warning(self, "Error", "Name and Phone are required")
             return
             
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # Check for existing
                existing = conn.execute("SELECT id FROM pharmacy_customers WHERE phone = ?", (phone,)).fetchone()
                if existing:
                    conn.execute("""
                        UPDATE pharmacy_customers SET name=?, address=?, loan_enabled=?, loan_limit=?, kyc_photo=?, kyc_id_card=?
                        WHERE id=?
                    """, (name, address, loan_enabled, limit, photo, id_card, existing['id']))
                else:
                    conn.execute("""
                        INSERT INTO pharmacy_customers (name, phone, address, loan_enabled, loan_limit, kyc_photo, kyc_id_card)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (name, phone, address, loan_enabled, limit, photo, id_card))
                conn.commit()
            
            self.load_customers()
            self.clear_form()
            self.customers_updated.emit()
            QMessageBox.information(self, "Success", "Customer data saved")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_customers(self):
        self.table.setRowCount(0)
        try:
            with db_manager.get_pharmacy_connection() as conn:
                rows = conn.execute("SELECT * FROM pharmacy_customers WHERE is_active=1").fetchall()
                for i, row in enumerate(rows):
                    self.table.insertRow(i)
                    self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                    self.table.setItem(i, 1, QTableWidgetItem(row['name']))
                    self.table.setItem(i, 2, QTableWidgetItem(row['phone']))
                    
                    bal_item = QTableWidgetItem(f"$ {row['balance']:,.2f}")
                    if row['balance'] < 0:
                        bal_item.setForeground(Qt.GlobalColor.darkGreen)
                        bal_item.setText(f"Credit: ${abs(row['balance']):,.2f}")
                    elif row['balance'] > 0:
                        bal_item.setForeground(Qt.GlobalColor.red)
                    self.table.setItem(i, 3, bal_item)
                    
                    actions = QWidget()
                    act_layout = QHBoxLayout(actions)
                    act_layout.setContentsMargins(0,0,0,0)
                    act_layout.setSpacing(5)
                    
                    pay_btn = QPushButton("Cash")
                    style_button(pay_btn, variant="info", size="small")
                    
                    edit_btn = QPushButton("Edit")
                    style_button(edit_btn, variant="success", size="small")
                    edit_btn.clicked.connect(lambda ch, r=row: self.edit_customer(r))
                    
                    del_btn = QPushButton("Del")
                    style_button(del_btn, variant="danger", size="small")
                    del_btn.clicked.connect(lambda ch, cid=row['id']: self.delete_customer(cid))
                    
                    view_btn = QPushButton("Details")
                    style_button(view_btn, variant="outline", size="small")
                    view_btn.clicked.connect(lambda ch, r=row: self.show_visual_details(r))
                    
                    act_layout.addWidget(pay_btn)
                    act_layout.addWidget(view_btn)
                    act_layout.addWidget(edit_btn)
                    act_layout.addWidget(del_btn)
                    self.table.setCellWidget(i, 4, actions)
        except Exception as e:
            print(f"Error loading customers: {e}")

    def show_visual_details(self, row):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Customer Information - {row['name']}")
        dialog.setMinimumWidth(700)
        
        l = QVBoxLayout(dialog)
        
        # Data Section
        data_gb = QGroupBox("Basic Information")
        data_layout = QFormLayout(data_gb)
        data_layout.addRow("<b>Full Name:</b>", QLabel(row['name']))
        data_layout.addRow("<b>Phone:</b>", QLabel(row['phone']))
        data_layout.addRow("<b>Address:</b>", QLabel(row['address'] or "N/A"))
        
        if row['balance'] > 0:
            balance_lbl = QLabel(f"<b>{row['balance']:,.2f} AFN</b>")
            balance_lbl.setStyleSheet("color: #ef4444; font-size: 16px;")
        elif row['balance'] < 0:
            balance_lbl = QLabel(f"<b>Credit: {abs(row['balance']):,.2f} AFN</b>")
            balance_lbl.setStyleSheet("color: #10b981; font-size: 16px;")
        else:
            balance_lbl = QLabel("<b>0.00 AFN</b>")
            balance_lbl.setStyleSheet("color: #64748b; font-size: 16px;")
        data_layout.addRow("<b>Current Balance:</b>", balance_lbl)
        
        loan_status = "Enabled" if row['loan_enabled'] else "Disabled"
        data_layout.addRow("<b>Loan Feature:</b>", QLabel(loan_status))
        data_layout.addRow("<b>Loan Limit:</b>", QLabel(f"{row['loan_limit']:,.2f} AFN"))
        
        l.addWidget(data_gb)
        
        img_layout = QHBoxLayout()
        
        # Photo
        photo_v = QVBoxLayout()
        photo_lbl = QLabel("<b>Customer Photo:</b>")
        photo_img = QLabel()
        photo_img.setFixedSize(300, 300)
        photo_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_img.setStyleSheet("border: 2px solid #3b82f633; border-radius: 8px; background: #f8fafc;")
        
        if row['kyc_photo']:
            pix = QPixmap(row['kyc_photo'])
            if not pix.isNull():
                photo_img.setPixmap(pix.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                photo_img.setText("Photo File Missing")
        else:
            photo_img.setText("No Photo Uploaded")
            
        photo_v.addWidget(photo_lbl)
        photo_v.addWidget(photo_img)
        img_layout.addLayout(photo_v)
        
        # ID Card
        id_v = QVBoxLayout()
        id_lbl = QLabel("<b>ID Card / Document:</b>")
        id_img = QLabel()
        id_img.setFixedSize(300, 300)
        id_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        id_img.setStyleSheet("border: 2px solid #3b82f633; border-radius: 8px; background: #f8fafc;")
        
        if row['kyc_id_card']:
            pix_id = QPixmap(row['kyc_id_card'])
            if not pix_id.isNull():
                id_img.setPixmap(pix_id.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                id_img.setText("ID File Missing")
        else:
            id_img.setText("No ID Uploaded")
            
        id_v.addWidget(id_lbl)
        id_v.addWidget(id_img)
        img_layout.addLayout(id_v)
        
        l.addLayout(img_layout)
        
        close_btn = QPushButton("Close Details")
        style_button(close_btn, variant="outline")
        close_btn.clicked.connect(dialog.accept)
        l.addWidget(close_btn)
        
        dialog.exec()

    def edit_customer(self, row):
        self.name_input.setText(row['name'])
        self.phone_input.setText(row['phone'])
        self.address_input.setText(row['address'] or "")
        self.loan_cb.setChecked(bool(row['loan_enabled']))
        self.loan_limit.setText(str(row['loan_limit']))
        self.photo_path.setText(row['kyc_photo'] or "")
        self.id_card_path.setText(row['kyc_id_card'] or "")

    def delete_customer(self, cid):
        if QMessageBox.question(self, "Confirm", "Delete this customer?") == QMessageBox.StandardButton.Yes:
            with db_manager.get_pharmacy_connection() as conn:
                conn.execute("UPDATE pharmacy_customers SET is_active=0 WHERE id=?", (cid,))
                conn.commit()
            self.load_customers()
            self.customers_updated.emit()

    def clear_form(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.address_input.clear()
        self.loan_cb.setChecked(False)
        self.loan_limit.clear()
        self.photo_path.clear()
        self.id_card_path.clear()
