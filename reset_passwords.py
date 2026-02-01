from src.core.auth import Auth
from src.database.db_manager import db_manager

def reset_pass():
    username = "sales"
    password = "sales123"
    hashed = Auth.hash_password(password)
    with db_manager.get_connection() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, username))
        conn.commit()
    print(f"Password for {username} reset to {password}")

    # Also reset admin for good measure
    username = "admin"
    password = "admin123"
    hashed = Auth.hash_password(password)
    with db_manager.get_connection() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, username))
        conn.commit()
    print(f"Password for {username} reset to {password}")
    
    # Also reset manager
    username = "manager"
    password = "price123"
    hashed = Auth.hash_password(password)
    with db_manager.get_connection() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, username))
        conn.commit()
    print(f"Password for {username} reset to {password}")

if __name__ == "__main__":
    reset_pass()
