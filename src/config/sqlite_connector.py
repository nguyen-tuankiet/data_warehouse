
import sqlite3
import os
from threading import Lock

from src.helpper.logger_config import logger


SQLITE_DB_PATH = os.path.join(os.getcwd(), "database/metadata.sqlite")
_connection = None
_lock = Lock()


def get_sqlite_connection():

    global _connection

    # Nếu đã có connection đang mở thì dùng lại
    if _connection is not None:
        try:
            _connection.execute("SELECT 1")  # kiểm tra connection còn sống
            return _connection
        except sqlite3.Error:
            _connection = None  # nếu connection lỗi → reset

    # Dùng lock tránh race condition khi đa luồng
    with _lock:
        if _connection is None:
            try:
                conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
                conn.row_factory = sqlite3.Row  # truy cập kiểu dict
                _connection = conn
                logger.info("SQLite connection created")
            except sqlite3.Error as e:
                logger.error(f"Cannot connect to SQLite DB: {e}")
                _connection = None

    return _connection

def clear_flight_metadata():
    connection = get_sqlite_connection()
    if not connection:
        logger.error("Cannot connect to SQLite database. Program terminated.")
        return
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM flights_metadata")
            logger.info("All records deleted from flights_metadata table.")
            return True
    except sqlite3.Error as e:
        logger.error(f"Error clearing SQLite database: {e}")

def get_all():
    connection = get_sqlite_connection()
    if not connection:
        logger.error("Cannot connect to SQLite database. Program terminated.")
        return None
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM flights_metadata")
            rows = cursor.fetchall()
            return rows
    except sqlite3.Error as e:
        logger.error(f"Error fetching all rows from SQLite database: {e}")
        return None

def get_batch( page = 0, size = 500):
    connection = get_sqlite_connection()
    if not connection:
        logger.error("Cannot connect to SQLite database. Program terminated.")
        return

    cursor = connection.cursor()
    offset = page * size

    while True:
        cursor.execute(
            "SELECT * FROM flights_metadata LIMIT ? OFFSET ?",
            (size, offset)
        )
        rows = cursor.fetchall()
        if not rows:
            break

        rows_as_dict = [dict(r) for r in rows]  # convert row → dict
        return rows_as_dict



def process_missing_data():
    connection = get_sqlite_connection()
    if not connection:
        logger.error("Cannot connect to SQLite database. Program terminated.")
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
            logger.info(f"Processed {cursor.rowcount} rows with missing data.")
            return cursor.rowcount

    except sqlite3.Error as e:
        logger.error(f"Error processing missing data in SQLite database: {e}")

def process_duplicate_data():
    connection = get_sqlite_connection()
    if not connection:
        logger.error("Cannot connect to SQLite database. Program terminated.")
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
            logger.info(f"Processed {cursor.rowcount} rows with duplicate data.")
            return cursor.rowcount

    except sqlite3.Error as e:
        logger.error(f"Error processing duplicate data in SQLite database: {e}")

def get_source_by_name(name):
    connection = get_sqlite_connection()
    if not connection:
        logger.error("Cannot connect to SQLite database. Program terminated.")
        return None
    try:
        with connection:
            cursor = connection.cursor()
            name = name.strip()
            cursor.execute("SELECT  * FROM source "
                           "WHERE source_name like ? AND is_active = TRUE ", (name,))
            row = cursor.fetchone()
            return row

    except sqlite3.Error as e:
        logger.error(f"Error fetching source names from SQLite database: {e}")
        return None

def get_airport():
    connection = get_sqlite_connection()
    if not connection:
        logger.error("Cannot connect to SQLite database. Program terminated.")
        return None
    try:
        cursor = connection.cursor()
        airports = (cursor.execute("SELECT code FROM dim_airport where is_active = TRUE")
                    .fetchall())

        logger.info(f"Fetched {len(airports)} airports from database.")
        if airports is None :
            logger.error("No airport found in database.")
            return []

        connection.row_factory = sqlite3.Row
        return [row['code'] for row in airports]

    except sqlite3.Error as e:
        logger.error(f"Error fetching airport from SQLite database: {e}")
        return None

