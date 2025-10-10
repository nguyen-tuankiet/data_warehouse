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
        logging.error("Cannot connect to SQLite database. Program terminated.")
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

def process_missing_data():
    connection = get_sqlite_connection()
    if not connection:
        logging.error("Cannot connect to SQLite database. Program terminated.")
        return None

    try:
        with connection:
            cursor = connection.cursor()
            query = """
                DELETE FROM flights_metadata
                WHERE airline IS NULL
                   OR departure_airport IS NULL
                   OR departure_time IS NULL
                   OR destination_airport IS NULL
                   OR destination_time IS NULL
                   OR duration_time IS NULL
                   OR price IS NULL
                ;
            """
            cursor.execute(query)
            connection.commit()
            logging.info(f"Processed {cursor.rowcount} rows with missing data.")
            return cursor.rowcount

    except sqlite3.Error as e:
        logging.error(f"Error processing missing data in SQLite database: {e}")


def process_duplicate_data():
    connection = get_sqlite_connection()
    if not connection:
        logging.error("Cannot connect to SQLite database. Program terminated.")
        return None
    try:
        with connection:
            cursor = connection.cursor()
            query = """
                DELETE FROM flights_metadata
                WHERE id NOT IN (
                    SELECT min(id)
                    FROM flights_metadata
                    GROUP BY airline, departure_airport,
                                departure_time, destination_airport,
                                destination_time, duration_time, price
                    )
                ;
            """
            cursor.execute(query)
            connection.commit()
            logging.info(f"Processed {cursor.rowcount} rows with duplicate data.")
            return cursor.rowcount

    except sqlite3.Error as e:
        logging.error(f"Error processing duplicate data in SQLite database: {e}")
