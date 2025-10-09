import logging
import sqlite3
import os


SQLITE_DB_PATH = os.path.join(os.getcwd(), "database/metadata.sqlite")

def get_sqlite_connection():
    try:
        connection = sqlite3.connect(SQLITE_DB_PATH)
        return connection
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite database: {e}")
        return None

def init_sqlite_db():
    connection = get_sqlite_connection()
    if not connection:
        return
    try:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS flights_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                airline TEXT,
                departure_airport TEXT,
                departure_time TEXT,
                destination_airport TEXT,
                destination_time TEXT,
                duration_time INTEGER,
                price REAL
                );
            """)
    except sqlite3.Error as e:
        logging.error(f"Error initializing SQLite database: {e}")


def clear_sqlite_db():
    connection = get_sqlite_connection()
    if not connection:
        return
    try:
        with connection:
            connection.execute("DELETE FROM flights_metadata")
    except sqlite3.Error as e:
        logging.error(f"Error clearing SQLite database: {e}")

def get_all():
    connection = get_sqlite_connection()
    if not connection:
        return None
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM flights_metadata")
            rows = cursor.fetchall()
            return rows
    except sqlite3.Error as e:
        logging.error(f"Error fetching all rows from SQLite database: {e}")
        return None
