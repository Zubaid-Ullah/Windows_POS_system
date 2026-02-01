from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
                             QComboBox, QPushButton, QScrollArea, QGridLayout, QLineEdit, QCompleter, QMessageBox)
from PyQt6.QtCore import Qt, QRectF, QPointF, QStringListModel, QTimer, QVariantAnimation

from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient, QConicalGradient, QTextDocument, \
    QTextCursor, QTextTable, QTextTableFormat, QPageSize, QPageLayout, QTextCharFormat, QTextLength
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt6.QtWidgets import QGroupBox
from src.database.db_manager import db_manager
from src.core.localization import lang_manager
from datetime import datetime, timedelta
import qtawesome as qta
from src.ui.table_styles import style_table
from src.ui.theme_manager import theme_manager
from src.ui.button_styles import style_button

class StatCard(QFrame):
    def __init__(self, title, value, subtext, icon_name, icon_color):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumHeight(120)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Icon Container
        icon_bg = QFrame()
        icon_bg.setFixedSize(50, 50)
        curr_color = QColor(icon_color)
        icon_bg.setStyleSheet(f"background-color: {curr_color.lighter(180).name()}; border-radius: 25px; border: none;")
        icon_layout = QVBoxLayout(icon_bg)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(24, 24))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_lbl)
        
        # Text Info
        text_layout = QVBoxLayout()
        # Point: "small label background should be none"
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #a3aed0; font-size: 14px; font-weight: 500; border: none; background: transparent;")
        
        v_color = "#ffffff" if theme_manager.is_dark else "#1b2559"
        self.value_lbl = QLabel(value)
        self.value_lbl.setFixedHeight(35)
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl.setStyleSheet(f"color: {v_color}; font-size: 24px; font-weight: bold; border: none; background: transparent;")
        
        self.sub_lbl = QLabel(subtext)
        self.sub_lbl.setStyleSheet("color: #a3aed0; font-size: 12px; border: none; background: transparent;")
        
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(self.value_lbl)
        text_layout.addWidget(self.sub_lbl)
        
        layout.addWidget(icon_bg)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Hover Animation
        self.hover_anim = QVariantAnimation()
        self.hover_anim.setDuration(400)
        self.hover_anim.setStartValue(QColor(255, 255, 255, 0))
        self.hover_anim.setEndValue(QColor(255, 255, 255, 20))
        self.hover_anim.valueChanged.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        t = theme_manager.DARK if theme_manager.is_dark else theme_manager.QUICKMART
        
        # Background
        painter.setBrush(QBrush(QColor(t['bg_card'])))
        painter.setPen(QPen(QColor(t['border']), 1))
        painter.drawRoundedRect(self.rect().adjusted(1,1,-1,-1), 12, 12)
        
        # Hover Overlay
        overlay = self.hover_anim.currentValue()
        if isinstance(overlay, QColor):
            painter.setBrush(QBrush(overlay))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect().adjusted(1,1,-1,-1), 12, 12)

    def enterEvent(self, event):
        self.hover_anim.setDirection(QVariantAnimation.Direction.Forward)
        self.hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hover_anim.setDirection(QVariantAnimation.Direction.Backward)
        self.hover_anim.start()
        super().leaveEvent(event)

    def update_data(self, value, subtext):
        self.value_lbl.setText(value)
        self.sub_lbl.setText(subtext)

class ModernPieChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.is_online = False # Simulation
        self.update_data()

    def update_data(self):
        # Point: "remove mobile option from pie chart if it is not online"
        if self.is_online:
            self.data = [("Cash", 60, "#05cd99"), ("Credit", 25, "#4318ff"), ("Mobile", 15, "#ffb547")]
        else:
            self.data = [("Cash", 75, "#05cd99"), ("Credit", 25, "#4318ff")]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        size = min(self.width(), self.height()) - 60
        rect = QRectF((self.width() - size)/2 - 40, (self.height() - size)/2, size, size)
        
        start_angle = 90 * 16
        total_val = sum(d[1] for d in self.data)
        for label, val, color in self.data:
            span_angle = int((val / total_val) * 360 * 16)
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawPie(rect, start_angle, span_angle)
            start_angle += span_angle

        # Legend
        legend_x = rect.right() + 40
        legend_y = rect.top() + 40
        for i, (label, val, color) in enumerate(self.data):
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(legend_x), int(legend_y + i*30), 12, 12)
            
            chart_text = "#ffffff" if theme_manager.is_dark else "#1b2559"
            painter.setPen(QColor(chart_text))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(legend_x + 20), int(legend_y + i*30 + 10), f"{label} {val}%")

class ModernBarChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)
        self.data = [2000, 3200, 4500, 6000, 8000, 10500, 4500, 3800]
        self.labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        padding_x, padding_y = 60, 40
        chart_w = w - padding_x * 2
        chart_h = h - padding_y * 2
        
        for i in range(5):
            y = padding_y + chart_h - (i * chart_h / 4)
            grid_color = "#1b2559" if theme_manager.is_dark else "#e0e5f2"
            painter.setPen(QPen(QColor(grid_color), 1))
            painter.drawLine(int(padding_x), int(y), int(padding_x + chart_w), int(y))
            painter.setPen(QColor("#a3aed0"))
            painter.drawText(10, int(y + 5), f"{i*2.5}k")
            painter.setPen(QPen(QColor("#e0e5f2"), 1))

        if not self.data: return
        max_val = max(self.data) if max(self.data) > 0 else 10000
        bar_gap = 20
        bar_w = (chart_w / len(self.data)) - bar_gap
        
        for i, val in enumerate(self.data):
            bar_h = (val / max_val) * chart_h
            x = padding_x + (i * (bar_w + bar_gap)) + bar_gap / 2
            y = padding_y + chart_h - bar_h
            painter.setBrush(QBrush(QColor("#4318ff")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), 4, 4)
            painter.setPen(QColor("#a3aed0"))
            painter.drawText(QRectF(x, padding_y + chart_h + 10, bar_w, 20), Qt.AlignmentFlag.AlignCenter, self.labels[i % len(self.labels)])

class ReportsView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_period = "daily"  # daily, weekly, monthly
        self.last_clear_date = datetime.now().date()
        self.init_ui()
        self.load_dashboard_data()
        
        # Setup midnight check timer
        self.midnight_timer = QTimer()
        self.midnight_timer.timeout.connect(self.check_midnight)
        self.midnight_timer.start(60000)  # Check every minute
        # Auto-refresh dashboard periodically so cards update after new sales
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_dashboard_data)
        self.refresh_timer.start(10000)  # refresh every 10 seconds
    
    def check_midnight(self):
        """Clear table data at midnight without affecting database"""
        current_date = datetime.now().date()
        if current_date > self.last_clear_date:
            self.last_clear_date = current_date
            # Clear all table displays
            self.stock_table.setRowCount(0)
            self.trans_table.setRowCount(0)
            self.sold_summary_table.setRowCount(0)
            self.pl_table.setRowCount(0)
            self.returns_table.setRowCount(0)
            # Reload fresh data for new day
            self.load_dashboard_data()
    
    def showEvent(self, event):
        """Auto-refresh data when view becomes visible"""
        super().showEvent(event)
        self.load_dashboard_data()

    def init_ui(self):
        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(20, 20, 20, 20)
        
        # Point: "the searchbar of 'search product..' should show a list of product"
        self.search_card = QFrame()
        self.search_card_layout = QHBoxLayout(self.search_card)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Product in Inventory...")
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet("border: none; font-size: 15px;")
        
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_input.setCompleter(self.completer)
        self.search_input.textChanged.connect(self.update_search_suggestions)
        
        
        self.search_icon = QLabel("🔍")
        self.search_card_layout.addWidget(self.search_icon)
        self.search_card_layout.addWidget(self.search_input)

        # Period filter ComboBox
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Daily", "Weekly", "Monthly"])
        self.period_combo.setFixedHeight(40)
        self.period_combo.setFixedWidth(150)
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        self.search_card_layout.addWidget(self.period_combo)

        # Full Report Print Button
        self.full_report_btn = QPushButton("🖨️ Complete Report")
        style_button(self.full_report_btn, variant="success", size="normal")
        self.full_report_btn.clicked.connect(self.print_full_report)
        self.search_card_layout.addWidget(self.full_report_btn)
        
        main_vbox.addWidget(self.search_card)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(25)
        scroll.setWidget(scroll_content)
        main_vbox.addWidget(scroll)

        # 1. Stats Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        self.card_sales = StatCard("Today's Sales", "0 AFN", "↑ 0%", "fa5s.check-circle", "#05cd99")
        self.card_orders = StatCard("Active Orders", "0 orders", "0 pending", "fa5s.shopping-cart", "#ffb547")
        self.card_stock = StatCard("Low Stock", "0 items", "Requires action", "fa5s.exclamation-circle", "#ee5d50")
        self.card_top_product = StatCard("Top Product", "None", "0 sold", "fa5s.award", "#4318ff")
        
        stats_layout.addWidget(self.card_sales)
        stats_layout.addWidget(self.card_orders)
        stats_layout.addWidget(self.card_stock)
        stats_layout.addWidget(self.card_top_product)
        layout.addLayout(stats_layout)

        # 2. Main Content Grid
        grid = QGridLayout()
        grid.setSpacing(20)
        
        sales_chart_card = QFrame()
        sales_chart_card.setObjectName("card")
        sc_layout = QVBoxLayout(sales_chart_card)
        sc_layout.addWidget(QLabel("Daily Sales", styleSheet="font-weight: bold; font-size: 16px; border: none; background: transparent;"))
        self.bar_chart = ModernBarChart()
        sc_layout.addWidget(self.bar_chart)
        grid.addWidget(sales_chart_card, 0, 0, 2, 2)
        
        pie_card = QFrame()
        pie_card.setObjectName("card")
        pie_layout = QVBoxLayout(pie_card)
        pie_layout.addWidget(QLabel("Payment Methods", styleSheet="font-weight: bold; font-size: 14px; border: none; background: transparent;"))
        self.pie_chart = ModernPieChart()
        pie_layout.addWidget(self.pie_chart)
        grid.addWidget(pie_card, 0, 2, 2, 2)
        
        layout.addLayout(grid)

        # 3. Tables Row
        tables_row = QHBoxLayout()

        # Low Stock Table with Print Button
        stock_group = QGroupBox("Critical Stock Alert")
        stock_layout = QVBoxLayout(stock_group)

        stock_header = QHBoxLayout()
        stock_title = QLabel("<b>Low Stock Items</b>")
        stock_title.setStyleSheet("border:none; background:transparent;")
        stock_header.addWidget(stock_title)

        stock_header.addStretch()
        self.stock_print_btn = QPushButton("🖨️ Print Report")
        style_button(self.stock_print_btn, variant="info", size="small")
        self.stock_print_btn.clicked.connect(lambda: self.print_table_report("Low Stock Alert", self.stock_table))
        stock_header.addWidget(self.stock_print_btn)

        stock_layout.addLayout(stock_header)

        self.stock_table = QTableWidget(0, 4)
        self.stock_table.setHorizontalHeaderLabels(["Product", "Current", "Min", "Status"])
        style_table(self.stock_table, variant="compact")
        self.stock_table.setFixedHeight(250)
        stock_layout.addWidget(self.stock_table)
        tables_row.addWidget(stock_group, 2)

        # Recent Transactions Table with Print Button
        trans_group = QGroupBox("Recent Transactions")
        trans_layout = QVBoxLayout(trans_group)

        trans_header = QHBoxLayout()
        trans_title = QLabel("<b>Invoice Transactions</b>")
        trans_title.setStyleSheet("border:none; background:transparent;")
        trans_header.addWidget(trans_title)

        trans_header.addStretch()
        self.trans_print_btn = QPushButton("🖨️ Print Report")
        style_button(self.trans_print_btn, variant="info", size="small")
        self.trans_print_btn.clicked.connect(lambda: self.print_table_report("Invoice Transactions", self.trans_table))
        trans_header.addWidget(self.trans_print_btn)

        trans_layout.addLayout(trans_header)

        self.trans_table = QTableWidget(0, 7)
        self.trans_table.setHorizontalHeaderLabels(["Inv #", "Time", "Customer", "Sold Items", "Amount", "Discount", "Method"])
        style_table(self.trans_table, variant="compact")
        self.trans_table.setFixedHeight(250)
        self.trans_table.itemDoubleClicked.connect(self.show_invoice_details)
        trans_layout.addWidget(self.trans_table)
        tables_row.addWidget(trans_group, 5)
        layout.addLayout(tables_row)

        # 4. Summary Row (Point: summary table for sold items & profit and loss)
        summary_row = QHBoxLayout()
        
        # Sold Items Summary Table with Print Button
        sold_summary_card = QFrame()
        sold_summary_card.setFixedHeight(400)
        sold_summary_card.setObjectName("card")
        sc_layout = QVBoxLayout(sold_summary_card)

        sold_header = QHBoxLayout()
        sold_title = QLabel("<b>Sold Items Breakdown</b>")
        sold_title.setStyleSheet("border:none; background:transparent;")
        sold_header.addWidget(sold_title)

        sold_header.addStretch()
        self.sold_print_btn = QPushButton("🖨️ Print Summary")
        style_button(self.sold_print_btn, variant="info", size="small")
        self.sold_print_btn.clicked.connect(lambda: self.print_table_report("Sold Items Summary", self.sold_summary_table))
        sold_header.addWidget(self.sold_print_btn)

        sc_layout.addLayout(sold_header)

        self.sold_summary_table = QTableWidget(0, 4)
        self.sold_summary_table.setHorizontalHeaderLabels(["Product", "Qty Sold", "Total Discount", "Total Sale"])
        style_table(self.sold_summary_table, variant="compact")
        sc_layout.addWidget(self.sold_summary_table)
        summary_row.addWidget(sold_summary_card, 3)

        # Profit & Loss Summary Card with Print Button
        pl_card = QFrame()
        pl_card.setFixedHeight(400)
        pl_card.setObjectName("card")
        pl_card_layout = QVBoxLayout(pl_card)

        pl_header = QHBoxLayout()
        pl_title = QLabel("<b>Profit & Loss Overview</b>")
        pl_title.setStyleSheet("border:none; background:transparent;")
        pl_header.addWidget(pl_title)

        pl_header.addStretch()
        self.pl_print_btn = QPushButton("🖨️ Print Report")
        style_button(self.pl_print_btn, variant="info", size="small")
        self.pl_print_btn.clicked.connect(lambda: self.print_table_report("Profit & Loss Report", self.pl_table))
        pl_header.addWidget(self.pl_print_btn)

        pl_card_layout.addLayout(pl_header)

        self.pl_table = QTableWidget(0, 2)
        self.pl_table.setHorizontalHeaderLabels(["Metric", "Value (AFN)"])
        style_table(self.pl_table, variant="compact")
        pl_card_layout.addWidget(self.pl_table)
        summary_row.addWidget(pl_card, 2)
        
        layout.addLayout(summary_row)

        # 5. Returns Row (Point: "in report window return items are not showing")
        returns_card = QFrame()
        returns_card.setObjectName("card")
        rc_layout = QVBoxLayout(returns_card)
        rc_layout.addWidget(QLabel("<b>Recent Returns</b>", styleSheet="border:none; background:transparent;"))
        self.returns_table = QTableWidget(0, 5)
        self.returns_table.setHorizontalHeaderLabels(["Date", "Invoice", "Product", "Qty", "Refund"])
        style_table(self.returns_table, variant="compact")
        self.returns_table.setFixedHeight(250)
        rc_layout.addWidget(self.returns_table)
        layout.addWidget(returns_card)
        
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def apply_theme(self):
        t = theme_manager.DARK if theme_manager.is_dark else theme_manager.QUICKMART
        
        self.search_card.setStyleSheet(f"""
            QFrame {{
                background-color: {t['bg_card']};
                border-radius: 10px;
                border: 1px solid {t['border']};
            }}
        """)
        
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                font-size: 15px;
                color: {t['text_main']};
                background: transparent;
            }}
        """)
        
        self.search_icon.setStyleSheet(f"color: {t['text_secondary']}; border: none; background: transparent;")
        
        # ComboBox Styling
        self.period_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 5px;
                background-color: {t['bg_main']};
                color: {t['text_main']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 0px;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t['bg_card']};
                color: {t['text_main']};
                selection-background-color: {t['primary']};
                selection-color: white;
            }}
        """)
    
    def on_period_changed(self, index):
        periods = ["daily", "weekly", "monthly"]
        self.current_period = periods[index]
        self.load_dashboard_data()

    def update_search_suggestions(self, text):
        if len(text) < 2: return
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name_en FROM products WHERE name_en LIKE ? LIMIT 10", (f"%{text}%",))
            res = [r[0] for r in cursor.fetchall()]
            self.completer.setModel(QStringListModel(res))

    def load_dashboard_data(self):
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate date range based on period
            if self.current_period == "daily":
                start_date = datetime.now().strftime('%Y-%m-%d')
                # Use strict date equality for daily, adjusting for local time
                date_filter = f"DATE(created_at, 'localtime') = '{start_date}'"
                period_label = "Today's"
            elif self.current_period == "weekly":
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                date_filter = f"DATE(created_at, 'localtime') >= '{start_date}'"
                period_label = "This Week's"
            else:  # monthly
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                date_filter = f"DATE(created_at, 'localtime') >= '{start_date}'"
                period_label = "This Month's"
            
            # Update sales card
            cursor.execute(f"SELECT SUM(total_amount) FROM sales WHERE {date_filter}")
            val = cursor.fetchone()[0] or 0
            self.card_sales.update_data(lang_manager.localize_digits(f"{val:,.0f} AFN"), f"{period_label} Revenue")
            
            # Update orders card
            cursor.execute(f"SELECT COUNT(*) FROM sales WHERE {date_filter.replace('created_at', 'sales.created_at')}")
            orders_count = cursor.fetchone()[0] or 0
            
            # Calculate total items sold
            join_date_filter = date_filter.replace("created_at", "s.created_at")
            cursor.execute(f"""
                SELECT SUM(si.quantity) 
                FROM sale_items si 
                JOIN sales s ON si.sale_id = s.id 
                WHERE {join_date_filter}
            """)
            items_count = cursor.fetchone()[0] or 0
            
            self.card_orders.update_data(lang_manager.localize_digits(f"{orders_count} orders"), 
                                       lang_manager.localize_digits(f"{items_count} items sold"))
            
            # Update low stock card (Inventory is state-based, not time-based)
            cursor.execute("SELECT COUNT(*) FROM inventory i JOIN products p ON i.product_id = p.id WHERE i.quantity <= p.min_stock")
            self.card_stock.update_data(lang_manager.localize_digits(f"{cursor.fetchone()[0]} items"), "Low stock items")
            
            # Update top product card
            cursor.execute(f"""
                SELECT p.name_en, SUM(si.quantity) as total_qty 
                FROM sale_items si 
                JOIN products p ON si.product_id = p.id 
                JOIN sales s ON si.sale_id = s.id 
                WHERE {join_date_filter}
                GROUP BY p.name_en 
                ORDER BY total_qty DESC LIMIT 1
            """)
            top_product = cursor.fetchone()
            if top_product:
                self.card_top_product.update_data(top_product[0], f"{int(top_product[1])} sold")
            else:
                self.card_top_product.update_data("None", "0 sold")
            
            # Check online status logic
            cursor.execute("SELECT mode FROM system_settings WHERE id = 1")
            row = cursor.fetchone()
            if row:
                self.pie_chart.is_online = (dict(row)['mode'] == 'ONLINE')
                self.pie_chart.update_data()
            
            self.populate_stock_table(cursor)
            self.populate_trans_table(cursor, date_filter)
            # Pass date_filter so summaries and P/L are scoped to the selected period
            # store last filter so other methods can access it if needed
            self._last_date_filter = date_filter
            self.populate_sold_summary(cursor, date_filter)
            self.populate_profit_loss(cursor, date_filter)
            self.populate_returns_table(cursor, date_filter)

    def populate_stock_table(self, cursor):
        cursor.execute("SELECT p.name_en, i.quantity, p.min_stock FROM inventory i JOIN products p ON i.product_id = p.id WHERE i.quantity <= p.min_stock LIMIT 5")
        stocks = cursor.fetchall()
        self.stock_table.setRowCount(0)
        for i, row in enumerate(stocks):
            self.stock_table.insertRow(i)
            self.stock_table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.stock_table.setItem(i, 1, QTableWidgetItem(lang_manager.localize_digits(str(row[1]))))
            self.stock_table.setItem(i, 2, QTableWidgetItem(lang_manager.localize_digits(str(row[2]))))
            self.stock_table.setItem(i, 3, QTableWidgetItem("Low"))

    def populate_trans_table(self, cursor, date_filter=None):
        where_clause = ""
        if date_filter:
            where_clause = f"WHERE {date_filter.replace('created_at', 's.created_at')}"
            
        cursor.execute(f"""
            SELECT s.invoice_number, s.created_at, IFNULL(c.name_en, 'Walk-in'), 
            (SELECT COUNT(*) FROM sale_items WHERE sale_id = s.id), s.total_amount, 
            0 as discount_placeholder, s.payment_type 
            FROM sales s LEFT JOIN customers c ON s.customer_id = c.id 
            {where_clause}
            ORDER BY s.created_at DESC LIMIT 5
        """)
        trans = cursor.fetchall()
        self.trans_table.setRowCount(0)
        for i, row in enumerate(trans):
            self.trans_table.insertRow(i)
            self.trans_table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.trans_table.setItem(i, 1, QTableWidgetItem(lang_manager.localize_digits(row[1].split()[-1] if ' ' in row[1] else row[1])))
            self.table_item(self.trans_table, i, 2, row[2])
            self.table_item(self.trans_table, i, 3, lang_manager.localize_digits(str(row[3])))
            self.table_item(self.trans_table, i, 4, lang_manager.localize_digits(f"{row[4]:.2f}"))
            self.table_item(self.trans_table, i, 5, lang_manager.localize_digits("0.00")) # Placeholder for discount logic
            self.table_item(self.trans_table, i, 6, row[6])

    def populate_sold_summary(self, cursor, date_filter=None):
        # Limit sold summary to the current period when date_filter is provided
        # date_filter is generated in load_dashboard_data and references a generic created_at
        sales_filter = None
        if date_filter:
            # qualify created_at with sales table alias
            sales_filter = date_filter.replace("created_at", "s.created_at")
            where_clause = f"WHERE {sales_filter}"
        else:
            where_clause = ""

        cursor.execute(f"""
            SELECT si.product_name, SUM(si.quantity) as qty, 0 as discount, SUM(si.total_price) as total
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            {where_clause}
            GROUP BY si.product_id
            ORDER BY SUM(si.quantity) DESC LIMIT 5
        """)
        
        rows = cursor.fetchall()
        self.sold_summary_table.setRowCount(0)
        for i, row in enumerate(rows):
            self.sold_summary_table.insertRow(i)
            self.sold_summary_table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.sold_summary_table.setItem(i, 1, QTableWidgetItem(lang_manager.localize_digits(str(row[1]))))
            self.sold_summary_table.setItem(i, 2, QTableWidgetItem(lang_manager.localize_digits(f"{row[2]:.2f}")))
            self.sold_summary_table.setItem(i, 3, QTableWidgetItem(lang_manager.localize_digits(f"{row[3]:.2f}")))

    def populate_profit_loss(self, cursor, date_filter=None):
        # Scope revenue and cost to selected period
        sales_filter = None
        if date_filter:
            sales_filter = date_filter.replace("created_at", "s.created_at")
            where_clause = f"WHERE {sales_filter}"
        else:
            where_clause = ""

        cursor.execute(f"""
            SELECT 
                SUM(si.total_price) as total_revenue,
                SUM(si.quantity * p.cost_price) as total_cost
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            {where_clause}
        """)
        res = cursor.fetchone()
        raw_revenue = res[0] or 0
        raw_cost = res[1] or 0

        # Deduct returns (scope by sales_returns.created_at when a filter is present)
        if date_filter:
            returns_filter = date_filter.replace("created_at", "sr.created_at")
            cursor.execute(f"SELECT SUM(sr.refund_amount) FROM sales_returns sr JOIN sales s ON sr.sale_id = s.id WHERE {returns_filter}")
        else:
            cursor.execute("SELECT SUM(refund_amount) FROM sales_returns")
        returned_revenue = cursor.fetchone()[0] or 0

        if date_filter:
            cursor.execute(f"""
                SELECT SUM(ri.quantity * p.cost_price) 
                FROM return_items ri 
                JOIN products p ON ri.product_id = p.id
                JOIN sales_returns sr ON ri.return_id = sr.id
                JOIN sales s ON sr.sale_id = s.id
                WHERE {returns_filter}
            """)
        else:
            cursor.execute("""
                SELECT SUM(ri.quantity * p.cost_price) 
                FROM return_items ri 
                JOIN products p ON ri.product_id = p.id
            """)
        returned_cost = cursor.fetchone()[0] or 0
        
        revenue = raw_revenue - returned_revenue
        cost = raw_cost - returned_cost
        profit = revenue - cost
        
        metrics = [
            ("Total Sales (Net)", revenue),
            ("Total Cost (Net)", cost),
            ("Total Returns", returned_revenue),
            ("Gross Profit", profit),
            ("Net Margin (%)", (profit/revenue*100) if revenue > 0 else 0)
        ]
        
        self.pl_table.setRowCount(0)
        for i, (label, val) in enumerate(metrics):
            self.pl_table.insertRow(i)
            self.pl_table.setItem(i, 0, QTableWidgetItem(label))
            suffix = "%" if "Margin" in label else ""
            self.pl_table.setItem(i, 1, QTableWidgetItem(lang_manager.localize_digits(f"{val:.2f}{suffix}")))

    def populate_returns_table(self, cursor, date_filter=None):
        # Scope recent returns to the selected period when provided
        if date_filter:
            returns_filter = date_filter.replace("created_at", "sr.created_at")
            cursor.execute(f"""
                SELECT sr.created_at, s.invoice_number, p.name_en, ri.quantity, ri.refund_price
                FROM sales_returns sr
                JOIN sales s ON sr.sale_id = s.id
                JOIN return_items ri ON ri.return_id = sr.id
                JOIN products p ON ri.product_id = p.id
                WHERE {returns_filter}
                ORDER BY sr.created_at DESC LIMIT 5
            """)
        else:
            cursor.execute("""
                SELECT sr.created_at, s.invoice_number, p.name_en, ri.quantity, ri.refund_price
                FROM sales_returns sr
                JOIN sales s ON sr.sale_id = s.id
                JOIN return_items ri ON ri.return_id = sr.id
                JOIN products p ON ri.product_id = p.id
                ORDER BY sr.created_at DESC LIMIT 5
            """)
        rows = cursor.fetchall()
        self.returns_table.setRowCount(0)
        for i, row in enumerate(rows):
            self.returns_table.insertRow(i)
            self.returns_table.setItem(i, 0, QTableWidgetItem(lang_manager.localize_digits(row[0].split()[-1] if ' ' in row[0] else row[0])))
            self.returns_table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.returns_table.setItem(i, 2, QTableWidgetItem(row[2]))
            self.returns_table.setItem(i, 3, QTableWidgetItem(lang_manager.localize_digits(str(row[3]))))
            self.returns_table.setItem(i, 4, QTableWidgetItem(lang_manager.localize_digits(f"{row[4]:.2f}")))

    def table_item(self, table, row, col, text):
        table.setItem(row, col, QTableWidgetItem(str(text)))

    def print_table_report(self, title, table):
        """Print a table report with preview"""
        if table.rowCount() == 0:
            QMessageBox.information(self, "No Data", "No data available to print.")
            return

        # Create printer
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        # Create print preview dialog
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle(f"Print Preview - {title}")
        preview.setMinimumSize(800, 600)

        # Connect print function
        preview.paintRequested.connect(lambda p: self.render_table_document(p, title, table))

        # Show preview
        preview.exec()

    def render_table_document(self, printer, title, table):
        """Render table as printable document"""
        document = QTextDocument()
        cursor = QTextCursor(document)

        # Title
        title_format = QTextCharFormat()
        title_format.setFontPointSize(16)
        title_format.setFontWeight(QFont.Weight.Bold)
        cursor.insertText(f"{title}\n", title_format)
        cursor.insertText("\n")

        # Date and period info
        info_format = QTextCharFormat()
        info_format.setFontPointSize(10)
        period_text = self.period_combo.currentText()
        cursor.insertText(f"Report Period: {period_text}\n", info_format)
        cursor.insertText(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", info_format)
        cursor.insertText("\n")

        # Create table
        rows = table.rowCount()
        cols = table.columnCount()

        if rows > 0 and cols > 0:
            # Create table format
            table_format = QTextTableFormat()
            table_format.setBorderStyle(QTextTableFormat.BorderStyle.BorderStyle_Solid)
            table_format.setCellPadding(5)
            table_format.setCellSpacing(0)
            table_format.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))

            # Insert table
            text_table = cursor.insertTable(rows + 1, cols, table_format)  # +1 for header

            # Header row
            header_format = QTextCharFormat()
            header_format.setFontWeight(QFont.Weight.Bold)
            header_format.setBackground(QColor("#f0f0f0"))

            for col in range(cols):
                header_item = table.horizontalHeaderItem(col)
                if header_item:
                    cell_cursor = text_table.cellAt(0, col).firstCursorPosition()
                    cell_cursor.insertText(header_item.text(), header_format)

            # Data rows
            for row in range(rows):
                for col in range(cols):
                    item = table.item(row, col)
                    if item:
                        cell_cursor = text_table.cellAt(row + 1, col).firstCursorPosition()
                        cell_cursor.insertText(item.text())

        # Footer with summary
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText("\n\n")

        footer_format = QTextCharFormat()
        footer_format.setFontPointSize(10)
        footer_format.setFontItalic(True)

        if "Low Stock" in title and table == self.stock_table:
            low_stock_count = table.rowCount()
            cursor.insertText(f"Total Low Stock Items: {low_stock_count}\n", footer_format)

        elif "Invoice Transactions" in title and table == self.trans_table:
            total_sales = 0
            for row in range(table.rowCount()):
                amount_item = table.item(row, 4)  # Amount column
                if amount_item:
                    try:
                        amount = float(amount_item.text().replace(',', ''))
                        total_sales += amount
                    except:
                        pass
            cursor.insertText(".2f", footer_format)

        elif "Sold Items Summary" in title and table == self.sold_summary_table:
            total_qty = 0
            total_sales = 0
            for row in range(table.rowCount()):
                qty_item = table.item(row, 1)
                sales_item = table.item(row, 3)
                if qty_item:
                    try:
                        total_qty += int(qty_item.text())
                    except:
                        pass
                if sales_item:
                    try:
                        total_sales += float(sales_item.text().replace(',', ''))
                    except:
                        pass
            cursor.insertText(".2f", footer_format)

        # Print the document
        document.print(printer)

    def print_full_report(self):
        """Print a comprehensive full report with all tables"""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)

        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle("Print Preview - Complete Reports Summary")
        preview.setMinimumSize(1000, 700)

        preview.paintRequested.connect(self.render_full_report)
        preview.exec()

    def render_full_report(self, printer):
        """Render complete report with all sections"""
        document = QTextDocument()
        cursor = QTextCursor(document)

        # Main title
        title_format = QTextCharFormat()
        title_format.setFontPointSize(18)
        title_format.setFontWeight(QFont.Weight.Bold)
        cursor.insertText("Complete Business Reports Summary\n", title_format)
        cursor.insertText("\n")

        # Date info
        info_format = QTextCharFormat()
        info_format.setFontPointSize(10)
        cursor.insertText(f"Report Period: {self.period_combo.currentText()}\n", info_format)
        cursor.insertText(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", info_format)
        cursor.insertText("\n")

        # Add each section
        sections = [
            ("Low Stock Alert", self.stock_table),
            ("Invoice Transactions", self.trans_table),
            ("Sold Items Breakdown", self.sold_summary_table),
            ("Profit & Loss Overview", self.pl_table)
        ]

        for section_title, table in sections:
            if table.rowCount() > 0:
                # Section header
                section_format = QTextCharFormat()
                section_format.setFontPointSize(14)
                section_format.setFontWeight(QFont.Weight.Bold)
                cursor.insertText(f"{section_title}\n", section_format)

                # Create table for this section
                rows = table.rowCount()
                cols = table.columnCount()

                table_format = QTextTableFormat()
                table_format.setBorderStyle(QTextTableFormat.BorderStyle.BorderStyle_Solid)
                table_format.setCellPadding(3)
                table_format.setCellSpacing(0)
                table_format.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))

                text_table = cursor.insertTable(rows + 1, cols, table_format)

                # Headers
                header_format = QTextCharFormat()
                header_format.setFontWeight(QFont.Weight.Bold)
                header_format.setBackground(QColor("#f0f0f0"))

                for col in range(cols):
                    header_item = table.horizontalHeaderItem(col)
                    if header_item:
                        cell_cursor = text_table.cellAt(0, col).firstCursorPosition()
                        cell_cursor.insertText(header_item.text(), header_format)

                # Data
                for row in range(rows):
                    for col in range(cols):
                        item = table.item(row, col)
                        if item:
                            cell_cursor = text_table.cellAt(row + 1, col).firstCursorPosition()
                            cell_cursor.insertText(item.text())

                cursor.insertText("\n\n")

        document.print(printer)

    def show_invoice_details(self, item):
        """Show popup with sold products for specific invoice"""
        row = item.row()
        inv_item = self.trans_table.item(row, 0)  # Invoice number column
        if not inv_item:
            return

        invoice_number = inv_item.text().strip()
        if not invoice_number:
            return

        # Create popup dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QHBoxLayout, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Invoice Details - {invoice_number}")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)

        # Header info
        header_layout = QHBoxLayout()
        inv_label = QLabel(f"<b>Invoice:</b> {invoice_number}")
        time_item = self.trans_table.item(row, 1)
        customer_item = self.trans_table.item(row, 2)
        amount_item = self.trans_table.item(row, 4)

        time_text = time_item.text() if time_item else "N/A"
        customer_text = customer_item.text() if customer_item else "N/A"
        amount_text = amount_item.text() if amount_item else "0.00"

        time_label = QLabel(f"<b>Time:</b> {time_text}")
        customer_label = QLabel(f"<b>Customer:</b> {customer_text}")
        amount_label = QLabel(f"<b>Total:</b> {amount_text} AFN")

        header_layout.addWidget(inv_label)
        header_layout.addWidget(time_label)
        header_layout.addWidget(customer_label)
        header_layout.addWidget(amount_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Products table
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["Product", "Quantity", "Unit Price", "Total", "Batch"])
        style_table(table, variant="compact")

        layout.addWidget(QLabel("<b>Sold Products:</b>"))
        layout.addWidget(table)

        # Load invoice items
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Get sale ID first
                cursor.execute("SELECT id FROM sales WHERE invoice_number = ?", (invoice_number,))
                sale_result = cursor.fetchone()

                if sale_result:
                    sale_id = sale_result['id']

                    # Get sale items with product details
                    cursor.execute("""
                        SELECT si.*, p.name_en as product_name, p.barcode,
                               'N/A' as batch
                        FROM sale_items si
                        JOIN products p ON si.product_id = p.id
                        WHERE si.sale_id = ?
                        ORDER BY si.id
                    """, (sale_id,))

                    items = cursor.fetchall()

                    for i, item in enumerate(items):
                        table.insertRow(i)
                        table.setItem(i, 0, QTableWidgetItem(item['product_name']))
                        table.setItem(i, 1, QTableWidgetItem(str(item['quantity'])))
                        table.setItem(i, 2, QTableWidgetItem(f"{item['unit_price']:.2f}"))
                        table.setItem(i, 3, QTableWidgetItem(f"{item['total_price']:.2f}"))
                        table.setItem(i, 4, QTableWidgetItem(item['batch']))

        except Exception as e:
            error_table = QTableWidget(1, 1)
            error_table.setItem(0, 0, QTableWidgetItem(f"Error loading data: {str(e)}"))
            layout.addWidget(error_table)

        # Close button
        close_btn = QPushButton("Close")
        style_button(close_btn, variant="primary")
        close_btn.clicked.connect(dialog.accept)

        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.exec()

    def add_full_report_button(self):
        """Add a button to print full report"""
        # This will be called during UI initialization
        full_report_btn = QPushButton("🖨️ Print Complete Report")
        style_button(full_report_btn, variant="success")
        full_report_btn.clicked.connect(self.print_full_report)

        # Add to the main layout - this would need to be positioned properly
        # For now, we'll add it to the search card layout
        self.search_card_layout.addWidget(full_report_btn)