import getpass
import hashlib
import secrets
from database import connect_database

def main():
    username = input("Choose admin username: ").strip()
    if not username or len(username) > 50:
        print("Username must contain 1-50 characters.")
        return

    password = getpass.getpass("Choose admin password (12+ characters): ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        return
    if len(password) < 12:
        print("Use at least 12 characters for the password.")
        return

    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(
        password.encode("utf-8"), salt=salt,
        n=2**14, r=8, p=1, dklen=32
    )
    stored = f"scrypt${salt.hex()}${key.hex()}"

    conn = connect_database()
    if conn is None:
        print("Could not connect to MySQL. Check backend/database.py settings.")
        return
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
            (username, stored)
        )
        conn.commit()
        print("Admin account created. You can now log in.")
    except Exception as exc:
        conn.rollback()
        print("Could not create admin:", exc)
    finally:
        if cursor:
            cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
