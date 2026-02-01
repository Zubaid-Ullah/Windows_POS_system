from datetime import datetime

import bcrypt
import json
from src.database.db_manager import db_manager
from src.utils.logger import log_info, log_error

class PharmacyAuth:
    _current_user = None

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def check_password(password, hashed):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            return False

    @classmethod
    def login(cls, username, password):
        with db_manager.get_pharmacy_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pharmacy_users WHERE username = ? AND is_active = 1", (username,))
            user = cursor.fetchone()
            
            try:
                if user and cls.check_password(password, user['password_hash']):
                    cls._current_user = dict(user)
                    log_info(f"Pharmacy User {username} logged in successfully")
                    return True
            except Exception as e:
                log_error(f"Pharmacy Login error for {username}: {e}")
            
            return False

    @classmethod
    def logout(cls):
        cls._current_user = None

    @classmethod
    def set_current_user(cls, user_data):
        cls._current_user = user_data

    @classmethod
    def get_current_user(cls):
        # If no pharmacy user is logged in, check if a SuperAdmin is logged in to the main system
        if not cls._current_user:
            try:
                from src.core.auth import Auth
                main_user = Auth.get_current_user()
                if main_user and (main_user.get('is_super_admin') or 'pharmacy' in Auth.get_user_permissions(main_user)):
                    # For SuperAdmin or users with 'pharmacy' permission, 
                    # we can treat them as a pharmacy admin for the session
                    # But we should mark it so we know it's a bridged user
                    return {
                        'id': f"main_{main_user.get('id')}",
                        'username': main_user.get('username'),
                        'role': 'Manager' if main_user.get('is_super_admin') else 'Pharmacist',
                        'is_super_admin': main_user.get('is_super_admin'),
                        'permissions': main_user.get('permissions'),
                        'is_bridged': True
                    }
            except:
                pass
        return cls._current_user

    @staticmethod
    def get_user_permissions(user):
        if not user: return []
        
        # Super Admin check
        if user.get('is_super_admin') or user.get('username') == 'pharmacy_admin':
            return ['*']
            
        if user.get('permissions'):
            try:
                perms = json.loads(user['permissions'])
                if isinstance(perms, list):
                    return perms
            except:
                return [p.strip() for p in user['permissions'].split(',') if p.strip()]
        
        # Default Permissions based on role
        role = user.get('role', 'Pharmacist')
        if role == 'Manager':
            return ['*'] # Full access within pharmacy
        else:
            # Standard Pharmacist perms
            return ['pharmacy_dashboard', 'pharmacy_sales', 'pharmacy_inventory', 'pharmacy_customers', 'pharmacy_price_check', 'pharmacy_returns']

    @staticmethod
    def check_is_active():
        """Checks if the pharmacy business license is active in pharmacy_pos.db"""
        try:
            with db_manager.get_pharmacy_connection() as conn:
                res = conn.execute("SELECT is_active, valid_until FROM system_settings WHERE id = 1").fetchone()
                if res:
                    valid_until = datetime.strptime(res['valid_until'], '%Y-%m-%d')
                    return res['is_active'] == 1 and valid_until > datetime.now()
        except: pass
        return False

def init_pharmacy_defaults():
    with db_manager.get_pharmacy_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Standard Admin
        cursor.execute("SELECT COUNT(*) FROM pharmacy_users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            hashed = PharmacyAuth.hash_password("admin123")
            cursor.execute("""
                INSERT INTO pharmacy_users (username, password_hash, title, role, permissions)
                VALUES (?, ?, ?, ?, ?)
            """, ("admin", hashed, "Pharmacy Admin", "Manager", json.dumps(['*'])))
            
        # 2. Support for psuper bridge if needed or local psuper
        cursor.execute("SELECT COUNT(*) FROM pharmacy_users WHERE username = 'psuper'")
        if cursor.fetchone()[0] == 0:
             hashed = PharmacyAuth.hash_password("secure_Sys_2026!")
             cursor.execute("""
                INSERT INTO pharmacy_users (username, password_hash, title, role, permissions, is_super_admin)
                VALUES (?, ?, ?, ?, ?, 1)
            """, ("psuper", hashed, "Pharmacy Super Owner", "Manager", json.dumps(['*'])))
            
        conn.commit()

init_pharmacy_defaults()
