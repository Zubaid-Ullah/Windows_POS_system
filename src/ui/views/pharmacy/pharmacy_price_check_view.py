from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QLabel, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import qtawesome as qta
from src.database.db_manager import db_manager
from src.core.localization import lang_manager

class PharmacyPriceCheckView(QWidget):
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Auto-clear timer (5 seconds after showing result)
        self.clear_timer = QTimer(self)
        self.clear_timer.setSingleShot(True)
        self.clear_timer.timeout.connect(self.clear_display)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)

        # Large Search Box
        search_container = QFrame()
        search_container.setObjectName("card")
        search_layout = QHBoxLayout(search_container)
        
        search_icon = QLabel()
        search_icon.setPixmap(qta.icon("fa5s.barcode", color="#3b82f6").pixmap(40, 40))
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(lang_manager.get("search") + " " + lang_manager.get("medicine") + "...")
        self.search_input.setStyleSheet("border: none; font-size: 24px; padding: 10px; background: transparent;")
        self.search_input.textChanged.connect(self.search_product)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_container)

        # Result Display Area
        self.result_card = QFrame()
        self.result_card.setObjectName("card")
        self.result_layout = QVBoxLayout(self.result_card)
        self.result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_layout.setSpacing(20)
        
        self.placeholder_lbl = QLabel(lang_manager.get("price_check_placeholder"))
        self.placeholder_lbl.setStyleSheet("font-size: 20px; color: #94a3b8;")
        self.result_layout.addWidget(self.placeholder_lbl)
        
        layout.addWidget(self.result_card, 1)

    def search_product(self):
        term = self.search_input.text().strip()
        if not term:
            self.show_placeholder()
            return
            
        try:
            with db_manager.get_pharmacy_connection() as conn:
                row = conn.execute("""
                    SELECT p.name_en, p.sale_price, SUM(i.quantity) as total_qty, p.size
                    FROM pharmacy_products p
                    LEFT JOIN pharmacy_inventory i ON p.id = i.product_id
                    WHERE p.barcode = ? OR p.name_en LIKE ?
                    GROUP BY p.id
                    LIMIT 1
                """, (term, f"%{term}%")).fetchone()
                
                if row:
                    self.show_result(row)
                else:
                    self.show_not_found()
        except Exception as e:
            print(f"Price check error: {e}")

    def show_result(self, data):
        # Clear layout
        for i in reversed(range(self.result_layout.count())): 
            self.result_layout.itemAt(i).widget().setParent(None)
            
        name_lbl = QLabel(data['name_en'])
        name_lbl.setObjectName("page_header")
        name_lbl.setStyleSheet("font-size: 48px;")
        
        size_lbl = QLabel(data['size'] or "")
        size_lbl.setStyleSheet("font-size: 24px; opacity: 0.7;")
        
        price_lbl = QLabel(f"$ {data['sale_price']:,.2f}")
        price_lbl.setStyleSheet("font-size: 72px; font-weight: 800; color: #059669;")
        
        qty = data['total_qty'] or 0
        qty_lbl = QLabel(f"{lang_manager.get('stock')}: {qty}")
        qty_lbl.setStyleSheet(f"font-size: 28px; font-weight: 600; color: {'#059669' if qty > 10 else '#dc2626'};")
        
        self.result_layout.addWidget(name_lbl)
        self.result_layout.addWidget(size_lbl)
        self.result_layout.addWidget(price_lbl)
        self.result_layout.addWidget(qty_lbl)
        
        # Start clear timer to wipe display after 5 seconds
        self.clear_timer.start(5000)
    
    def clear_display(self):
        """Clear the search input and result display"""
        self.search_input.clear()
        self.show_placeholder()

    def show_placeholder(self):
        for i in reversed(range(self.result_layout.count())): 
            widget = self.result_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        placeholder_lbl = QLabel(lang_manager.get("price_check_placeholder"))
        placeholder_lbl.setStyleSheet("font-size: 20px; color: #94a3b8;")
        self.result_layout.addWidget(placeholder_lbl)

    def show_not_found(self):
        # Stop clear timer if searching
        self.clear_timer.stop()
        for i in reversed(range(self.result_layout.count())): 
            widget = self.result_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        nf = QLabel(lang_manager.get("not_found"))
        nf.setObjectName("page_header")
        nf.setStyleSheet("color: #ef4444;")
        self.result_layout.addWidget(nf)
        # Clear after 3 seconds
        self.clear_timer.start(3000)
