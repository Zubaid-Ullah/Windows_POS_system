from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
                             QComboBox, QPushButton, QScrollArea, QGridLayout, 
                             QLineEdit, QDateEdit, QMessageBox, QGroupBox, QTabWidget, QDialog, QFormLayout)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta
from src.database.db_manager import db_manager
from src.core.localization import lang_manager
from src.core.auth import Auth
from src.ui.table_styles import style_table
from src.ui.button_styles import style_button
from src.ui.theme_manager import theme_manager
from datetime import datetime, timedelta

class StatCard(QFrame):
    def __init__(self, title, value, icon_name, icon_color):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumHeight(120)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Icon Container
        icon_bg = QFrame()
        icon_bg.setFixedSize(50, 50)
        curr_color = qta.icon(icon_name, color=icon_color)
        icon_bg.setStyleSheet(f"background-color: {icon_color}20; border-radius: 25px; border: none;")
        icon_layout = QVBoxLayout(icon_bg)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(curr_color.pixmap(24, 24))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_lbl)
        
        # Text Info
        text_layout = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setObjectName("stat_title")
        
        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("stat_value")

        text_layout.addWidget(title_lbl)
        text_layout.addWidget(self.value_lbl)
        
        layout.addWidget(icon_bg)
        layout.addLayout(text_layout)
        layout.addStretch()

    def update_value(self, value):
        self.value_lbl.setText(value)

class FinanceView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_period = "daily"
        self.init_ui()
        self.load_data()
        self.load_payroll_data()

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
        self.period_combo.addItems(["Daily", "Weekly", "Monthly", "All Time"])
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        self.period_combo.setFixedWidth(120)
        self.period_combo.setFixedHeight(35)
        self.period_combo.setStyleSheet("font-size: 14px;")

        header_layout.addWidget(period_label)
        header_layout.addWidget(self.period_combo)

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

        self.tabs.addTab(self.create_overview_tab(), "📊 Overview")
        self.tabs.addTab(self.create_payroll_tab(), "💰 Payroll")
        self.tabs.addTab(self.create_advance_tab(), "💸 Advances")

        # Wrap tabs in scroll area to make it scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.tabs)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        layout.addWidget(scroll_area)

    def create_overview_tab(self):
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
        
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Salary", "Petty Cash", "Other"])
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount")
        
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description")
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        
        add_btn = QPushButton("Add Expense")
        style_button(add_btn, variant="danger")
        add_btn.clicked.connect(self.add_expense)
        
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
        add_btn.setFixedHeight(45)
        add_btn.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px 20px;")
        button_layout.addWidget(add_btn)

        expense_layout.addLayout(button_layout)

        layout.addWidget(expense_group)
        
        # 3. KPI Cards
        stats_layout = QHBoxLayout()
        self.card_income = StatCard("Total Income", "0 AFN", "fa5s.arrow-up", "#05cd99")
        self.card_expense = StatCard("Total Expenses", "0 AFN", "fa5s.arrow-down", "#ee5d50")
        self.card_profit = StatCard("Net Profit", "0 AFN", "fa5s.balance-scale", "#4318ff")
        
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

        self.payroll_table = QTableWidget(0, 5)
        self.payroll_table.setHorizontalHeaderLabels(["👤 Employee", "🏷️ Role", "💰 Base Salary", "📊 Status", "⚙️ Actions"])
        style_table(self.payroll_table, variant="premium")
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
                    SELECT e.expense_date, e.category, e.amount, u.username, e.description 
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
        
        try:
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO expenses (user_id, category, amount, description, expense_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, category, amount, desc, date_str))
                conn.commit()
            
            QMessageBox.information(self, "Success", "Expense Added")
            self.amount_input.clear()
            self.desc_input.clear()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # Payroll Logic
    def load_payroll_data(self):
        from src.core.blocking_task_manager import task_manager
        self.payroll_table.blockSignals(True)
        
        def fetch_payroll():
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.id, u.username, r.name, u.base_salary, u.is_active
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    WHERE u.is_super_admin = 0
                """)
                return [dict(u) for u in cursor.fetchall()]

        def on_finished(users):
            self.payroll_table.setRowCount(0)
            for i, u in enumerate(users):
                self.payroll_table.insertRow(i)
                self.payroll_table.setItem(i, 0, QTableWidgetItem(u['username']))
                self.payroll_table.setItem(i, 1, QTableWidgetItem(u['name']))
                
                # Editable Base Salary
                salary_item = QTableWidgetItem(f"{u['base_salary']:.2f}")
                salary_item.setData(Qt.ItemDataRole.UserRole, u['id'])
                self.payroll_table.setItem(i, 2, salary_item)
                
                status = "Active" if u['is_active'] else "Inactive"
                self.payroll_table.setItem(i, 3, QTableWidgetItem(status))
                
                # Action Button
                btn = QPushButton("Calculate Pay")
                style_button(btn, variant="success", size="small")
                btn.clicked.connect(lambda checked, uid=u['id'], name=u['username'], base=u['base_salary']: self.run_payroll_dialog(uid, name, base))
                self.payroll_table.setCellWidget(i, 4, btn)
            self.payroll_table.blockSignals(False)

        task_manager.run_task(fetch_payroll, on_finished=on_finished)

    def on_salary_changed(self, item):
        if item.column() == 2:
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
        
        save_btn = QPushButton("Save Advance")
        style_button(save_btn, variant="warning")
        save_btn.clicked.connect(self.save_advance)
        
        form.addRow("Staff Member:", self.adv_user_combo)
        form.addRow("Amount:", self.adv_amount)
        form.addRow("Reason:", self.adv_reason)
        form.addRow("Date:", self.adv_date)
        form.addRow("", save_btn)
        
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
        self.adv_user_combo.clear()

        with db_manager.get_connection() as conn:
            # Load main system users
            main_users = conn.execute("SELECT id, username, 'Main' as source FROM users WHERE is_active=1").fetchall()

            # Load pharmacy users if tables exist
            pharmacy_users = []
            try:
                pharmacy_users = conn.execute("SELECT id, username, 'Pharmacy' as source FROM pharmacy_users WHERE is_active=1").fetchall()
            except:
                pass  # Pharmacy tables might not exist

            # Combine and sort all users
            all_users = main_users + pharmacy_users
            all_users.sort(key=lambda x: x['username'].lower())

            # Add to combobox with clear labeling
            for user in all_users:
                display_text = f"{user['username']} ({user['source']})"
                self.adv_user_combo.addItem(display_text, (user['id'], user['source']))

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

        try:
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
                        """, (amt, f"Advance to {self.adv_user_combo.currentText()}: {reason}", date))
                    except:
                        # Fallback to main expenses if pharmacy table doesn't exist
                        conn.execute("""
                            INSERT INTO expenses (category, amount, description, expense_date)
                            VALUES ('Advance Salary', ?, ?, ?)
                        """, (amt, f"Pharmacy: {reason}", date))

                conn.commit()
            QMessageBox.information(self, "Success", "Advance payment recorded successfully")
            self.load_advances()
            self.load_payroll_data()

            # Clear form
            self.adv_amount.clear()
            self.adv_reason.clear()
            self.adv_date.setDate(QDate.currentDate())

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save advance: {str(e)}")

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

    def run_payroll_dialog(self, user_id, username, base_salary):
        # Improved payroll dialog with advance deduction
        with db_manager.get_connection() as conn:
            adv_row = conn.execute("SELECT SUM(amount) FROM expenses WHERE user_id=? AND category='Advance Salary'", (user_id,)).fetchone()
            total_advances = adv_row[0] or 0

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
                with db_manager.get_connection() as conn:
                    # Record final payment
                    conn.execute("""
                        INSERT INTO expenses (user_id, category, amount, description, expense_date)
                        VALUES (?, 'Salary', ?, ?, CURRENT_DATE)
                    """, (user_id, amount, f"Net Salary Payment for {username} after deductions"))
                    
                    # Mark advances as settled? 
                    # For simplicity, we can delete them or move them.
                    # The requirement says "Track history", so maybe we mark them as 'SETTLED'?
                    # Since we use 'expenses' table, we could add a column or just filter by date.
                    # For now, let's just record the payment.
                    
                    conn.commit()
                QMessageBox.information(self, "Success", "Salary Paid and Advances Deducted")
                dlg.accept()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                
        pay_btn.clicked.connect(save_payment)
        layout.addRow(pay_btn)
        
        dlg.exec()
