from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel, QFrame, QScrollArea
from PyQt6.QtCore import Qt, QSize, pyqtSignal
import qtawesome as qta
from src.ui.theme_manager import theme_manager
from src.ui.views.pharmacy.pharmacy_sales_view import PharmacySalesView
from src.ui.views.pharmacy.pharmacy_inventory_view import PharmacyInventoryView
from src.ui.views.pharmacy.pharmacy_reports_view import PharmacyReportsView
from src.ui.views.pharmacy.pharmacy_dashboard_view import PharmacyDashboardView
from src.ui.views.pharmacy.pharmacy_finance_view import PharmacyFinanceView
from src.ui.views.pharmacy.pharmacy_customer_view import PharmacyCustomerView
from src.ui.views.pharmacy.pharmacy_supplier_view import PharmacySupplierView
from src.ui.views.pharmacy.pharmacy_loan_view import PharmacyLoanView
from src.ui.views.pharmacy.pharmacy_price_check_view import PharmacyPriceCheckView
from src.ui.views.pharmacy.pharmacy_returns_view import PharmacyReturnsView
from src.ui.views.pharmacy.pharmacy_users_view import PharmacyUsersView
from src.ui.views.pharmacy.pharmacy_settings_view import PharmacySettingsView
from src.ui.views.credentials_view import CredentialsView

from src.ui.views.pharmacy.pharmacy_login_view import PharmacyLoginView
from src.core.pharmacy_auth import PharmacyAuth

class PharmacyHub(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        
        # 1. Login View is always first
        self.login_view = PharmacyLoginView()
        self.login_view.login_success.connect(self.on_login_success)
        self.stack.addWidget(self.login_view)
        
        layout.addWidget(self.stack)
        
        # If already logged in (via Gateway), skip login
        if PharmacyAuth.get_current_user():
            self.on_login_success()

    def on_login_success(self):
        # Once logged in, initialize all other modules
        self.nav_items = [
            ("pharmacy_login", QWidget), # Placeholder for index 0
            ("pharmacy_dashboard", PharmacyDashboardView),
            ("pharmacy_finance", PharmacyFinanceView),
            ("pharmacy_inventory", PharmacyInventoryView),
            ("pharmacy_sales", PharmacySalesView),
            ("pharmacy_customers", PharmacyCustomerView),
            ("pharmacy_suppliers", PharmacySupplierView),
            ("pharmacy_loans", PharmacyLoanView),
            ("pharmacy_reports", PharmacyReportsView),
            ("pharmacy_price_check", PharmacyPriceCheckView),
            ("pharmacy_returns", PharmacyReturnsView),
            ("pharmacy_users", PharmacyUsersView),
            ("pharmacy_settings", PharmacySettingsView),
            ("pharmacy_credentials", CredentialsView),
        ]

        self.views = {"pharmacy_login": self.login_view}
        
        # We need to skip index 0
        for key, ViewClass in self.nav_items[1:]:
            try:
                view = ViewClass()
                self.views[key] = view
                if key == "pharmacy_dashboard":
                    view.navigation_requested.connect(self.handle_dashboard_navigation)
                if key == "pharmacy_price_check":
                    view.finished.connect(lambda: self.switch_module("pharmacy_dashboard"))
            except Exception as e:
                view = QLabel(f"Error loading {key}: {str(e)}")
                self.views[key] = view
            self.stack.addWidget(view)

        # Connect Sales & Returns to Reports and Dashboard (Live Update)
        if "pharmacy_reports" in self.views and hasattr(self.views["pharmacy_reports"], "load_data"):
            reports_view = self.views["pharmacy_reports"]
            dashboard_view = self.views.get("pharmacy_dashboard")
            
            if "pharmacy_sales" in self.views and hasattr(self.views["pharmacy_sales"], "sale_completed"):
                sales_view = self.views["pharmacy_sales"]
                sales_view.sale_completed.connect(reports_view.load_data)
                if dashboard_view and hasattr(dashboard_view, "load_products_data"):
                    sales_view.sale_completed.connect(dashboard_view.load_products_data)
            
            if "pharmacy_returns" in self.views and hasattr(self.views["pharmacy_returns"], "return_processed"):
                returns_view = self.views["pharmacy_returns"]
                returns_view.return_processed.connect(reports_view.load_data)
                if dashboard_view and hasattr(dashboard_view, "load_products_data"):
                    returns_view.return_processed.connect(dashboard_view.load_products_data)

        # Connect Customers to Sales (Live Update)
        if "pharmacy_sales" in self.views and "pharmacy_customers" in self.views:
            sales_view = self.views["pharmacy_sales"]
            cust_view = self.views["pharmacy_customers"]
            if hasattr(cust_view, "customers_updated") and hasattr(sales_view, "load_customers"):
                cust_view.customers_updated.connect(sales_view.load_customers)

        self.switch_module("pharmacy_dashboard")

    def switch_module(self, module_key):
        # Redirect all switches to login if not authenticated
        if not PharmacyAuth.get_current_user():
            self.stack.setCurrentIndex(0)
            return

        mapping = {item[0]: i for i, item in enumerate(self.nav_items)}
        idx = mapping.get(module_key, 1)
        self.stack.setCurrentIndex(idx)

    def handle_dashboard_navigation(self, key):
        # This will be used if the dashboard cards are clicked
        # We should notify the main window to update its sub-menu selection if possible, 
        # but for now just switching context is fine.
        self.switch_module(key)

    back_to_shop_requested = pyqtSignal()
    navigation_requested = pyqtSignal(str)

    def update_theme(self):
        # Pharmacy content area background is now handled by Main Window content_area
        # or can be set here if specific background is needed.
        pass
