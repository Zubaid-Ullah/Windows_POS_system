from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import qtawesome as qta
from datetime import datetime

# Import Views
from src.ui.views.pharmacy.pharmacy_dashboard_view import PharmacyDashboardView
from src.ui.views.pharmacy.pharmacy_finance_view import PharmacyFinanceView
from src.ui.views.pharmacy.pharmacy_inventory_view import PharmacyInventoryView
from src.ui.views.pharmacy.pharmacy_sales_view import PharmacySalesView
from src.ui.views.pharmacy.pharmacy_customer_view import PharmacyCustomerView
from src.ui.views.pharmacy.pharmacy_supplier_view import PharmacySupplierView
from src.ui.views.pharmacy.pharmacy_loan_view import PharmacyLoanView
from src.ui.views.pharmacy.pharmacy_reports_view import PharmacyReportsView
from src.ui.views.pharmacy.pharmacy_price_check_view import PharmacyPriceCheckView
from src.ui.views.pharmacy.pharmacy_returns_view import PharmacyReturnsView
# New View
from src.ui.views.pharmacy.pharmacy_users_view import PharmacyUsersView

from src.ui.theme_manager import theme_manager
from src.core.auth import Auth

class PharmacyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pharmacy Management System (Isolated)")
        self.setMinimumSize(1200, 1000)
        
        # Central Widget & Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Apply Theme (Respects Dark Mode from Main Window if same manager is used)
        self.setStyleSheet(theme_manager.get_style())
        theme_manager.theme_changed.connect(self.apply_theme)
        
        layout = QHBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar
        self.init_sidebar()
        layout.addWidget(self.sidebar)
        
        # Content Area
        self.content_container = QFrame()
        self.content_container.setObjectName("content_area") # Styled by theme
        # Ensure white background default if theme didn't catch it
        if not theme_manager.is_dark:
            self.content_container.setStyleSheet("background-color: #f3f4f6;")
            
        content_main_layout = QVBoxLayout(self.content_container)
        content_main_layout.setContentsMargins(30, 30, 30, 30)
        content_main_layout.setSpacing(20)
        
        # Header
        self.init_header(content_main_layout)
        
        # Stacked Views
        self.view_stack = QStackedWidget()
        content_main_layout.addWidget(self.view_stack)
        
        layout.addWidget(self.content_container)
        
        # Load Views (Lazy load map)
        self.views = {}
        
        # Default View
        self.switch_view("pharmacy_dashboard")

    def apply_theme(self):
        self.setStyleSheet(theme_manager.get_style())
        
    def init_header(self, parent_layout):
        header_layout = QHBoxLayout()
        self.header_title = QLabel("Pharmacy Dashboard")
        self.header_title.setStyleSheet("font-size: 26px; font-weight: bold; color: #6d759f;") # Override color if needed
        
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()
        
        date_label = QLabel(datetime.now().strftime("%B %d, %Y"))
        
        # Dark mode adjust (simple check)
        text_color = "#a3aed0"
        if theme_manager.is_dark:
            self.header_title.setStyleSheet("font-size: 26px; font-weight: bold; color: #e2e8f0;")
        
        date_label.setStyleSheet(f"color: {text_color}; font-weight: 500; margin-right: 20px;")
        header_layout.addWidget(date_label)
        
        parent_layout.addLayout(header_layout)

    def init_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar") # Will pick up Main Window sidebar styles
        self.sidebar.setFixedWidth(260)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 30, 0, 30)
        
        # Pharmacy Logo Section
        # Clickable for collapse
        self.logo_driver = ClickableLogo(callback=self.toggle_sidebar)
        logo_layout = QHBoxLayout(self.logo_driver)
        logo_layout.setContentsMargins(0,0,0,0)
        
        logo_icon = QLabel()
        logo_icon.setFixedSize(40, 40)
        # Use a green pill icon or similar to distinguish
        logo_icon.setPixmap(qta.icon("fa5s.clinic-medical", color="#10b981").pixmap(35, 35))
        
        self.logo_text = QLabel("Pharmacy")
        self.logo_text.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin-left: 10px; background: transparent;")
        
        logo_layout.addStretch()
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(self.logo_text)
        logo_layout.addStretch()
        
        sidebar_layout.addWidget(self.logo_driver)
        sidebar_layout.addSpacing(40)
        
        # Menu Items
        self.menu_buttons = []
        self.original_button_texts = {}
        
        # Pharmacy Specific Menu
        # Key definition: key -> (icon, Label, ViewClass)
        self.menu_map = {
            "pharmacy_dashboard": ("fa5s.th-large", "Dashboard", PharmacyDashboardView),
            "pharmacy_finance": ("fa5s.chart-pie", "Finance", PharmacyFinanceView),
            "pharmacy_users": ("fa5s.user-nurse", "Users", PharmacyUsersView),
            "pharmacy_inventory": ("fa5s.boxes", "Inventory", PharmacyInventoryView),
            "pharmacy_sales": ("fa5s.file-invoice-dollar", "Sales", PharmacySalesView),
            "pharmacy_customers": ("fa5s.users", "Customers", PharmacyCustomerView),
            "pharmacy_suppliers": ("fa5s.truck", "Suppliers", PharmacySupplierView),
            "pharmacy_loans": ("fa5s.hand-holding-usd", "Loans", PharmacyLoanView),
            "pharmacy_reports": ("fa5s.chart-line", "Reports", PharmacyReportsView),
            "pharmacy_price_check": ("fa5s.tag", "Price Check", PharmacyPriceCheckView),
            "pharmacy_returns": ("fa5s.undo", "Returns", PharmacyReturnsView)
        }
        
        # Order and Permissions Check
        menu_order = [
            "pharmacy_dashboard", "pharmacy_finance", "pharmacy_users", 
            "pharmacy_inventory", "pharmacy_sales", "pharmacy_customers", 
            "pharmacy_suppliers", "pharmacy_loans", "pharmacy_reports", 
            "pharmacy_price_check", "pharmacy_returns"
        ]
        
        user = Auth.get_current_user()
        user_perms = Auth.get_user_permissions(user) if user else []
        
        for key in menu_order:
            # Check permissions (dashboard is always visible, or if user has '*' perms)
            if key != "pharmacy_dashboard" and "*" not in user_perms and key not in user_perms:
                continue
                
            icon, label_text, _ = self.menu_map[key]
            
            btn = QPushButton(f"  {label_text}")
            btn.setIcon(qta.icon(icon, color="#a5b4fc"))
            btn.setObjectName("menu_button") # Reuses MainWindow button styles
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            self.original_button_texts[btn] = f"  {label_text}"
            
            btn.clicked.connect(lambda checked, k=key: self.switch_view(k))
            
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)
            
        sidebar_layout.addStretch()
        
        # Back to Shop Button
        back_btn = QPushButton("  Back to Shop")
        back_btn.setIcon(qta.icon("fa5s.store", color="#ef4444")) # Red/Warning color to leave
        back_btn.setObjectName("menu_button")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.original_button_texts[back_btn] = "  Back to Shop"
        back_btn.clicked.connect(self.close) # Closing this window returns provided MainWindow was kept open? Or we re-open it.
        
        sidebar_layout.addWidget(back_btn)
        self.menu_buttons.append(back_btn)

    def toggle_sidebar(self):
        is_collapsed = self.sidebar.width() < 100
        if is_collapsed:
            self.sidebar.setFixedWidth(260)
            self.logo_text.show()
            for btn in self.menu_buttons:
                if btn in self.original_button_texts:
                    btn.setText(self.original_button_texts[btn])
                btn.setToolTip("")
        else:
            self.sidebar.setFixedWidth(70)
            self.logo_text.hide()
            for btn in self.menu_buttons:
                btn.setToolTip(btn.text().strip())
                btn.setText("")

    def switch_view(self, key):
        if key not in self.menu_map: return
        
        _, label_text, ViewClass = self.menu_map[key]
        self.header_title.setText(label_text if "Pharmacy" in label_text else f"Pharmacy {label_text}")
        
        # Update Styles
        for btn in self.menu_buttons:
            if btn.text().strip() == label_text or btn.toolTip() == label_text:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
        
        # Load View if not exists
        if key not in self.views:
            try:
                self.views[key] = ViewClass()
                self.view_stack.addWidget(self.views[key])
                # If dashboard, connect nav signals if they exist
                if key == "pharmacy_dashboard":
                    if hasattr(self.views[key], 'navigation_requested'):
                        self.views[key].navigation_requested.connect(self.switch_view)
            except Exception as e:
                print(f"Error loading {key}: {e}")
                err_label = QLabel(f"Error loading {label_text}: {e}")
                self.view_stack.addWidget(err_label)
                self.views[key] = err_label

        self.view_stack.setCurrentWidget(self.views[key])
        
        # Requirement: Update everything when new window loading except sale window
        if key != "pharmacy_sales":
            target_view = self.views[key]
            if hasattr(target_view, 'load_data'):
                target_view.load_data()
            elif hasattr(target_view, 'refresh'):
                target_view.refresh()
            elif hasattr(target_view, 'load_users'):
                target_view.load_users()
            elif hasattr(target_view, 'load_customers'):
                target_view.load_customers()
            elif hasattr(target_view, 'load_inventory'):
                target_view.load_inventory()
            elif hasattr(target_view, 'load_suppliers'):
                target_view.load_suppliers()
            elif hasattr(target_view, 'load_loans'):
                target_view.load_loans()

# Helper Class for Logo (Same as Main Window)
class ClickableLogo(QFrame):
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.callback = callback
    def mouseDoubleClickEvent(self, event):
        if self.callback: self.callback()
        super().mouseDoubleClickEvent(event)
