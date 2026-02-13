from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                             QGroupBox,
                             QTabWidget, QWidget, QComboBox, QDoubleSpinBox, QSpinBox, QGridLayout)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from src.database.db_manager import db_manager
from src.ui.button_styles import style_button
from src.ui.table_styles import style_table

class PharmacyMonthCloseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pharmacy Month-End Close & Cash Reconciliation")
        self.setFixedWidth(900)
        self.setFixedHeight(750)
        self.current_data = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Report
        self.tab_report = QWidget()
        self.init_report_tab()
        self.tabs.addTab(self.tab_report, "Month-End Report")
        
        # Tab 2: Cash Reconciliation
        self.tab_cash = QWidget()
        self.init_cash_tab()
        self.tabs.addTab(self.tab_cash, "Cash Reconciliation")
        
        # Bottom Actions
        action_layout = QHBoxLayout()
        close_btn = QPushButton("Close Dialog")
        close_btn.clicked.connect(self.close)
        
        self.close_month_btn = QPushButton("Confirm & Close Month")
        style_button(self.close_month_btn, variant="danger")
        self.close_month_btn.setEnabled(False) 
        self.close_month_btn.clicked.connect(self.finalize_month_close)
        
        action_layout.addStretch()
        action_layout.addWidget(close_btn)
        action_layout.addWidget(self.close_month_btn)
        
        main_layout.addLayout(action_layout)

    def init_report_tab(self):
        layout = QVBoxLayout(self.tab_report)
        
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

    def init_cash_tab(self):
        layout = QVBoxLayout(self.tab_cash)
        
        # Instructions
        layout.addWidget(QLabel("Enter denominations to reconcile cash with system expected total."))
        
        # Table
        # Columns: Type, Denomination, Count, Total
        self.cash_table = QTableWidget(0, 4)
        self.cash_table.setHorizontalHeaderLabels(["Type", "Denomination", "Count", "Subtotal"])
        self.cash_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        style_table(self.cash_table)
        layout.addWidget(self.cash_table)
        
        # Table Actions
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        style_button(add_btn, variant="info")
        add_btn.clicked.connect(self.add_cash_row)
        
        remove_btn = QPushButton("Remove Selected")
        style_button(remove_btn, variant="outline")
        remove_btn.clicked.connect(self.remove_cash_row)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Summary Area
        sum_group = QGroupBox("Reconciliation Report")
        sum_layout = QGridLayout(sum_group)
        
        font_big = QFont("Arial", 12, QFont.Weight.Bold)
        
        sum_layout.addWidget(QLabel("Expected System Total:"), 0, 0)
        self.lbl_system_total = QLabel("0.00")
        self.lbl_system_total.setFont(font_big)
        sum_layout.addWidget(self.lbl_system_total, 0, 1)
        
        sum_layout.addWidget(QLabel("Counted Cash Total:"), 1, 0)
        self.lbl_counted_total = QLabel("0.00")
        self.lbl_counted_total.setFont(font_big)
        sum_layout.addWidget(self.lbl_counted_total, 1, 1)
        
        sum_layout.addWidget(QLabel("Difference:"), 2, 0)
        self.lbl_diff = QLabel("0.00")
        self.lbl_diff.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        sum_layout.addWidget(self.lbl_diff, 2, 1)
        
        layout.addWidget(sum_group)
        
        # Add some initial rows
        for val in [1000, 500, 100, 50, 20, 10]:
            self.add_cash_row("Note", val)
        for val in [5, 2, 1]:
            self.add_cash_row("Coin", val)

    def add_cash_row(self, type_def="Note", val_def=0):
        row = self.cash_table.rowCount()
        self.cash_table.insertRow(row)
        
        # Type
        cb_type = QComboBox()
        cb_type.addItems(["Note", "Coin"])
        cb_type.setCurrentText(str(type_def))
        self.cash_table.setCellWidget(row, 0, cb_type)
        
        # Denom
        sb_denom = QDoubleSpinBox()
        sb_denom.setRange(0, 100000)
        sb_denom.setValue(val_def)
        sb_denom.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        sb_denom.valueChanged.connect(self.request_calculation)
        self.cash_table.setCellWidget(row, 1, sb_denom)
        
        # Count
        sb_count = QSpinBox()
        sb_count.setRange(0, 10000)
        sb_count.valueChanged.connect(self.request_calculation)
        self.cash_table.setCellWidget(row, 2, sb_count)
        
        # Subtotal (Label in widget)
        lbl_sub = QLabel("0.00")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.cash_table.setCellWidget(row, 3, lbl_sub)
        
    def remove_cash_row(self):
        row = self.cash_table.currentRow()
        if row >= 0:
            self.cash_table.removeRow(row)
            self.request_calculation()

    def request_calculation(self):
        """Debounce calculation to prevent UI freeze on rapid updates"""
        if not hasattr(self, 'calc_timer'):
            from PyQt6.QtCore import QTimer
            self.calc_timer = QTimer(self)
            self.calc_timer.setSingleShot(True)
            self.calc_timer.setInterval(200) # 200ms debounce
            self.calc_timer.timeout.connect(self._do_calculate_cash_total)
        
        self.calc_timer.start()

    def _do_calculate_cash_total(self):
        total = 0.0
        for i in range(self.cash_table.rowCount()):
            denom_w = self.cash_table.cellWidget(i, 1)
            count_w = self.cash_table.cellWidget(i, 2)
            sub_w = self.cash_table.cellWidget(i, 3)
            
            if denom_w and count_w and sub_w:
                try:
                    val = denom_w.value()
                    cnt = count_w.value()
                    sub = val * cnt
                    total += sub
                    sub_w.setText(f"{sub:,.2f}")
                except RuntimeError:
                    # Widget might be deleted
                    continue
        
        self.lbl_counted_total.setText(f"{total:,.2f}")
        
        # Update Diff
        try:
            sys_total = float(self.lbl_system_total.text().replace(",", ""))
        except:
            sys_total = 0.0
            
        diff = total - sys_total
        self.lbl_diff.setText(f"{diff:+,.2f}")
        
        if abs(diff) < 0.01:
            self.lbl_diff.setText("Matched")
            self.lbl_diff.setStyleSheet("color: green;")
        elif diff < 0:
            self.lbl_diff.setStyleSheet("color: red;")
        else:
            self.lbl_diff.setStyleSheet("color: blue;")

    def generate_report(self):
        s_date = self.start_date.date().toString("yyyy-MM-dd")
        e_date = self.end_date.date().toString("yyyy-MM-dd")
        
        # Disable button while loading
        self.sender().setEnabled(False)
        
        from src.core.blocking_task_manager import task_manager
        
        def do_generate_report():
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
                    cursor = conn.cursor()
                    
                    # Sales Metrics
                    sales_row = cursor.execute("""
                        SELECT 
                            COUNT(*) as inv_count,
                            COALESCE(SUM(total_amount), 0) as gross, 
                            0 as disc,
                            COALESCE(SUM(total_amount), 0) as net
                        FROM pharmacy_sales 
                        WHERE created_at BETWEEN ? AND ?
                    """, (s_date + ' 00:00:00', e_date + ' 23:59:59')).fetchone()
                    
                    # Items & Profit
                    profit_row = cursor.execute("""
                        SELECT 
                            COALESCE(SUM(quantity), 0) as total_qty,
                            COALESCE(SUM(total_price - (cost_price_at_sale * quantity)), 0) as gross_profit
                        FROM pharmacy_sale_items 
                        WHERE created_at BETWEEN ? AND ?
                    """, (s_date + ' 00:00:00', e_date + ' 23:59:59')).fetchone()
                    
                    # Expenses
                    exp_rows = cursor.execute("""
                        SELECT category, SUM(amount) as total
                        FROM pharmacy_expenses
                        WHERE expense_date BETWEEN ? AND ?
                        GROUP BY category
                    """, (s_date, e_date)).fetchall()
                    
                    expenses_map = {row['category']: row['total'] for row in exp_rows}
                    total_expenses = sum(expenses_map.values())
                    
                    # Calculations
                    gross_sales = sales_row['gross']
                    net_sales = sales_row['net']
                    gross_profit = profit_row['gross_profit']
                    
                    final_net_profit = gross_profit - total_expenses
                    
                    return {
                        "success": True,
                        "sales_row": sales_row,
                        "profit_row": profit_row,
                        "expenses_map": expenses_map,
                        "total_expenses": total_expenses,
                        "gross_sales": gross_sales,
                        "net_sales": net_sales,
                        "gross_profit": gross_profit,
                        "final_net_profit": final_net_profit,
                        "s_date": s_date, "e_date": e_date
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_report_generated(result):
            # Try to re-enable button if possible
            # Simplified for now
            
            if not result["success"]:
                QMessageBox.critical(self, "Error", f"Report Error: {result['error']}")
                return

            sales_row = result['sales_row']
            profit_row = result['profit_row']
            expenses_map = result['expenses_map']
            total_expenses = result['total_expenses']
            gross_sales = result['gross_sales']
            net_sales = result['net_sales']
            gross_profit = result['gross_profit']
            final_net_profit = result['final_net_profit']
            
            # Display
            data = [
                ("Total Invoices", str(sales_row['inv_count'])),
                ("Total Items Sold", f"{profit_row['total_qty']:,.2f}"),
                ("Gross Sales (Total Amount)", f"{gross_sales:,.2f}"),
                ("Total Discount", f"{sales_row['disc']:,.2f}"),
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
            
            self.summary_table.setRowCount(0) # Clear
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
                "start": result['s_date'], "end": result['e_date'],
                "sales": net_sales,
                "profit": gross_profit,
                "expenses": total_expenses,
                "net_profit": final_net_profit
            }
            
            # Update Cash Tab Expected Total
            # Assuming Net Sales is the Cash Expected for now
            self.lbl_system_total.setText(f"{net_sales:,.2f}")
            self.request_calculation()
            
            self.close_month_btn.setEnabled(True)
            self.tabs.setCurrentWidget(self.tab_report) # Stay on report or maybe switch depending on workflow
            
        task_manager.run_task(do_generate_report, on_finished=on_report_generated)

    def finalize_month_close(self):
        if not self.current_data: return
        
        reply = QMessageBox.question(self, "Confirm Close", 
                                     "Are you sure you want to close this month?\nThis will save a snapshot. It cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.close_month_btn.setEnabled(False) # Prevent double click
            
            from src.core.blocking_task_manager import task_manager
            
            # Capture needed data
            m_str = self.current_data['start'][:7] # YYYY-MM
            sales_val = self.current_data['sales']
            profit_val = self.current_data['profit']
            net_val = self.current_data['net_profit']
            
            def do_close():
                try:
                    with db_manager.get_pharmacy_connection() as conn:
                        conn.execute("""
                            INSERT INTO pharmacy_month_close 
                            (month_str, total_sales, total_profit, net_profit, closed_by)
                            VALUES (?, ?, ?, ?, ?)
                        """, (m_str, sales_val, profit_val, net_val, 1)) 
                        # 1 is hardcoded user for now or get from Auth
                        conn.commit()
                        return {"success": True}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            def on_finished(result):
                if result["success"]:
                    QMessageBox.information(self, "Success", "Month Closed Successfully.")
                    self.accept()
                else:
                    self.close_month_btn.setEnabled(True)
                    QMessageBox.critical(self, "Error", f"Wait! {result['error']}")

            task_manager.run_task(do_close, on_finished=on_finished)
