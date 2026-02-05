from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QPushButton, QLabel, QHeaderView, QGroupBox, 
                             QFormLayout, QLineEdit, QComboBox, QDateEdit, QMessageBox, QTableWidgetItem,
                             QTabWidget, QDoubleSpinBox, QGridLayout, QFrame)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.database.db_manager import db_manager
from src.core.localization import lang_manager
from src.core.pharmacy_auth import PharmacyAuth as Auth

class PharmacyFinanceView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Professional Header
        header = QFrame()
        header.setObjectName("pharmacy_finance_header")
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 15, 30, 15)

        title_icon = QLabel()
        title_icon.setPixmap(qta.icon("fa5s.prescription-bottle-alt", color="#10b981").pixmap(32, 32))

        title_text = QLabel(lang_manager.get("pharmacy_financial_management"))
        title_text.setStyleSheet("font-size: 28px; font-weight: bold; color: #065f46; margin-left: 15px;")

        header_layout.addWidget(title_icon)
        header_layout.addWidget(title_text)
        header_layout.addStretch()

        layout.addWidget(header)

        # Professional Tabs with better styling
        self.tabs = QTabWidget()
        self.tabs.setObjectName("pharmacy_finance_tabs")
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
                color: #10b981;
                border-bottom: 3px solid #10b981;
            }
            QTabBar::tab:hover {
                background: #e8f4fd;
                color: #10b981;
            }
        """)

        # Tab 1: Daily Expenses & Petty Cash
        self.expense_tab = QWidget()
        self.init_expense_tab()
        self.tabs.addTab(self.expense_tab, f"💰 {lang_manager.get('expenses')}")

        # Tab 2: Salaries
        self.salary_tab = QWidget()
        self.init_salary_tab()
        self.tabs.addTab(self.salary_tab, f"💸 {lang_manager.get('overview')}")

        # Tab 3: Monthly Summary & Profit
        self.summary_tab = QWidget()
        self.init_summary_tab()
        self.tabs.addTab(self.summary_tab, f"📊 {lang_manager.get('profit')}")

        layout.addWidget(self.tabs)

    def init_expense_tab(self):
        layout = QVBoxLayout(self.expense_tab)
        
        # Entry Form
        form_gb = QGroupBox(lang_manager.get("record_new_expense"))
        form_layout = QFormLayout(form_gb)
        
        self.exp_type = QComboBox()
        self.exp_type.addItems([
            lang_manager.get("daily_expense"), 
            lang_manager.get("petty_cash"), 
            lang_manager.get("utility"), 
            lang_manager.get("other")
        ])
        self.exp_type.setStyleSheet("border:1px solid #7b90ab;")
        self.exp_type.setMinimumWidth(500)
        self.exp_type.sizePolicy().horizontalPolicy().Expanding
        
        self.exp_amount = QDoubleSpinBox()
        self.exp_amount.setRange(0, 1000000)
        self.exp_amount.setSuffix(" AFN")
        self.exp_amount.setMinimumWidth(500)
        self.exp_amount.setStyleSheet("border:1px solid #7b90ab;")
        self.exp_amount.sizePolicy().horizontalPolicy().Expanding
        
        self.exp_purpose = QLineEdit()
        self.exp_purpose.setPlaceholderText(lang_manager.get("description_of_expense"))
        self.exp_purpose.setMinimumWidth(500)
        self.exp_purpose.setStyleSheet("border:1px solid #7b90ab;")
        self.exp_purpose.sizePolicy().horizontalPolicy().Expanding
        
        self.exp_date = QDateEdit()
        self.exp_date.setDate(QDate.currentDate())
        self.exp_date.setCalendarPopup(True)
        self.exp_date.setMinimumWidth(500)
        self.exp_date.setStyleSheet("border:1px solid #7b90ab;")
        self.exp_date.sizePolicy().horizontalPolicy().Expanding
        
        self.save_btn = QPushButton(lang_manager.get("save"))
        style_button(self.save_btn, variant="primary")
        self.save_btn.setMinimumWidth(500)
        self.save_btn.clicked.connect(self.save_expense)
        
        form_layout.addRow(lang_manager.get("type") + ":", self.exp_type)
        form_layout.addRow(lang_manager.get("amount") + ":", self.exp_amount)
        form_layout.addRow(lang_manager.get("description") + ":", self.exp_purpose)
        form_layout.addRow(lang_manager.get("date") + ":", self.exp_date)
        form_layout.addRow("", self.save_btn)
        
        layout.addWidget(form_gb)
        
        # Summary Row
        summary_layout = QHBoxLayout()
        self.daily_total_lbl = QLabel(lang_manager.get("daily_total") + ": 0.00 AFN")
        self.monthly_total_lbl = QLabel(lang_manager.get("monthly_total") + ": 0.00 AFN")
        self.daily_total_lbl.setObjectName("stat_value")
        self.monthly_total_lbl.setObjectName("stat_value")
        summary_layout.addWidget(self.daily_total_lbl)
        summary_layout.addStretch()
        summary_layout.addWidget(self.monthly_total_lbl)
        layout.addLayout(summary_layout)
        
        # Table
        self.exp_table = QTableWidget(0, 5)
        self.exp_table.setHorizontalHeaderLabels([
            "ID", lang_manager.get("date"), lang_manager.get("type"), 
            lang_manager.get("description"), lang_manager.get("amount")
        ])
        style_table(self.exp_table, variant="premium")
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.exp_table)
        
        self.load_expenses()

    def init_salary_tab(self):
        layout = QVBoxLayout(self.salary_tab)
        
        # Assignment Form (Moved from Users View)
        gb = QGroupBox(lang_manager.get("staff_salary_setup"))
        form = QFormLayout(gb)
        
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(500)
        self.user_combo.setStyleSheet("border:1px solid #7b90ab;")
        self.user_combo.sizePolicy().horizontalPolicy().Expanding
        self.load_users_combo()

        
        self.salary_amount = QDoubleSpinBox()
        self.salary_amount.setRange(0, 100000)
        self.salary_amount.setMinimumWidth(500)
        self.salary_amount.setStyleSheet("border:1px solid #7b90ab;")
        self.salary_amount.sizePolicy().horizontalPolicy().Expanding
        
        self.salary_type = QComboBox()
        self.salary_type.setMinimumWidth(500)
        self.salary_type.addItems([
            lang_manager.get("monthly_report").replace(" Report", ""), 
            "Weekly", 
            lang_manager.get("daily_report").replace(" Report", "")
        ]) # Note: We should probably add specific salary type keys, but for now reusing
        self.salary_type.setStyleSheet("border:1px solid #7b90ab;")
        self.salary_type.sizePolicy().horizontalPolicy().Expanding
        self.assign_btn = QPushButton(lang_manager.get("assign_salary"))
        self.assign_btn.setMinimumWidth(500)
        style_button(self.assign_btn, variant="success")
        self.assign_btn.clicked.connect(self.assign_salary)
        
        form.addRow(lang_manager.get("select_staff") + ":", self.user_combo)
        form.addRow(lang_manager.get("amount") + ":", self.salary_amount)
        form.addRow(lang_manager.get("type") + ":", self.salary_type)
        form.addRow("", self.assign_btn)
        
        layout.addWidget(gb)
        
        # Salary Table
        self.salary_table = QTableWidget(0, 5)
        self.salary_table.setHorizontalHeaderLabels([
            lang_manager.get("staff_name"), lang_manager.get("salary_type"), 
            lang_manager.get("amount"), lang_manager.get("status"), lang_manager.get("actions")
        ])
        style_table(self.salary_table)
        self.salary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.salary_table)
        
        self.load_salaries()

    def load_users_combo(self):
        self.user_combo.clear()
        
        curr_user = Auth.get_current_user()
        is_super = curr_user and (curr_user.get('is_super_admin') or curr_user.get('username') == 'admin')
        curr_user_id = curr_user.get('id') if curr_user else None

        main_users = []
        if is_super:
            try:
                with db_manager.get_connection() as conn:
                    main_users = conn.execute("SELECT id, username, 'Main' as source FROM users WHERE is_active=1").fetchall()
            except: pass

        pharmacy_users = []
        try:
            with db_manager.get_pharmacy_connection() as conn:
                if is_super:
                    # SuperAdmin sees everyone
                    pharmacy_users = conn.execute("SELECT id, username, 'Pharmacy' as source FROM pharmacy_users WHERE is_active=1").fetchall()
                else:
                    # Normal admin only sees users they created
                    pharmacy_users = conn.execute("""
                        SELECT id, username, 'Pharmacy' as source 
                        FROM pharmacy_users 
                        WHERE is_active=1 AND created_by=?
                    """, (curr_user_id,)).fetchall()
        except: pass

        # Combine and sort all users
        all_users = list(main_users) + list(pharmacy_users)
        all_users.sort(key=lambda x: str(x['username']).lower())

        # Add to combobox with clear labeling
        for user in all_users:
            display_text = f"{user['username']} ({user['source']})"
            self.user_combo.addItem(display_text, (user['id'], user['source']))

    def save_expense(self):
        etype = self.exp_type.currentText()
        amt = self.exp_amount.value()
        purpose = self.exp_purpose.text().strip()
        date = self.exp_date.date().toString("yyyy-MM-dd")
        
        from src.core.pharmacy_auth import PharmacyAuth
        user = PharmacyAuth.get_current_user()
        user_id = user['id'] if user else 1
        
        if amt <= 0 or not purpose:
            QMessageBox.warning(self, lang_manager.get("error"), f"{lang_manager.get('amount')} {lang_manager.get('and')} {lang_manager.get('description')} {lang_manager.get('required')}")
            return
            
        try:
            with db_manager.get_pharmacy_connection() as conn:
                conn.execute("""
                    INSERT INTO pharmacy_expenses (category, amount, description, expense_date, created_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (etype, amt, purpose, date, user_id))
                conn.commit()
            self.load_expenses()
            self.exp_amount.setValue(0)
            self.exp_purpose.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_expenses(self):
        self.exp_table.setRowCount(0)
        today = QDate.currentDate().toString("yyyy-MM-dd")
        month = QDate.currentDate().toString("yyyy-MM")
        
        daily_sum = 0
        monthly_sum = 0
        
        try:
            with db_manager.get_pharmacy_connection() as conn:
                rows = conn.execute("SELECT * FROM pharmacy_expenses ORDER BY expense_date DESC, id DESC LIMIT 100").fetchall()
                for i, row in enumerate(rows):
                    self.exp_table.insertRow(i)
                    self.exp_table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                    self.exp_table.setItem(i, 1, QTableWidgetItem(row['expense_date']))
                    self.exp_table.setItem(i, 2, QTableWidgetItem(row['category']))
                    self.exp_table.setItem(i, 3, QTableWidgetItem(row['description']))
                    self.exp_table.setItem(i, 4, QTableWidgetItem(f"{row['amount']:,.2f} AFN"))
                    
                    if row['expense_date'] == today: daily_sum += row['amount']
                    if row['expense_date'].startswith(month): monthly_sum += row['amount']
                    
                self.daily_total_lbl.setText(f"Daily Total: {daily_sum:,.2f} AFN")
            self.monthly_total_lbl.setText(f"Monthly Total: {monthly_sum:,.2f} AFN")
            
            # Autofit logic
            self.exp_table.resizeColumnsToContents()
            if self.exp_table.horizontalHeader().length() < self.exp_table.width():
                self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            else:
                self.exp_table.horizontalHeader().setStretchLastSection(True)
        except Exception as e:
            print(f"Error loading expenses: {e}")

    def assign_salary(self):
        user_data = self.user_combo.currentData()
        if not user_data:
            QMessageBox.warning(self, lang_manager.get("error"), lang_manager.get("select_staff"))
            return

        user_id, user_source = user_data
        amt = self.salary_amount.value()
        stype = self.salary_type.currentText()

        try:
            with db_manager.get_pharmacy_connection() as conn:
                if user_source == 'Main':
                    # For main users, we need to use the main salary table or expenses
                    # Since pharmacy_employee_salary is for pharmacy users, we'll use a different approach
                    QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("main_finance_notice"))
                    return
                else:
                    # For pharmacy users
                    existing = conn.execute("SELECT id FROM pharmacy_employee_salary WHERE user_id=? AND is_active=1", (user_id,)).fetchone()
                    if existing:
                        conn.execute("UPDATE pharmacy_employee_salary SET amount=?, salary_type=? WHERE id=?", (amt, stype, existing['id']))
                    else:
                        conn.execute("INSERT INTO pharmacy_employee_salary (user_id, amount, salary_type) VALUES (?, ?, ?)", (user_id, amt, stype))
                    conn.commit()

            self.load_salaries()
            QMessageBox.information(self, lang_manager.get("success"), lang_manager.get("salary_configured_success"))
        except Exception as e:
            QMessageBox.critical(self, lang_manager.get("error"), f"{lang_manager.get('error')}: {str(e)}")

    def load_salaries(self):
        self.salary_table.setRowCount(0)
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # Load pharmacy user salaries
                pharmacy_rows = conn.execute("""
                    SELECT s.*, u.username, 'Pharmacy' as source
                    FROM pharmacy_employee_salary s
                    JOIN pharmacy_users u ON s.user_id = u.id
                    WHERE s.is_active = 1
                """).fetchall()

                # For now, we'll only show pharmacy user salaries since the main salary management
                # is handled in the main finance view
                all_rows = pharmacy_rows

                for i, row in enumerate(all_rows):
                    self.salary_table.insertRow(i)
                    self.salary_table.setItem(i, 0, QTableWidgetItem(row['username']))
                    self.salary_table.setItem(i, 1, QTableWidgetItem(row['salary_type']))
                    self.salary_table.setItem(i, 2, QTableWidgetItem(f"{row['amount']:,.2f} AFN"))
                    self.salary_table.setItem(i, 3, QTableWidgetItem(lang_manager.get("active")))
                    
                    actions = QWidget()
                    act_layout = QHBoxLayout(actions)
                    act_layout.setContentsMargins(0,0,0,0)
                    btn = QPushButton(lang_manager.get("remove"))
                    style_button(btn, variant="danger", size="small")
                    btn.clicked.connect(lambda ch, sid=row['id']: self.remove_salary(sid))
                    act_layout.addWidget(btn)
                    self.salary_table.setCellWidget(i, 4, actions)
                    
                # Autofit logic
                self.salary_table.resizeColumnsToContents()
                if self.salary_table.horizontalHeader().length() < self.salary_table.width():
                    self.salary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                else:
                    self.salary_table.horizontalHeader().setStretchLastSection(True)
        except Exception as e:
            print(f"Error loading salaries: {e}")

    def init_summary_tab(self):
        layout = QVBoxLayout(self.summary_tab)
        layout.setSpacing(15)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            lang_manager.get("daily_report"), 
            lang_manager.get("weekly_report"), 
            lang_manager.get("monthly_report"), 
            lang_manager.get("custom_range")
        ])
        self.filter_combo.setCurrentText(lang_manager.get("monthly_report"))
        self.filter_combo.currentIndexChanged.connect(self.load_summary)

        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        
        filter_btn = QPushButton(lang_manager.get("search"))
        style_button(filter_btn, variant="info", size="small")
        filter_btn.clicked.connect(self.load_summary)

        filter_layout.addWidget(QLabel(lang_manager.get("preset") + ":"))
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(QLabel(lang_manager.get("from") + ":"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel(lang_manager.get("to") + ":"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(filter_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Header with current month
        self.month_lbl = QLabel(lang_manager.get("overview"))
        self.month_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #3b82f6;")
        layout.addWidget(self.month_lbl)
        
        # Cards for summary
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # Row 1: Sales Breakdown
        self.gross_sale_card = self.create_summary_card(lang_manager.get("gross_sales"), "0.00 AFN", "#3b82f6")
        self.ret_sale_card = self.create_summary_card(lang_manager.get("total_returns"), "0.00 AFN", "#ef4444")
        self.net_sale_card = self.create_summary_card(lang_manager.get("total_sales"), "0.00 AFN", "#2563eb")
        
        # Row 2: COGS Breakdown
        self.gross_cost_card = self.create_summary_card(lang_manager.get("gross_cogs"), "0.00 AFN", "#64748b")
        self.ret_cost_card = self.create_summary_card(lang_manager.get("total_returns"), "0.00 AFN", "#94a3b8")
        self.net_cost_card = self.create_summary_card(lang_manager.get("net_cogs"), "0.00 AFN", "#475569")
        
        # Row 3: Profit & Ops
        self.net_profit_card = self.create_summary_card(lang_manager.get("trading_profit"), "0.00 AFN", "#10b981")
        self.total_exp_card = self.create_summary_card(lang_manager.get("opex"), "0.00 AFN", "#f59e0b")
        self.final_net_card = self.create_summary_card(lang_manager.get("net_monthly_profit"), "0.00 AFN", "#8b5cf6")
        
        grid.addWidget(self.gross_sale_card, 0, 0)
        grid.addWidget(self.ret_sale_card, 0, 1)
        grid.addWidget(self.net_sale_card, 0, 2)
        
        grid.addWidget(self.gross_cost_card, 1, 0)
        grid.addWidget(self.ret_cost_card, 1, 1)
        grid.addWidget(self.net_cost_card, 1, 2)
        
        grid.addWidget(self.net_profit_card, 2, 0)
        grid.addWidget(self.total_exp_card, 2, 1)
        grid.addWidget(self.final_net_card, 2, 2)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        refresh_btn = QPushButton(lang_manager.get("refresh"))
        style_button(refresh_btn, variant="outline")
        refresh_btn.clicked.connect(self.load_summary)
        layout.addWidget(refresh_btn)

    def create_summary_card(self, title, val, color):
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"QFrame#card {{ background: transparent; border: 2px solid {color}33; border-radius: 12px; padding: 15px; }}")
        l = QVBoxLayout(card)
        
        t_lbl = QLabel(title)
        v_lbl = QLabel(val)
        v_lbl.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
        
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        
        card.title_lbl = t_lbl
        card.value_lbl = v_lbl
        return card

    def load_summary(self):
        try:
            with db_manager.get_pharmacy_connection() as conn:
                filter_text = self.filter_combo.currentText()
                days_count = 30 # Default for monthly
                
                if lang_manager.get("daily_report") in filter_text:
                    time_filter = "date({T}.created_at) = date('now')"
                    exp_filter = "date({T}.expense_date) = date('now')"
                    period_name = lang_manager.get("today")
                    days_count = 1
                elif lang_manager.get("weekly_report") in filter_text:
                    time_filter = "date({T}.created_at) >= date('now', '-7 days')"
                    exp_filter = "date({T}.expense_date) >= date('now', '-7 days')"
                    period_name = lang_manager.get("last_7_days")
                    days_count = 7
                elif lang_manager.get("monthly_report") in filter_text:
                    time_filter = "date({T}.created_at) >= date('now', 'start of month')"
                    exp_filter = "date({T}.expense_date) >= date('now', 'start of month')"
                    period_name = lang_manager.get("this_month")
                    days_count = 30
                else:
                    # Custom Range
                    d_from = self.date_from.date().toString("yyyy-MM-dd")
                    d_to = self.date_to.date().toString("yyyy-MM-dd")
                    time_filter = f"date({{T}}.created_at) BETWEEN '{d_from}' AND '{d_to}'"
                    exp_filter = f"date({{T}}.expense_date) BETWEEN '{d_from}' AND '{d_to}'"
                    period_name = f"{d_from} {lang_manager.get('to')} {d_to}"
                    days_count = self.date_from.date().daysTo(self.date_to.date()) + 1
                    if days_count <= 0: days_count = 1

                self.month_lbl.setText(f"{lang_manager.get('overview')} ({period_name})")

                # 1. Net Sales (Gross - Returns)
                sale_row = conn.execute(f"SELECT SUM(total_amount) as total FROM pharmacy_sales s WHERE {time_filter.format(T='s')}").fetchone()
                gross_sales = sale_row['total'] or 0
                
                ret_row = conn.execute(f"SELECT SUM(refund_amount) as total FROM pharmacy_returns r WHERE {time_filter.format(T='r')}").fetchone()
                returns_total = ret_row['total'] or 0
                
                net_sales = gross_sales - returns_total

                # 2. Net Cost of Goods
                cost_data = conn.execute(f"""
                    SELECT SUM(si.quantity * p.cost_price) as cost
                    FROM pharmacy_sale_items si
                    JOIN pharmacy_products p ON si.product_id = p.id
                    JOIN pharmacy_sales s ON si.sale_id = s.id
                    WHERE {time_filter.format(T='s')}
                """).fetchone()
                gross_cost = cost_data['cost'] or 0

                ret_cost_data = conn.execute(f"""
                    SELECT SUM(ri.quantity * p.cost_price) as cost
                    FROM pharmacy_return_items ri
                    JOIN pharmacy_products p ON ri.product_id = p.id
                    JOIN pharmacy_returns r ON ri.return_id = r.id
                    WHERE {time_filter.format(T='r')}
                """).fetchone()
                return_cost = ret_cost_data['cost'] or 0
                
                net_cost = gross_cost - return_cost
                trading_profit = net_sales - net_cost
                
                # 3. Total Salaries (Pro-rated for the period)
                full_monthly_salaries = conn.execute("SELECT SUM(amount) as total FROM pharmacy_employee_salary WHERE is_active=1").fetchone()
                total_salaries_config = full_monthly_salaries['total'] or 0
                total_salaries = (total_salaries_config / 30.0) * days_count
                
                # 4. Total Expenses
                expense_data = conn.execute(f"SELECT SUM(amount) as total FROM pharmacy_expenses e WHERE {exp_filter.format(T='e')}").fetchone()
                total_expenses = expense_data['total'] or 0
                
                final_net = trading_profit - total_salaries - total_expenses
                
                self.gross_sale_card.value_lbl.setText(f"{gross_sales:,.2f} AFN")
                self.ret_sale_card.value_lbl.setText(f"{returns_total:,.2f} AFN")
                self.net_sale_card.value_lbl.setText(f"{net_sales:,.2f} AFN")
                
                self.gross_cost_card.value_lbl.setText(f"{gross_cost:,.2f} AFN")
                self.ret_cost_card.value_lbl.setText(f"{return_cost:,.2f} AFN")
                self.net_cost_card.value_lbl.setText(f"{net_cost:,.2f} AFN")
                
                self.net_profit_card.value_lbl.setText(f"{trading_profit:,.2f} AFN")
                self.total_exp_card.value_lbl.setText(f"{(total_salaries + total_expenses):,.2f} AFN")
                self.final_net_card.value_lbl.setText(f"{final_net:,.2f} AFN")
                
                # Update final net label based on periodicity
                if days_count == 1:
                    self.final_net_card.title_lbl.setText(lang_manager.get("net_profit"))
                elif days_count <= 7:
                    self.final_net_card.title_lbl.setText(lang_manager.get("weekly_report"))
                else:
                    self.final_net_card.title_lbl.setText(lang_manager.get("net_monthly_profit"))

                if final_net < 0:
                    self.final_net_card.value_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #f43f5e;")
                else:
                    self.final_net_card.value_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #8b5cf6;")

        except Exception as e:
            print(f"Error loading summary: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self.load_expenses()
        self.load_salaries()
        self.load_summary()

    def remove_salary(self, sid):
        if QMessageBox.question(self, lang_manager.get("confirm"), lang_manager.get("confirm_remove_salary")) == QMessageBox.StandardButton.Yes:
            with db_manager.get_pharmacy_connection() as conn:
                conn.execute("UPDATE pharmacy_employee_salary SET is_active=0 WHERE id=?", (sid,))
                conn.commit()
            self.load_salaries()
            self.load_summary()
