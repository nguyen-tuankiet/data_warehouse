from datetime import datetime

from src.config.data_warehouse_connector import insert_flights
from src.helpper.logger_config import logger
from src.config.sqlite_connector import process_missing_data, process_duplicate_data, get_batch
import re

from src.transform.update_dim import update_dim_airline

airport_set = set()
airline_set = set()
def transform_and_load_data():

    # Check missing and duplicate
    process_missing_data()
    process_duplicate_data()


    # Standardize
    page = 0
    while True:
        flights = get_batch(page)

        if not flights or flights is None:
            break

        standardized_flights = standardize_data(flights)
        logger.info(f"Standardized {len(standardized_flights)} flights")

        update_dim_airline(airline_set)
        update_dim_airline(airline_set)

        # Load to data_warehouse
        insert_flights(standardized_flights)

        page += 1


def standardize_data(flights):
    standardized_flights = []
    logger.info(type(flights))
    global airport_set
    global airline_set

    for f in flights:

        new_flight = {
            "airline": f["airline"],
            "departure_airport": f["departure_airport"],
            "destination_airport": f["destination_airport"],
            "departure_time": normalize_datetime(f["departure_time"]),
            "destination_time": normalize_datetime(f["destination_time"]),
            "duration_minutes": parse_duration(f["duration_time"]),
            "price": parse_price(f["price"]),
            "currency": parse_currency(f["price"]),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": f["source"],
            "scraper_time": normalize_datetime(f["crawled_at"]),
        }

        if validate_data(new_flight):
            standardized_flights.append(new_flight)

        airport_set.add(new_flight.get("departure_airport"))
        airport_set.add(new_flight.get("destination_airport"))
        airline_set.add(new_flight.get("airline"))

    return standardized_flights

def validate_data(flight):
    required_fields = [
        "airline",
        "departure_airport",
        "destination_airport",
        "departure_time",
        "destination_time",
        "price",
        "currency"
    ]

    # 1️⃣ Trường bắt buộc không được None hoặc rỗng
    for field in required_fields:
        if field not in flight or flight[field] in (None, ""):
            logger.warning(f"Missing required field: {field} in flight {flight}")
            return False


    # 2️⃣ Kiểm tra kiểu dữ liệu datetime
    datetime_fields = ["departure_time", "destination_time", "scaper_time"]
    for dt_field in datetime_fields:
        if dt_field in flight and flight[dt_field]:
            value = flight[dt_field]
            if isinstance(value, str):
                try:
                    datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logger.warning(f"Invalid datetime format for {dt_field}: {value}")
                    return False
            elif not isinstance(value, datetime):
                logger.warning(f"Invalid type for {dt_field}: {type(value)}")
                return False

    # 3️⃣ Kiểm tra price là số >= 0
    try:
        price = float(flight["price"])
        if price < 0:
            logger.warning(f"Invalid price: {flight['price']} in flight {flight}")
            return False
    except (ValueError, TypeError):
        logger.warning(f"Price is not a number: {flight['price']} in flight {flight}")
        return False

        # 4️⃣ Kiểm tra duration_minutes là int >=0 nếu có
    if "duration_minutes" in flight and flight["duration_minutes"] is not None:
        try:
            duration = int(flight["duration_minutes"])
            if duration < 0:
                logger.warning(f"Invalid duration_minutes: {flight['duration_minutes']} in flight {flight}")
                return False
        except (ValueError, TypeError):
            logger.warning(f"duration_minutes is not an integer: {flight['duration_minutes']} in flight {flight}")
            return False

    return True

def normalize_datetime(dt_str):
    for fmt in (
        "%d-%m-%Y : %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%H:%M",
    ):
        try:
            dt = datetime.strptime(dt_str.strip(), fmt)
            if fmt == "%H:%M":
                today = datetime.now().strftime("%Y-%m-%d")
                return f"{today} {dt_str.strip()}:00"
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
    return None

def parse_price(price_str):
    if not price_str:
        return None
    # Lấy tất cả ký tự số
    digits = re.findall(r'\d+', price_str)
    if not digits:
        return None
    return int(''.join(digits))

def parse_duration(duration_str):
    hours = 0
    minutes = 0
    if 'h' in duration_str:
        parts = duration_str.split('h')
        hours = int(parts[0].strip())
        if 'm' in parts[1]:
            minutes = int(parts[1].replace('m', '').strip())
    elif 'm' in duration_str:
        minutes = int(duration_str.replace('m', '').strip())
    return hours * 60 + minutes

def parse_currency(price_str: str):

    if not price_str:
        return None

    currencies = ['VND', 'USD', 'EUR', 'JPY', 'KRW', 'THB', 'AUD']

    for cur in currencies:
        if cur in price_str:
            return cur

    match = re.search(r'[A-Z]{2,4}', price_str)
    return match.group(0) if match else None