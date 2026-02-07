import sqlite3
import os
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_path=None):
        import sys
        
        # Determine Writable Base Path
        if getattr(sys, 'frozen', False):
            # Production Mode: Use OS-specific writable data directories
            import platform
            app_name = "FaqiriTech"
            if platform.system() == "Darwin":
                # macOS: ~/Library/Application Support/FaqiriTech
                self.base_dir = os.path.expanduser(f"~/Library/Application Support/{app_name}")
            elif platform.system() == "Windows":
                # Windows: %APPDATA%/FaqiriTech
                self.base_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), app_name)
            else:
                # Linux: ~/.local/share/FaqiriTech
                self.base_dir = os.path.expanduser(f"~/.local/share/{app_name}")
        else:
            # Dev Mode: Root of project
            self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        if not os.path.exists(self.base_dir):
            try: os.makedirs(self.base_dir, exist_ok=True)
            except: pass

        # We now have two separate database files
        self.store_db = os.path.join(self.base_dir, "faqiritech_store.db")
        self.pharmacy_db = os.path.join(self.base_dir, "faqiritech_pharmacy.db")
        
        # Override if path provided
        if db_path:
            self.store_db = db_path
            self.pharmacy_db = db_path.replace(".db", "_pharmacy.db")

        self.get_connection = self.get_store_connection # Alias for backward compatibility if needed

        self._create_store_tables()
        self._create_pharmacy_tables()
        self.seed_initial_data()
        self._enable_wal_mode()
        self._auto_backup()

    def get_store_connection(self):
        """Returns connection to General Store database (Main)."""
        conn = sqlite3.connect(self.store_db)
        conn.row_factory = sqlite3.Row
        return conn

    def _auto_backup(self):
        """Creates timestamped auto-backups for both databases."""
        import shutil
        # Backup path relative to base directory
        backup_dir = os.path.join(self.base_dir, "Backup", "auto")
        if not os.path.exists(backup_dir):
            try: os.makedirs(backup_dir)
            except: pass
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        for db in [self.store_db, self.pharmacy_db]:
            if os.path.exists(db):
                backup_path = os.path.join(backup_dir, f"{os.path.basename(db)}_{ts}.db")
                try:
                    shutil.copy2(db, backup_path)
                except Exception as e:
                    print(f"Auto-backup failed for {db}: {e}")
        
        # Cleanup: keep last 5 backups per DB
        try:
            backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir)])
            if len(backups) > 10: # 5 per database
                for b in backups[:-10]:
                    os.remove(b)
        except: pass

    def get_connection(self):
        """Returns connection to General Store database (Main)."""
        self._check_thread_safety()
        conn = sqlite3.connect(self.store_db, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def get_pharmacy_connection(self):
        """Returns connection to Pharmacy database (Isolated)."""
        self._check_thread_safety()
        conn = sqlite3.connect(self.pharmacy_db, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _check_thread_safety(self):
        """Logs a warning if DB is accessed from Main Thread after initialization."""
        import threading
        from PyQt6.QtWidgets import QApplication
        if threading.current_thread() == threading.main_thread():
            if QApplication.instance():
                # Avoid flooding logs by only warning once per minute per session
                now = datetime.now()
                if not hasattr(self, '_last_thread_warn') or (now - self._last_thread_warn).seconds > 60:
                    self._last_thread_warn = now
                    print(f"[WARNING] Database accessed from MAIN UI THREAD. This may cause GUI freezes. Use task_manager instead.")

    def _enable_wal_mode(self):
        for db in [self.store_db, self.pharmacy_db]:
            try:
                conn = sqlite3.connect(db)
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.close()
            except: pass

    def _create_store_tables(self):
        """Schema for General Store Database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Common / Core Tables
            cursor.execute('CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, description TEXT)')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
                    role_id INTEGER, is_active INTEGER DEFAULT 1, profile_picture TEXT, is_super_admin INTEGER DEFAULT 0,
                    valid_until TIMESTAMP, title TEXT, permissions TEXT, base_salary REAL DEFAULT 0,
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                )
            ''')
            
            cursor.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name_en TEXT, name_ps TEXT, name_dr TEXT, parent_id INTEGER, FOREIGN KEY (parent_id) REFERENCES categories(id))')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, barcode TEXT UNIQUE NOT NULL, sku TEXT, name_en TEXT NOT NULL,
                    name_ps TEXT, name_dr TEXT, brand TEXT, category_id INTEGER, sub_category TEXT,
                    product_type TEXT DEFAULT 'Simple', cost_price REAL DEFAULT 0, sale_price REAL DEFAULT 0,
                    wholesale_price REAL DEFAULT 0, tax_rate REAL DEFAULT 0, unit TEXT, min_stock REAL DEFAULT 5,
                    max_stock REAL DEFAULT 100, expiry_date DATE, mfg_date DATE, batch_number TEXT, serial_number TEXT,
                    supplier_id INTEGER, supplier_sku TEXT, shelf_location TEXT, allow_negative_stock INTEGER DEFAULT 0,
                    returnable INTEGER DEFAULT 1, track_inventory INTEGER DEFAULT 1, allow_pos_price_change INTEGER DEFAULT 0,
                    allow_zero_price INTEGER DEFAULT 0, image_path TEXT, internal_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER, last_updated_by INTEGER, is_active INTEGER DEFAULT 1, scope TEXT DEFAULT 'SHOP',
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
            ''')
            
            cursor.execute('CREATE TABLE IF NOT EXISTS inventory (product_id INTEGER PRIMARY KEY, quantity REAL DEFAULT 0, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (product_id) REFERENCES products(id))')
            cursor.execute('CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, contact TEXT, balance REAL DEFAULT 0, company_name TEXT)')
            cursor.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name_en TEXT NOT NULL, name_ps TEXT, name_dr TEXT, phone TEXT, loan_enabled INTEGER DEFAULT 0, loan_limit REAL DEFAULT 0, balance REAL DEFAULT 0, is_active INTEGER DEFAULT 1, home_address TEXT, photo TEXT, id_card_photo TEXT, scope TEXT DEFAULT 'SHOP')")
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_number TEXT UNIQUE NOT NULL, user_id INTEGER,
                    customer_id INTEGER, total_amount REAL NOT NULL, payment_type TEXT DEFAULT 'CASH',
                    sync_status INTEGER DEFAULT 0, uuid TEXT UNIQUE, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, scope TEXT DEFAULT 'SHOP',
                    FOREIGN KEY (user_id) REFERENCES users(id), FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER, product_id INTEGER, barcode TEXT,
                    product_name TEXT, quantity REAL NOT NULL, unit_price REAL NOT NULL, total_price REAL NOT NULL,
                    sync_status INTEGER DEFAULT 0, uuid TEXT UNIQUE, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scope TEXT DEFAULT 'SHOP', FOREIGN KEY (sale_id) REFERENCES sales(id), FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, sale_id INTEGER, loan_amount REAL,
                    paid_amount REAL DEFAULT 0, due_date DATE, status TEXT DEFAULT 'PENDING', customer_phone TEXT,
                    customer_photo TEXT, id_photo TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scope TEXT DEFAULT 'SHOP', FOREIGN KEY (customer_id) REFERENCES customers(id), FOREIGN KEY (sale_id) REFERENCES sales(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales_returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER, user_id INTEGER, reason TEXT,
                    refund_amount REAL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scope TEXT DEFAULT 'SHOP', FOREIGN KEY (sale_id) REFERENCES sales(id), FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS return_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, return_id INTEGER, product_id INTEGER,
                    quantity REAL NOT NULL, refund_price REAL NOT NULL, FOREIGN KEY (return_id) REFERENCES sales_returns(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, opening_cash REAL NOT NULL,
                    closing_cash REAL, started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, ended_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cash_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, shift_id INTEGER, type TEXT CHECK(type IN ('IN', 'OUT')),
                    amount REAL NOT NULL, reason TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (shift_id) REFERENCES shifts(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT NOT NULL,
                    table_name TEXT, record_id INTEGER, details TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            cursor.execute('CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)')
            # Set to 2023 for reactivation as requested (Point 4: Reactivation Date)
            back_date = "2023-01-01"
            cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('contract_end', ?)", (back_date,))
            cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('security_key', 'faqiri2026')")
            cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('whatsapp_number', '')")

            cursor.execute('CREATE TABLE IF NOT EXISTS company_info (id INTEGER PRIMARY KEY DEFAULT 1, name TEXT, address TEXT, phone TEXT, email TEXT)')
            cursor.execute("INSERT OR IGNORE INTO company_info (id, name, address, phone, email) VALUES (1, 'Kabul City Center', 'Main Road, Kabul', '0700000000', 'info@mall.af')")

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INTEGER PRIMARY KEY DEFAULT 1, is_active INTEGER DEFAULT 1, activation_key TEXT,
                    mode TEXT DEFAULT 'OFFLINE', server_url TEXT, valid_until TIMESTAMP, last_sync TIMESTAMP
                )
            ''')
            cursor.execute("INSERT OR IGNORE INTO system_settings (id, is_active, mode, valid_until) VALUES (1, 1, 'OFFLINE', ?)", (back_date,))

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, category TEXT NOT NULL CHECK(category IN ('Salary', 'Petty Cash', 'Other')),
                    amount REAL NOT NULL, description TEXT, expense_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, scope TEXT DEFAULT 'SHOP',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, amount REAL NOT NULL,
                    payment_method TEXT DEFAULT 'CASH', reference_number TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            ''')

            # Performance Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_pid ON inventory(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_cust ON sales(customer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date)")
            
            conn.commit()

    def _create_pharmacy_tables(self):
        """Schema for Isolated Pharmacy Database."""
        print(f"[DEBUG] Initializing Pharmacy Database at: {self.pharmacy_db}")
        try:
            with self.get_pharmacy_connection() as conn:
                cursor = conn.cursor()
            
            # Pharmacy specific tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
                    title TEXT, role TEXT DEFAULT 'Pharmacist', permissions TEXT, is_active INTEGER DEFAULT 1,
                    is_super_admin INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Migration: Add created_by to pharmacy_users if missing
            try:
                cursor.execute("ALTER TABLE pharmacy_users ADD COLUMN created_by INTEGER")
            except: pass
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, barcode TEXT UNIQUE NOT NULL, name_en TEXT NOT NULL,
                    generic_name TEXT, brand TEXT, size TEXT, cost_price REAL DEFAULT 0, sale_price REAL DEFAULT 0,
                    min_stock REAL DEFAULT 10, shelf_location TEXT, supplier_id INTEGER, description TEXT,
                    uom TEXT DEFAULT 'Box', is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, batch_number TEXT NOT NULL,
                    expiry_date DATE NOT NULL, quantity REAL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES pharmacy_products(id), UNIQUE(product_id, batch_number)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_number TEXT UNIQUE NOT NULL, user_id INTEGER,
                    customer_id INTEGER, total_amount REAL NOT NULL, gross_amount REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0, net_amount REAL DEFAULT 0, payment_type TEXT DEFAULT 'CASH',
                    is_synced INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER, product_id INTEGER, product_name TEXT,
                    batch_number TEXT, expiry_date DATE, quantity REAL NOT NULL, unit_price REAL NOT NULL,
                    total_price REAL NOT NULL, cost_price_at_sale REAL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sale_id) REFERENCES pharmacy_sales(id), FOREIGN KEY (product_id) REFERENCES pharmacy_products(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT, loan_enabled INTEGER DEFAULT 0,
                    loan_limit REAL DEFAULT 0, balance REAL DEFAULT 0, is_active INTEGER DEFAULT 1,
                    address TEXT, kyc_photo TEXT, kyc_id_card TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, contact TEXT, balance REAL DEFAULT 0,
                    company_name TEXT, address TEXT, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Migration: Add address to pharmacy_suppliers if missing
            try:
                cursor.execute("ALTER TABLE pharmacy_suppliers ADD COLUMN address TEXT")
            except: pass

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, sale_id INTEGER, loan_amount REAL,
                    total_amount REAL DEFAULT 0, paid_amount REAL DEFAULT 0, balance REAL DEFAULT 0,
                    due_date DATE, status TEXT DEFAULT 'PENDING', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES pharmacy_customers(id), FOREIGN KEY (sale_id) REFERENCES pharmacy_sales(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT CHECK(category IN ('Salary', 'Petty Cash', 'Other')),
                    amount REAL NOT NULL, description TEXT, expense_date DATE DEFAULT CURRENT_DATE,
                    created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER, customer_id INTEGER, loan_id INTEGER,
                    payment_method TEXT, amount REAL, transaction_ref TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_employee_salary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL NOT NULL,
                    salary_type TEXT, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, original_sale_id INTEGER, refund_amount REAL,
                    refund_type TEXT DEFAULT 'ACCOUNT',
                    reason TEXT, user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (original_sale_id) REFERENCES pharmacy_sales(id)
                )
            ''')
            # Migration: Add refund_type to pharmacy_returns if missing
            try:
                cursor.execute("ALTER TABLE pharmacy_returns ADD COLUMN refund_type TEXT DEFAULT 'ACCOUNT'")
            except: pass

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_return_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, return_id INTEGER, 
                    sale_item_id INTEGER, product_id INTEGER,
                    quantity REAL NOT NULL, unit_price REAL NOT NULL, action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (return_id) REFERENCES pharmacy_returns(id),
                    FOREIGN KEY (product_id) REFERENCES pharmacy_products(id)
                )
            ''')
            # Migration: Add sale_item_id to pharmacy_return_items if missing
            try:
                cursor.execute("ALTER TABLE pharmacy_return_items ADD COLUMN sale_item_id INTEGER")
            except: pass

            # Table to track replacement items when action is REPLACEMENT
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_replacement_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_item_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name TEXT,
                    quantity REAL NOT NULL,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (return_item_id) REFERENCES pharmacy_return_items(id),
                    FOREIGN KEY (product_id) REFERENCES pharmacy_products(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacy_month_close (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, month_str TEXT UNIQUE, total_sold_items REAL,
                    total_sales REAL, total_profit REAL, total_petty_cash REAL, total_salaries REAL,
                    net_profit REAL, closed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, closed_by INTEGER
                )
            ''')
            
            # Duplicated app/system settings for Pharmacy logic independence
            cursor.execute('CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)')
            cursor.execute("CREATE TABLE IF NOT EXISTS system_settings (id INTEGER PRIMARY KEY DEFAULT 1, is_active INTEGER DEFAULT 1, activation_key TEXT, mode TEXT DEFAULT 'OFFLINE', valid_until TIMESTAMP)")
            
            back_date = "2023-01-01"
            cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('contract_end', ?)", (back_date,))
            cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('whatsapp_number', '')")

            cursor.execute('CREATE TABLE IF NOT EXISTS pharmacy_info (id INTEGER PRIMARY KEY DEFAULT 1, name TEXT, address TEXT, phone TEXT, email TEXT)')
            cursor.execute("INSERT OR IGNORE INTO pharmacy_info (id, name, address, phone, email) VALUES (1, 'FaqiriTech Pharmacy', 'Main Road, Kabul', '0700000000', 'pharmacy@faqiritech.com')")
            cursor.execute("INSERT OR IGNORE INTO system_settings (id, is_active, mode, valid_until) VALUES (1, 1, 'OFFLINE', ?)", (back_date,))

            # Performance Indexes for Pharmacy
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ph_prod_bc ON pharmacy_products(barcode)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ph_inv_pid ON pharmacy_inventory(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ph_sales_date ON pharmacy_sales(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ph_sale_items_sid ON pharmacy_sale_items(sale_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ph_payments_sid ON pharmacy_payments(sale_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ph_payments_date ON pharmacy_payments(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ph_returns_date ON pharmacy_returns(created_at)")

            conn.commit()
        except Exception as e:
            print(f"[CRITICAL] Pharmacy DB Init Error: {e}")
            import traceback
            traceback.print_exc()

    def seed_initial_data(self):
        # 1. Main Store Data
        with self.get_connection() as conn:
            cursor = conn.cursor()
            roles = [('SuperAdmin', 'System Owner'), ('Admin', 'Biz Admin'), ('Manager', 'Stock Mgr'), ('Salesman', 'Cashier'), ('PriceChecker', 'Display')]
            for name, desc in roles:
                cursor.execute("INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)", (name, desc))
            cursor.execute("INSERT OR IGNORE INTO customers (id, name_en) VALUES (1, 'Walking Customer')")
            conn.commit()
            
        # 2. Pharmacy Data
        with self.get_pharmacy_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pharmacy_customers WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO pharmacy_customers (id, name) VALUES (1, 'Pharmacy Walking Customer')")
            conn.commit()

    def cleanup_old_data(self):
        # Cleanup both
        for db_func in [self.get_connection, self.get_pharmacy_connection]:
            try:
                with db_func() as conn:
                    cursor = conn.cursor()
                    cutoff = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
                    # This is generic, might fail on some tables if they don't exist in one DB
                    for table in ['sales', 'audit_logs', 'pharmacy_sales']:
                        try: cursor.execute(f"DELETE FROM {table} WHERE created_at < ?", (cutoff,))
                        except: pass
                    conn.commit()
            except: pass

    def run_maintenance(self):
        """Runs heavy DB tasks in a background thread to prevent UI freezing."""
        import threading
        def _maintenance():
            try:
                self._auto_backup()
                self.seed_initial_data()
                self.cleanup_old_data()
            except Exception as e:
                print(f"Background maintenance error: {e}")
        
        m_thread = threading.Thread(target=_maintenance, daemon=True)
        m_thread.start()

db_manager = DatabaseManager()
# Trigger maintenance in background so GUI doesn't hang at splash/login
db_manager.run_maintenance()