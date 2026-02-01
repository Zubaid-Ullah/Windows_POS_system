from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFrame)
from PyQt6.QtCore import Qt
import qtawesome as qta
from src.database.db_manager import db_manager
from src.core.localization import lang_manager
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button

class StockAlertView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_alert_data()

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
        header.addStretch()
        
        refresh_btn = QPushButton(" Refresh List")
        style_button(refresh_btn, variant="success")
        refresh_btn.setIcon(qta.icon("fa5s.sync", color="white"))
        refresh_btn.clicked.connect(self.load_alert_data)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Explanation
        info = QLabel("The following items have reached a critical stock level and need immediate restocking.")
        info.setStyleSheet("color: #a3aed0; font-style: italic; font-size: 14px;")
        layout.addWidget(info)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "ID", "Barcode", "Product Name", "Available Quantity"
        ])
        style_table(self.table, variant="premium")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        main_layout.addWidget(self.container)

    def load_alert_data(self):
        lang = lang_manager.current_lang
        lang_col = f'name_{lang}'
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT p.*, i.quantity 
                FROM products p 
                JOIN inventory i ON p.id = i.product_id
                WHERE i.quantity <= 3 AND p.is_active = 1
                ORDER BY i.quantity ASC
            """)
            items = cursor.fetchall()
            
            self.table.setRowCount(0)
            for i, p in enumerate(items):
                name = p[lang_col] or p['name_en']
                self.table.insertRow(i)
                
                id_item = QTableWidgetItem(str(p['id']))
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                bc_item = QTableWidgetItem(p['barcode'])
                bc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                nm_item = QTableWidgetItem(name)
                
                qty_val = p['quantity'] or 0
                qty_item = QTableWidgetItem(str(qty_val))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                qty_item.setForeground(Qt.GlobalColor.red)
                font = qty_item.font()
                font.setBold(True)
                qty_item.setFont(font)
                
                self.table.setItem(i, 0, id_item)
                self.table.setItem(i, 1, bc_item)
                self.table.setItem(i, 2, nm_item)
                self.table.setItem(i, 3, qty_item)
