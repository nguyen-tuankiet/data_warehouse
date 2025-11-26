# database/data_warehouse_connector.py
import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
import threading


_db_connection = None
_db_lock = threading.Lock()


def get_db_connection():
    global _db_connection

    load_dotenv()

    # Nếu đã có connection thì thử kiểm tra còn sống
    if _db_connection is not None:
        try:
            with _db_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return _db_connection
        except pymysql.Error:
            # Nếu lỗi, reset connection
            _db_connection = None

    # Dùng lock để tránh race condition khi đa luồng
    with _db_lock:
        if _db_connection is None:
            try:
                config = {
                    'host': os.getenv('DB_HOST'),
                    'user': os.getenv('DB_USERNAME'),
                    'password': os.getenv('DB_PASSWORD'),
                    'database': os.getenv('DB_NAME'),
                    'port': int(os.getenv('DB_PORT')),
                    'cursorclass': pymysql.cursors.DictCursor,
                    'charset': 'utf8mb4'
                }

                if os.getenv('DB_USE_SSL', 'false').lower() == 'true':
                    ssl_ca_path = os.getenv('DB_SSL_CA')
                    if not ssl_ca_path or not os.path.exists(ssl_ca_path):
                        print(f"Error: DB_USE_SSL enabled but file not found at DB_SSL_CA: '{ssl_ca_path}'")
                        return None
                    config['ssl'] = {'ca': ssl_ca_path}
                    print("Connecting using SSL/TLS with PyMySQL...")

                # Tạo connection
                _db_connection = pymysql.connect(**config)
                print("Database connection successful (singleton)!")
            except pymysql.Error as e:
                print(f"Error connecting to MySQL with PyMySQL: {e}")
                _db_connection = None

    return _db_connection

def check_if_job_completed (date_check : str): 
    query = '''
    SELECT COUNT(*) FROM flights 
    WHERE date(departure_time) = date(%s)
    '''
    connection = get_db_connection()
    if not connection:
        print("Cannot connect to DB. Aborting check.")
        return False
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (date_check,))
            count = cursor.fetchone()
            return count['COUNT(*)'] > 0
    except pymysql.Error as e:
        print(f"Error checking job completion: {e}")
        return False
    finally:
        connection.close()


def insert_flights(flights: list):
    if not flights:
        print("No flights to insert.")
        return 0

    connection = get_db_connection()
    if not connection:
        print("Cannot connect to DB. Aborting insert.")
        return 0

    inserted_count = 0
    try:
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO flights (
                airline,
                departure_airport,
                destination_airport,
                departure_time,
                destination_time,
                duration_minutes,
                price,
                currency,
                created_at,
                source,
                scaper_time
            ) VALUES (
                %(airline)s,
                %(departure_airport)s,
                %(destination_airport)s,
                %(departure_time)s,
                %(destination_time)s,
                %(duration_minutes)s,
                %(price)s,
                %(currency)s,
                %(created_at)s,
                %(source)s,
                %(scraper_time)s
            )
            """

            # Thực hiện insert từng record
            for f in flights:
                cursor.execute(sql, f)
                inserted_count += 1

        connection.commit()
        print(f"Inserted {inserted_count} flights successfully.")

    except pymysql.Error as e:
        print(f"Error inserting flights: {e}")
        connection.rollback()
    finally:
        connection.close()

    return inserted_count
