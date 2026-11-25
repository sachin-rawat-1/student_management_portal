import os
import mysql.connector
from mysql.connector import Error

def connect_database():
    """Connect to the local MySQL database.

    Set DB_HOST, DB_USER, DB_PASSWORD and DB_NAME environment variables
    if your MySQL configuration differs from the defaults.
    """
    try:
        return mysql.connector.connect(
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", "student_portal"),
            connection_timeout=5,
        )
    except Error as exc:
        print("MySQL connection error:", exc)
        return None
