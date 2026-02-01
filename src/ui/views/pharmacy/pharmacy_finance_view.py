from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QPushButton, QLabel, QHeaderView, QGroupBox, 
                             QFormLayout, QLineEdit, QComboBox, QDateEdit, QMessageBox, QTableWidgetItem,
                             QTabWidget, QDoubleSpinBox, QGridLayout, QFrame)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table
from src.database.db_manager import db_manager

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

        title_text = QLabel("Pharmacy Financial Management")
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
        self.tabs.addTab(self.expense_tab, "💰 Expenses")

        # Tab 2: Salaries
        self.salary_tab = QWidget()
        self.init_salary_tab()
        self.tabs.addTab(self.salary_tab, "💸 Salaries")

        # Tab 3: Monthly Summary & Profit
        self.summary_tab = QWidget()
        self.init_summary_tab()
        self.tabs.addTab(self.summary_tab, "📊 Summary")

        layout.addWidget(self.tabs)

    def init_expense_tab(self):
        layout = QVBoxLayout(self.expense_tab)
        
        # Entry Form
        form_gb = QGroupBox("Record New Expense / Petty Cash")
        form_layout = QFormLayout(form_gb)
        
        self.exp_type = QComboBox()
        self.exp_type.addItems(["Daily Expense", "Petty Cash", "Utility", "Other"])
        self.exp_type.setMinimumWidth(500)
        
        self.exp_amount = QDoubleSpinBox()
        self.exp_amount.setRange(0, 1000000)
        self.exp_amount.setSuffix(" AFN")
        self.exp_amount.setMinimumWidth(500)
        
        self.exp_purpose = QLineEdit()
        self.exp_purpose.setPlaceholderText("Description of expense")
        self.exp_purpose.setMinimumWidth(500)
        
        self.exp_date = QDateEdit()
        self.exp_date.setDate(QDate.currentDate())
        self.exp_date.setCalendarPopup(True)
        self.exp_date.setMinimumWidth(500)
        
        self.save_btn = QPushButton("Save Record")
        style_button(self.save_btn, variant="primary")
        self.save_btn.setMinimumWidth(500)
        self.save_btn.clicked.connect(self.save_expense)
        
        form_layout.addRow("Type:", self.exp_type)
        form_layout.addRow("Amount:", self.exp_amount)
        form_layout.addRow("Purpose:", self.exp_purpose)
        form_layout.addRow("Date:", self.exp_date)
        form_layout.addRow("", self.save_btn)
        
        layout.addWidget(form_gb)
        
        # Summary Row
        summary_layout = QHBoxLayout()
        self.daily_total_lbl = QLabel("Daily Total: 0.00 AFN")
        self.monthly_total_lbl = QLabel("Monthly Total: 0.00 AFN")
        self.daily_total_lbl.setObjectName("stat_value")
        self.monthly_total_lbl.setObjectName("stat_value")
        summary_layout.addWidget(self.daily_total_lbl)
        summary_layout.addStretch()
        summary_layout.addWidget(self.monthly_total_lbl)
        layout.addLayout(summary_layout)
        
        # Table
        self.exp_table = QTableWidget(0, 5)
        self.exp_table.setHorizontalHeaderLabels(["ID", "Date", "Type", "Purpose", "Amount"])
        style_table(self.exp_table, variant="premium")
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.exp_table)
        
        self.load_expenses()

    def init_salary_tab(self):
        layout = QVBoxLayout(self.salary_tab)
        
        # Assignment Form (Moved from Users View)
        gb = QGroupBox("Staff Salary Setup")
        form = QFormLayout(gb)
        
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(500)
        self.load_users_combo()
        
        self.salary_amount = QDoubleSpinBox()
        self.salary_amount.setRange(0, 100000)
        self.salary_amount.setMinimumWidth(500)
        
        self.salary_type = QComboBox()
        self.salary_type.setMinimumWidth(500)
        self.salary_type.addItems(["Monthly", "Weekly", "Daily"])
        
        self.assign_btn = QPushButton("Assign Salary")
        self.assign_btn.setMinimumWidth(500)
        style_button(self.assign_btn, variant="success")
        self.assign_btn.clicked.connect(self.assign_salary)
        
        form.addRow("Select Staff:", self.user_combo)
        form.addRow("Amount:", self.salary_amount)
        form.addRow("Type:", self.salary_type)
        form.addRow("", self.assign_btn)
        
        layout.addWidget(gb)
        
        # Salary Table
        self.salary_table = QTableWidget(0, 5)
        self.salary_table.setHorizontalHeaderLabels(["Staff Name", "Salary Type", "Amount", "Status", "Actions"])
        style_table(self.salary_table)
        self.salary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.salary_table)
        
        self.load_salaries()

    def load_users_combo(self):
        self.user_combo.clear()

        main_users = []
        try:
            with db_manager.get_connection() as conn:
                main_users = conn.execute("SELECT id, username, 'Main' as source FROM users WHERE is_active=1").fetchall()
        except: pass

        pharmacy_users = []
        try:
            with db_manager.get_pharmacy_connection() as conn:
                pharmacy_users = conn.execute("SELECT id, username, 'Pharmacy' as source FROM pharmacy_users WHERE is_active=1").fetchall()
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
            QMessageBox.warning(self, "Error", "Amount and Purpose are required")
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
        except Exception as e:
            print(f"Error loading expenses: {e}")

    def assign_salary(self):
        user_data = self.user_combo.currentData()
        if not user_data:
            QMessageBox.warning(self, "Error", "Please select a staff member")
            return

        user_id, user_source = user_data
        amt = self.salary_amount.value()
        stype = self.salary_type.currentText()

        try:
            with db_manager.get_pharmacy_connection() as conn:
                if user_source == 'Main':
                    # For main users, we need to use the main salary table or expenses
                    # Since pharmacy_employee_salary is for pharmacy users, we'll use a different approach
                    QMessageBox.warning(self, "Info", "Salary assignment for main system users should be done from the main Finance module.")
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
            QMessageBox.information(self, "Success", "Salary configured successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure salary: {str(e)}")

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
                    self.salary_table.setItem(i, 3, QTableWidgetItem("Active"))
                    
                    actions = QWidget()
                    act_layout = QHBoxLayout(actions)
                    act_layout.setContentsMargins(0,0,0,0)
                    btn = QPushButton("Remove")
                    style_button(btn, variant="danger", size="small")
                    btn.clicked.connect(lambda ch, sid=row['id']: self.remove_salary(sid))
                    act_layout.addWidget(btn)
                    self.salary_table.setCellWidget(i, 4, actions)
        except Exception as e:
            print(f"Error loading salaries: {e}")

    def init_summary_tab(self):
        layout = QVBoxLayout(self.summary_tab)
        layout.setSpacing(15)
        
        # Header with current month
        self.month_lbl = QLabel(f"Summary for {QDate.currentDate().toString('MMMM yyyy')}")
        self.month_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #3b82f6;")
        layout.addWidget(self.month_lbl)
        
        # Cards for summary
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # Row 1: Sales Breakdown
        self.gross_sale_card = self.create_summary_card("Gross Sales", "0.00 AFN", "#3b82f6")
        self.ret_sale_card = self.create_summary_card("Returns Amount", "0.00 AFN", "#ef4444")
        self.net_sale_card = self.create_summary_card("Net Sales", "0.00 AFN", "#2563eb")
        
        # Row 2: COGS Breakdown
        self.gross_cost_card = self.create_summary_card("Gross COGS", "0.00 AFN", "#64748b")
        self.ret_cost_card = self.create_summary_card("Returns COGS", "0.00 AFN", "#94a3b8")
        self.net_cost_card = self.create_summary_card("Net COGS", "0.00 AFN", "#475569")
        
        # Row 3: Profit & Ops
        self.net_profit_card = self.create_summary_card("Trading Profit", "0.00 AFN", "#10b981")
        self.total_exp_card = self.create_summary_card("Total OpEx", "0.00 AFN", "#f59e0b")
        self.final_net_card = self.create_summary_card("Net Monthly Profit", "0.00 AFN", "#8b5cf6")
        
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
        
        refresh_btn = QPushButton("Refresh Summary")
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
        
        card.value_lbl = v_lbl
        return card

    def load_summary(self):
        month = QDate.currentDate().toString("yyyy-MM")
        self.month_lbl.setText(f"Summary for {QDate.currentDate().toString('MMMM yyyy')}")
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # 1. Net Sales (Gross - Returns)
                sale_row = conn.execute(f"SELECT SUM(total_amount) as total FROM pharmacy_sales WHERE created_at LIKE '{month}%'").fetchone()
                gross_sales = sale_row['total'] or 0
                
                # Deduct Returns for this month
                ret_row = conn.execute(f"SELECT SUM(refund_amount) as total FROM pharmacy_returns WHERE created_at LIKE '{month}%'").fetchone()
                returns_total = ret_row['total'] or 0
                
                net_sales = gross_sales - returns_total

                # 2. Net Cost of Goods (Cost of Sales - Cost of Returns)
                # Cost of Sales
                cost_data = conn.execute(f"""
                    SELECT SUM(si.quantity * p.cost_price) as cost
                    FROM pharmacy_sale_items si
                    JOIN pharmacy_products p ON si.product_id = p.id
                    JOIN pharmacy_sales s ON si.sale_id = s.id
                    WHERE s.created_at LIKE '{month}%'
                """).fetchone()
                gross_cost = cost_data['cost'] or 0

                # Cost of Returns (Items returned back to stock)
                ret_cost_data = conn.execute(f"""
                    SELECT SUM(ri.quantity * p.cost_price) as cost
                    FROM pharmacy_return_items ri
                    JOIN pharmacy_products p ON ri.product_id = p.id
                    JOIN pharmacy_returns r ON ri.return_id = r.id
                    WHERE r.created_at LIKE '{month}%'
                """).fetchone()
                return_cost = ret_cost_data['cost'] or 0
                
                net_cost = gross_cost - return_cost
                
                trading_profit = net_sales - net_cost
                
                # 3. Total Salaries
                salary_data = conn.execute("SELECT SUM(amount) as total FROM pharmacy_employee_salary WHERE is_active=1").fetchone()
                total_salaries = salary_data['total'] or 0
                
                # 4. Total Expenses
                expense_data = conn.execute(f"SELECT SUM(amount) as total FROM pharmacy_expenses WHERE expense_date LIKE '{month}%'").fetchone()
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
        if QMessageBox.question(self, "Confirm", "Remove this salary configuration?") == QMessageBox.StandardButton.Yes:
            with db_manager.get_pharmacy_connection() as conn:
                conn.execute("UPDATE pharmacy_employee_salary SET is_active=0 WHERE id=?", (sid,))
                conn.commit()
            self.load_salaries()
            self.load_summary()
