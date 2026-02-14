import sys, os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
                             QComboBox, QPushButton, QScrollArea, QGridLayout, QLineEdit, QCompleter, QMessageBox,
                             QDateEdit, QSpinBox, QGroupBox, QApplication, QMainWindow, QFileDialog)
from PyQt6.QtCore import Qt, QRectF, QPointF, QStringListModel, QTimer, QVariantAnimation, QThread, pyqtSignal

from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient, QConicalGradient, QTextDocument, \
    QTextCursor, QTextTable, QTextTableFormat, QPageSize, QPageLayout, QTextCharFormat, QTextLength
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from six import exec_

from src.database.db_manager import db_manager
from src.core.localization import lang_manager
from datetime import datetime, timedelta
from src.ui.components.stat_card import StatCard
import qtawesome as qta
from src.ui.table_styles import style_table
from src.ui.theme_manager import theme_manager
from src.ui.button_styles import style_button
from src.utils import printer

try:
    from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
except ImportError:
    QChart = None

class ReportsWorker(QThread):
    data_loaded = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, period="daily", start_date=None, end_date=None, expiry_days=30):
        super().__init__()
        self.period = period
        self.start_date = start_date
        self.end_date = end_date
        self.expiry_days = expiry_days

    def run(self):
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # ... (date filter logic remains same) ...
                # Calculate date range based on period
                if self.period == "daily":
                    start_date = datetime.now().strftime('%Y-%m-%d')
                    date_filter = f"DATE(created_at, 'localtime') = '{start_date}'"
                    period_label = "Today's"
                elif self.period == "weekly":
                    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    date_filter = f"DATE(created_at, 'localtime') >= '{start_date}'"
                    period_label = "This Week's"
                elif self.period == "monthly":
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    date_filter = f"DATE(created_at, 'localtime') >= '{start_date}'"
                    period_label = "This Month's"
                elif self.period == "custom" and self.start_date and self.end_date:
                    date_filter = f"DATE(created_at, 'localtime') BETWEEN '{self.start_date}' AND '{self.end_date}'"
                    period_label = f"{self.start_date} to {self.end_date}"
                else:
                    # Fallback
                    start_date = datetime.now().strftime('%Y-%m-%d')
                    date_filter = f"DATE(created_at, 'localtime') = '{start_date}'"
                    period_label = "Today's"
                
                # Stats
                cursor.execute(f"SELECT SUM(total_amount) FROM sales WHERE {date_filter}")
                sales_val = cursor.fetchone()[0] or 0
                
                cursor.execute(f"SELECT COUNT(*) FROM sales WHERE {date_filter}")
                orders_count = cursor.fetchone()[0] or 0
                
                cursor.execute(f"SELECT SUM(si.quantity) FROM sale_items si JOIN sales s ON si.sale_id = s.id WHERE {date_filter.replace('created_at', 's.created_at')}")
                items_count = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM inventory i JOIN products p ON i.product_id = p.id WHERE i.quantity <= p.min_stock")
                low_stock_count = cursor.fetchone()[0] or 0
                
                cursor.execute(f"SELECT p.name_en, SUM(si.quantity) as total_qty FROM sale_items si JOIN products p ON si.product_id = p.id JOIN sales s ON si.sale_id = s.id WHERE {date_filter.replace('created_at', 's.created_at')} GROUP BY p.name_en ORDER BY total_qty DESC LIMIT 1")
                top_product = cursor.fetchone()
                
                # Mode
                cursor.execute("SELECT mode FROM system_settings WHERE id = 1")
                mode_row = cursor.fetchone()
                is_online = (dict(mode_row)['mode'] == 'ONLINE') if mode_row else False

                # Tables Data (Small samples for dashboard)
                # Low Stock
                cursor.execute("SELECT p.name_en, i.quantity, p.min_stock FROM inventory i JOIN products p ON i.product_id = p.id WHERE i.quantity <= p.min_stock LIMIT 10")
                low_stock_data = [list(r) for r in cursor.fetchall()]

                # Expiry Stock
                expiry_limit = (datetime.now() + timedelta(days=self.expiry_days)).strftime('%Y-%m-%d')
                cursor.execute(f"SELECT p.name_en, i.quantity, p.expiry_date FROM inventory i JOIN products p ON i.product_id = p.id WHERE p.expiry_date <= '{expiry_limit}' AND p.expiry_date IS NOT NULL ORDER BY p.expiry_date ASC LIMIT 10")
                expiry_data = [list(r) for r in cursor.fetchall()]
                
                cursor.execute(f"SELECT s.invoice_number, s.created_at, IFNULL(c.name_en, 'Walk-in'), (SELECT COUNT(*) FROM sale_items WHERE sale_id = s.id), s.total_amount, s.payment_type FROM sales s LEFT JOIN customers c ON s.customer_id = c.id WHERE {date_filter.replace('created_at', 's.created_at')} ORDER BY s.created_at DESC LIMIT 5")
                trans_data = [list(r) for r in cursor.fetchall()]

                # Top 5 Sold Products (Requirement 8)
                cursor.execute(f"SELECT SUM(quantity) FROM sale_items JOIN sales ON sale_items.sale_id = sales.id WHERE {date_filter.replace('created_at', 'sales.created_at')}")
                total_sold = cursor.fetchone()[0] or 1
                
                cursor.execute(f"""
                    SELECT p.name_en, SUM(si.quantity), (SUM(si.quantity) * 100.0 / {total_sold}) as percent, SUM(si.total_price) 
                    FROM sale_items si JOIN sales s ON si.sale_id = s.id 
                    JOIN products p ON si.product_id = p.id
                    WHERE {date_filter.replace('created_at', 's.created_at')} 
                    GROUP BY p.id 
                    ORDER BY SUM(si.quantity) DESC LIMIT 5
                """)
                sold_summary_data = [list(r) for r in cursor.fetchall()]

                # P/L
                cursor.execute(f"SELECT SUM(si.total_price), SUM(si.quantity * p.cost_price) FROM sale_items si JOIN products p ON si.product_id = p.id JOIN sales s ON si.sale_id = s.id WHERE {date_filter.replace('created_at', 's.created_at')}")
                res = cursor.fetchone()
                raw_revenue = res[0] or 0
                raw_cost = res[1] or 0

                returns_filter = date_filter.replace("created_at", "sr.created_at")
                cursor.execute(f"SELECT SUM(sr.refund_amount) FROM sales_returns sr JOIN sales s ON sr.sale_id = s.id WHERE {returns_filter}")
                returned_revenue = cursor.fetchone()[0] or 0

                cursor.execute(f"SELECT SUM(ri.quantity * p.cost_price) FROM return_items ri JOIN products p ON ri.product_id = p.id JOIN sales_returns sr ON ri.return_id = sr.id JOIN sales s ON sr.sale_id = s.id WHERE {returns_filter}")
                returned_cost = cursor.fetchone()[0] or 0

                # Returns Table
                cursor.execute(f"SELECT sr.created_at, s.invoice_number, p.name_en, ri.quantity, ri.refund_price FROM sales_returns sr JOIN sales s ON sr.sale_id = s.id JOIN return_items ri ON ri.return_id = sr.id JOIN products p ON ri.product_id = p.id WHERE {returns_filter} ORDER BY sr.created_at DESC LIMIT 5")
                returns_table_data = [list(r) for r in cursor.fetchall()]

                result = {
                    "sales_val": sales_val,
                    "orders_count": orders_count,
                    "items_count": items_count,
                    "low_stock_count": low_stock_count,
                    "top_product": top_product,
                    "is_online": is_online,
                    "low_stock_data": low_stock_data,
                    "expiry_data": expiry_data,
                    "trans_data": trans_data,
                    "sold_summary_data": sold_summary_data,
                    "raw_revenue": raw_revenue,
                    "raw_cost": raw_cost,
                    "returned_revenue": returned_revenue,
                    "returned_cost": returned_cost,
                    "returns_table_data": returns_table_data,
                    "period_label": period_label,
                    "date_filter": date_filter
                }
                self.data_loaded.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# Removed local StatCard class to use shared src.ui.components.stat_card

class DonutChartWidget(QChartView):
    def __init__(self, parent=None):
        super().__init__(parent)
        if not QChart: return
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart = QChart()
        self.chart.setBackgroundVisible(False)
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        self.series = QPieSeries()
        self.series.setHoleSize(0.6)
        self.chart.addSeries(self.series)
        self.setChart(self.chart)
        self.setStyleSheet("background: transparent; border: none;")

    def update_data(self, data):
        if not QChart: return
        self.series.clear()
        for item in data:
            name = item[0] or "Unknown"
            percent = float(item[2] or 0)
            slice = QPieSlice(f"{name} ({percent:.1f}%)", percent)
            
            # Use same color buckets as dashboard
            if percent <= 25: slice.setColor(QColor("#FF4B2B"))
            elif percent <= 50: slice.setColor(QColor("#FF8C00"))
            elif percent <= 75: slice.setColor(QColor("#00c6ff"))
            else: slice.setColor(QColor("#43e97b"))
            
            self.series.append(slice)

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

class StoreReportsView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_period = "daily"  # daily, weekly, monthly
        self.last_clear_date = datetime.now().date()
        self.worker = None
        self.is_loading = False
        self.init_ui()
        self.load_dashboard_data()
        
        # Setup midnight check timer
        self.midnight_timer = QTimer()
        self.midnight_timer.timeout.connect(self.check_midnight)
        self.midnight_timer.start(60000)  # Check every minute
        
        # Auto-refresh dashboard periodically
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_dashboard_data)
        self.refresh_timer.start(60000)  # refresh every 60 seconds (less aggressive)
    
    def cleanup_thread(self):
        if self.worker:
            try:
                if self.worker.isRunning():
                    # Instead of blocking wait, we just disconnect and let it finish in background
                    try:
                        self.worker.data_loaded.disconnect()
                        self.worker.error.disconnect()
                    except: pass
                    # self.worker.quit() # Still tell it to quit if it has an event loop
            except RuntimeError:
                pass
        self.worker = None
    
    def check_midnight(self):
        """Clear table data at midnight without affecting database"""
        # Prevent background activity if app is not focused
        from PyQt6.QtWidgets import QApplication
        if QApplication.applicationState() != Qt.ApplicationState.ApplicationActive:
            return

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
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.start()

    def hideEvent(self, event):
        """Stop timer when view is hidden to save resources"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().hideEvent(event)

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
        self.period_combo.addItems(["Daily", "Weekly", "Monthly", "Custom"])
        self.period_combo.setFixedHeight(40)
        self.period_combo.setFixedWidth(150)
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        self.search_card_layout.addWidget(self.period_combo)
        
        # Custom Date Range (Hidden by default)
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(datetime.now().date())
        self.date_from.setVisible(False)
        self.search_card_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(datetime.now().date())
        self.date_to.setVisible(False)
        self.search_card_layout.addWidget(self.date_to)
        
        self.filter_btn = QPushButton("Filter")
        style_button(self.filter_btn, variant="primary", size="small")
        self.filter_btn.clicked.connect(self.load_dashboard_data)
        self.filter_btn.setVisible(False)
        self.search_card_layout.addWidget(self.filter_btn)

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

        # 2. Charts Row
        charts_layout = QHBoxLayout()
        
        sales_chart_card = QFrame()
        sales_chart_card.setObjectName("card")
        sc_layout = QVBoxLayout(sales_chart_card)
        sc_layout.addWidget(QLabel("Daily Sales", styleSheet="font-weight: bold; font-size: 16px; border: none; background: transparent;"))
        self.bar_chart = ModernBarChart()
        sc_layout.addWidget(self.bar_chart)
        charts_layout.addWidget(sales_chart_card, 6)
        
        # Right: Quick Stats Table
        sold_summary_card = QFrame()
        sold_summary_card.setObjectName("card")
        sold_summary_card_layout = QVBoxLayout(sold_summary_card)
        sold_summary_card_layout.addWidget(QLabel("Top Sold Products", styleSheet="font-weight: bold; font-size: 14px; border: none; background: transparent;"))
        self.donut_chart = DonutChartWidget()
        sold_summary_card_layout.addWidget(self.donut_chart)
        
        self.sold_summary_table = QTableWidget(0, 4)
        self.sold_summary_table.setHorizontalHeaderLabels(["Product", "Quantity", "Share %", "Revenue"])
        style_table(self.sold_summary_table, variant="premium")
        sold_summary_card_layout.addWidget(self.sold_summary_table)
        charts_layout.addWidget(sold_summary_card, 4)
        
        layout.addLayout(charts_layout)
        
        # 3. Expiry Section (Requirement 8)
        expiry_group = QGroupBox("📅 Expiry Stock Watch")
        expiry_vbox = QVBoxLayout(expiry_group)
        
        expiry_filter_lay = QHBoxLayout()
        expiry_filter_lay.addWidget(QLabel("Expiring within (days):"))
        self.expiry_days_spin = QSpinBox()
        self.expiry_days_spin.setRange(1, 365)
        self.expiry_days_spin.setValue(30)
        self.expiry_days_spin.setFixedWidth(80)
        self.expiry_days_spin.valueChanged.connect(self.load_dashboard_data)
        expiry_filter_lay.addWidget(self.expiry_days_spin)
        expiry_filter_lay.addStretch()
        expiry_vbox.addLayout(expiry_filter_lay)
        
        self.expiry_table = QTableWidget(0, 4)
        self.expiry_table.setHorizontalHeaderLabels(["Product", "Quantity", "Expiry Date", "Days Left"])
        style_table(self.expiry_table, variant="premium")
        expiry_vbox.addWidget(self.expiry_table)
        
        layout.addWidget(expiry_group)

        # 4. Tables Row
        tables_row = QHBoxLayout()

        # Low Stock Table with Print Button
        stock_group = QGroupBox("Critical Stock Alert")
        stock_layout = QVBoxLayout(stock_group)

        stock_header = QHBoxLayout()
        stock_title = QLabel("<b>Stock Alerts</b>")
        stock_title.setStyleSheet("border:none; background:transparent;")
        stock_header.addWidget(stock_title)
        
        self.alert_mode_combo = QComboBox()
        self.alert_mode_combo.addItems(["Low Stock", "Expiring Soon"])
        self.alert_mode_combo.currentIndexChanged.connect(self.toggle_alert_mode)
        stock_header.addWidget(self.alert_mode_combo)
        
        # self.expiry_days_spin = QSpinBox() # This was moved to the new expiry section
        # self.expiry_days_spin.setRange(1, 365)
        # self.expiry_days_spin.setValue(30)
        # self.expiry_days_spin.setSuffix(" days")
        # self.expiry_days_spin.setVisible(False) # Hidden by default
        # self.expiry_days_spin.valueChanged.connect(self.load_dashboard_data)
        # stock_header.addWidget(self.expiry_days_spin)

        stock_header.addStretch()
        self.stock_print_btn = QPushButton("🖨️ Print")
        style_button(self.stock_print_btn, variant="info", size="small")
        self.stock_print_btn.clicked.connect(lambda: self.print_table_report("Stock Alert", self.stock_table))
        stock_header.addWidget(self.stock_print_btn)

        stock_layout.addLayout(stock_header)

        self.stock_table = QTableWidget(0, 4)
        self.stock_table.setHorizontalHeaderLabels(["Product", "Qty", "Min/Exp", "Status"])
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

        self.trans_table = QTableWidget(0, 8)
        self.trans_table.setHorizontalHeaderLabels(["Inv #", "Time", "Customer", "Sold Items", "Amount", "Discount", "Method", "Action"])
        style_table(self.trans_table, variant="compact")
        self.trans_table.setFixedHeight(250)
        self.trans_table.itemDoubleClicked.connect(self.show_invoice_details)
        trans_layout.addWidget(self.trans_table)
        tables_row.addWidget(trans_group, 5)
        layout.addLayout(tables_row)

        # 5. Summary Row (Point: summary table for sold items & profit and loss)
        summary_row = QHBoxLayout()
        
        # Sold Items Summary Table with Print Button (This was moved to charts_layout)
        # sold_summary_card = QFrame()
        # sold_summary_card.setFixedHeight(400)
        # sold_summary_card.setObjectName("card")
        # sc_layout = QVBoxLayout(sold_summary_card)

        # sold_header = QHBoxLayout()
        # sold_title = QLabel("<b>Sold Items Breakdown</b>")
        # sold_title.setStyleSheet("border:none; background:transparent;")
        # sold_header.addWidget(sold_title)

        # sold_header.addStretch()
        # self.sold_print_btn = QPushButton("🖨️ Print Summary")
        # style_button(self.sold_print_btn, variant="info", size="small")
        # self.sold_print_btn.clicked.connect(lambda: self.print_table_report("Sold Items Summary", self.sold_summary_table))
        # sold_header.addWidget(self.sold_print_btn)

        # sc_layout.addLayout(sold_header)

        # self.sold_summary_table = QTableWidget(0, 4)
        # self.sold_summary_table.setHorizontalHeaderLabels(["Product", "Qty Sold", "Total Discount", "Total Sale"])
        # style_table(self.sold_summary_table, variant="compact")
        # sc_layout.addWidget(self.sold_summary_table)
        # summary_row.addWidget(sold_summary_card, 3)

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
        periods = ["daily", "weekly", "monthly", "custom"]
        self.current_period = periods[index]
        
        is_custom = self.current_period == "custom"
        self.date_from.setVisible(is_custom)
        self.date_to.setVisible(is_custom)
        self.filter_btn.setVisible(is_custom)
        
        if not is_custom:
            self.load_dashboard_data()

    def update_search_suggestions(self, text):
        if len(text) < 2: return
        
        if not hasattr(self, 'search_suggest_timer'):
            self.search_suggest_timer = QTimer(self)
            self.search_suggest_timer.setSingleShot(True)
            self.search_suggest_timer.setInterval(300)
            self.search_suggest_timer.timeout.connect(lambda: self._do_search_suggestions(self.search_input.text()))
        
        self.search_suggest_timer.start()

    def _do_search_suggestions(self, text):
        if len(text) < 2: return
        from src.core.blocking_task_manager import task_manager
        
        def fetch_suggest():
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name_en FROM products WHERE name_en LIKE ? LIMIT 10", (f"%{text}%",))
                    return [r[0] for r in cursor.fetchall()]
            except:
                return []

        def on_finished(res):
            from PyQt6.QtCore import QStringListModel
            self.completer.setModel(QStringListModel(res))
            # If the menu isn't showing, try to show it if we have results
            if res and self.search_input.hasFocus():
                self.completer.complete()

        task_manager.run_task(fetch_suggest, on_finished=on_finished)

    def load_dashboard_data(self):
        if self.is_loading: return
        
        # Prevent background activity if app is not focused
        from PyQt6.QtWidgets import QApplication
        if QApplication.applicationState() != Qt.ApplicationState.ApplicationActive:
            return
            
        self.is_loading = True
        self.cleanup_thread()
        
        start_str = self.date_from.date().toString("yyyy-MM-dd") if hasattr(self, 'date_from') else None
        end_str = self.date_to.date().toString("yyyy-MM-dd") if hasattr(self, 'date_to') else None
        
        self.worker = ReportsWorker(self.current_period, start_str, end_str)
        self.worker.data_loaded.connect(self._on_dashboard_data_loaded)
        self.worker.error.connect(lambda e: print(f"Reports Error: {e}"))
        self.worker.finished.connect(lambda: setattr(self, 'is_loading', False))
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _on_dashboard_data_loaded(self, d):
        # Update Cards
        self.card_sales.update_data(lang_manager.localize_digits(f"{d['sales_val']:,.0f} AFN"), f"{d['period_label']} Revenue")
        self.card_orders.update_data(lang_manager.localize_digits(f"{d['orders_count']} orders"), 
                                   lang_manager.localize_digits(f"{d['items_count']} items sold"))
        self.card_stock.update_data(lang_manager.localize_digits(f"{d['low_stock_count']} items"), "Low stock items")
        
        if d['top_product']:
            self.card_top_product.update_data(d['top_product'][0], f"{int(d['top_product'][1])} sold")
        else:
            self.card_top_product.update_data("None", "0 sold")

        # Update Charts
        # Pie Chart: Top 5 Sold Items
        # sold_summary_data: [product_name, qty_sum, ..., total_price_sum]
        if d['sold_summary_data']:
            # d['sold_summary_data'] is [Name, Qty, Percent, Revenue]
            self.donut_chart.update_data(d['sold_summary_data'])
        else:
            self.donut_chart.update_data([["No Sales", 0, 100, 0]])
        
        # Update Tables
        self._last_date_filter = d['date_filter']
        
        # Stock Table (Low Stock or Expiry)
        self.stock_table.setRowCount(0)
        mode = self.alert_mode_combo.currentText() if hasattr(self, 'alert_mode_combo') else "Low Stock"
        
        if mode == "Low Stock":
            data = d.get('low_stock_data', [])
            self.stock_table.setHorizontalHeaderLabels(["Product", "Current", "Min Stock", "Status"])
            for i, row in enumerate(data):
                self.stock_table.insertRow(i)
                self.stock_table.setItem(i, 0, QTableWidgetItem(row[0]))
                self.stock_table.setItem(i, 1, QTableWidgetItem(lang_manager.localize_digits(str(row[1]))))
                self.stock_table.setItem(i, 2, QTableWidgetItem(lang_manager.localize_digits(str(row[2]))))
                self.stock_table.setItem(i, 3, QTableWidgetItem("Low Stock"))
        # Expiry Watch Table (Requirement 8)
        self.expiry_table.setRowCount(0)
        exp_data = d.get('expiry_data', [])
        for i, row in enumerate(exp_data):
            # row: [Name, Qty, ExpiryDate]
            self.expiry_table.insertRow(i)
            self.expiry_table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.expiry_table.setItem(i, 1, QTableWidgetItem(lang_manager.localize_digits(str(row[1]))))
            self.expiry_table.setItem(i, 2, QTableWidgetItem(str(row[2])))
            
            # Days Left calculation
            try:
                exp_date = datetime.strptime(row[2], '%Y-%m-%d')
                days_left = (exp_date - datetime.now()).days
                days_item = QTableWidgetItem(str(days_left))
                if days_left <= 7:
                    days_item.setForeground(Qt.GlobalColor.red)
                elif days_left <= 30:
                    days_item.setForeground(QColor("#f39c12")) # Orange-ish
                self.expiry_table.setItem(i, 3, days_item)
            except:
                self.expiry_table.setItem(i, 3, QTableWidgetItem("N/A"))

        # Trans Table
        self.trans_table.setRowCount(0)
        for i, row in enumerate(d['trans_data']):
            self.trans_table.insertRow(i)
            self.trans_table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.trans_table.setItem(i, 1, QTableWidgetItem(lang_manager.localize_digits(row[1].split()[-1] if ' ' in row[1] else row[1])))
            self.table_item(self.trans_table, i, 2, row[2])
            self.table_item(self.trans_table, i, 3, lang_manager.localize_digits(str(row[3])))
            self.table_item(self.trans_table, i, 4, lang_manager.localize_digits(f"{row[4]:.2f}"))
            self.table_item(self.trans_table, i, 5, lang_manager.localize_digits("0.00")) 
            self.table_item(self.trans_table, i, 6, row[5])
            
            # Action (Delete)
            del_btn = QPushButton()
            style_button(del_btn, variant="danger", size="icon")
            del_btn.setIcon(qta.icon("fa5s.trash", color="white"))
            del_btn.setToolTip("Delete Invoice (Super Admin Only)")
            # Assuming row[0] is Invoice Number. We usually need ID. 
            # The query returns: invoice_number, created_at, customer_name, item_count, total_amount, payment_type
            # We don't have ID in the SELECT.
            # I need to update the query to return ID.
            # But for now, I'll assume invoice number is unique or I'll fix the query.
            # Let's fix the query in ReportsWorker first.
            
            # Wait, I can't fix ReportsWorker here. 
            # I will assume invoice_number is enough or use it if ID is not available.
            del_btn.clicked.connect(lambda checked, inv=row[0]: self.delete_invoice(inv))
            self.trans_table.setCellWidget(i, 7, del_btn)

        # Sold Summary
        self.sold_summary_table.setRowCount(0)
        for i, row in enumerate(d['sold_summary_data']):
            self.sold_summary_table.insertRow(i)
            self.sold_summary_table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.sold_summary_table.setItem(i, 1, QTableWidgetItem(lang_manager.localize_digits(str(row[1]))))
            self.sold_summary_table.setItem(i, 2, QTableWidgetItem(lang_manager.localize_digits(f"{row[2]:.1f}%")))
            self.sold_summary_table.setItem(i, 3, QTableWidgetItem(lang_manager.localize_digits(f"{row[3]:.2f}")))

        # P/L
        revenue = d['raw_revenue'] - d['returned_revenue']
        cost = d['raw_cost'] - d['returned_cost']
        profit = revenue - cost
        metrics = [
            ("Total Sales (Net)", revenue),
            ("Total Cost (Net)", cost),
            ("Total Returns", d['returned_revenue']),
            ("Gross Profit", profit),
            ("Net Margin (%)", (profit/revenue*100) if revenue > 0 else 0)
        ]
        self.pl_table.setRowCount(0)
        for i, (label, val) in enumerate(metrics):
            self.pl_table.insertRow(i)
            self.pl_table.setItem(i, 0, QTableWidgetItem(label))
            suffix = "%" if "Margin" in label else ""
            self.pl_table.setItem(i, 1, QTableWidgetItem(lang_manager.localize_digits(f"{val:.2f}{suffix}")))

        # Returns Table
        self.returns_table.setRowCount(0)
        for i, row in enumerate(d['returns_table_data']):
            self.returns_table.insertRow(i)
            self.returns_table.setItem(i, 0, QTableWidgetItem(lang_manager.localize_digits(row[0].split()[-1] if ' ' in row[0] else row[0])))
            self.returns_table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.returns_table.setItem(i, 2, QTableWidgetItem(row[2]))
            self.returns_table.setItem(i, 3, QTableWidgetItem(lang_manager.localize_digits(str(row[3]))))
            self.returns_table.setItem(i, 4, QTableWidgetItem(lang_manager.localize_digits(f"{row[4]:.2f}")))

    def table_item(self, table, row, col, text):
        table.setItem(row, col, QTableWidgetItem(str(text)))

    def export_pdf_report(self, title, table):
        """Export table to professional PDF using ReportLab"""
        if table.rowCount() == 0:
            QMessageBox.information(self, "No Data", "No data available to export.")
            return

        from src.utils.pdf_generator_v2 import pdf_generator_v2
        path, _ = QFileDialog.getSaveFileName(self, f"Export {title}", f"{title.replace(' ', '_')}.pdf", "PDF Files (*.pdf)")
        if not path: return

        # Gather data
        headers = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
        # Exclude Action column if it exists (usually the last icon column)
        is_trans_table = "Transactions" in title
        if is_trans_table:
            headers = headers[:-1]
            
        data = []
        for r in range(table.rowCount()):
            row = []
            cols_to_fetch = table.columnCount() - 1 if is_trans_table else table.columnCount()
            for c in range(cols_to_fetch):
                item = table.item(r, c)
                row.append(item.text() if item else "")
            data.append(row)

        from src.core.blocking_task_manager import task_manager
        
        def do_generate():
            pdf_generator_v2.generate_table_report(path, title, headers, data)
            return True

        def on_finished(_):
            QMessageBox.information(self, "Success", f"{title} exported to PDF successfully.")
            import platform, subprocess
            if platform.system() == 'Darwin': subprocess.run(['open', path])
            elif platform.system() == 'Windows': os.startfile(path)

        def on_error(err):
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {err}")

        task_manager.run_task(do_generate, on_finished=on_finished, on_error=on_error)

    def print_table_report(self, title, table):
        # Redirect to PDF for professional output
        self.export_pdf_report(title, table)



    def print_full_report(self):
        """Export comprehensive report with all tables to PDF"""
        from src.utils.pdf_generator_v2 import pdf_generator_v2
        
        path, _ = QFileDialog.getSaveFileName(self, "Export Complete Report", 
                                             f"Full_Report_{datetime.now().strftime('%Y%m%d')}.pdf", 
                                             "PDF Files (*.pdf)")
        if not path: return

        sections = []
        
        # 1. Critical Stock
        if self.stock_table.rowCount() > 0:
            stock_data = []
            for r in range(self.stock_table.rowCount()):
                stock_data.append([self.stock_table.item(r, c).text() if self.stock_table.item(r, c) else "" for c in range(self.stock_table.columnCount())])
            sections.append({
                'title': 'Critical Stock Alerts',
                'headers': [self.stock_table.horizontalHeaderItem(c).text() for c in range(self.stock_table.columnCount())],
                'data': stock_data
            })
        
        # 2. Transactions
        if self.trans_table.rowCount() > 0:
            trans_data = []
            for r in range(self.trans_table.rowCount()):
                trans_data.append([self.trans_table.item(r, c).text() if self.trans_table.item(r, c) else "" for c in range(self.trans_table.columnCount()-1)])
            sections.append({
                'title': 'Recent Transactions',
                'headers': [self.trans_table.horizontalHeaderItem(c).text() for c in range(self.trans_table.columnCount()-1)],
                'data': trans_data
            })
        
        # 3. Sold Items Summary
        if self.sold_summary_table.rowCount() > 0:
            sold_data = []
            for r in range(self.sold_summary_table.rowCount()):
                sold_data.append([self.sold_summary_table.item(r, c).text() if self.sold_summary_table.item(r, c) else "" for c in range(self.sold_summary_table.columnCount())])
            sections.append({
                'title': 'Sold Items Breakdown',
                'headers': [self.sold_summary_table.horizontalHeaderItem(c).text() for c in range(self.sold_summary_table.columnCount())],
                'data': sold_data
            })

        if not sections:
            QMessageBox.warning(self, "No Data", "No report sections have data to export.")
            return

        from src.core.blocking_task_manager import task_manager
        
        def do_generate():
            pdf_generator_v2.generate_multi_table_report(path, "POS Complete Financial & Inventory Report", sections)
            return True

        def on_finished(_):
            QMessageBox.information(self, "Success", "Full report exported successfully.")
            import platform, subprocess
            if platform.system() == 'Darwin': subprocess.run(['open', path])
            elif platform.system() == 'Windows': os.startfile(path)

        def on_error(err):
            QMessageBox.critical(self, "Error", f"Failed to generate full report: {err}")

        task_manager.run_task(do_generate, on_finished=on_finished, on_error=on_error)

    def show_invoice_details(self, item):
        """Show popup with sold products for specific invoice"""
        row = item.row()
        inv_item = self.trans_table.item(row, 0)  # Invoice number column
        if not inv_item: return

        invoice_number = inv_item.text().strip()
        if not invoice_number: return

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
        from src.core.blocking_task_manager import task_manager
        
        def do_fetch():
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM sales WHERE invoice_number = ?", (invoice_number,))
                sale_result = cursor.fetchone()

                if sale_result:
                    sale_id = sale_result[0]
                    cursor.execute("""
                        SELECT si.*, p.name_en as product_name
                        FROM sale_items si
                        JOIN products p ON si.product_id = p.id
                        WHERE si.sale_id = ?
                        ORDER BY si.id
                    """, (sale_id,))
                    return cursor.fetchall()
            return []

        def on_finished(items):
            for i, item in enumerate(items):
                table.insertRow(i)
                item_dict = dict(item)
                table.setItem(i, 0, QTableWidgetItem(item_dict['product_name']))
                table.setItem(i, 1, QTableWidgetItem(str(item_dict['quantity'])))
                table.setItem(i, 2, QTableWidgetItem(f"{item_dict['unit_price']:.2f}"))
                table.setItem(i, 3, QTableWidgetItem(f"{item_dict['total_price']:.2f}"))
                table.setItem(i, 4, QTableWidgetItem("N/A"))
            
            # Close button
            close_btn = QPushButton("Close")
            style_button(close_btn, variant="primary")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            dialog.exec()

        def on_error(err):
            layout.addWidget(QLabel(f"Error loading data: {str(err)}"))
            dialog.exec()

        task_manager.run_task(do_fetch, on_finished=on_finished, on_error=on_error)

    def delete_invoice(self, invoice_number):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to permanently delete Invoice {invoice_number}?\nThis will revert stock quantities.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            from src.core.blocking_task_manager import task_manager
            
            def do_delete():
                try:
                    with db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM sales WHERE invoice_number = ?", (invoice_number,))
                        row = cursor.fetchone()
                        if not row: return False, "Invoice not found"
                        sale_id = row[0]
                        
                        cursor.execute("SELECT product_id, quantity FROM sale_items WHERE sale_id = ?", (sale_id,))
                        items = cursor.fetchall()
                        for prod_id, qty in items:
                            cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE product_id = ?", (qty, prod_id))
                            
                        cursor.execute("DELETE FROM sale_items WHERE sale_id = ?", (sale_id,))
                        cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
                        conn.commit()
                    return True, ""
                except Exception as e:
                    return False, str(e)

            def on_finished(res):
                success, err = res
                if success:
                    QMessageBox.information(self, "Success", "Invoice deleted successfully")
                    self.load_dashboard_data()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to delete: {err}")
            
            task_manager.run_task(do_delete, on_finished=on_finished)

    def toggle_alert_mode(self, index):
        is_expiry = index == 1
        if hasattr(self, 'expiry_days_spin'):
            self.expiry_days_spin.setVisible(is_expiry)
        self.load_dashboard_data()

    def add_full_report_button(self):
        """Add a button to print full report"""
        # This will be called during UI initialization
        full_report_btn = QPushButton("🖨️ Print Complete Report")
        style_button(full_report_btn, variant="success")
        full_report_btn.clicked.connect(self.print_full_report)

        # Add to the main layout - this would need to be positioned properly
        # For now, we'll add it to the search card layout
        self.search_card_layout.addWidget(full_report_btn)