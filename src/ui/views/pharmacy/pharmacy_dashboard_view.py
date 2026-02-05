from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QFrame, QScrollArea, 
                             QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QVariantAnimation, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont
import qtawesome as qta
from src.ui.theme_manager import theme_manager
from src.core.localization import lang_manager
from src.database.db_manager import db_manager

class DonutChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.percentage = 0
        self.product_name = ""
        self.visible_chart = False
        self.setMinimumHeight(400)

    def set_data(self, name, percentage):
        self.product_name = name
        self.percentage = float(percentage)
        self.visible_chart = True
        self.update()

    def clear(self):
        self.visible_chart = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_dark = theme_manager.is_dark

        if not self.visible_chart:
            # Draw placeholder message
            painter.setPen(QColor("#64748b")) # slate-400
            painter.setFont(QFont("Arial", 14))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                             lang_manager.get("select_product_info") or "Select a product to view stats")
            return

        width = self.width()
        height = self.height()
        # Leave room for title/name
        size = min(width, height - 100) - 60
        rect = QRectF((width - size) / 2, (height - size) / 2 - 20, size, size)
        
        # Determine color for "Sold" portion
        if self.percentage <= 25:
            color = QColor("#ef4444") # Red
        elif self.percentage <= 75:
            color = QColor("#3b82f6") # Blue
        else:
            color = QColor("#10b981") # Green
            
        # Draw background circle (Remaining/Total)
        painter.setPen(Qt.PenStyle.NoPen)
        bg_color = QColor("#334155" if is_dark else "#e2e8f0")
        painter.setBrush(bg_color)
        painter.drawEllipse(rect)
        
        # Draw sold arc
        start_angle = 90 * 16 # 12 o'clock
        span_angle = int(-self.percentage * 3.6 * 16)
        
        painter.setBrush(color)
        painter.drawPie(rect, start_angle, span_angle)
        
        # Draw inner circle (donut hole)
        inner_size = size * 0.7
        inner_rect = QRectF((width - inner_size) / 2, (height - inner_size) / 2 - 20, inner_size, inner_size)
        
        # Use white for the hole to match the forced white background
        hole_color = QColor("white")
        painter.setBrush(hole_color)
        painter.drawEllipse(inner_rect)
        
        # Draw percentage text in middle - always dark for white background
        painter.setPen(QColor("#1e293b"))
        font = QFont("Arial", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(inner_rect, Qt.AlignmentFlag.AlignCenter, f"{self.percentage:.1f}%")
        
        # Draw product name below
        font.setPointSize(18)
        painter.setFont(font)
        name_rect = QRectF(20, rect.bottom() + 30, width - 40, 40)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, self.product_name)
        
        font.setPointSize(12)
        font.setBold(False)
        painter.setFont(font)
        subtitle_rect = QRectF(20, name_rect.bottom(), width - 40, 30)
        painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, "Inventory Sold Percentage")

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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: #afcdf4;")

        
        content_widget = QWidget()
        content_widget.setObjectName("dashboard_content")
        self.container_layout = QVBoxLayout(content_widget)
        self.container_layout.setSpacing(30)
        self.container_layout.setContentsMargins(20, 20, 20, 20)

        # Quick Actions Grid
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setSpacing(20)
        
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
        max_cols = 4

        for trans_key, icon, key, color in actions:
            has_perm = "*" in user_perms or key in user_perms or f"{key}_view" in user_perms
            if not has_perm:
                continue
            
            label = lang_manager.get(trans_key)
            card = PharmacyDashboardCard(label, icon, key, color, translation_key=trans_key)
            card.icon_lbl.setProperty("icon_name", icon)
            card.clicked.connect(self.navigation_requested.emit)
            grid.addWidget(card, row, col)
            self.cards.append(card)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        self.container_layout.addWidget(grid_container)

        # Statistics Section (70/30)
        stats_frame = QFrame()
        stats_frame.setObjectName("stats_frame")
        stats_frame.setMinimumHeight(550)
        stats_frame.setStyleSheet("background: white;")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(15, 15, 15, 15)
        stats_layout.setSpacing(25)

        # Left: Donut Chart area (70%)
        self.chart_widget = DonutChartWidget()
        stats_layout.addWidget(self.chart_widget, 7)

        # Right: Product List (30%)
        list_container = QWidget()
        list_vbox = QVBoxLayout(list_container)
        
        list_label = QLabel(lang_manager.get("inventory_stats") or "Inventory Statistics")
        list_label.setStyleSheet("font-weight: bold; font-size: 18px;")
        list_vbox.addWidget(list_label)
        
        self.product_list = QListWidget()
        self.product_list.setObjectName("product_stats_list")
        self.product_list.itemClicked.connect(self.on_product_selected)
        list_vbox.addWidget(self.product_list)
        
        stats_layout.addWidget(list_container, 3)

        self.container_layout.addWidget(stats_frame)
        self.container_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        self.load_products_data()

    def load_products_data(self):
        # Prevent multiple simultaneous loads - Safely handle deleted C++ objects
        try:
            if hasattr(self, '_loading_thread') and self._loading_thread and self._loading_thread.isRunning():
                return
        except RuntimeError:
            self._loading_thread = None

        self.product_list.clear()
        self.product_list.addItem("Loading statistics...")

        from PyQt6.QtCore import QThread, pyqtSignal
        class StatsWorker(QThread):
            data_received = pyqtSignal(list)
            def run(self):
                try:
                    with db_manager.get_pharmacy_connection() as conn:
                        products = conn.execute("""
                            SELECT 
                                p.id, 
                                p.name_en,
                                COALESCE(sales.total_sold, 0) as sold_qty,
                                COALESCE(inv.total_current, 0) as current_qty
                            FROM pharmacy_products p
                            LEFT JOIN (
                                SELECT product_id, SUM(quantity) as total_sold 
                                FROM pharmacy_sale_items 
                                GROUP BY product_id
                            ) sales ON p.id = sales.product_id
                            LEFT JOIN (
                                SELECT product_id, SUM(quantity) as total_current 
                                FROM pharmacy_inventory 
                                GROUP BY product_id
                            ) inv ON p.id = inv.product_id
                            WHERE p.is_active = 1
                            ORDER BY p.name_en ASC
                        """).fetchall()
                        # Convert sqlite3.Row to list of dicts for safe thread passing
                        self.data_received.emit([dict(p) for p in products])
                except Exception as e:
                    print(f"StatsWorker Error: {e}")
                    self.data_received.emit([])

        # Remember selection before clear
        selected_items = self.product_list.selectedItems()
        self.last_selected_name = selected_items[0].text() if selected_items else None

        self._loading_thread = StatsWorker()
        self._loading_thread.data_received.connect(self._on_stats_loaded)
        self._loading_thread.finished.connect(self._cleanup_loading_thread)
        self._loading_thread.finished.connect(self._loading_thread.deleteLater)
        self._loading_thread.start()

    def _cleanup_loading_thread(self):
        """Nullify the thread reference after it finishes to prevent RuntimeError."""
        self._loading_thread = None

    def _on_stats_loaded(self, products):
        self.product_list.clear()
        if not products:
            self.product_list.addItem("No statistics available")
            return

        for p in products:
            sold_qty = p['sold_qty']
            current_qty = p['current_qty']
            total = sold_qty + current_qty
            
            percentage = (sold_qty / total * 100) if total > 0 else 0
            
            item = QListWidgetItem(p['name_en'])
            item.setData(Qt.ItemDataRole.UserRole, percentage)
            self.product_list.addItem(item)
            
            # Restore selection and update chart
            if hasattr(self, 'last_selected_name') and p['name_en'] == self.last_selected_name:
                item.setSelected(True)
                if self.chart_widget.visible_chart:
                    self.chart_widget.set_data(p['name_en'], percentage)

    def on_product_selected(self, item):
        name = item.text()
        percentage = item.data(Qt.ItemDataRole.UserRole)
        # Avoid trying to set data on the loading placeholder
        if name != "Loading statistics...":
            self.chart_widget.set_data(name, percentage)

    def mousePressEvent(self, event):
        # Deselect if clicking empty space in the dashboard
        if not self.product_list.geometry().contains(self.mapFromGlobal(event.globalPosition().toPoint())):
             self.product_list.clearSelection()
             self.chart_widget.clear()
        super().mousePressEvent(event)

    def update_labels(self):
        for card in self.cards:
            card.update_label()
        self.load_products_data() # Refresh list with new names if needed

    def update_theme(self):
        is_dark = theme_manager.is_dark
        text_color = "#f8fafc" if is_dark else "#1e293b"
        card_bg = "#1e293b" if is_dark else "white"
        hover_bg = "#334155" if is_dark else "#f1f5f9"
        
        stats_bg = "white"
        list_bg = "white"

        self.setStyleSheet(f"""
            QFrame#stats_frame {{
                background-color: {stats_bg};
                border-radius: 20px;
                border: 1px solid {"#334155" if is_dark else "#e2e8f0"};
            }}
            QListWidget#product_stats_list {{
                background-color: {list_bg};
                border: 1px solid {"#334155" if is_dark else "#e2e8f0"};
                border-radius: 10px;
                padding: 5px;
                color: #1e293b;
            }}
            QListWidget#product_stats_list::item {{
                padding: 8px;
                border-radius: 5px;
            }}
            QListWidget#product_stats_list::item:selected {{
                background-color: #3b82f6;
                color: white;
            }}
            QLabel {{
                color: #1e293b;
            }}
        """)

        for card in self.cards:
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
