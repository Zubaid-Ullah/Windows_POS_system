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
        # Once logged in, define all other modules (DO NOT INSTANTIATE YET - Lazy Load)
        self.nav_classes = {
            "pharmacy_dashboard": PharmacyDashboardView,
            "pharmacy_finance": PharmacyFinanceView,
            "pharmacy_inventory": PharmacyInventoryView,
            "pharmacy_sales": PharmacySalesView,
            "pharmacy_customers": PharmacyCustomerView,
            "pharmacy_suppliers": PharmacySupplierView,
            "pharmacy_loans": PharmacyLoanView,
            "pharmacy_reports": PharmacyReportsView,
            "pharmacy_price_check": PharmacyPriceCheckView,
            "pharmacy_returns": PharmacyReturnsView,
            "pharmacy_users": PharmacyUsersView,
            "pharmacy_settings": PharmacySettingsView,
            "pharmacy_credentials": CredentialsView,
        }

        self.views = {"pharmacy_login": self.login_view}
        self.nav_order = ["pharmacy_login"] + list(self.nav_classes.keys())
        
        # We only add the login view to the stack initially
        # Others will be added dynamically by switch_module
        
        self.switch_module("pharmacy_dashboard")

    def switch_module(self, module_key):
        # Redirect all switches to login if not authenticated
        if not PharmacyAuth.get_current_user():
            self.stack.setCurrentIndex(0)
            return

        if module_key not in self.views and module_key in self.nav_classes:
            # Lazy Instantiate
            try:
                ViewClass = self.nav_classes[module_key]
                view = ViewClass()
                self.views[module_key] = view
                
                # Setup specific connections
                if module_key == "pharmacy_dashboard":
                    view.navigation_requested.connect(self.handle_dashboard_navigation)
                elif module_key == "pharmacy_price_check":
                    view.finished.connect(lambda: self.switch_module("pharmacy_dashboard"))
                
                # Cross-view linking (if peers exist)
                self._link_view_signals(module_key, view)
                
                self.stack.addWidget(view)
            except Exception as e:
                print(f"Error lazy loading {module_key}: {e}")
                error_lbl = QLabel(f"Error loading {module_key}: {str(e)}")
                self.views[module_key] = error_lbl
                self.stack.addWidget(error_lbl)

        # Get the index in the stack
        target_view = self.views.get(module_key)
        if target_view:
            self.stack.setCurrentWidget(target_view)

    def _link_view_signals(self, key, view):
        """Wires up signals between a newly instantiated view and existing peers."""
        # This ensures live updates between sales/returns/reports even with lazy loading
        r_view = self.views.get("pharmacy_reports")
        d_view = self.views.get("pharmacy_dashboard")
        s_view = self.views.get("pharmacy_sales")
        ret_view = self.views.get("pharmacy_returns")
        c_view = self.views.get("pharmacy_customers")

        # 1. If we just created Sales, link to Reports/Dashboard if they exist
        if key == "pharmacy_sales":
            if r_view and hasattr(r_view, 'load_data'): view.sale_completed.connect(r_view.load_data)
            if d_view and hasattr(d_view, 'load_products_data'): view.sale_completed.connect(d_view.load_products_data)
        
        # 2. If we just created Reports/Dashboard, look for Sales/Returns
        elif key in ["pharmacy_reports", "pharmacy_dashboard"]:
            slot = view.load_data if key == "pharmacy_reports" else view.load_products_data
            if s_view: s_view.sale_completed.connect(slot)
            if ret_view: ret_view.return_processed.connect(slot)

        # 3. Customer -> Sales link
        if key == "pharmacy_customers" and s_view:
            if hasattr(s_view, 'load_customers'): view.customers_updated.connect(s_view.load_customers)
        elif key == "pharmacy_sales" and c_view:
            if hasattr(c_view, 'customers_updated'): c_view.customers_updated.connect(view.load_customers)

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
