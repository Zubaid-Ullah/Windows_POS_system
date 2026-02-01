from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QStackedWidget, QSpacerItem, QSizePolicy, QLineEdit, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
import qtawesome as qta
from src.ui.views.login_view import LoginView
from src.ui.views.sales_view import SalesView
from src.ui.views.inventory_view import InventoryView
from src.ui.views.customer_view import CustomerView
from src.ui.views.reports_view import ReportsView
from src.ui.views.settings_view import SettingsView
from src.ui.views.supplier_view import SupplierView
from src.ui.views.loan_view import LoanView
from src.ui.views.stock_alert_view import StockAlertView
from src.ui.views.price_check_view import PriceCheckView
from src.ui.views.returns_view import ReturnsView
from src.ui.views.returns_view import ReturnsView
from src.ui.views.pharmacy.pharmacy_hub import PharmacyHub
from src.ui.theme_manager import theme_manager
from src.core.localization import lang_manager
from src.core.auth import Auth
from src.core.pharmacy_auth import PharmacyAuth
from datetime import datetime
from src.ui.views.super_admin_view import SuperAdminView
from src.ui.views.dashboard_view import DashboardView
from src.ui.views.finance_view import FinanceView
from src.ui.views.user_management_view import UserManagementView
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline POS & Inventory Management")
        self.setMinimumSize(1200, 1000)
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        
        self.business_mode = "STORE"
        self.login_view = LoginView()
        self.login_view.login_success.connect(self.show_main_app)
        
        self.central_widget.addWidget(self.login_view)
        
        self.apply_theme()
        lang_manager.language_changed.connect(self.on_language_changed)
        theme_manager.theme_changed.connect(self.apply_theme)

    def on_language_changed(self, lang):
        # Only refresh main app if user is logged in
        if hasattr(self, 'main_app_widget') and (Auth.get_current_user() or PharmacyAuth.get_current_user()):
            # Refresh Sidebar and Header
            self.show_main_app(self.business_mode) 
        self.apply_theme()

    def apply_theme(self):
        self.setStyleSheet(theme_manager.get_style())

    def show_main_app(self, mode="STORE"):
        # Cleanup existing main app widget if it exists to avoid stacking
        if hasattr(self, 'main_app_widget'):
            self.central_widget.removeWidget(self.main_app_widget)
            self.main_app_widget.deleteLater()
        
        # Reset pharmacy hub reference to avoid deleted object errors
        if hasattr(self, 'pharmacy_hub'):
            self.pharmacy_hub = None
            
        self.business_mode = mode
        self.main_app_widget = QWidget()
        
        # Mode-based branding
        branding = {
            "STORE": {
                "color": "#1a3a8a",
                "icon": "fa5s.store",
                "title": "Afex POS",
                "auth_class": Auth
            },
            "PHARMACY": {
                "color": "#065f46", # Emerald 900
                "icon": "fa5s.prescription-bottle-alt",
                "title": "Afex Pharmacy",
                "auth_class": PharmacyAuth
            }
        }[mode]
        
        user_auth = branding["auth_class"]
        user = user_auth.get_current_user()
        
        if not user:
            print("Error: No user logged in during show_main_app")
            return self.handle_logout()
            
        permissions = user_auth.get_user_permissions(user)

        # RTL Support
        if lang_manager.is_rtl():
            self.main_app_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.main_app_widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        layout = QHBoxLayout(self.main_app_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Helper Classes for Interactivity
        class ClickableSidebar(QFrame):
            def __init__(self, sidebar_ref, toggle_callback):
                super().__init__()
                self.sidebar_ref = sidebar_ref
                self.callback = toggle_callback
            def mousePressEvent(self, event):
                # If collapsed, single click expands
                if self.sidebar_ref.width() < 100:
                    self.callback()
                super().mousePressEvent(event)
            def mouseDoubleClickEvent(self, event):
                if self.callback: self.callback()
                super().mouseDoubleClickEvent(event)

        class ClickableLogo(QFrame):
            def __init__(self, sidebar_ref, toggle_callback):
                super().__init__()
                self.sidebar_ref = sidebar_ref
                self.callback = toggle_callback
            def mousePressEvent(self, event):
                if self.sidebar_ref.width() < 100:
                    self.callback()
                super().mousePressEvent(event)
            def mouseDoubleClickEvent(self, event):
                if self.callback: self.callback()
                super().mouseDoubleClickEvent(event)

        # Sidebar
        self.sidebar = QWidget() # Placeholder for reference
        self.sidebar = ClickableSidebar(sidebar_ref=self.sidebar, toggle_callback=self.toggle_sidebar)
        # Fix circular reference for init
        self.sidebar.sidebar_ref = self.sidebar
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet(f"background-color: {branding['color']};")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 30, 0, 30)
        
        # Logo Section
        self.logo_container = ClickableLogo(sidebar_ref=self.sidebar, toggle_callback=self.toggle_sidebar)
        self.logo_container.setStyleSheet("background: transparent;")
        logo_lay = QHBoxLayout(self.logo_container)
        
        # Logo Icon with Fallback
        # Logo Icon with Fallback
        self.logo_icon_lbl = QLabel()
        import os, sys
        if getattr(sys, 'frozen', False):
            base = getattr(sys, '_MEIPASS', os.path.join(os.path.dirname(sys.executable), "..", "Resources"))
            logo_path = os.path.join(base, "Logo", "logo.ico")
        else:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Logo", "logo.ico")
            
        logo_pix = QPixmap(logo_path)
        if mode == "STORE" and not logo_pix.isNull():
            self.logo_icon_lbl.setPixmap(logo_pix.scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.logo_icon_lbl.setPixmap(qta.icon(branding["icon"], color="white").pixmap(35, 35))
        logo_lay.addWidget(self.logo_icon_lbl)
        
        self.logo_text = QLabel(branding["title"])
        self.logo_text.setStyleSheet("color: white; font-size: 19px; font-weight: bold; border: none;")
        logo_lay.addWidget(self.logo_text)
        sidebar_layout.addWidget(self.logo_container)
        sidebar_layout.addSpacing(30)
        
        # Scrollable Menu
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")
        
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        
        self.menu_buttons = []
        self.original_button_texts = {}

        if mode == "STORE":
            menus = [
                ("dashboard", "fa5s.th-large", "Dashboard"),
                ("finance", "fa5s.chart-pie", "Finance"),
                ("users", "fa5s.user-cog", "Users"),
                ("inventory", "fa5s.boxes", "Inventory"),
                ("sales", "fa5s.file-invoice-dollar", "Sales"),
                ("customers", "fa5s.users", "Customers"),
                ("suppliers", "fa5s.truck", "Suppliers"),
                ("loans", "fa5s.hand-holding-usd", "Loans"),
                ("reports", "fa5s.chart-line", "Reports"),
                ("low_stock", "fa5s.bell", "Low Stock"),
                ("returns", "fa5s.undo", "Returns"),
                ("price_check", "fa5s.tag", "Price Check"),
                ("settings", "fa5s.cog", "Settings")
            ]
            if user.get('is_super_admin'):
                menus.insert(-1, ("credentials", "fa5s.key", "Credentials"))
        else: # PHARMACY
            menus = [
                ("pharm_dashboard", "fa5s.th-large", "Dashboard"),
                ("pharm_finance", "fa5s.chart-pie", "Finance"),
                ("pharm_inventory", "fa5s.boxes", "Inventory"),
                ("pharm_sales", "fa5s.file-invoice-dollar", "Sales"),
                ("pharm_customers", "fa5s.users", "Customers"),
                ("pharm_suppliers", "fa5s.truck", "Suppliers"),
                ("pharm_loans", "fa5s.hand-holding-usd", "Loans"),
                ("pharm_reports", "fa5s.chart-line", "Reports"),
                ("pharm_price_check", "fa5s.tag", "Price Check"),
                ("pharm_returns", "fa5s.undo", "Returns"),
                ("pharm_users", "fa5s.user-nurse", "Staff Mgmt"),
                ("pharm_settings", "fa5s.cog", "Ph-Settings")
            ]
            if user.get('is_super_admin'):
                menus.append(("pharm_credentials", "fa5s.key", "Credentials"))

        for key, icon, label in menus:
            check_key = key.replace("pharm_", "pharmacy_") if mode == "PHARMACY" else key
            if check_key == "dashboard": check_key = "reports"
            
            has_perm = '*' in permissions or check_key in permissions or f"{check_key}_view" in permissions
            if not has_perm:
                continue
                
            btn = QPushButton(f"  {label}")
            btn.setIcon(qta.icon(icon, color="#a5b4fc"))
            btn.setObjectName("menu_button")
            btn.setProperty("view_key", key) # Durable ID
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self.switch_view(k))
            
            buttons_layout.addWidget(btn)
            self.menu_buttons.append(btn)
            self.original_button_texts[btn] = f"  {label}"

        buttons_layout.addStretch()
        scroll_area.setWidget(buttons_container)
        sidebar_layout.addWidget(scroll_area)
        
        # Profile section at bottom
        self.profile_frame = QFrame()
        self.profile_frame.setStyleSheet(f"border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;")
        prof_lay = QHBoxLayout(self.profile_frame)
        
        self.user_name_lbl = QLabel(user.get('username', 'User').capitalize())
        self.user_name_lbl.setStyleSheet("color: white; font-weight: bold; border: none;")
        prof_lay.addWidget(self.user_name_lbl)
        prof_lay.addStretch()
        
        logout_btn = QPushButton(qta.icon("fa5s.power-off", color="#f87171"), "")
        logout_btn.setStyleSheet("background: transparent; border: none;")
        logout_btn.clicked.connect(self.handle_logout)
        prof_lay.addWidget(logout_btn)
        
        sidebar_layout.addWidget(self.profile_frame)
        layout.addWidget(self.sidebar)
        
        # Content Area
        self.content_container = QFrame()
        content_lay = QVBoxLayout(self.content_container)
        content_lay.setContentsMargins(30, 30, 30, 30)
        
        self.header_title = QLabel("Dashboard")
        self.header_title.setStyleSheet("font-size: 26px; font-weight: bold; color: #1e293b;")
        content_lay.addWidget(self.header_title)
        
        self.view_stack = QStackedWidget()
        content_lay.addWidget(self.view_stack)
        
        layout.addWidget(self.content_container)
        self.central_widget.addWidget(self.main_app_widget)
        self.central_widget.setCurrentWidget(self.main_app_widget)
        
        # Initialize Pharmacy Hub if in pharmacy mode
        if mode == "PHARMACY":
            from src.ui.views.pharmacy.pharmacy_hub import PharmacyHub
            self.pharmacy_hub = PharmacyHub()
            self.view_stack.addWidget(self.pharmacy_hub)

        # Default View
        default = "pharm_dashboard" if mode == "PHARMACY" else "dashboard"
        self.switch_view(default)


    def toggle_sidebar(self):
        is_collapsed = self.sidebar.width() < 100
        if is_collapsed:
            # Expand
            self.sidebar.setFixedWidth(260)
            self.logo_text.show()
            if hasattr(self, 'user_name_lbl'): self.user_name_lbl.show()
            for btn in self.menu_buttons:
                if btn in self.original_button_texts:
                    btn.setText(self.original_button_texts[btn])
                btn.setToolTip("")
                btn.setStyleSheet(btn.styleSheet().replace("text-align: center;", "text-align: left;"))
        else:
            # Collapse
            self.sidebar.setFixedWidth(70)
            self.logo_text.hide()
            if hasattr(self, 'user_name_lbl'): self.user_name_lbl.hide()
            for btn in self.menu_buttons:
                btn.setToolTip(btn.text().strip())
                btn.setText("") # Hide text, icon remains centered
                btn.setStyleSheet(btn.styleSheet().replace("text-align: left;", "text-align: center;"))

    def handle_super_admin_click(self):
        user_auth = PharmacyAuth if self.business_mode == "PHARMACY" else Auth
        user = user_auth.get_current_user()
        if user and (user.get('is_super_admin') or user.get('role') == 'Manager'):
            self.switch_view("super_admin" if self.business_mode == "STORE" else "pharm_users")
        else:
            QMessageBox.critical(self, "Access Denied", "Only Admin or Manager can access this panel.")

    def switch_view(self, view_key):
        # Determine Auth Class
        user_auth = PharmacyAuth if self.business_mode == "PHARMACY" else Auth
        
        # Security Check
        user = user_auth.get_current_user()
        permissions = user_auth.get_user_permissions(user)
        
        # Determine permission key
        perm_key = view_key
        if view_key.startswith("pharm_"):
            perm_key = view_key.replace("pharm_", "pharmacy_")
        elif view_key == "pharmacy":
            perm_key = "pharmacy_dashboard"
            
        role = user.get('role', '').lower() if user else ""
        is_admin = user and ("admin" in role or "manager" in role or user.get('is_super_admin'))
        has_perm = is_admin or "*" in permissions or perm_key in permissions or f"{perm_key}_view" in permissions
        
        # Exceptions for common views
        if view_key in ["dashboard", "pharm_dashboard", "price_check", "pharm_price_check", "settings"]:
             has_perm = True
             
        if not has_perm:
            QMessageBox.critical(self, "Security", "You do not have permission to access this module.")
            return

        # Special handling: Single-click on "pharmacy" button should load dashboard
        if view_key == "pharmacy":
            view_key = "pharm_dashboard"
        
        # Update header title
        raw_key = view_key
        if view_key.startswith("pharm_"):
            raw_key = view_key.replace("pharm_", "Pharmacy ")
        
        display_name = lang_manager.get(raw_key) if lang_manager.get(raw_key) else raw_key.replace('_', ' ').title()
        self.header_title.setText(display_name)
        
        # UI Tweak: Full Bleed for Dashboard
        # Remove margins and hide default header for Dashboard views to allow
        # the dashboard's internal background to fill the screen.
        is_dashboard = (view_key == "dashboard" or view_key == "pharm_dashboard" or view_key == "pharmacy")
        layout = self.content_container.layout()
        if is_dashboard:
            layout.setContentsMargins(0, 0, 0, 0)
            self.header_title.hide()
        else:
            layout.setContentsMargins(5, 5, 5, 5)
            self.header_title.show()
        
        # Update button states
        for btn in self.menu_buttons:
            btn_key = btn.property("view_key")
            # Highlight if key matches or if it's the dashboard redirect
            is_active = (btn_key == view_key)
            if view_key == "pharmacy" and btn_key == "pharm_dashboard":
                is_active = True
            btn.setChecked(is_active)
            
        # Clean up old view
        if self.view_stack.count() > 0:
            current = self.view_stack.currentWidget()
            if current:
                # Requirement: Do not delete PharmacyHub if we are staying in pharmacy
                if isinstance(current, PharmacyHub) and view_key.startswith("pharm"):
                    pass # Keep it
                else:
                    self.view_stack.removeWidget(current)
                    if current != getattr(self, 'pharmacy_hub', None):
                        current.deleteLater()
            
        # Create and add new view
        if view_key == "dashboard":
            self.current_view = DashboardView()
            self.current_view.navigation_requested.connect(self.switch_view)
        elif view_key == "finance":
            self.current_view = FinanceView()
        elif view_key == "users":
            self.current_view = UserManagementView()
        elif view_key in ["sales"]:
            self.current_view = SalesView()
        elif view_key == "inventory":
            self.current_view = InventoryView()
        elif view_key == "customers":
            self.current_view = CustomerView()
        elif view_key == "reports":
            self.current_view = ReportsView()
        elif view_key == "settings":
            self.current_view = SettingsView()
        elif view_key == "low_stock":
            self.current_view = StockAlertView()
        elif view_key == "price_check":
            self.current_view = PriceCheckView()
            # Requirement: Visible for 5 seconds
            # Actually, the view itself handles the 5s timer for the result.
            # If the user means the WHOLE WINDOW, we handle it in PriceCheckView by emitting a signal.
            # if hasattr(self.current_view, 'finished'):
            #     self.current_view.finished.connect(lambda: self.switch_view("dashboard"))
        elif view_key == "returns":
            self.current_view = ReturnsView()
        elif view_key == "suppliers":
            self.current_view = SupplierView()
        elif view_key == "loans":
            self.current_view = LoanView()
        elif view_key.startswith("pharm"):
             if not hasattr(self, 'pharmacy_hub'):
                 self.pharmacy_hub = PharmacyHub()
                 # Wire up internal dashboard to main window navigation
                 self.pharmacy_hub.navigation_requested.connect(lambda k: self.switch_view(f"pharm_{k}"))
             
             self.current_view = self.pharmacy_hub
             # Tell hub which module to show
             if view_key == "pharmacy":
                 sub_key = "pharmacy_dashboard"
             elif view_key.startswith("pharm_"):
                 # if it's pharm_dashboard -> pharmacy_dashboard
                 # if it's pharm_pharmacy_dashboard -> pharmacy_dashboard
                 stripped = view_key.replace("pharm_", "")
                 sub_key = stripped if stripped.startswith("pharmacy_") else f"pharmacy_{stripped}"
             else:
                 sub_key = view_key if view_key.startswith("pharmacy_") else f"pharmacy_{view_key}"
             
             self.pharmacy_hub.switch_module(sub_key)
             
             # Also update sub-button checked state
             if hasattr(self, 'pharm_sub_btns'):
                for sbtn in self.pharm_sub_btns:
                    # sbtn text is e.g. "Ph-Dashboard"
                    # sub_key is e.g. "pharmacy_dashboard"
                    clean_sbtn_text = sbtn.text().strip().lower().replace("ph-", "pharmacy_")
                    sbtn.setChecked(clean_sbtn_text == sub_key)
             
             if self.view_stack.indexOf(self.current_view) == -1:
                 self.view_stack.addWidget(self.current_view)
             self.view_stack.setCurrentWidget(self.current_view)
             
             # Auto-refresh target pharmacy view if it's not the sales view
             if sub_key != "pharmacy_sales" and hasattr(self.pharmacy_hub, 'views'):
                 target_ph_view = self.pharmacy_hub.views.get(sub_key)
                 if target_ph_view:
                     for method_name in ['load_data', 'load_inventory', 'load_users', 'load_customers', 'load_suppliers', 'load_loans', 'refresh']:
                         method = getattr(target_ph_view, method_name, None)
                         if method and callable(method):
                             method()
                             break

             return # Skip standard create/add logic below
        elif view_key == "super_admin":
            user = user_auth.get_current_user()
            if user and user.get('is_super_admin'):
                self.current_view = SuperAdminView()
            else:
                 # Should not happen via switch_view if button is secured, but as failsafe:
                 self.current_view = QLabel("Access Denied")
                 self.current_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif view_key in ["credentials", "pharm_credentials"]:
            user = user_auth.get_current_user()
            if user and user.get('is_super_admin'):
                from src.ui.views.credentials_view import CredentialsView
                self.current_view = CredentialsView()
            else:
                self.current_view = QLabel("Access Denied")
                self.current_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            # Placeholder for others
            self.current_view = QLabel(f"Welcome to {view_key.capitalize()} View")
            self.current_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.current_view.setStyleSheet("font-size: 24px; color: #2f3640;")
            
        self.view_stack.addWidget(self.current_view)
        self.view_stack.setCurrentWidget(self.current_view)

    def handle_logout(self):
        from src.core.pharmacy_auth import PharmacyAuth
        if self.business_mode == "PHARMACY":
            PharmacyAuth.logout()
        else:
            Auth.logout()
        
        if hasattr(self, "pharmacy_hub"):
            self.pharmacy_hub = None
        self.login_view.stack.setCurrentIndex(0)
        self.central_widget.setCurrentWidget(self.login_view)