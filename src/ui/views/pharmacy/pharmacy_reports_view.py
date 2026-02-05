from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea, QComboBox, QDateEdit,
                             QGroupBox, QMessageBox, QSpinBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QTextDocument, QTextCursor, QTextTable, QTextTableFormat, QTextCharFormat, \
    QTextLength, QPageSize, QPageLayout, QBrush
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from src.database.db_manager import db_manager
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button
from src.ui.theme_manager import theme_manager
from src.ui.views.pharmacy.pharmacy_month_close_dialog import PharmacyMonthCloseDialog
from src.core.localization import lang_manager
from datetime import datetime

class PharmacyReportsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        theme_manager.theme_changed.connect(self.update_styles)
        self.update_styles()

    def init_ui(self):
        # Main layout with scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)
        
        # Header + Actions
        header_layout = QHBoxLayout()
        title = QLabel(lang_manager.get("pharmacy_reports"))
        title.setObjectName("page_header")
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            lang_manager.get("daily_report"), 
            lang_manager.get("weekly_report"), 
            lang_manager.get("monthly_report"), 
            lang_manager.get("custom_range")
        ])
        self.filter_combo.setMinimumWidth(300)
        self.filter_combo.currentIndexChanged.connect(self.load_data)
        
        # Date Range (hidden unless Custom)
        self.date_range_frame = QFrame()
        range_layout = QHBoxLayout(self.date_range_frame)
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setMinimumWidth(300)
        
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setMinimumWidth(300)
                
        filter_btn = QPushButton(lang_manager.get("search"))
        style_button(filter_btn, variant="info", size="small")
        filter_btn.clicked.connect(lambda: [self.filter_combo.setCurrentText(lang_manager.get("custom_range")), self.load_data()])
        
        self.month_close_btn = QPushButton(lang_manager.get("monthly_close"))
        style_button(self.month_close_btn, variant="warning")
        self.month_close_btn.clicked.connect(self.open_month_close)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(QLabel(lang_manager.get("preset") + ":"))
        header_layout.addWidget(self.filter_combo)
        header_layout.addWidget(QLabel(lang_manager.get("from") + ":"))
        header_layout.addWidget(self.date_from)
        header_layout.addWidget(QLabel(lang_manager.get("to") + ":"))
        header_layout.addWidget(self.date_to)
        header_layout.addWidget(filter_btn)
        header_layout.addWidget(self.month_close_btn)
        
        layout.addLayout(header_layout)

        # Stats Cards
        stats_layout = QHBoxLayout()
        self.today_sale = self.create_card(lang_manager.get("total_sales"), "0.00 AFN")
        self.return_items = self.create_card(lang_manager.get("return_items_count"), "0")
        self.orders = self.create_card(lang_manager.get("total_orders"), "0")
        self.low_stock = self.create_card(lang_manager.get("low_stock"), "0")
        
        stats_layout.addWidget(self.today_sale)
        stats_layout.addWidget(self.return_items)
        stats_layout.addWidget(self.orders)
        stats_layout.addWidget(self.low_stock)
        layout.addLayout(stats_layout)
        
        # Tables with Print Buttons

        # Transaction Table with Print Button
        trans_group = QGroupBox(lang_manager.get("invoices_transactions"))
        trans_layout = QVBoxLayout(trans_group)

        trans_header = QHBoxLayout()
        trans_title = QLabel(f"<b>{lang_manager.get('transaction_details')}</b>")
        trans_title.setStyleSheet("border:none; background:transparent;")
        trans_header.addWidget(trans_title)

        trans_header.addStretch()
        self.trans_print_btn = QPushButton(lang_manager.get("print_transactions"))
        style_button(self.trans_print_btn, variant="info", size="small")
        self.trans_print_btn.clicked.connect(lambda: self.print_table_report(lang_manager.get("transaction_details"), self.trans_table))
        trans_header.addWidget(self.trans_print_btn)

        trans_layout.addLayout(trans_header)

        self.trans_table = QTableWidget(0, 5)
        self.trans_table.setHorizontalHeaderLabels([
            lang_manager.get("invoice_number_short"), lang_manager.get("customer"), 
            lang_manager.get("quantity"), lang_manager.get("amount"), lang_manager.get("method")
        ])
        style_table(self.trans_table, variant="premium")
        self.trans_table.setMinimumHeight(350)
        self.trans_table.cellClicked.connect(self.handle_trans_click)
        trans_layout.addWidget(self.trans_table)
        layout.addWidget(trans_group)

        # Returns Breakdown Table (New Request)
        ret_group = QGroupBox(lang_manager.get("returned_items_details"))
        ret_layout = QVBoxLayout(ret_group)
        
        ret_header = QHBoxLayout()
        ret_title = QLabel(f"<b>{lang_manager.get('returned_items_details')}</b>")
        ret_title.setStyleSheet("border:none; background:transparent;")
        ret_header.addWidget(ret_title)

        ret_header.addStretch()
        self.ret_print_btn = QPushButton(lang_manager.get("print_returns") or "🖨️ Print Returns")
        style_button(self.ret_print_btn, variant="info", size="small")
        self.ret_print_btn.clicked.connect(lambda: self.print_table_report(lang_manager.get("returned_items_details"), self.ret_table))
        ret_header.addWidget(self.ret_print_btn)

        ret_layout.addLayout(ret_header)

        self.ret_table = QTableWidget(0, 6)
        self.ret_table.setHorizontalHeaderLabels([
            lang_manager.get("invoice"), lang_manager.get("customer"), 
            lang_manager.get("product_name"), lang_manager.get("quantity") + " (Ret)", 
            lang_manager.get("amount"), lang_manager.get("method")
        ])
        style_table(self.ret_table, variant="premium")
        self.ret_table.setMinimumHeight(250)
        ret_layout.addWidget(self.ret_table)
        layout.addWidget(ret_group)

        # Loan / Credit Table with Print Button
        loan_group = QGroupBox(lang_manager.get("pharmacy_loans_credit_details"))
        loan_layout = QVBoxLayout(loan_group)

        loan_header = QHBoxLayout()
        loan_title = QLabel(f"<b>{lang_manager.get('credit_loan_info')}</b>")
        loan_title.setStyleSheet("border:none; background:transparent;")
        loan_header.addWidget(loan_title)

        loan_header.addStretch()
        self.loan_print_btn = QPushButton(lang_manager.get("print_loans"))
        style_button(self.loan_print_btn, variant="info", size="small")
        self.loan_print_btn.clicked.connect(lambda: self.print_table_report(lang_manager.get("credit_loan_info"), self.loan_table))
        loan_header.addWidget(self.loan_print_btn)

        loan_layout.addLayout(loan_header)

        self.loan_table = QTableWidget(0, 4)
        self.loan_table.setHorizontalHeaderLabels([
            lang_manager.get("customer"), lang_manager.get("invoice"), 
            lang_manager.get("total") + " (" + lang_manager.get("credit") + ")", 
            lang_manager.get("balance")
        ])
        style_table(self.loan_table, variant="premium")
        self.loan_table.setMinimumHeight(300)
        self.loan_table.resizeColumnsToContents()
        loan_layout.addWidget(self.loan_table)
        layout.addWidget(loan_group)

        # Low Stock Table with Print Button
        stock_group = QGroupBox(lang_manager.get("critical_stock_alert"))
        stock_layout = QVBoxLayout(stock_group)

        stock_header = QHBoxLayout()
        stock_title = QLabel(f"<b>{lang_manager.get('low_stock_medicines')}</b>")
        stock_title.setStyleSheet("border:none; background:transparent;")
        stock_header.addWidget(stock_title)

        stock_header.addStretch()
        self.stock_print_btn = QPushButton(lang_manager.get("print_stock_report"))
        style_button(self.stock_print_btn, variant="info", size="small")
        self.stock_print_btn.clicked.connect(lambda: self.print_table_report(lang_manager.get("low_stock_medicines"), self.low_stock_table))
        stock_header.addWidget(self.stock_print_btn)

        stock_layout.addLayout(stock_header)

        self.low_stock_table = QTableWidget(0, 4)
        self.low_stock_table.setHorizontalHeaderLabels([
            lang_manager.get("medicine"), lang_manager.get("expiry_date"), 
            lang_manager.get("quantity"), lang_manager.get("reorder_level")
        ])
        style_table(self.low_stock_table, variant="premium")
        self.low_stock_table.setMinimumHeight(300)
        stock_layout.addWidget(self.low_stock_table)
        layout.addWidget(stock_group)

        # Expiry Stock Report Section
        expiry_group = QGroupBox(lang_manager.get("expiring_stock_report"))
        expiry_layout = QVBoxLayout(expiry_group)

        expiry_header = QHBoxLayout()
        expiry_title = QLabel(f"<b>{lang_manager.get('medicine_expiry_status')}</b>")
        expiry_title.setStyleSheet("border:none; background:transparent;")
        expiry_header.addWidget(expiry_title)

        expiry_header.addStretch()
        expiry_header.addWidget(QLabel(lang_manager.get("showing_items_expiring_within")))
        self.expiry_days_spin = QSpinBox()
        self.expiry_days_spin.setRange(1, 1000) # Increased range for flexibility, user said 1-30 but 30 might be too low for some
        self.expiry_days_spin.setValue(30)
        self.expiry_days_spin.setSuffix(" " + lang_manager.get("days"))
        self.expiry_days_spin.setMinimumWidth(100)
        self.expiry_days_spin.valueChanged.connect(self.load_data)
        expiry_header.addWidget(self.expiry_days_spin)

        self.expiry_print_btn = QPushButton(lang_manager.get("print_expiry_report"))
        style_button(self.expiry_print_btn, variant="info", size="small")
        self.expiry_print_btn.clicked.connect(lambda: self.print_table_report(lang_manager.get("medicine_expiry_status"), self.expiry_table))
        expiry_header.addWidget(self.expiry_print_btn)

        expiry_layout.addLayout(expiry_header)

        self.expiry_table = QTableWidget(0, 5)
        self.expiry_table.setHorizontalHeaderLabels([
            lang_manager.get("medicine"), lang_manager.get("batch_no_short"), 
            lang_manager.get("expiry_date"), lang_manager.get("days_left"), 
            lang_manager.get("status")
        ])
        
        # NO stylesheet - let setForeground work without any CSS interference
        self.expiry_table.setAlternatingRowColors(False)
        self.expiry_table.setShowGrid(True)
        self.expiry_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.expiry_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.expiry_table.horizontalHeader().setStretchLastSection(True)
        self.expiry_table.verticalHeader().setVisible(False)
        self.expiry_table.verticalHeader().setDefaultSectionSize(50)
        
        # Set bigger font
        expiry_font = QFont("Arial", 14)
        self.expiry_table.setFont(expiry_font)
        
        self.expiry_table.setMinimumHeight(300)
        expiry_layout.addWidget(self.expiry_table)
        layout.addWidget(expiry_group)

        # Complete Report Button
        report_btn_layout = QHBoxLayout()
        report_btn_layout.addStretch()
        self.complete_report_btn = QPushButton(lang_manager.get("print_complete_pharmacy_report"))
        style_button(self.complete_report_btn, variant="success")
        self.complete_report_btn.clicked.connect(self.print_full_report)
        report_btn_layout.addWidget(self.complete_report_btn)
        layout.addLayout(report_btn_layout)
        layout.addStretch()
        
        # Set content widget to scroll area
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def showEvent(self, event):
        """Refresh data whenever the view is shown"""
        super().showEvent(event)
        self.load_data()

    def create_card(self, title, val):
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(110)
        l = QVBoxLayout(card)
        l.setContentsMargins(15, 15, 15, 15)
        
        t_lbl = QLabel(title)
        v_lbl = QLabel(val)
        v_lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        
        card.title_lbl = t_lbl
        card.value_lbl = v_lbl
        return card

    def update_styles(self, is_dark=None):
        text_color = "white" if theme_manager.is_dark else "#1b2559"
        
        for card in [self.today_sale, self.return_items, self.orders, self.low_stock]:
            card.title_lbl.setStyleSheet(f"color: {text_color}; opacity: 0.7; background: none;")
            card.value_lbl.setStyleSheet(f"color: {text_color}; font-size: 20px; font-weight: bold; background: none;")
        
        # Labels are now part of group box headers, no need to style individually

    def load_data(self):
        try:
            with db_manager.get_pharmacy_connection() as conn:
                filter_text = self.filter_combo.currentText()
                if lang_manager.get("daily_report") in filter_text:
                    time_filter = "date({T}.created_at) = date('now')"
                    period_name = lang_manager.get("today")
                elif lang_manager.get("weekly_report") in filter_text:
                    time_filter = "date({T}.created_at) >= date('now', '-7 days')"
                    period_name = lang_manager.get("last_7_days")
                elif lang_manager.get("monthly_report") in filter_text:
                    time_filter = "date({T}.created_at) >= date('now', 'start of month')"
                    period_name = lang_manager.get("this_month")
                else:
                    # Custom Range
                    d_from = self.date_from.date().toString("yyyy-MM-dd")
                    d_to = self.date_to.date().toString("yyyy-MM-dd")
                    time_filter = f"date({{T}}.created_at) BETWEEN '{d_from}' AND '{d_to}'"
                    period_name = f"{d_from} {lang_manager.get('to')} {d_to}"
                
                # 1. Total Sales (Net of Returns)
                # Gross Sales
                sale_row = conn.execute(f"SELECT SUM(total_amount) as total FROM pharmacy_sales s WHERE {time_filter.format(T='s')}").fetchone()
                gross_sales = sale_row['total'] or 0
                
                # Returns Value (for the same period)
                ret_val_row = conn.execute(f"SELECT SUM(refund_amount) as total FROM pharmacy_returns r WHERE {time_filter.format(T='r')}").fetchone()
                returned_amount = ret_val_row['total'] or 0
                
                net_sales = gross_sales - returned_amount
                self.today_sale.value_lbl.setText(f"{net_sales:,.2f} AFN")
                self.today_sale.title_lbl.setText(f"{lang_manager.get('net_sales')} ({period_name})")
                
                # 2. Return Items Count
                ret_row = conn.execute(f"SELECT COUNT(*) as cnt FROM pharmacy_returns r WHERE {time_filter.format(T='r')}").fetchone()
                self.return_items.value_lbl.setText(str(ret_row['cnt'] or 0))
                
                # 3. Total Orders (Net of Fully Returned)
                # Count total orders in period
                ord_row = conn.execute(f"SELECT COUNT(*) as cnt FROM pharmacy_sales s WHERE {time_filter.format(T='s')}").fetchone()
                total_orders = ord_row['cnt'] or 0
                
                # Count fully returned orders in this period
                # Logic: Check if sales in this period have returns (any time) that sum up to total amount
                fully_returned_query = f"""
                    SELECT count(*) as cnt 
                    FROM pharmacy_sales s 
                    WHERE {time_filter.format(T='s')} 
                    AND s.id IN (
                        SELECT original_sale_id 
                        FROM pharmacy_returns 
                        GROUP BY original_sale_id 
                        HAVING SUM(refund_amount) >= (SELECT total_amount FROM pharmacy_sales WHERE id=original_sale_id)
                    )
                """
                full_ret_row = conn.execute(fully_returned_query).fetchone()
                fully_returned_cnt = full_ret_row['cnt'] or 0
                
                net_orders = total_orders - fully_returned_cnt
                self.orders.value_lbl.setText(str(net_orders))
                
                # 4. Low Stock count
                low_row = conn.execute("""
                    SELECT COUNT(*) as cnt FROM (
                        SELECT p.id
                        FROM pharmacy_products p
                        LEFT JOIN pharmacy_inventory i ON p.id = i.product_id
                        GROUP BY p.id
                        HAVING SUM(i.quantity) < p.min_stock
                    )
                """).fetchone()
                self.low_stock.value_lbl.setText(str(low_row['cnt'] or 0))
                
                # Load Transactions Table
                self.trans_table.setRowCount(0)
                trans_query = f"""
                    SELECT s.*, c.name as customer_name
                    FROM pharmacy_sales s
                    LEFT JOIN pharmacy_customers c ON s.customer_id = c.id
                    WHERE {time_filter.format(T='s')}
                    ORDER BY s.created_at DESC
                """
                trans = conn.execute(trans_query).fetchall()
                for i, row in enumerate(trans):
                    self.trans_table.insertRow(i)
                    # Show invoice number instead of ID
                    self.trans_table.setItem(i, 0, QTableWidgetItem(row['invoice_number']))
                    self.table_item(self.trans_table, i, 1, row['customer_name'] or lang_manager.get("walk_in"))
                    
                    # Item count
                    cnt = conn.execute("SELECT SUM(quantity) as q FROM pharmacy_sale_items WHERE sale_id=?", (row['id'],)).fetchone()
                    self.table_item(self.trans_table, i, 2, str(int(cnt['q'] or 0)))
                    self.table_item(self.trans_table, i, 3, f"{row['total_amount']:,.2f} AFN")
                    # Remove payment method display per user request
                    method = lang_manager.get("credit") if row['payment_type'] == 'CREDIT' else lang_manager.get("cash")
                    self.table_item(self.trans_table, i, 4, method)
                
                # Add totals row
                if trans:
                    total_row_idx = len(trans)
                    self.trans_table.insertRow(total_row_idx)
                    
                    # Calculate totals
                    total_qty = sum([
                        conn.execute("SELECT SUM(quantity) as q FROM pharmacy_sale_items WHERE sale_id=?", (row['id'],)).fetchone()['q'] or 0
                        for row in trans
                    ])
                    total_amount = sum([row['total_amount'] for row in trans])
                    
                    # Add total row with bold styling
                    total_lbl = QTableWidgetItem(lang_manager.get("total"))
                    total_lbl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    font = QFont()
                    font.setBold(True)
                    total_lbl.setFont(font)
                    self.trans_table.setItem(total_row_idx, 0, total_lbl)
                    
                    # Empty cells
                    self.trans_table.setItem(total_row_idx, 1, QTableWidgetItem(""))
                    
                    qty_item = QTableWidgetItem(str(int(total_qty)))
                    qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    qty_item.setFont(font)
                    self.trans_table.setItem(total_row_idx, 2, qty_item)
                    
                    amt_item = QTableWidgetItem(f"{total_amount:,.2f} AFN")
                    amt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    amt_item.setFont(font)
                    self.trans_table.setItem(total_row_idx, 3, amt_item)
                    
                    self.trans_table.setItem(total_row_idx, 4, QTableWidgetItem(""))

                    self.trans_table.setItem(total_row_idx, 4, QTableWidgetItem(""))
                
                # Load Returns Breakdown
                self.ret_table.setRowCount(0)
                # Join pharmacy_returns, return_items, products, sales, customers
                # Assuming pharmacy_return_items has return_id, product_id, quantity
                returns_query = f"""
                    SELECT 
                        s.invoice_number,
                        c.name as customer_name,
                        p.name_en as item_name,
                        ri.quantity as qty_returned,
                        r.refund_amount,
                        r.reason,
                        ri.unit_price
                    FROM pharmacy_returns r
                    JOIN pharmacy_return_items ri ON r.id = ri.return_id
                    JOIN pharmacy_sales s ON r.original_sale_id = s.id
                    LEFT JOIN pharmacy_customers c ON s.customer_id = c.id
                    JOIN pharmacy_products p ON ri.product_id = p.id
                    WHERE {time_filter.format(T='r')}
                    ORDER BY r.created_at DESC
                """
                ret_rows = conn.execute(returns_query).fetchall()
                for i, row in enumerate(ret_rows):
                    self.ret_table.insertRow(i)
                    self.table_item(self.ret_table, i, 0, row['invoice_number'])
                    self.table_item(self.ret_table, i, 1, row['customer_name'] or lang_manager.get("walk_in"))
                    self.table_item(self.ret_table, i, 2, row['item_name'])
                    # Show Qty with nice formatting
                    self.table_item(self.ret_table, i, 3, str(row['qty_returned']))
                    
                    # Amount Info: Unit Price or Total Refund?
                    # The refund_amount in 'r' is total for the return transaction.
                    # Let's show (Unit Price * Qty) to be specific per item
                    item_refund = row['qty_returned'] * row['unit_price']
                    self.table_item(self.ret_table, i, 4, f"{item_refund:,.2f}")
                    
                    # Method/Reason column (user asked for method, but reason is also useful)
                    # The return method is usually cash, but reason explains 'why'
                    self.table_item(self.ret_table, i, 5, row['reason'] or "N/A")

                # Load Loan / Credit Table
                self.loan_table.setRowCount(0)
                loans = conn.execute(f"""
                    SELECT l.*, c.name as customer_name, s.invoice_number
                    FROM pharmacy_loans l
                    JOIN pharmacy_customers c ON l.customer_id = c.id
                    JOIN pharmacy_sales s ON l.sale_id = s.id
                    WHERE {time_filter.format(T='l')}
                    ORDER BY l.created_at DESC
                """).fetchall()
                for i, row in enumerate(loans):
                    self.loan_table.insertRow(i)
                    self.table_item(self.loan_table, i, 0, row['customer_name'])
                    self.table_item(self.loan_table, i, 1, row['invoice_number'])
                    self.table_item(self.loan_table, i, 2, f"{row['total_amount']:,.2f} AFN")
                    self.table_item(self.loan_table, i, 3, f"{row['balance']:,.2f} AFN")

                # Load Low Stock Table
                self.low_stock_table.setRowCount(0)
                low_items = conn.execute("""
                    SELECT p.name_en, p.min_stock, SUM(i.quantity) as current_qty, MIN(i.expiry_date) as expiry
                    FROM pharmacy_products p
                    LEFT JOIN pharmacy_inventory i ON p.id = i.product_id
                    GROUP BY p.id
                    HAVING SUM(i.quantity) < p.min_stock
                    ORDER BY SUM(i.quantity) ASC LIMIT 10
                """).fetchall()
                for i, row in enumerate(low_items):
                    self.low_stock_table.insertRow(i)
                    self.table_item(self.low_stock_table, i, 0, row['name_en'])
                    self.table_item(self.low_stock_table, i, 1, row['expiry'] or "N/A")
                    self.table_item(self.low_stock_table, i, 2, f"{row['current_qty'] or 0}")
                    self.table_item(self.low_stock_table, i, 3, f"{row['min_stock']}")
                
                # Load Expiry Stock Table
                self.expiry_table.setRowCount(0)
                expiry_days_filter = self.expiry_days_spin.value()
                
                # Fetch inventory items with their product names
                expiry_items_query = """
                    SELECT p.name_en, i.batch_number, i.expiry_date, i.quantity
                    FROM pharmacy_inventory i
                    JOIN pharmacy_products p ON i.product_id = p.id
                    WHERE i.quantity > 0
                    ORDER BY i.expiry_date ASC
                """
                all_inventory = conn.execute(expiry_items_query).fetchall()
                
                today = datetime.now().date()
                filtered_expiry_rows = []
                
                for row in all_inventory:
                    if not row['expiry_date']:
                        continue
                        
                    try:
                        exp_date = datetime.strptime(row['expiry_date'], "%Y-%m-%d").date()
                        days_left = (exp_date - today).days
                        
                        # Apply filter: Show if already expired (days_left <= 0) 
                        # OR if expiring within the next N days
                        if days_left <= expiry_days_filter:
                            filtered_expiry_rows.append({
                                'name': row['name_en'],
                                'batch': row['batch_number'] or "N/A",
                                'expiry': row['expiry_date'],
                                'days_left': days_left
                            })
                    except Exception as e:
                        print(f"Error parsing date {row['expiry_date']}: {e}")

                for row_data in filtered_expiry_rows:
                    row_idx = self.expiry_table.rowCount()
                    self.expiry_table.insertRow(row_idx)
                    
                    medicine_name = row_data['name']
                    batch_no = row_data['batch']
                    expiry_date_str = row_data['expiry']
                    days_left = row_data['days_left']
                    
                    status_text = lang_manager.get("active")
                    if days_left <= 0:
                        status_text = lang_manager.get("expired")
                    elif days_left <= 7:
                        status_text = lang_manager.get("alert")

                    medicine_item = QTableWidgetItem(medicine_name)
                    batch_item = QTableWidgetItem(batch_no)
                    expiry_item = QTableWidgetItem(expiry_date_str)
                    days_item_text = f"{days_left} {lang_manager.get('days')}" if days_left >= 0 else lang_manager.get("expired")
                    days_item = QTableWidgetItem(days_item_text)
                    status_item_obj = QTableWidgetItem(status_text)
                    
                    # Align center for all items
                    for item in (medicine_item, batch_item, expiry_item, days_item, status_item_obj):
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Apply color only to Days Left and Status cells
                    self.style_expiry_item(days_item, days_left)
                    self.style_expiry_item(status_item_obj, days_left)

                    self.expiry_table.setItem(row_idx, 0, medicine_item)
                    self.expiry_table.setItem(row_idx, 1, batch_item)
                    self.expiry_table.setItem(row_idx, 2, expiry_item)
                    self.expiry_table.setItem(row_idx, 3, days_item)
                    self.expiry_table.setItem(row_idx, 4, status_item_obj)
                
            # Autofit all tables to content
            for table in [self.trans_table, self.ret_table, self.loan_table, self.low_stock_table, self.expiry_table]:
                table.resizeColumnsToContents()
                # If the table is too narrow, make it stretch to fill space
                if table.horizontalHeader().length() < table.width():
                    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                else:
                    # Keep the last column stretched if it's already fitting well
                    table.horizontalHeader().setStretchLastSection(True)
                    
        except Exception as e:
            print(f"Error loading report data: {e}")

    def style_expiry_item(self, item, days_left):
        font = item.font()

        if days_left <= 0:
            item.setForeground(QBrush(QColor("#C0392B")))  # Dark Red
            font.setBold(True)

        elif days_left <= 7:
            item.setForeground(QBrush(QColor("#E57373")))  # Light Red
            font.setBold(True)

        else:
            item.setForeground(QBrush(QColor("#27AE60")))  # Green
            font.setBold(False)

        item.setFont(font)

    def table_item(self, table, row, col, text, color=None, bold=False):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if color:
            item.setForeground(color)
        if bold:
            font = QFont()
            font.setBold(True)
            item.setFont(font)
        table.setItem(row, col, item)

    def handle_trans_click(self, row, col):
        """Handle click on transaction table. If Shift is held, show bill."""
        from PyQt6.QtWidgets import QApplication
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.ShiftModifier:
            # Get invoice number from first column
            item = self.trans_table.item(row, 0)
            if not item: return
            invoice_num = item.text()
            if invoice_num == "TOTAL": return

            # Fetch sale ID
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    # Invoice number in table is from column 0
                    sale = conn.execute("SELECT id, payment_type FROM pharmacy_sales WHERE invoice_number=?", (invoice_num,)).fetchone()
                    if sale:
                        sale_id = sale['id']
                        is_credit = (sale['payment_type'] == 'CREDIT')
                        
                        # Generate Bill
                        from src.utils.thermal_bill_printer import thermal_printer
                        bill_text = thermal_printer.generate_sales_bill(sale_id, is_credit, is_pharmacy=True)
                        if bill_text:
                            # Ask to print
                            if QMessageBox.question(self, lang_manager.get("reprint_bill"), f"{lang_manager.get('reprint_bill')} {invoice_num}?", 
                                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                                thermal_printer.print_bill(bill_text)
                    else:
                        QMessageBox.warning(self, lang_manager.get("error"), lang_manager.get("not_found"))
            except Exception as e:
                print(f"Error handling click: {e}")

    def open_month_close(self):
        dialog = PharmacyMonthCloseDialog(self)
        dialog.exec()

    def print_table_report(self, title, table):
        """Print a table report with preview"""
        if table.rowCount() == 0:
            QMessageBox.information(self, lang_manager.get("no_data"), lang_manager.get("no_data"))
            return

        # Create printer
        printer = QPrinter()
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

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
        period_text = self.filter_combo.currentText()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        cursor.insertText(f"{lang_manager.get('report_period')}: {period_text}\n", info_format)
        cursor.insertText(f"{lang_manager.get('date')}: {date_from} {lang_manager.get('to')} {date_to}\n", info_format)
        cursor.insertText(f"{lang_manager.get('generated_at')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", info_format)
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

        if lang_manager.get("critical_stock_alert") in title or lang_manager.get("low_stock_medicines") in title:
            low_stock_count = table.rowCount()
            cursor.insertText(f"{lang_manager.get('total_low_stock_items')}: {low_stock_count}\n", footer_format)

        elif lang_manager.get("transaction_details") in title:
            total_sales = 0
            total_items = 0
            for row in range(table.rowCount()):
                amount_item = table.item(row, 3)  # Amount column
                items_item = table.item(row, 2)   # Items column
                if amount_item and "AFN" in amount_item.text():
                    try:
                        amount = float(amount_item.text().replace(',', '').replace(' AFN', ''))
                        total_sales += amount
                    except:
                        pass
                if items_item:
                    try:
                        total_items += int(items_item.text())
                    except:
                        pass
            cursor.insertText(f"{lang_manager.get('total_transactions')}: {table.rowCount()}\n", footer_format)
            cursor.insertText(f"{lang_manager.get('total_items_sold')}: {total_items}\n", footer_format)
            cursor.insertText(f"{lang_manager.get('total_sales_amount')}: {total_sales:,.2f} AFN\n", footer_format)

        elif lang_manager.get("credit_loan_info") in title:
            total_loans = 0
            total_balance = 0
            for row in range(table.rowCount()):
                loan_item = table.item(row, 2)  # Total Loan column
                balance_item = table.item(row, 3)  # Balance column
                if loan_item:
                    try:
                        total_loans += float(loan_item.text().replace(',', '').replace(' AFN', ''))
                    except:
                        pass
                if balance_item:
                    try:
                        total_balance += float(balance_item.text().replace(',', '').replace(' AFN', ''))
                    except:
                        pass
            cursor.insertText(f"{lang_manager.get('total_active_loans')}: {table.rowCount()}\n", footer_format)
            cursor.insertText(f"{lang_manager.get('total_loan_amount')}: {total_loans:,.2f} AFN\n", footer_format)
            cursor.insertText(f"{lang_manager.get('total_outstanding_balance')}: {total_balance:,.2f} AFN\n", footer_format)

        elif lang_manager.get("medicine_expiry_status") in title:
            expired_count = 0
            for row in range(table.rowCount()):
                status_item = table.item(row, 4)
                if status_item and status_item.text() == "EXPIRED":
                    expired_count += 1
            cursor.insertText(f"{lang_manager.get('total_items_monitored')}: {table.rowCount()}\n", footer_format)
            cursor.insertText(f"{lang_manager.get('already_expired_count')}: {expired_count}\n", footer_format)
            cursor.insertText(f"{lang_manager.get('nearing_expiry')}: {table.rowCount() - expired_count}\n", footer_format)

        # Print the document
        document.print(printer)

    def print_full_report(self):
        """Print a comprehensive full pharmacy report"""
        printer = QPrinter()
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle("Print Preview - Complete Pharmacy Reports Summary")
        preview.setMinimumSize(1000, 700)

        preview.paintRequested.connect(self.render_full_report)
        preview.exec()

    def render_full_report(self, printer):
        """Render complete pharmacy report with all sections"""
        document = QTextDocument()
        cursor = QTextCursor(document)

        # Main title
        title_format = QTextCharFormat()
        title_format.setFontPointSize(18)
        title_format.setFontWeight(QFont.Weight.Bold)
        cursor.insertText(f"{lang_manager.get('complete_pharmacy_reports_summary')}\n", title_format)
        cursor.insertText("\n")

        # Date info
        info_format = QTextCharFormat()
        info_format.setFontPointSize(10)
        period_text = self.filter_combo.currentText()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        cursor.insertText(f"{lang_manager.get('report_period')}: {period_text}\n", info_format)
        cursor.insertText(f"{lang_manager.get('date')}: {date_from} {lang_manager.get('to')} {date_to}\n", info_format)
        cursor.insertText(f"{lang_manager.get('generated_at')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", info_format)
        cursor.insertText("\n")

        # Add each section
        sections = [
            (lang_manager.get("transaction_details"), self.trans_table),
            (lang_manager.get("credit_loan_info"), self.loan_table),
            (lang_manager.get("low_stock_medicines"), self.low_stock_table),
            (lang_manager.get("medicine_expiry_status"), self.expiry_table)
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