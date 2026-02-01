from PyQt6.QtCore import QObject, pyqtSignal
import json
import os

class Localization(QObject):
    language_changed = pyqtSignal(str)
    _instance = None
    
    def __init__(self):
        super().__init__()
        self.current_lang = "en"
        self.translations = {
            "en": {
                "login": "Login",
                "username": "Username",
                "password": "Password",
                "sales": "Sales",
                "inventory": "Inventory",
                "customers": "Customers",
                "suppliers": "Suppliers",
                "loans": "Loans",
                "reports": "Reports",
                "settings": "Settings",
                "logout": "Logout",
                "product_name": "Product Name",
                "barcode": "Barcode",
                "price": "Price",
                "quantity": "Quantity",
                "total": "Total",
                "add": "Add",
                "edit": "Edit",
                "delete": "Delete",
                "save": "Save",
                "cancel": "Cancel",
                "search": "Search",
                "print": "Print",
                "checkout": "Checkout",
                "discount": "Discount",
                "cash": "Cash",
                "credit": "Credit",
                "back": "Back",
                "admin": "Admin",
                "cashier": "Cashier",
                "low_stock": "Low Stock",
                "price_check": "Price Check",
                "returns": "Returns",
                "pharmacy": "Pharmacy",
                "dashboard": "Dashboard",
                "finance": "Finance",
                "users": "Users",
                "pharm_dashboard": "Ph-Dashboard",
                "pharm_finance": "Ph-Finance",
                "pharm_inventory": "Ph-Inventory",
                "pharm_sales": "Ph-Sales",
                "pharm_customers": "Ph-Customers",
                "pharm_suppliers": "Ph-Suppliers",
                "pharm_loans": "Ph-Loan",
                "pharm_reports": "Ph-Reports",
                "pharm_price_check": "Ph-PriceCheck",
                "pharm_returns": "Ph-Returns",
                "pharm_users": "Ph-Users"
            },
            "ps": {
                "login": "ننووتل",
                "username": "کارن نوم",
                "password": "پټنوم",
                "sales": "پلور",
                "inventory": "ګودام",
                "customers": "پېرودونکي",
                "suppliers": "برابروونکي",
                "loans": "پورونه",
                "reports": "راپورونه",
                "settings": "تنظیمات",
                "logout": "وتل",
                "product_name": "د توکي نوم",
                "barcode": "بارکوډ",
                "price": "بیه",
                "quantity": "شمېر",
                "total": "ټول",
                "add": "زیاتول",
                "edit": "سمون",
                "delete": "له منځه وړل",
                "save": "ساتل",
                "cancel": "بندول",
                "search": "لټون",
                "print": "چاپ",
                "checkout": "تادیه",
                "discount": "تخفیف",
                "cash": "نغدې",
                "credit": "پور",
                "back": "شاته",
                "admin": "اډمین",
                "cashier": "کاشیر",
                "low_stock": "کم ذخیره",
                "price_check": "نرخ کتل",
                "returns": "ګرځول شوي توکي",
                "pharmacy": "درملتون",
                "dashboard": "ډشبورډ",
                "finance": "مالي",
                "users": "کارونکي",
                "pharm_dashboard": "ډشبورډ",
                "pharm_finance": "مالي",
                "pharm_inventory": "ګودام",
                "pharm_sales": "پلور",
                "pharm_customers": "پېرودونکي",
                "pharm_suppliers": "برابروونکي",
                "pharm_loans": "قرضې",
                "pharm_reports": "راپورونه",
                "pharm_price_check": "نرخ",
                "pharm_returns": "ګرځول",
                "pharm_users": "کارونکي"
            },
            "dr": {
                "login": "ورود",
                "username": "نام کاربری",
                "password": "رمز عبور",
                "sales": "فروش",
                "inventory": "موجودی",
                "customers": "مشتریان",
                "suppliers": "تامین کنندگان",
                "loans": "قرضه‌ها",
                "reports": "گزارش‌ها",
                "settings": "تنظیمات",
                "logout": "خروج",
                "product_name": "نام محصول",
                "barcode": "بارکد",
                "price": "قیمت",
                "quantity": "تعداد",
                "total": "مجموع",
                "add": "افزودن",
                "edit": "ویرایش",
                "delete": "حذف",
                "save": "ذخیره",
                "cancel": "لغو",
                "search": "جستجو",
                "print": "چاپ",
                "checkout": "پرداخت",
                "discount": "تخفیف",
                "cash": "نقد",
                "credit": "قرضه",
                "back": "بازگشت",
                "admin": "ادمین",
                "cashier": "کاشیر",
                "low_stock": "کمبود موجودی",
                "price_check": "بررسی قیمت",
                "returns": "کالاهای مرجوعی",
                "pharmacy": "داروخانه",
                "dashboard": "داشبورد",
                "finance": "مالی",
                "users": "کاربران",
                "pharm_dashboard": "داشبورد",
                "pharm_finance": "مالی",
                "pharm_inventory": "موجودی",
                "pharm_sales": "فروش",
                "pharm_customers": "مشتریان",
                "pharm_suppliers": "تامين کنندگان",
                "pharm_loans": "قرضه ها",
                "pharm_reports": "گزارش‌ها",
                "pharm_price_check": "نرخ",
                "pharm_returns": "مرجوعی",
                "pharm_users": "کاربران"
            }
        }

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_language(self, lang):
        if lang in self.translations:
            self.current_lang = lang
            self.language_changed.emit(lang)

    def get(self, key):
        return self.translations.get(self.current_lang, self.translations["en"]).get(key, key)

    def is_rtl(self):
        return self.current_lang in ["ps", "dr"]

    def localize_digits(self, text):
        if self.current_lang == "en":
            return str(text)
        
        digits_map = {
            '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
            '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
        }
        
        return "".join(digits_map.get(c, c) for c in str(text))

lang_manager = Localization.get_instance()
