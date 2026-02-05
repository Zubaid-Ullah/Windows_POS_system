from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QGridLayout, QScrollArea, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QLinearGradient, QBrush, QPen
import qtawesome as qta
from src.ui.theme_manager import theme_manager
from src.core.auth import Auth
from src.core.localization import lang_manager

class DashboardCard(QFrame):
    clicked = pyqtSignal()
    hovering = pyqtSignal(QColor)
    hover_left = pyqtSignal()
    
    def __init__(self, title, icon_name, gradient_colors, description=""):
        super().__init__()
        self.setFixedSize(260, 200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.colors = gradient_colors # (color1, color2)
        self.title = "  "+title
        self.icon_name = icon_name
        self.description = description
        self.is_hovered = False
        
        # Enhanced Shadow Effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(30)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(10)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self.shadow)
        
        # Animation for icon scaling
        self.icon_anim = QVariantAnimation()
        self.icon_anim.setDuration(300)
        self.icon_anim.setStartValue(50)
        self.icon_anim.setEndValue(80)
        self.icon_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.icon_anim.valueChanged.connect(self.update_icon)
        
        # Button Animation
        self.hover_progress = 0.0 # 0.0 to 1.0
        self.hover_anim = QVariantAnimation()
        self.hover_anim.setDuration(200)
        self.hover_anim.setStartValue(0.0)
        self.hover_anim.setEndValue(1.0)
        self.hover_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.hover_anim.valueChanged.connect(self.update_hover)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(10)
        
        # Title at top left
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; background: none;")
        layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Centered Icon
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_icon(50)
        layout.addWidget(self.icon_lbl, 1)
        
        # Description at bottom (optional/subtle)
        if self.description:
            self.desc_lbl = QLabel(self.description)
            self.desc_lbl.setStyleSheet("font-size: 11px; background: none;")
            self.desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.desc_lbl)
        
        self.update_colors()

    def update_colors(self):
        text_color = "white" if theme_manager.is_dark else "#1b2559"
        self.title_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {text_color}; background: none;")
        if hasattr(self, 'desc_lbl'):
            opacity = "0.7" if theme_manager.is_dark else "0.5"
            self.desc_lbl.setStyleSheet(f"font-size: 11px; color: {text_color}; opacity: {opacity}; background: none;")

    def update_hover(self, progress):
        self.hover_progress = progress
        self.update()

    def update_icon(self, size):
        self.icon_lbl.setPixmap(qta.icon(self.icon_name, color="white").pixmap(size, size))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate colors based on hover progress
        # If hovered, brighten the gradient colors
        c1 = QColor(self.colors[0])
        c2 = QColor(self.colors[1])
        
        if self.hover_progress > 0:
            # Shift towards a lighter version based on progress
            # Lighter factor: 100 is original, 120 is 20% lighter.
            # We want smooth transition.
            factor = 100 + (30 * self.hover_progress) # Max 130% brightness
            c1 = c1.lighter(int(factor))
            c2 = c2.lighter(int(factor))

        # Draw Gradient Background
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, c1)
        gradient.setColorAt(1, c2)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1)) # Glass border
        
        # Enforce rounded corners: 24px
        painter.drawRoundedRect(self.rect().adjusted(1,1,-1,-1), 24, 24)
        
        # Ensure colors are correct on repaint if theme changed
        self.update_colors()

    def enterEvent(self, event):
        self.is_hovered = True
        self.shadow.setBlurRadius(40)
        self.icon_anim.setDirection(QVariantAnimation.Direction.Forward)
        self.icon_anim.start()
        
        self.hover_anim.setDirection(QVariantAnimation.Direction.Forward)
        self.hover_anim.start()
        
        # Emit hover signal for background change
        # Use the first color of the gradient as the base for the background tint
        if self.colors:
            self.hovering.emit(QColor(self.colors[0]))
            
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.shadow.setBlurRadius(30)
        self.icon_anim.setDirection(QVariantAnimation.Direction.Backward)
        self.icon_anim.start()
        
        self.hover_anim.setDirection(QVariantAnimation.Direction.Backward)
        self.hover_anim.start()
        
        self.hover_left.emit()
        
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class BackgroundFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_color = QColor("#f4f7fe")
        self.current_color = QColor("#f4f7fe")
        self.target_color = QColor("#f4f7fe")
        
        self.bg_anim = QVariantAnimation()
        self.bg_anim.setDuration(400)
        self.bg_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.bg_anim.valueChanged.connect(self.update_bg_color)

    def set_default_color(self, color):
        self.default_color = QColor(color)
        if self.bg_anim.state() != QVariantAnimation.State.Running:
            self.current_color = self.default_color
            self.update()

    def animate_to_color(self, color):
        self.bg_anim.stop()
        self.bg_anim.setStartValue(self.current_color)
        
        # New Logic: Create a subtle but visible tint of the hovering color
        # We mix the button's vibrant color with the theme's base/default background.
        # Ratio: 20% Button Color, 80% Default Theme Color
        
        # Get base color (this matches the theme background)
        base = self.default_color
        
        r = (color.red() * 0.15) + (base.red() * 0.85)
        g = (color.green() * 0.15) + (base.green() * 0.85)
        b = (color.blue() * 0.15) + (base.blue() * 0.85)
        
        # Ensure values are within 0-255
        target = QColor(int(r), int(g), int(b))
             
        self.bg_anim.setEndValue(target)
        self.bg_anim.start()

    def revert_color(self):
        self.bg_anim.stop()
        self.bg_anim.setStartValue(self.current_color)
        self.bg_anim.setEndValue(self.default_color)
        self.bg_anim.start()

    def update_bg_color(self, color):
        self.current_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self.current_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

class DashboardView(QWidget):
    navigation_requested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Full view layout
        self.main_container = QVBoxLayout(self)
        self.main_container.setContentsMargins(0, 0, 0, 0)
        
        # Background Widget (for gradient)
        self.bg_frame = BackgroundFrame()
        bg_layout = QVBoxLayout(self.bg_frame)
        bg_layout.setContentsMargins(40, 40, 40, 40)
        bg_layout.setSpacing(30)
        
        # Header
        self.header = QLabel("Fairi Tech POS Smart Control")
        # Ensure header is transparent to show bg
        self.header.setStyleSheet("font-size: 14px; font-weight: 500; background: transparent;")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_layout.addWidget(self.header)
        
        self.update_theme_styles()
        theme_manager.theme_changed.connect(self.update_theme_styles)
        
        # Grid Center
        grid_area = QWidget()
        grid_area.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_area)
        grid.setSpacing(30)
        
        all_items = [
            ("Sales", "fa5s.file-invoice-dollar", ("#00b09b", "#96c93d"), "Process transactions", "sales"),
            ("Inventory", "fa5s.boxes", ("#8e2de2", "#4a00e0"), "Stock & supplies", "inventory"),
            ("Customers", "fa5s.users", ("#f83600", "#f9d423"), "Client management", "customers"),
            ("Reports", "fa5s.chart-line", ("#00c6ff", "#0072ff"), "Analytics & Profit", "reports"),
            ("Finance", "fa5s.chart-pie", ("#f093fb", "#f5576c"), "Expenses & Petty Cash", "finance"),
            ("Suppliers", "fa5s.truck", ("#4facfe", "#00f2fe"), "Vendor tracking", "suppliers"),
            ("Loans", "fa5s.hand-holding-usd", ("#43e97b", "#38f9d7"), "Credit management", "loans"),
            ("Price Check", "fa5s.tag", ("#fa71cd", "#c471ed"), "Scan & Verify", "price_check"),
            ("Returns", "fa5s.undo", ("#fccb90", "#d57eeb"), "Item reversals", "returns"),
            ("User Management", "fa5s.user-shield", ("#4b6cb7", "#182848"), "Manage staff & access", "users"),
            ("Settings", "fa5s.cog", ("#30e8bf", "#ff8235"), "System config", "settings")
        ]
        
        # Filter items based on user permissions
        curr_user = Auth.get_current_user()
        user_perms = Auth.get_user_permissions(curr_user)
        
        items = []
        for title, icon, colors, desc, perm_key in all_items:
            if '*' in user_perms or perm_key in user_perms:
                items.append((title, icon, colors, desc, perm_key))

        row, col = 0, 0
        for title, icon, colors, desc, perm_key in items:
            key = perm_key
            card = DashboardCard(title, icon, colors, desc)
            card.clicked.connect(lambda k=key: self.navigation_requested.emit(k))
            
            # Connect hover signals to background frame
            card.hovering.connect(lambda c, f=self.bg_frame: f.animate_to_color(c))
            card.hover_left.connect(lambda f=self.bg_frame: f.revert_color())
            
            grid.addWidget(card, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        bg_layout.addWidget(grid_area, 1, Qt.AlignmentFlag.AlignCenter)
        
        self.main_container.addWidget(self.bg_frame)
        
        # Apply Main Background Styling
        self.bg_frame.setObjectName("dashboard_bg")
    
    def update_theme_styles(self, is_dark=None):
        t = theme_manager.DARK if theme_manager.is_dark else theme_manager.QUICKMART
        
        # Set default background color for the custom frame
        default_bg = QColor(t['bg_main'])
        self.bg_frame.set_default_color(default_bg)
        
        self.header.setStyleSheet(f"color: {t['text_main']}; font-size: 14px; font-weight: 500; background: transparent;")
        
        # Repaint
        self.update()

    def update_bg(self):
        pass

    def paintEvent(self, event):
        super().paintEvent(event)
