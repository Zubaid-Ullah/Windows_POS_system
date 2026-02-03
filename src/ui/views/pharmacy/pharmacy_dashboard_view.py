from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QPushButton, 
                             QLabel, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QVariantAnimation
import qtawesome as qta
from src.ui.theme_manager import theme_manager
from src.core.localization import lang_manager

class PharmacyDashboardCard(QFrame):
    clicked = pyqtSignal(str)
    
    def __init__(self, label, icon_name, key, color_hex, translation_key=None):
        super().__init__()
        self.key = key
        self.color_hex = color_hex
        self.icon_name = icon_name
        self.translation_key = translation_key
        self.setObjectName("action_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_lbl)
        
        self.text_lbl = QLabel(label)
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text_lbl)
        
        # Animation
        self.icon_anim = QVariantAnimation()
        self.icon_anim.setDuration(400)
        self.icon_anim.setStartValue(40)
        self.icon_anim.setEndValue(65)
        self.icon_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.icon_anim.valueChanged.connect(self.update_icon)
        self.update_icon(40)
    
    def update_label(self):
        if self.translation_key:
            self.text_lbl.setText(lang_manager.get(self.translation_key))
        
    def update_icon(self, size):
        self.icon_lbl.setPixmap(qta.icon(self.icon_name, color=self.color_hex).pixmap(int(size), int(size)))

    def enterEvent(self, event):
        self.icon_anim.setDirection(QVariantAnimation.Direction.Forward)
        self.icon_anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.icon_anim.setDirection(QVariantAnimation.Direction.Backward)
        self.icon_anim.start()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        self.clicked.emit(self.key)
        super().mousePressEvent(event)

class PharmacyDashboardView(QWidget):
    navigation_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.cards = []
        self.init_ui()
        theme_manager.theme_changed.connect(self.update_theme)
        lang_manager.language_changed.connect(self.update_labels)
        self.update_theme()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Quick Actions Grid
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # (translation_key, icon, nav_key, color)
        actions = [
            ("pharmacy_finance", "fa5s.chart-pie", "pharmacy_finance", "#3b82f6"),
            ("inventory", "fa5s.boxes", "pharmacy_inventory", "#10b981"),
            ("sales", "fa5s.file-invoice-dollar", "pharmacy_sales", "#8b5cf6"),
            ("customers", "fa5s.users", "pharmacy_customers", "#f59e0b"),
            ("suppliers", "fa5s.truck", "pharmacy_suppliers", "#ec4899"),
            ("credit_controls", "fa5s.hand-holding-usd", "pharmacy_loans", "#6366f1"),
            ("reports", "fa5s.chart-line", "pharmacy_reports", "#14b8a6"),
            ("price_check", "fa5s.tag", "pharmacy_price_check", "#f43f5e"),
            ("returns", "fa5s.undo", "pharmacy_returns", "#f97316"),
            ("user_management", "fa5s.user-nurse", "pharmacy_users", "#64748b")
        ]

        from src.core.pharmacy_auth import PharmacyAuth as Auth
        user = Auth.get_current_user()
        user_perms = Auth.get_user_permissions(user) if user else []

        row = 0
        col = 0
        max_cols = 4 # 4 columns

        for trans_key, icon, key, color in actions:
            # Check permissions
            has_perm = "*" in user_perms or key in user_perms or f"{key}_view" in user_perms
            if not has_perm:
                continue
            
            label = lang_manager.get(trans_key)
            card = PharmacyDashboardCard(label, icon, key, color, translation_key=trans_key)
            # Store icon name for hover logic
            card.icon_lbl.setProperty("icon_name", icon)
            card.clicked.connect(self.navigation_requested.emit)
            grid.addWidget(card, row, col)
            self.cards.append(card)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        layout.addLayout(grid)
        layout.addStretch()
    
    def update_labels(self):
        for card in self.cards:
            card.update_label()

    def create_action_card(self, label, icon_name, key, color_hex):
        # Deprecated, moved to PharmacyDashboardCard class
        pass

    def update_theme(self):
        is_dark = theme_manager.is_dark
        text_color = "#f8fafc" if is_dark else "#1e293b"
        
        # Don't override main window background
        # self.setStyleSheet(f"background-color: {bg_color};")
        if hasattr(self, 'welcome_lbl'):
            self.welcome_lbl.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {text_color}; background: transparent;")

        for card in self.findChildren(QFrame):
            if card.objectName() == "action_card":
                card_bg = "#1e293b" if is_dark else "white"
                hover_bg = "#334155" if is_dark else "#f1f5f9"
                card.setStyleSheet(f"""
                    QFrame#action_card {{
                        background-color: {card_bg};
                        border: none;
                        border-radius: 16px;
                        padding: 20px;
                    }}
                    QFrame#action_card:hover {{
                        background-color: {hover_bg};
                    }}
                """)
                for lbl in card.findChildren(QLabel):
                    lbl.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {text_color}; margin-top: 10px; border: none; background: transparent;")

    # Override mousePress on the card? 
    # For simplicity, users click the icon/text which are inside the layout.
    # To improve UX, let's wrap logic in a button that FILLS the card.
    
