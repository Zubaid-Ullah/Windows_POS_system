import bcrypt
from src.database.db_manager import db_manager
from src.utils.logger import log_info, log_error

class Auth:
    _current_user = None

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def check_password(password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @classmethod
    def login(cls, username, password):
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, r.name as role_name 
                FROM users u 
                JOIN roles r ON u.role_id = r.id 
                WHERE u.username = ? AND u.is_active = 1
            """, (username,))
            user = cursor.fetchone()
            
            try:
                if user and cls.check_password(password, user['password_hash']):
                    cls._current_user = dict(user)
                    # Log the audit
                    cursor.execute("INSERT INTO audit_logs (user_id, action, table_name, record_id, details) VALUES (?, ?, ?, ?, ?)",
                                 (user['id'], 'LOGIN', 'users', user['id'], f'User {username} logged in'))
                    conn.commit()
                    log_info(f"User {username} logged in successfully")
                    return True
            except Exception as e:
                log_error(f"Login error for {username}: {e}")
            
            log_info(f"Failed login attempt for user: {username}")
            return False

    @classmethod
    def logout(cls):
        if cls._current_user:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO audit_logs (user_id, action, table_name, record_id, details) VALUES (?, ?, ?, ?, ?)",
                             (cls._current_user['id'], 'LOGOUT', 'users', cls._current_user['id'], f'User {cls._current_user["username"]} logged out'))
                conn.commit()
                log_info(f"User {cls._current_user['username']} logged out")
        cls._current_user = None

    @classmethod
    def get_current_user(cls):
        return cls._current_user
        
    @classmethod
    def set_current_user(cls, user_data):
        cls._current_user = user_data

    @staticmethod
    def create_user(username, password, role_name, profile_picture=None):
        hashed = Auth.hash_password(password)
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Find role_id
                cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
                role = cursor.fetchone()
                if not role:
                    print(f"Role {role_name} not found")
                    return False
                
                cursor.execute("INSERT INTO users (username, password_hash, role_id, profile_picture) VALUES (?, ?, ?, ?)",
                             (username, hashed, role['id'], profile_picture))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error creating user: {e}")
                return False

    @staticmethod
    def get_user_permissions(user):
        if not user: return []
        # 1. Check for specific user permissions override
        if user.get('permissions'):
            import json
            try:
                # Try parsing as JSON list first
                perms = json.loads(user['permissions'])
                if isinstance(perms, list):
                    if '*' in perms: return ['*']
                    
                    # Grant all pharmacy_* perms if 'pharmacy' is present for backward compatibility
                    if 'pharmacy' in perms:
                        pharm_perms = [
                            'pharmacy_dashboard', 'pharmacy_sales', 'pharmacy_inventory', 
                            'pharmacy_customers', 'pharmacy_suppliers', 'pharmacy_loans', 
                            'pharmacy_reports', 'pharmacy_finance', 'pharmacy_price_check', 
                            'pharmacy_returns', 'pharmacy_users'
                        ]
                        for p in pharm_perms:
                            if p not in perms: perms.append(p)
                            
                    return perms
            except:
                # Fallback to comma-separated string
                perms = [p.strip() for p in user['permissions'].split(',') if p.strip()]
                if perms:
                    if '*' in perms: return ['*']
                    
                    # Grant all pharmacy_* perms if 'pharmacy' is present for backward compatibility
                    if 'pharmacy' in perms:
                        pharm_perms = [
                            'pharmacy_dashboard', 'pharmacy_sales', 'pharmacy_inventory', 
                            'pharmacy_customers', 'pharmacy_suppliers', 'pharmacy_loans', 
                            'pharmacy_reports', 'pharmacy_finance', 'pharmacy_price_check', 
                            'pharmacy_returns', 'pharmacy_users'
                        ]
                        for p in pharm_perms:
                            if p not in perms: perms.append(p)
                            
                    return perms
        
        # 2. Fallback to Role Defaults
        role_name = user.get('role_name', '')
        permissions = {
            'SuperAdmin': ['*'], 
            'Admin': ['sales', 'inventory', 'customers', 'suppliers', 'loans', 'reports', 'finance', 'settings', 'low_stock', 'price_check', 'returns', 'pharmacy', 
                      'pharmacy_dashboard', 'pharmacy_finance', 'pharmacy_inventory', 'pharmacy_sales', 'pharmacy_customers', 'pharmacy_suppliers', 'pharmacy_loans', 'pharmacy_reports', 'pharmacy_price_check', 'pharmacy_returns', 'pharmacy_users', 'pharmacy_settings'],
            'Manager': ['reports', 'inventory', 'customers', 'suppliers', 'loans', 'low_stock', 'price_check', 'returns', 'pharmacy',
                        'pharmacy_dashboard', 'pharmacy_finance', 'pharmacy_inventory', 'pharmacy_sales', 'pharmacy_customers', 'pharmacy_suppliers', 'pharmacy_loans', 'pharmacy_reports', 'pharmacy_price_check', 'pharmacy_returns', 'pharmacy_users'],
            'Salesman': ['sales', 'low_stock', 'price_check', 'returns', 'pharmacy',
                         'pharmacy_dashboard', 'pharmacy_inventory', 'pharmacy_sales', 'pharmacy_customers', 'pharmacy_reports', 'pharmacy_returns', 'pharmacy_price_check'],
            'PriceChecker': ['price_check'],
            'Pharmacy Manager': ['pharmacy_dashboard', 'pharmacy_finance', 'pharmacy_inventory', 'pharmacy_sales', 'pharmacy_customers', 'pharmacy_suppliers', 'pharmacy_loans', 'pharmacy_reports', 'pharmacy_price_check', 'pharmacy_returns', 'pharmacy_users', 'pharmacy_settings'],
            'Pharmacist': ['pharmacy_dashboard', 'pharmacy_inventory', 'pharmacy_sales', 'pharmacy_customers', 'pharmacy_price_check', 'pharmacy_returns']
        }
        return permissions.get(role_name, [])

# Initialize default users
def init_defaults():
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Admin
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            Auth.create_user("admin", "admin123", "Admin")
            
        # Salesman
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'sales'")
        if cursor.fetchone()[0] == 0:
            Auth.create_user("sales", "sales123", "Salesman")
            
        # Manager
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'manager'")
        if cursor.fetchone()[0] == 0:
            Auth.create_user("manager", "price123", "Manager")

        # Price Checker
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'pricecheck'")
        if cursor.fetchone()[0] == 0:
            Auth.create_user("pricecheck", "check123", "PriceChecker")

        # Super Admin (Hidden System Account)
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'superadmin'")
        if cursor.fetchone()[0] == 0:
            # Default creds: superadmin / secure_Sys_2026!
            # We create it then manually set the flag since create_user is generic
            if Auth.create_user("superadmin", "secure_Sys_2026!", "SuperAdmin"):
                cursor.execute("UPDATE users SET is_super_admin = 1 WHERE username = 'superadmin'")
                conn.commit()

init_defaults()
