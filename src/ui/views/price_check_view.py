from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QLabel, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import qtawesome as qta
from src.database.db_manager import db_manager
from src.core.localization import lang_manager

class PriceCheckView(QWidget):
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Card Wrapper
        self.container = QFrame()
        self.container.setObjectName("card")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Scanner Icon
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.barcode", color="#4318ff").pixmap(100, 100))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)
        
        info = QLabel("Please scan any product barcode to see its information")
        info.setStyleSheet("font-size: 18px; color: #a3aed0; margin-bottom: 30px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
        # Display Box (Kiosk Style - Full Width)
        self.display_card = QFrame()
        self.display_card.setObjectName("card")
        self.display_card.setMinimumHeight(450)
        self.display_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        card_layout = QVBoxLayout(self.display_card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(20)
        
        self.product_name_lbl = QLabel("READY TO SCAN")
        self.product_name_lbl.setObjectName("page_header")
        self.product_name_lbl.setStyleSheet("font-size: 42px;")
        self.product_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.product_name_lbl.setWordWrap(True)
        
        self.price_lbl = QLabel("")
        self.price_lbl.setStyleSheet("font-size: 82px; font-weight: 900; color: #27ae60;")
        self.price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(self.product_name_lbl)
        card_layout.addWidget(self.price_lbl)
        layout.addWidget(self.display_card)
        
        # Hidden Scanner Input
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("SCAN HERE...")
        # Styling handled by ThemeManager
        self.scan_input.setFixedHeight(50)
        self.scan_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scan_input.returnPressed.connect(self.handle_scan)
        layout.addSpacing(30)
        layout.addWidget(self.scan_input)
        
        main_layout.addWidget(self.container)
        
        # Timer to clear display after 5 seconds
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.reset_display)
        
        # Ensure scan input is always focused
        self.scan_input.setFocus()

    def handle_scan(self):
        barcode = self.scan_input.text().strip()
        self.scan_input.clear()
        
        if not barcode: return
        
        lang = lang_manager.current_lang
        lang_col = f'name_{lang}'
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT {lang_col}, name_en, sale_price FROM products WHERE barcode = ? AND is_active = 1", (barcode,))
            product = cursor.fetchone()
            
            if product:
                name = product[0] or product[1]
                price = product[2]
                
                self.product_name_lbl.setText(name)
                self.price_lbl.setText(f"{price:.2f} AFN")
                self.display_card.setStyleSheet("")
                print('\a', end='', flush=True) # Beep
            else:
                self.product_name_lbl.setText("PRODUCT NOT FOUND")
                self.price_lbl.setText("---")
                self.display_card.setStyleSheet("""
                    QFrame {
                        background-color: #ffffff;
                        border: none;
                        border-radius: 30px;
                    }
                """)
            
            # Start timer
            self.clear_timer.start(4000) # 4 seconds

    def reset_display(self):
        self.clear_timer.stop()
        self.product_name_lbl.setText("READY TO SCAN")
        self.price_lbl.setText("")
        self.display_card.setStyleSheet("")
        self.scan_input.setFocus()
        self.finished.emit()

    def focusInEvent(self, event):
        self.scan_input.setFocus()
        super().focusInEvent(event)
