from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, QDate
from src.database.db_manager import db_manager
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table

class PharmacyMonthCloseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pharmacy Month-End Close")
        self.setFixedWidth(800)
        self.setFixedHeight(700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Date Selection
        date_group = QGroupBox("Select Period")
        date_layout = QHBoxLayout(date_group)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-QDate.currentDate().day() + 1)) # 1st of month
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        
        gen_btn = QPushButton("Generate Report")
        style_button(gen_btn, variant="primary")
        gen_btn.clicked.connect(self.generate_report)
        
        date_layout.addWidget(QLabel("Start Date:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("End Date:"))
        date_layout.addWidget(self.end_date)
        date_layout.addWidget(gen_btn)
        
        layout.addWidget(date_group)
        
        # 2. Results Area
        res_group = QGroupBox("Month-End Summary")
        res_layout = QVBoxLayout(res_group)
        
        self.summary_table = QTableWidget(0, 2)
        self.summary_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        style_table(self.summary_table)
        
        res_layout.addWidget(self.summary_table)
        layout.addWidget(res_group)
        
        # 3. Actions
        action_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        self.close_month_btn = QPushButton("Confirm & Close Month")
        style_button(self.close_month_btn, variant="danger")
        self.close_month_btn.setEnabled(False) 
        self.close_month_btn.clicked.connect(self.finalize_month_close)
        
        action_layout.addStretch()
        action_layout.addWidget(close_btn)
        action_layout.addWidget(self.close_month_btn)
        
        layout.addLayout(action_layout)
        
        self.current_data = None

    def generate_report(self):
        s_date = self.start_date.date().toString("yyyy-MM-dd")
        e_date = self.end_date.date().toString("yyyy-MM-dd")
        
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # Sales Metrics
                sales_row = conn.execute("""
                    SELECT 
                        COUNT(*) as inv_count,
                        SUM(gross_amount) as gross,
                        SUM(discount_amount) as disc,
                        SUM(net_amount) as net
                    FROM pharmacy_sales 
                    WHERE created_at BETWEEN ? AND ?
                """, (s_date + ' 00:00:00', e_date + ' 23:59:59')).fetchone()
                
                # Items & Profit
                # Need to join or use simple sum if profit is stored (not yet stored in sales, must compute or read)
                # Wait, User Request D.2 says: "Store in pharmacy_sale_items: cost_price_at_sale... total_price"
                # So profit = sum(total_price - (cost_at_sale * qty))
                
                profit_row = conn.execute("""
                    SELECT 
                        SUM(quantity) as total_qty,
                        SUM(total_price - (cost_price_at_sale * quantity)) as gross_profit
                    FROM pharmacy_sale_items 
                    WHERE created_at BETWEEN ? AND ?
                """, (s_date + ' 00:00:00', e_date + ' 23:59:59')).fetchone()
                
                # Expenses
                exp_rows = conn.execute("""
                    SELECT category, SUM(amount) as total
                    FROM pharmacy_expenses
                    WHERE expense_date BETWEEN ? AND ?
                    GROUP BY category
                """, (s_date, e_date)).fetchall()
                
                # Salaries (from expenses if recorded there, OR from pharmacy_employee_salary if we assume accrual?
                # User said: "deduct total salaries ... from profit"
                # If the user enters salaries as expenses, they appear here.
                # If not, we might need to check the salary table.
                # Let's assume for this report: Total Expenses (including Salary category) + active salaries if not in expenses?
                # Best practice: Only deduct what is in Expenses table. We should have a tool to "Post Salary to Expenses".
                # For now, let's rely on expenses table.
                
                expenses_map = {row['category']: row['total'] for row in exp_rows}
                total_expenses = sum(expenses_map.values())
                
                # Calculations
                gross_sales = sales_row['gross'] or 0
                net_sales = sales_row['net'] or 0
                gross_profit = profit_row['gross_profit'] or 0
                
                final_net_profit = gross_profit - total_expenses
                
                # Display
                data = [
                    ("Total Invoices", str(sales_row['inv_count'])),
                    ("Total Items Sold", f"{profit_row['total_qty'] or 0:,.2f}"),
                    ("Gross Sales", f"{gross_sales:,.2f}"),
                    ("Total Discount", f"{sales_row['disc'] or 0:,.2f}"),
                    ("Net Sales", f"{net_sales:,.2f}"),
                    ("---", ""),
                    ("Gross Profit (Sales - COGS)", f"{gross_profit:,.2f}"),
                    ("Less: Salaries", f"{expenses_map.get('Salary', 0):,.2f}"),
                    ("Less: Petty Cash", f"{expenses_map.get('Petty Cash', 0):,.2f}"),
                    ("Less: Other Expenses", f"{expenses_map.get('Other', 0):,.2f}"),
                    ("Total Expenses", f"{total_expenses:,.2f}"),
                    ("---", ""),
                    ("FINAL NET PROFIT", f"{final_net_profit:,.2f}")
                ]
                
                self.summary_table.setRowCount(len(data))
                for i, (k, v) in enumerate(data):
                    self.summary_table.setItem(i, 0, QTableWidgetItem(k))
                    self.summary_table.setItem(i, 1, QTableWidgetItem(v))
                    
                    if "FINAL" in k:
                        font = self.summary_table.item(i, 0).font()
                        font.setBold(True)
                        self.summary_table.item(i, 0).setFont(font)
                        self.summary_table.item(i, 1).setFont(font)
                        
                        color = Qt.GlobalColor.green if final_net_profit >= 0 else Qt.GlobalColor.red
                        self.summary_table.item(i, 1).setForeground(color)
                
                self.current_data = {
                    "start": s_date, "end": e_date,
                    "sales": net_sales,
                    "profit": gross_profit,
                    "expenses": total_expenses,
                    "net_profit": final_net_profit
                }
                
                self.close_month_btn.setEnabled(True)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Report Error: {e}")

    def finalize_month_close(self):
        if not self.current_data: return
        
        reply = QMessageBox.question(self, "Confirm Close", 
                                     "Are you sure you want to close this month?\nThis will save a snapshot. It cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Format Month Str
                # Use start date as reference
                m_str = self.current_data['start'][:7] # YYYY-MM
                
                with db_manager.get_pharmacy_connection() as conn:
                    conn.execute("""
                        INSERT INTO pharmacy_month_close 
                        (month_str, total_sales, total_profit, net_profit, closed_by)
                        VALUES (?, ?, ?, ?, ?)
                    """, (m_str, self.current_data['sales'], self.current_data['profit'], self.current_data['net_profit'], 1)) 
                    # 1 is hardcoded user for now or get from Auth
                    conn.commit()
                
                QMessageBox.information(self, "Success", "Month Closed Successfully.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Wait! {e}")
