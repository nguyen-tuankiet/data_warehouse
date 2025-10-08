from rich.logging import RichHandler
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

def execute_query(connection, query, data=None):
    """Hàm chung để thực thi một câu lệnh SQL"""
    cursor = connection.cursor()
    try:
        if data:
            if isinstance(data, list):
                cursor.executemany(query, data)
            else:
                cursor.execute(query, data)
        else:
            cursor.execute(query)
        connection.commit()
    except Exception as e:
        print(f"Error executing query: {e}")
    finally:
        cursor.close()

def execute_read_query(connection, query):
    """Hàm chung để thực thi câu lệnh SELECT và trả về kết quả"""
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(f"Error reading query: {e}")
    finally:
        cursor.close()


def setup_database(connection):
    """
    Tạo các bảng cần thiết (config, logs, flights, field_mappings) nếu chúng chưa tồn tại.
    """
    print("Checking and setting up database...")

    create_config_table = """
    CREATE TABLE IF NOT EXISTS config (
        id INT AUTO_INCREMENT PRIMARY KEY,
        source_name VARCHAR(255) NOT NULL UNIQUE,
        url VARCHAR(1024) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        scraper_class VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """

    create_logs_table = """
    CREATE TABLE IF NOT EXISTS logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        level VARCHAR(50),
        message TEXT,
        source_name VARCHAR(255),
        route VARCHAR(100)
    ) ENGINE=InnoDB;
    """

    create_flights_table = """
    CREATE TABLE IF NOT EXISTS flights (
        id INT AUTO_INCREMENT PRIMARY KEY,
        flight_code VARCHAR(100),
        airline VARCHAR(255),
        departure_airport VARCHAR(255),
        arrival_airport VARCHAR(255),
        departure_time DATETIME,
        arrival_time DATETIME,
        duration_minutes INT,
        price DECIMAL(10, 2),
        currency VARCHAR(10) DEFAULT 'VND',
        source VARCHAR(255),
        route VARCHAR(100),
        stops INT DEFAULT 0,
        aircraft_type VARCHAR(100),
        baggage_info TEXT,
        meal_info TEXT,
        seat_class VARCHAR(50),
        booking_url TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_flight (flight_code, departure_time, source, route)
    ) ENGINE=InnoDB;
    """

    create_field_mappings_table = """
    CREATE TABLE IF NOT EXISTS field_mappings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        source_name VARCHAR(255) NOT NULL,
        field_name VARCHAR(100) NOT NULL,
        selector_type ENUM('xpath', 'css', 'class', 'id', 'text') DEFAULT 'xpath',
        selector_value TEXT NOT NULL,
        is_required BOOLEAN DEFAULT FALSE,
        data_type ENUM('text', 'number', 'datetime', 'price') DEFAULT 'text',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_mapping (source_name, field_name)
    ) ENGINE=InnoDB;
    """
    
    execute_query(connection, create_config_table)
    execute_query(connection, create_logs_table)
    execute_query(connection, create_flights_table)
    execute_query(connection, create_field_mappings_table)
    
    # Chèn dữ liệu config mẫu cho 3 website
    insert_initial_configs = """
    INSERT IGNORE INTO config (source_name, url, is_active, scraper_class) VALUES
    ('Booking.com', 'https://flights.booking.com/api/flights/', TRUE, 'BookingApiScraper'),
    ('Agoda.com', 'https://www.agoda.com/flights', TRUE, 'AgodaScraperV2'),
    ('Traveloka.com', 'https://www.traveloka.com/vi-vn/flight', TRUE, 'TravelokaScraperV2');
    """
    execute_query(connection, insert_initial_configs)
    
    # Chèn field mappings mẫu
    insert_field_mappings = """
    INSERT IGNORE INTO field_mappings (source_name, field_name, selector_type, selector_value, is_required, data_type) VALUES
    ('Booking.com', 'airline', 'xpath', './/div[@data-testid="airline-name"]', TRUE, 'text'),
    ('Booking.com', 'flight_number', 'xpath', './/div[@data-testid="flight-number"]', FALSE, 'text'),
    ('Booking.com', 'departure_time', 'xpath', './/div[@data-testid="departure-time"]', TRUE, 'datetime'),
    ('Booking.com', 'arrival_time', 'xpath', './/div[@data-testid="arrival-time"]', TRUE, 'datetime'),
    ('Booking.com', 'price', 'xpath', './/div[@data-testid="price"]', TRUE, 'price'),
    
    ('Agoda', 'airline', 'xpath', './/div[@data-testid="airline-name"]', TRUE, 'text'),
    ('Agoda', 'flight_number', 'xpath', './/div[@data-testid="flight-number"]', FALSE, 'text'),
    ('Agoda', 'departure_time', 'xpath', './/div[@data-testid="departure-time"]', TRUE, 'datetime'),
    ('Agoda', 'arrival_time', 'xpath', './/div[@data-testid="arrival-time"]', TRUE, 'datetime'),
    ('Agoda', 'price', 'xpath', './/div[@data-testid="price"]', TRUE, 'price'),
    
    ('Traveloka', 'airline', 'xpath', './/div[contains(@class, "airline")]', TRUE, 'text'),
    ('Traveloka', 'flight_number', 'xpath', './/div[@data-testid="flight-number"]', FALSE, 'text'),
    ('Traveloka', 'departure_time', 'xpath', './/span[contains(@class, "time")]', TRUE, 'datetime'),
    ('Traveloka', 'arrival_time', 'xpath', './/span[contains(@class, "time")]', TRUE, 'datetime'),
    ('Traveloka', 'price', 'xpath', './/div[contains(@class, "price")]//span', TRUE, 'price');
    """
    execute_query(connection, insert_field_mappings)
    
    print("Database setup completed.")


def log_message(connection, level, message, source_name=None, route=None):
    query = "INSERT INTO logs (level, message, source_name, route) VALUES (%s, %s, %s, %s)"
    execute_query(connection, query, (level, message, source_name, route))


def get_active_configs(connection):
    query = "SELECT source_name, url, scraper_class, scrap_type FROM config WHERE is_active = TRUE"
    configs = execute_read_query(connection, query)
    return configs


def get_field_mappings(connection, source_name):
    """Lấy field mappings cho một source cụ thể."""
    query = "SELECT field_name, selector_type, selector_value, is_required, data_type FROM field_mappings WHERE source_name = %s"
    mappings = execute_read_query(connection, query, (source_name,))
    return mappings


def insert_flights_data(connection, flights):
    """
    Chèn một danh sách các chuyến bay vào bảng flights.
    Sử dụng ON DUPLICATE KEY UPDATE để tránh trùng lặp.
    """
    if not flights:
        return

    query = """
    INSERT INTO flights (flight_code, airline, departure_airport, arrival_airport, departure_time, arrival_time, duration_minutes, price, currency, source, route, stops, aircraft_type, baggage_info, meal_info, seat_class, booking_url)
    VALUES (%(flight_code)s, %(airline)s, %(departure_airport)s, %(arrival_airport)s, %(departure_time)s, %(arrival_time)s, %(duration_minutes)s, %(price)s, %(currency)s, %(source)s, %(route)s, %(stops)s, %(aircraft_type)s, %(baggage_info)s, %(meal_info)s, %(seat_class)s, %(booking_url)s)
    ON DUPLICATE KEY UPDATE
        airline = VALUES(airline),
        arrival_airport = VALUES(arrival_airport),
        arrival_time = VALUES(arrival_time),
        duration_minutes = VALUES(duration_minutes),
        price = VALUES(price),
        currency = VALUES(currency),
        stops = VALUES(stops),
        aircraft_type = VALUES(aircraft_type),
        baggage_info = VALUES(baggage_info),
        meal_info = VALUES(meal_info),
        seat_class = VALUES(seat_class),
        booking_url = VALUES(booking_url),
        scraped_at = CURRENT_TIMESTAMP;
    """
    execute_query(connection, query, flights)


def update_field_mapping(connection, source_name, field_name, selector_type, selector_value, is_required=False, data_type='text'):
    """Cập nhật hoặc tạo mới field mapping."""
    query = """
    INSERT INTO field_mappings (source_name, field_name, selector_type, selector_value, is_required, data_type)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        selector_type = VALUES(selector_type),
        selector_value = VALUES(selector_value),
        is_required = VALUES(is_required),
        data_type = VALUES(data_type);
    """
    execute_query(connection, query, (source_name, field_name, selector_type, selector_value, is_required, data_type))


def get_airport(connection):
    query = "SELECT code FROM airport where status = 'ACTIVE'"
    airports = execute_read_query(connection, query)
    if airports is None :
        logger.error("No airport found in database.")
        return []
    return [row['code'] for row in airports]

