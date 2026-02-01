from src.core.auth import Auth
import bcrypt
def reset_pass():
    username = "sales"
    password = "sales123"
    hashed = Auth.hash_password(password)
    print(hashed)
    Auth.hash_password(hashed)
    print(hashed)
    # Hashing (at registration)
    hashed = Auth.hash_password(password)
    print(hashed)

    # Verifying (at login)
    is_correct = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')))
    print(hashed)
    print(is_correct)
reset_pass()
