import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
                             QComboBox, QPushButton, QScrollArea, QGridLayout, 
                             QLineEdit, QDateEdit, QMessageBox, QGroupBox, QTabWidget, QDialog, QFormLayout, QFileDialog)
from PyQt6.QtCore import Qt, QDate, QRect
from PyQt6.QtGui import QColor, QFont, QTextDocument, QTextCursor, QTextTableFormat, QTextCharFormat, QTextLength, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
import sqlite3
import qtawesome as qta
import pandas as pd
from src.database.db_manager import db_manager
from src.core.localization import lang_manager
from src.core.auth import Auth
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button
from src.ui.theme_manager import theme_manager
from datetime import datetime, timedelta
from src.ui.components.stat_card import StatCard


# Removed local StatCard class to use shared src.ui.components.stat_card

class StoreFinanceView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_period = "daily"
        self._tabs_loaded = set()  # Track which tabs have been loaded
        self.init_ui()
        # DO NOT load data here - it freezes the UI!
        # Data will be loaded when user switches to each tab


    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Professional Header
        header = QFrame()
        header.setObjectName("finance_header")
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 15, 30, 15)

        title_icon = QLabel()
        title_icon.setPixmap(qta.icon("fa5s.chart-line", color="#4318ff").pixmap(32, 32))

        title_text = QLabel("Financial Management")
        title_text.setStyleSheet("font-size: 28px; font-weight: bold; color: #1b2559; margin-left: 15px;")

        header_layout.addWidget(title_icon)
        header_layout.addWidget(title_text)
        header_layout.addStretch()

        # Period selector in header
        period_label = QLabel("View Period:")
        period_label.setStyleSheet("font-size: 14px; color: #666;")
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Daily", "Weekly", "Monthly", "Custom", "Specific Day"])
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        self.period_combo.setFixedWidth(120)
        self.period_combo.setFixedHeight(35)
        
        self.header_date_from = QDateEdit()
        self.header_date_from.setCalendarPopup(True)
        self.header_date_from.setDate(QDate.currentDate())
        self.header_date_from.setFixedWidth(120)
        self.header_date_from.hide()
        
        self.header_date_to = QDateEdit()
        self.header_date_to.setCalendarPopup(True)
        self.header_date_to.setDate(QDate.currentDate())
        self.header_date_to.setFixedWidth(120)
        self.header_date_to.hide()

        header_layout.addWidget(period_label)
        header_layout.addWidget(self.period_combo)
        header_layout.addWidget(self.header_date_from)
        header_layout.addWidget(self.header_date_to)

        layout.addWidget(header)

        # Professional Tabs with better styling
        self.tabs = QTabWidget()
        self.tabs.setObjectName("finance_tabs")
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e5f2;
                background: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #f8f9fa;
                border: 1px solid #e0e5f2;
                padding: 12px 24px;
                margin-right: 2px;
                border-radius: 8px 8px 0 0;
                font-size: 14px;
                font-weight: 500;
                color: #666;
            }
            QTabBar::tab:selected {
                background: white;
                color: #4318ff;
                border-bottom: 3px solid #4318ff;
            }
            QTabBar::tab:hover {
                background: #e8f4fd;
                color: #4318ff;
            }
        """)

        self.tabs.addTab(self.create_expense_tab(), "📊 Expenses")
        self.tabs.addTab(self.create_payroll_tab(), "💰 Payroll")
        self.tabs.addTab(self.create_summary_tab(), "📈 Summary")
        self.tabs.addTab(self.create_reports_tab(), "📋 Reports")
        self.tabs.addTab(self.create_advance_tab(), "💸 Advances")
        
        # Connect tab change to lazy loading
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Wrap tabs in scroll area to make it scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.tabs)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        layout.addWidget(scroll_area)
    
    def _on_tab_changed(self, index):
        """Lazy load data when user switches to a tab"""
        if index in self._tabs_loaded:
            return  # Already loaded
            
        self._tabs_loaded.add(index)
        
        # Load data based on which tab was opened
        if index == 0:  # Expenses
            self.load_data()
        elif index == 1:  # Payroll
            self.load_payroll_data()
        elif index == 2:  # Summary
            self.load_summary_data()
        elif index == 3:  # Reports
            pass  # Reports load on demand via "Generate" button
        elif index == 4:  # Advances
            self.load_advances()
    
    def showEvent(self, event):
        """Load first tab data when window is first shown"""
        super().showEvent(event)
        if not self._tabs_loaded:
            # Load the currently visible tab (usually index 0)
            self._on_tab_changed(self.tabs.currentIndex())

    def create_expense_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # 1. Header & Controls
        header_layout = QHBoxLayout()
        
        title = QLabel("Financial Overview")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Daily", "Weekly", "Monthly", "All Time"])
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        self.period_combo.setFixedWidth(150)
        self.period_combo.setFixedHeight(40)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Period:"))
        header_layout.addWidget(self.period_combo)
        
        layout.addLayout(header_layout)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Expense Title (e.g. Electricity Bill)")

        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Electricity", "Gas"])
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount")
        
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Additional Description")
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        
        self.add_expense_btn = QPushButton("Add Expense")
        style_button(self.add_expense_btn, variant="danger")
        self.add_expense_btn.clicked.connect(self.add_expense)
        
        # Professional Expense Recording Section
        expense_group = QFrame()
        expense_group.setObjectName("expense_group")
        expense_group.setStyleSheet("""
            QFrame#expense_group {
                background-color: #f8f9fa;
                border-radius: 12px;
                border: 2px solid #e9ecef;
                padding: 20px;
            }
        """)

        expense_layout = QVBoxLayout(expense_group)

        # Header
        expense_header = QHBoxLayout()
        expense_icon = QLabel()
        expense_icon.setPixmap(qta.icon("fa5s.plus-circle", color="#dc3545").pixmap(24, 24))

        expense_title = QLabel("Record New Expense")
        expense_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #495057; margin-left: 10px;")

        expense_header.addWidget(expense_icon)
        expense_header.addWidget(expense_title)
        expense_header.addStretch()

        expense_layout.addLayout(expense_header)

        # Form Grid
        form_grid = QGridLayout()
        form_grid.setSpacing(15)
        form_grid.setContentsMargins(0, 20, 0, 20)

        # Row 1
        form_grid.addWidget(QLabel("Category:"), 0, 0)
        self.cat_combo.setFixedHeight(40)
        self.cat_combo.setStyleSheet("font-size: 14px; padding: 5px;")
        form_grid.addWidget(self.cat_combo, 0, 1)

        form_grid.addWidget(QLabel("Amount:"), 0, 2)
        self.amount_input.setFixedHeight(40)
        self.amount_input.setStyleSheet("font-size: 14px; padding: 5px;")
        form_grid.addWidget(self.amount_input, 0, 3)

        # Row 2
        form_grid.addWidget(QLabel("Date:"), 1, 0)
        self.date_input.setFixedHeight(40)
        self.date_input.setStyleSheet("font-size: 14px; padding: 5px;")
        form_grid.addWidget(self.date_input, 1, 1)

        form_grid.addWidget(QLabel("Description:"), 1, 2)
        self.desc_input.setFixedHeight(40)
        self.desc_input.setStyleSheet("font-size: 14px; padding: 5px;")
        form_grid.addWidget(self.desc_input, 1, 3)

        expense_layout.addLayout(form_grid)

        # Button Row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.add_expense_btn.setFixedHeight(50)
        self.add_expense_btn.setFixedWidth(200)
        self.add_expense_btn.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 20px;")
        self.add_expense_btn.setDefault(True)
        button_layout.addWidget(self.add_expense_btn)

        expense_layout.addLayout(button_layout)

        layout.addWidget(expense_group)
        
        # 3. KPI Cards
        stats_layout = QHBoxLayout()
        self.card_income = StatCard("Total Income", "0 AFN", "Monthly revenue", "fa5s.arrow-up", "#05cd99")
        self.card_expense = StatCard("Total Expenses", "0 AFN", "Operating costs", "fa5s.arrow-down", "#ee5d50")
        self.card_profit = StatCard("Net Profit", "0 AFN", "Net earnings", "fa5s.balance-scale", "#4318ff")
        
        stats_layout.addWidget(self.card_income)
        stats_layout.addWidget(self.card_expense)
        stats_layout.addWidget(self.card_profit)
        
        layout.addLayout(stats_layout)
        
        # 4. Tables
        grid_tables = QGridLayout()
        
        # Expense Log
        expense_box = QGroupBox("Expense History")
        eb_layout = QVBoxLayout(expense_box)
        self.expense_table = QTableWidget(0, 5)
        self.expense_table.setHorizontalHeaderLabels(["Date", "Category", "Amount", "User", "Description"])
        style_table(self.expense_table, variant="compact")
        self.expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        eb_layout.addWidget(self.expense_table)
        grid_tables.addWidget(expense_box, 0, 0)
        
        # Sales Summary
        sales_box = QGroupBox("Revenue Summary")
        sb_layout = QVBoxLayout(sales_box)
        self.sales_table = QTableWidget(0, 3)
        self.sales_table.setHorizontalHeaderLabels(["Date", "Sales Count", "Total Revenue"])
        style_table(self.sales_table, variant="compact")
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        sb_layout.addWidget(self.sales_table)
        grid_tables.addWidget(sales_box, 0, 1)
        
        layout.addLayout(grid_tables)
        return tab

    def create_payroll_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Professional Header
        header_layout = QHBoxLayout()

        header_icon = QLabel()
        header_icon.setPixmap(qta.icon("fa5s.users-cog", color="#4318ff").pixmap(28, 28))

        header_text = QLabel("Staff Payroll Management")
        header_text.setStyleSheet("font-size: 22px; font-weight: bold; color: #1b2559; margin-left: 12px;")

        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_text)
        header_layout.addStretch()

        # Refresh button in header
        refresh_btn = QPushButton("🔄 Refresh")
        style_button(refresh_btn, variant="info", size="small")
        refresh_btn.clicked.connect(self.load_payroll_data)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Info Card
        info_frame = QFrame()
        info_frame.setObjectName("payroll_info")
        info_frame.setStyleSheet("""
            QFrame#payroll_info {
                background-color: #e8f4fd;
                border-radius: 8px;
                border: 1px solid #90cdf4;
                padding: 15px;
            }
        """)

        info_layout = QHBoxLayout(info_frame)

        info_icon = QLabel()
        info_icon.setPixmap(qta.icon("fa5s.info-circle", color="#3182ce").pixmap(20, 20))

        info_text = QLabel("Double-click on salary amounts to edit them. Changes are saved automatically.")
        info_text.setStyleSheet("color: #2d3748; font-size: 13px; margin-left: 10px;")

        info_layout.addWidget(info_icon)
        info_layout.addWidget(info_text)
        info_layout.addStretch()

        layout.addWidget(info_frame)

        # Payroll Table with professional styling
        table_frame = QFrame()
        table_frame.setObjectName("payroll_table_frame")
        table_frame.setStyleSheet("""
            QFrame#payroll_table_frame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
            }
        """)

        table_layout = QVBoxLayout(table_frame)

        table_header = QLabel("Current Staff Salaries")
        table_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a5568; margin-bottom: 10px;")
        table_layout.addWidget(table_header)

        self.payroll_table = QTableWidget(0, 8)
        self.payroll_table.setHorizontalHeaderLabels([
            "📅 Date", "👤 Employee", "🏷️ Role", "💰 Base Salary", "📈 Adv. Taken", "💹 Net To Pay", "📊 Status", "⚙️ Actions"
        ])
        style_table(self.payroll_table, variant="premium")
        self.payroll_table.setStyleSheet(self.payroll_table.styleSheet() + "QTableWidget { font-size: 14px; }")
        self.payroll_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payroll_table.itemChanged.connect(self.on_salary_changed)

        # Set column widths
        self.payroll_table.setColumnWidth(0, 200)  # Employee
        self.payroll_table.setColumnWidth(1, 120)  # Role
        self.payroll_table.setColumnWidth(2, 150)  # Salary
        self.payroll_table.setColumnWidth(3, 100)  # Status
        self.payroll_table.setColumnWidth(4, 120)  # Actions

        table_layout.addWidget(self.payroll_table)
        layout.addWidget(table_frame)

        return tab

    # Removed local apply_theme as it's handled by ThemeManager globally

    def on_period_changed(self):
        self.current_period = self.period_combo.currentText().lower().replace(" ", "_")
        self.load_data()

    def get_date_filter(self):
        today = datetime.now()
        if self.current_period == "daily":
            start = today.strftime("%Y-%m-%d")
            return f"DATE(created_at, 'localtime') = '{start}'", f"DATE(expense_date) = '{start}'"
        elif self.current_period == "weekly":
            start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            return f"DATE(created_at, 'localtime') >= '{start}'", f"DATE(expense_date) >= '{start}'"
        elif self.current_period == "monthly":
            start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            return f"DATE(created_at, 'localtime') >= '{start}'", f"DATE(expense_date) >= '{start}'"
        else:
            return "1=1", "1=1"

    def load_data(self):
        from src.core.blocking_task_manager import task_manager
        sales_filter, expense_filter = self.get_date_filter()
        
        def fetch_finance_data():
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"SELECT SUM(total_amount) FROM sales WHERE {sales_filter}")
                total_income = cursor.fetchone()[0] or 0
                
                cursor.execute(f"SELECT SUM(amount) FROM expenses WHERE {expense_filter}")
                total_expense = cursor.fetchone()[0] or 0
                
                sales_filter_items = sales_filter.replace("created_at", "s.created_at")
                cursor.execute(f"""
                    SELECT SUM(si.quantity * p.cost_price)
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.id
                    JOIN products p ON si.product_id = p.id
                    WHERE {sales_filter_items}
                """)
                cogs = cursor.fetchone()[0] or 0
                
                gross_profit = total_income - cogs
                net_profit = gross_profit - total_expense
                
                # Fetch tables
                cursor.execute(f"""
                    SELECT e.expense_date, e.title, e.amount, e.description, u.username 
                    FROM expenses e
                    LEFT JOIN users u ON e.user_id = u.id
                    WHERE {expense_filter}
                    ORDER BY e.expense_date DESC
                """)
                expense_rows = [list(r) for r in cursor.fetchall()]

                cursor.execute(f"""
                    SELECT DATE(created_at, 'localtime') as sale_date, COUNT(*) as count, SUM(total_amount) as total
                    FROM sales 
                    WHERE {sales_filter}
                    GROUP BY sale_date
                    ORDER BY sale_date DESC
                    LIMIT 50
                """)
                sales_rows = [list(r) for r in cursor.fetchall()]

                return {
                    "total_income": total_income,
                    "total_expense": total_expense,
                    "net_profit": net_profit,
                    "expense_rows": expense_rows,
                    "sales_rows": sales_rows
                }

        def on_finished(data):
            self.card_income.update_value(lang_manager.localize_digits(f"{data['total_income']:.0f} AFN"))
            self.card_expense.update_value(lang_manager.localize_digits(f"{data['total_expense']:.0f} AFN"))
            self.card_profit.update_value(lang_manager.localize_digits(f"{data['net_profit']:.0f} AFN"))
            
            # Populate tables
            self.expense_table.setRowCount(0)
            for i, row in enumerate(data['expense_rows']):
                self.expense_table.insertRow(i)
                for j, val in enumerate(row):
                    self.expense_table.setItem(i, j, QTableWidgetItem(str(val if val is not None else "")))

            self.sales_table.setRowCount(0)
            for i, row in enumerate(data['sales_rows']):
                self.sales_table.insertRow(i)
                self.sales_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.sales_table.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.sales_table.setItem(i, 2, QTableWidgetItem(f"{row[2]:,.2f}"))

        task_manager.run_task(fetch_finance_data, on_finished=on_finished)

    def load_expense_table(self, cursor, filter_sql):
        # Deprecated: logic combined into load_data
        pass

    def load_sales_summary_table(self, cursor, filter_sql):
        # Deprecated: logic combined into load_data
        pass

    def add_expense(self):
        try:
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid Amount")
            return
            
        category = self.cat_combo.currentText()
        desc = self.desc_input.text()
        date_str = self.date_input.date().toString("yyyy-MM-dd")
        user = Auth.get_current_user()
        user_id = user['id'] if user else None
        
        from src.core.blocking_task_manager import task_manager
        
        def do_add():
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO expenses (user_id, category, amount, description, expense_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, category, amount, desc, date_str))
                conn.commit()
            return True

        def on_finished(_):
            self.add_expense_btn.setEnabled(True)
            QMessageBox.information(self, "Success", "Expense Added")
            self.amount_input.clear()
            self.desc_input.clear()
            self.load_data()

        def on_error(err):
            self.add_expense_btn.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Failed to add expense: {str(err)}")

        self.add_expense_btn.setEnabled(False)
        task_manager.run_task(do_add, on_finished=on_finished, on_error=on_error)

    # Payroll Logic
    def load_payroll_data(self):
        from src.core.blocking_task_manager import task_manager
        self.payroll_table.blockSignals(True)
        
        def fetch_payroll():
            # ALL database operations must happen here, NOT in on_finished!
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Get all users
                cursor.execute("""
                    SELECT u.id, u.username, r.name, u.base_salary, u.is_active
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    WHERE u.is_super_admin = 0
                """)
                users = [dict(u) for u in cursor.fetchall()]
                
                # 2. Get paid status for current month
                month_str = datetime.now().strftime("%Y-%m")
                cursor.execute("SELECT user_id, payment_date FROM payroll WHERE month_year=?", (month_str,))
                paid_data = {r[0]: r[1] for r in cursor.fetchall()}
                
                # 3. Get advances for each user
                user_advances = {}
                for u in users:
                    cursor.execute(
                        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id=? AND category='Advance Salary'",
                        (u['id'],)
                    )
                    user_advances[u['id']] = cursor.fetchone()[0]
                
                return {
                    'users': users,
                    'paid_data': paid_data,
                    'advances': user_advances
                }

        def on_finished(data):
            # NO database operations here - only UI updates!
            self.payroll_table.setRowCount(0)
            users = data['users']
            paid_data = data['paid_data']
            user_advances = data['advances']
                
            for i, u in enumerate(users):
                self.payroll_table.insertRow(i)
                
                # Date Column (Index 0)
                is_paid = u['id'] in paid_data
                pay_date = paid_data.get(u['id'], "-")
                self.payroll_table.setItem(i, 0, QTableWidgetItem(str(pay_date)))
                
                # Employee (Index 1)
                self.payroll_table.setItem(i, 1, QTableWidgetItem(u['username']))
                
                # Role (Index 2)
                self.payroll_table.setItem(i, 2, QTableWidgetItem(u['name']))
                
                total_adv = user_advances.get(u['id'], 0)
                
                # Base Salary (Index 3)
                salary_item = QTableWidgetItem(f"{u['base_salary']:,.2f}")
                salary_item.setData(Qt.ItemDataRole.UserRole, u['id'])
                self.payroll_table.setItem(i, 3, salary_item)
                
                # Advance Taken (Index 4)
                adv_item = QTableWidgetItem(f"{total_adv:,.2f}" if total_adv > 0 else "")
                adv_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.payroll_table.setItem(i, 4, adv_item)
                
                # Net To Pay (Index 5)
                net = max(0, u['base_salary'] - total_adv)
                net_item = QTableWidgetItem(f"{net:,.2f}")
                net_item.setForeground(QColor("#4318ff"))
                net_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                self.payroll_table.setItem(i, 5, net_item)
                
                # Status (Index 6)
                status_item = QTableWidgetItem("✅ Paid" if is_paid else "⏳ Not Paid")
                if is_paid: status_item.setForeground(QColor("#05cd99"))
                else: status_item.setForeground(QColor("#ee5d50"))
                self.payroll_table.setItem(i, 6, status_item)
                
                # Action Button (Index 7)
                btn = QPushButton(" Paid Successfully" if is_paid else " Calculate Pay")
                btn.setIcon(qta.icon("fa5s.check-circle" if is_paid else "fa5s.calculator", color="white"))
                style_button(btn, variant="secondary" if is_paid else "success", size="small")
                btn.setEnabled(not is_paid)
                btn.clicked.connect(lambda checked, uid=u['id'], name=u['username'], base=u['base_salary'], adv=total_adv: self.run_payroll_dialog(uid, name, base, adv))
                self.payroll_table.setCellWidget(i, 7, btn)
            self.payroll_table.blockSignals(False)

        task_manager.run_task(fetch_payroll, on_finished=on_finished)

    def on_salary_changed(self, item):
        if item.column() == 3:
            try:
                new_salary = float(item.text())
                user_id = item.data(Qt.ItemDataRole.UserRole)
                from src.core.blocking_task_manager import task_manager
                
                def update_salary():
                    with db_manager.get_connection() as conn:
                        conn.execute("UPDATE users SET base_salary = ? WHERE id = ?", (new_salary, user_id))
                        conn.commit()
                    return True

                task_manager.run_task(update_salary)
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid Salary Value")
                self.load_payroll_data() # Reset

    def create_advance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Advance Form
        gb = QGroupBox("Record Advance / Loan to Staff")
        form = QFormLayout(gb)
        
        self.adv_user_combo = QComboBox()
        self.load_adv_users()
        self.adv_amount = QLineEdit()
        self.adv_amount.setPlaceholderText("Amount")
        self.adv_amount.setStyleSheet("border: 1px solid #D3D3D3;")
        self.adv_reason = QLineEdit()
        self.adv_reason.setPlaceholderText("Reason")
        self.adv_reason.setStyleSheet("border: 1px solid #D3D3D3;")
        self.adv_date = QDateEdit()
        self.adv_date.setDate(QDate.currentDate())
        self.adv_date.setStyleSheet("border: 1px solid #D3D3D3;")
        self.adv_date.setCalendarPopup(True)
        
        self.save_advance_btn = QPushButton("Save Advance")
        style_button(self.save_advance_btn, variant="warning")
        self.save_advance_btn.clicked.connect(self.save_advance)
        
        form.addRow("Staff Member:", self.adv_user_combo)
        form.addRow("Amount:", self.adv_amount)
        form.addRow("Reason:", self.adv_reason)
        form.addRow("Date:", self.adv_date)
        form.addRow("", self.save_advance_btn)
        
        layout.addWidget(gb)
        
        # Advance Table
        self.adv_table = QTableWidget(0, 5)
        self.adv_table.setHorizontalHeaderLabels(["Employee", "Date", "Amount", "Reason", "Actions"])
        style_table(self.adv_table)
        self.adv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.adv_table)
        
        self.load_advances()
        return tab

    def load_adv_users(self):
        from src.core.blocking_task_manager import task_manager
        self.adv_user_combo.clear()
        self.adv_user_combo.addItem("Loading...", None)
        self.adv_user_combo.setEnabled(False)

        def fetch_all():
            try:
                with db_manager.get_connection() as conn:
                    # Load main system users (Store Staff)
                    # Filter for General Store related staff/users (Requirement 3: Advance Tab)
                    # Assuming scope="SHOP" or role-based check
                    # We'll use role_id check or just load all who are NOT pharmacy-only if possible
                    # For now, we'll assume SHOP scope exists from db_manager.py
                    main_users = [dict(u) for u in conn.execute("SELECT id, username FROM users WHERE is_active=1 AND scope='SHOP'").fetchall()]
                    main_users.sort(key=lambda x: x['username'].lower())
                    return main_users
            except Exception:
                return []

        def on_finished(all_users):
            self.adv_user_combo.clear()
            self.adv_user_combo.setEnabled(True)
            for user in all_users:
                self.adv_user_combo.addItem(user['username'], (user['id'], 'Main'))

        task_manager.run_task(fetch_all, on_finished=on_finished)

    def save_advance(self):
        user_data = self.adv_user_combo.currentData()
        if not user_data:
            QMessageBox.warning(self, "Error", "Please select a staff member")
            return

        user_id, user_source = user_data

        try:
            amt = float(self.adv_amount.text())
        except:
            QMessageBox.warning(self, "Error", "Invalid Amount")
            return

        reason = self.adv_reason.text().strip()
        if not reason:
            reason = "Advance Payment"

        date = self.adv_date.date().toString("yyyy-MM-dd")
        staff_name = self.adv_user_combo.currentText()
        
        from src.core.blocking_task_manager import task_manager

        def do_save():
            with db_manager.get_connection() as conn:
                if user_source == 'Main':
                    # Save to main expenses table
                    conn.execute("""
                        INSERT INTO expenses (user_id, category, amount, description, expense_date)
                        VALUES (?, 'Advance Salary', ?, ?, ?)
                    """, (user_id, amt, reason, date))
                else:
                    # For pharmacy users, save to pharmacy_expenses table
                    try:
                        conn.execute("""
                            INSERT INTO pharmacy_expenses (category, amount, description, expense_date)
                            VALUES ('Advance Salary', ?, ?, ?)
                        """, (amt, f"Advance to {staff_name}: {reason}", date))
                    except:
                        # Fallback to main expenses if pharmacy table doesn't exist
                        conn.execute("""
                            INSERT INTO expenses (category, amount, description, expense_date)
                            VALUES ('Advance Salary', ?, ?, ?)
                        """, (amt, f"Pharmacy: {reason}", date))

                conn.commit()
            return True

        def on_finished(_):
            self.save_advance_btn.setEnabled(True)
            QMessageBox.information(self, "Success", "Advance payment recorded successfully")
            self.load_advances()
            self.load_payroll_data()

            # Clear form
            self.adv_amount.clear()
            self.adv_reason.clear()
            self.adv_date.setDate(QDate.currentDate())

        def on_error(err):
            self.save_advance_btn.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Failed to save advance: {str(err)}")

        self.save_advance_btn.setEnabled(False)
        task_manager.run_task(do_save, on_finished=on_finished, on_error=on_error)

    def load_advances(self):
        from src.core.blocking_task_manager import task_manager
        
        def fetch_advances():
            with db_manager.get_connection() as conn:
                return conn.execute("""
                    SELECT e.*, u.username
                    FROM expenses e
                    JOIN users u ON e.user_id = u.id
                    WHERE e.category = 'Advance Salary'
                    ORDER BY e.expense_date DESC
                """).fetchall()

        def on_finished(rows):
            self.adv_table.setRowCount(0)
            for i, row in enumerate(rows):
                self.adv_table.insertRow(i)
                self.adv_table.setItem(i, 0, QTableWidgetItem(row['username']))
                self.adv_table.setItem(i, 1, QTableWidgetItem(row['expense_date']))
                self.adv_table.setItem(i, 2, QTableWidgetItem(f"{row['amount']:.2f}"))
                self.adv_table.setItem(i, 3, QTableWidgetItem(row['description']))
                
                btn = QPushButton("Del")
                style_button(btn, variant="danger", size="small")
                # Add delete logic if needed
                self.adv_table.setCellWidget(i, 4, btn)

        task_manager.run_task(fetch_advances, on_finished=on_finished)

    def run_payroll_dialog(self, user_id, username, base_salary, adv_taken=0):
        # Improved payroll dialog with advance deduction
        total_advances = adv_taken

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Run Payroll: {username}")
        layout = QFormLayout(dlg)
        
        month_label = QLabel(datetime.now().strftime("%B %Y"))
        layout.addRow("Month:", month_label)
        
        base_label = QLabel(f"{base_salary:.2f} AFN")
        layout.addRow("Base Salary:", base_label)
        
        # Advance Deduction
        adv_label = QLabel(f"{total_advances:.2f} AFN")
        layout.addRow("Total Advances to Deduct:", adv_label)
        
        total_days_input = QLineEdit("30")
        layout.addRow("Days in Month:", total_days_input)
        
        worked_days_input = QLineEdit("30")
        layout.addRow("Days Worked:", worked_days_input)
        
        calc_label = QLabel(f"{max(0, base_salary - total_advances):.2f}")
        layout.addRow("Calculated Payout (Net):", calc_label)
        
        def recalc():
            try:
                total = float(total_days_input.text())
                worked = float(worked_days_input.text())
                if total > 0:
                    gross = (base_salary / total) * worked
                    net = max(0, gross - total_advances)
                    calc_label.setText(f"{net:.2f}")
            except:
                calc_label.setText("Error")

        total_days_input.textChanged.connect(recalc)
        worked_days_input.textChanged.connect(recalc)
        
        pay_btn = QPushButton("Confirm Payment")
        style_button(pay_btn, variant="primary")
        
        def save_payment():
            try:
                amount = float(calc_label.text())
                month_str = datetime.now().strftime("%Y-%m")
                current_user = Auth.get_current_user()
                auth_id = current_user['id'] if current_user else None
                
                from src.core.blocking_task_manager import task_manager
                
                def do_save():
                    with db_manager.get_connection() as conn:
                        # Point: "Track payment history" (REQ-SUM-01)
                        # Use specialized 'payroll' table instead of 'expenses' for salary
                        conn.execute("""
                            INSERT INTO payroll (user_id, month_year, base_salary, deductions, net_paid, authorized_by)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (user_id, month_str, base_salary, total_advances, amount, auth_id))
                        conn.commit()
                    return True

                def on_finished(_):
                    pay_btn.setEnabled(True)
                    QMessageBox.information(self, "Success", f"Salary for {month_str} paid successfully.")
                    dlg.accept()
                    self.load_data()
                    self.load_payroll_data()
                    self.load_summary_data()

                def on_error(err):
                    pay_btn.setEnabled(True)
                    if "UNIQUE constraint failed" in str(err):
                        QMessageBox.warning(self, "Duplicate", f"Salary for {username} in {month_str} has already been paid.")
                    else:
                        QMessageBox.critical(self, "Error", f"Failed to save payment: {str(err)}")

                pay_btn.setEnabled(False)
                task_manager.run_task(do_save, on_finished=on_finished, on_error=on_error)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                
        pay_btn.clicked.connect(save_payment)
        layout.addRow(pay_btn)
        
        dlg.exec()

    def create_summary_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)
        
        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 1. Filters
        filter_frame = QFrame()
        filter_frame.setObjectName("filter_frame")
        filter_frame.setStyleSheet("#filter_frame { background: white; border-radius: 8px; border: 1px solid #e2e8f0; padding: 10px; }")
        
        h_filter = QHBoxLayout(filter_frame)
        h_filter.addWidget(QLabel("Date Range:"))
        
        self.sum_period_combo = QComboBox()
        self.sum_period_combo.addItems(["Daily", "Weekly", "Monthly", "Custom"])
        self.sum_period_combo.currentIndexChanged.connect(self.toggle_custom_date)
        h_filter.addWidget(self.sum_period_combo)
        
        self.sum_date_from = QDateEdit()
        self.sum_date_from.setCalendarPopup(True)
        self.sum_date_from.setDate(QDate.currentDate())
        self.sum_date_from.setEnabled(False)
        
        self.sum_date_to = QDateEdit()
        self.sum_date_to.setCalendarPopup(True)
        self.sum_date_to.setDate(QDate.currentDate())
        self.sum_date_to.setEnabled(False)
        
        h_filter.addWidget(QLabel("From:"))
        h_filter.addWidget(self.sum_date_from)
        h_filter.addWidget(QLabel("To:"))
        h_filter.addWidget(self.sum_date_to)
        
        btn_calc = QPushButton(" Calculate")
        style_button(btn_calc, variant="primary")
        btn_calc.setIcon(qta.icon("fa5s.calculator", color="white"))
        btn_calc.clicked.connect(self.load_summary_data)
        h_filter.addWidget(btn_calc)
        h_filter.addStretch()
        
        layout.addWidget(filter_frame)

        # 2. Metrics Grid (Requirement 3)
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # Row 1: Sales Step
        self.card_total_sales = StatCard("Gross Sales", "0", "Total revenue", "fa5s.shopping-cart", "#3498db")
        self.card_returns_sales = StatCard("Returns", "0", "Refunded items", "fa5s.undo", "#e74c3c")
        self.card_net_sales = StatCard("Net Sales", "0", "Sales after returns", "fa5s.check-circle", "#2ecc71")
        
        grid.addWidget(self.card_total_sales, 0, 0)
        grid.addWidget(self.card_returns_sales, 0, 1)
        grid.addWidget(self.card_net_sales, 0, 2)
        
        # Row 2: COGS & Gross Profit Step
        self.card_total_cogs = StatCard("Cost of Goods (COGS)", "0", "Total cost", "fa5s.tags", "#e67e22")
        self.card_gross_profit = StatCard("Gross Profit", "0", "Net Sales - COGS", "fa5s.chart-line", "#9b59b6")
        self.card_spacer1 = QWidget() # Placeholder
        
        grid.addWidget(self.card_total_cogs, 1, 0)
        grid.addWidget(self.card_gross_profit, 1, 1)
        grid.addWidget(self.card_spacer1, 1, 2)
        
        # Row 3: Expenses & Net Profit Step
        self.card_op_expenses = StatCard("Total Expenses", "0", "Operating costs", "fa5s.receipt", "#c0392b")
        self.card_salaries = StatCard("Salaries", "0", "Staff payroll", "fa5s.user-tie", "#34495e")
        self.card_net_profit = StatCard("Net Profit", "0", "Gross Profit - Exp - Sal", "fa5s.award", "#1abc9c")
        
        grid.addWidget(self.card_op_expenses, 2, 0)
        grid.addWidget(self.card_salaries, 2, 1)
        grid.addWidget(self.card_net_profit, 2, 2)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        return tab

    def toggle_custom_date(self):
        is_custom = self.sum_period_combo.currentText() == "Custom"
        self.sum_date_from.setEnabled(is_custom)
        self.sum_date_to.setEnabled(is_custom)

    def load_summary_data(self):
        from src.core.blocking_task_manager import task_manager
        
        def do_calc():
            with db_manager.get_connection() as conn:
                # 1. Sales Revenue
                gross = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales").fetchone()[0]
                
                # 2. COGS (Cost of Goods Sold)
                cogs = conn.execute("""
                    SELECT COALESCE(SUM(si.quantity * p.cost_price), 0)
                    FROM sale_items si JOIN products p ON si.product_id = p.id
                """).fetchone()[0]
                
                # 3. Operating Expenses (EXCLUDE all salary-related to avoid double-counting)
                expenses = conn.execute("""
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM expenses 
                    WHERE category NOT IN ('Salary', 'Advance Salary', 'Payroll')
                """).fetchone()[0]
                
                # 4. Salaries
                salaries = conn.execute("SELECT COALESCE(SUM(net_paid), 0) FROM payroll").fetchone()[0]
                
                # Net Profit = Revenue - COGS - Operating Expenses - Salaries
                profit = gross - cogs - expenses - salaries
                
                return {
                    "gross": gross, 
                    "cogs": cogs, 
                    "expenses": expenses, 
                    "salaries": salaries, 
                    "profit": profit
                }

        def on_finished(res):
            self.card_total_sales.update_value(f"{res['gross']:,.2f} AFN")
            self.card_total_cogs.update_value(f"{res['cogs']:,.2f} AFN")
            self.card_op_expenses.update_value(f"{res['expenses']:,.2f} AFN")
            self.card_salaries.update_value(f"{res['salaries']:,.2f} AFN")
            
            # Color code profit: green if positive, red if negative
            profit_color = "#05cd99" if res['profit'] >= 0 else "#ee5d50"
            self.card_net_profit.update_value(f"{res['profit']:,.2f} AFN")
            self.card_net_profit.value_lbl.setStyleSheet(f"color: {profit_color}; font-size: 28px; font-weight: bold;")
            
        task_manager.run_task(do_calc, on_finished=on_finished)

    def create_reports_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Filters
        filter_box = QFrame()
        filter_box.setObjectName("card")
        f_layout = QHBoxLayout(filter_box)
        
        self.rpt_type = QComboBox()
        self.rpt_type.addItems(["All", "Salaries", "Expenses", "Profit Analysis"])
        self.rpt_type.setFixedWidth(150)
        
        self.rpt_from = QDateEdit()
        self.rpt_from.setCalendarPopup(True)
        self.rpt_from.setDate(QDate.currentDate().addDays(-30))
        
        self.rpt_to = QDateEdit()
        self.rpt_to.setCalendarPopup(True)
        self.rpt_to.setDate(QDate.currentDate())
        
        search_btn = QPushButton("Generate")
        style_button(search_btn, variant="primary")
        search_btn.clicked.connect(self.load_report_data)
        
        f_layout.addWidget(QLabel("Type:"))
        f_layout.addWidget(self.rpt_type)
        f_layout.addWidget(QLabel("From:"))
        f_layout.addWidget(self.rpt_from)
        f_layout.addWidget(QLabel("To:"))
        f_layout.addWidget(self.rpt_to)
        f_layout.addWidget(search_btn)
        f_layout.addStretch()
        
        # Export buttons
        btn_layout = QHBoxLayout()
        self.print_btn = QPushButton("Print A4")
        style_button(self.print_btn, variant="outline")
        self.print_btn.clicked.connect(self.print_report)
        
        self.export_btn = QPushButton(" Export to Excel")
        style_button(self.export_btn, variant="info")
        self.export_btn.setIcon(qta.icon("fa5s.file-excel", color="white"))
        self.export_btn.clicked.connect(self.export_to_excel)
        
        self.pdf_btn = QPushButton(" Download PDF")
        style_button(self.pdf_btn, variant="danger")
        self.pdf_btn.setIcon(qta.icon("fa5s.file-pdf", color="white"))
        self.pdf_btn.clicked.connect(self.export_to_pdf)
        
        btn_layout.addWidget(self.print_btn)
        btn_layout.addWidget(self.pdf_btn)
        btn_layout.addWidget(self.export_btn)
        f_layout.addLayout(btn_layout)
        
        layout.addWidget(filter_box)
        
        # Report Table
        self.report_table = QTableWidget(0, 7)
        self.report_table.setHorizontalHeaderLabels(["Date", "Category/Type", "Reference", "User/Authorizer", "Amount", "Details", "Actions"])
        style_table(self.report_table, variant="premium")
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.report_table.setColumnWidth(6, 120)
        layout.addWidget(self.report_table)
        
        return tab

    def load_report_data(self):
        from src.core.blocking_task_manager import task_manager
        t = self.rpt_type.currentText()
        d_from = self.rpt_from.date().toString("yyyy-MM-dd")
        d_to = self.rpt_to.date().toString("yyyy-MM-dd")
        
        def fetch():
            rows = []
            with db_manager.get_connection() as conn:
                # 1. Expenses
                if t in ["All", "Expenses"]:
                    e_rows = conn.execute("""
                        SELECT expense_date, category, 'Expense-' || e.id, COALESCE(u.username, 'N/A'), amount, description
                        FROM expenses e LEFT JOIN users u ON e.user_id = u.id
                        WHERE expense_date BETWEEN ? AND ?
                        ORDER BY expense_date DESC
                    """, (d_from, d_to)).fetchall()
                    rows.extend([list(r) for r in e_rows])
                
                # 2. Salaries
                if t in ["All", "Salaries"]:
                    # Use COALESCE to handle null payment_date, fall back to created_at date
                    p_rows = conn.execute("""
                        SELECT 
                            COALESCE(DATE(payment_date), DATE(created_at)) as pay_date,
                            'Salary' as type,
                            month_year as reference,
                            u.username as employee,
                            net_paid as amount,
                            'Paid by: ' || COALESCE(auth.username, 'System') as details
                        FROM payroll p 
                        JOIN users u ON p.user_id = u.id
                        LEFT JOIN users auth ON p.authorized_by = auth.id
                        WHERE COALESCE(DATE(payment_date), DATE(created_at)) BETWEEN ? AND ?
                        ORDER BY pay_date DESC
                    """, (d_from, d_to)).fetchall()
                    rows.extend([list(r) for r in p_rows])
            
            # Sort all rows by date descending
            rows.sort(key=lambda x: x[0] if x[0] else '', reverse=True)
            return rows

        def on_finished(data):
            self.report_table.setRowCount(0)
            if not data:
                QMessageBox.information(self, "No Records", f"No records found for the selected period ({d_from} to {d_to}).")
                return
            for i, row in enumerate(data):
                self.report_table.insertRow(i)
                for j, val in enumerate(row):
                    self.report_table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ''))
                
                # Delete Action (Requirement 3)
                act_btn = QPushButton(" Delete")
                act_btn.setIcon(qta.icon("fa5s.trash", color="white"))
                style_button(act_btn, variant="danger", size="small")
                ref = row[2] # Reference (e.g. Expense-1)
                act_btn.clicked.connect(lambda checked, r=ref: self.delete_transaction(r))
                self.report_table.setCellWidget(i, 6, act_btn)
        
        task_manager.run_task(fetch, on_finished=on_finished)

    def delete_transaction(self, ref):
        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete {ref}?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes: return
        
        from src.core.blocking_task_manager import task_manager
        
        def do_delete():
            try:
                with db_manager.get_connection() as conn:
                    if ref.startswith("Expense-"):
                        e_id = ref.split("-")[1]
                        conn.execute("DELETE FROM expenses WHERE id=?", (e_id,))
                    elif ref.startswith("Salary-"):
                        s_id = ref.split("-")[1]
                        conn.execute("DELETE FROM payroll WHERE id=?", (s_id,))
                    conn.commit()
                    return True
            except: return False
            
        def on_done(success):
            if success:
                self.load_report_data()
                QMessageBox.information(self, "Success", "Transaction deleted.")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete transaction.")
                
        task_manager.run_task(do_delete, on_done)

    def print_report(self):
        # Optional: Ask user if they want PDF or Print Preview
        # For now, keep simple Print Preview as is, or redirect to PDF
        self.export_to_pdf()

    def export_to_pdf(self):
        from src.utils.pdf_generator_v2 import pdf_generator_v2
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF Report", "", "PDF Files (*.pdf)")
        if not path: return
        
        # Gather data from table
        headers = [self.report_table.horizontalHeaderItem(c).text() for c in range(self.report_table.columnCount() - 1)] # Exclude Actions
        data = []
        for r in range(self.report_table.rowCount()):
            row = []
            for c in range(self.report_table.columnCount() - 1):
                item = self.report_table.item(r, c)
                row.append(item.text() if item else "")
            data.append(row)
        
        title = f"Financial Report ({self.rpt_from.text()} - {self.rpt_to.text()})"
        from src.core.blocking_task_manager import task_manager
        
        def do_generate():
            pdf_generator_v2.generate_table_report(path, title, headers, data)
            return True

        def on_finished(_):
            QMessageBox.information(self, "Success", "PDF Report generated successfully.")
            import platform, subprocess
            if platform.system() == 'Darwin': subprocess.run(['open', path])
            elif platform.system() == 'Windows': os.startfile(path)

        def on_error(err):
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {err}")

        task_manager.run_task(do_generate, on_finished=on_finished, on_error=on_error)

    def generate_print_document(self, printer):
        doc = QTextDocument()
        cursor = QTextCursor(doc)
        
        # Header
        title_fmt = QTextCharFormat()
        title_fmt.setFontPointSize(20)
        title_fmt.setFontWeight(QFont.Weight.Bold)
        cursor.insertText("FaqiriTech Store Financial Report\n", title_fmt)
        
        info_fmt = QTextCharFormat()
        info_fmt.setFontPointSize(10)
        cursor.insertText(f"Period: {self.rpt_from.text()} to {self.rpt_to.text()}\n", info_fmt)
        cursor.insertText(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", info_fmt)
        cursor.insertText("-" * 80 + "\n\n")
        
        # Table
        rows = self.report_table.rowCount()
        cols = self.report_table.columnCount()
        
        tbl_fmt = QTextTableFormat()
        tbl_fmt.setBorder(1)
        tbl_fmt.setCellPadding(5)
        tbl_fmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
        
        text_table = cursor.insertTable(rows + 1, cols, tbl_fmt)
        
        # Headers
        header_fmt = QTextCharFormat()
        header_fmt.setFontWeight(QFont.Weight.Bold)
        for c in range(cols):
            cell = text_table.cellAt(0, c)
            cell_cursor = cell.firstCursorPosition()
            cell_cursor.insertText(self.report_table.horizontalHeaderItem(c).text(), header_fmt)
            
        # Data
        for r in range(rows):
            for c in range(cols):
                item = self.report_table.item(r, c)
                if item:
                    cell = text_table.cellAt(r + 1, c)
                    cell.firstCursorPosition().insertText(item.text())
        
        doc.print(printer)

    def export_to_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", "", "Excel Files (*.xlsx)")
        if not path: return
        
        data = []
        for r in range(self.report_table.rowCount()):
            row = []
            for c in range(self.report_table.columnCount()):
                item = self.report_table.item(r, c)
                row.append(item.text() if item else "")
            data.append(row)
            
        headers = [self.report_table.horizontalHeaderItem(c).text() for c in range(self.report_table.columnCount())]
        from src.core.blocking_task_manager import task_manager
        
        def do_export():
            df = pd.DataFrame(data, columns=headers)
            df.to_excel(path, index=False)
            return True

        def on_finished(_):
            QMessageBox.information(self, "Success", "Report exported to Excel successfully.")

        def on_error(err):
            QMessageBox.critical(self, "Error", f"Failed to export: {str(err)}")

        task_manager.run_task(do_export, on_finished=on_finished, on_error=on_error)
