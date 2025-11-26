import argparse
from datetime import datetime, timedelta

from src.config.data_warehouse_connector import insert_flights, check_if_job_completed
from src.helpper.logger_config import logger
from src.config.sqlite_connector import (
    process_missing_data,
    process_duplicate_data,
    get_batch,
    update_dim_airline,
    update_dim_airport,
)
import re
from src.constant.LogType import LogType
from src.config.log_database import DBLogger
from src.helpper.get_Ip import get_ip_address

SERVICE_NAME = "transform_and_load_data"
ACTION_NAME = "transform_and_load_data"
dblogger = DBLogger()


def transform_and_load_data(target_date_str):

    # 1. Get ip address
    ip_address = get_ip_address()
    start_time_job = datetime.now()

    # 2. Preprocess data 
    try:
        process_missing_data()
        process_duplicate_data()
    except Exception as e:
        logger.error(f"Error processing pre-data: {e}")
        return

    # 3. Update airline data 
    updated_airline_count = update_dim_airline()
    if updated_airline_count > 0:
        dblogger.write_log(
            LogType.INFO,
            SERVICE_NAME,
            "UPDATE_DIM_AIRLINE",
            f"Updated {updated_airline_count}",
            start_time=start_time_job,
            end_time=datetime.now(),
            ip_address=ip_address,
        )
    # 4. Update airport data
    updated_airport_count = update_dim_airport()
    if updated_airport_count > 0:
        dblogger.write_log(
            LogType.INFO,
            SERVICE_NAME,
            "UPDATE_DIM_AIRPORT",
            f"Updated {updated_airport_count}",
            start_time=start_time_job,
            end_time=datetime.now(),
            ip_address=ip_address,
        )

    # 5. Insert data to data warehouse
    page = 0
    total_flights_loaded = 0

    try:
        while True:
            # 6. get flights data
            flights = get_batch(page)

            # 7. Check if there are no more flights
            if not flights:
                # 8. break if no more flights
                break
            
            # 9. Standardize data
            standardized_flights = standardize_data(flights)

            # 10. Insert data to data warehouse
            count = insert_flights(standardized_flights)

            # 11. Check count inserted
            if count > 0:
                total_flights_loaded += count
                logger.info(f"Page {page}: Loaded {count} flights")
            page += 1

        # 12. Write log when insert successfully
        dblogger.write_log(
            LogType.INFO,
            SERVICE_NAME,
            ACTION_NAME,
            f"SUCCESS: Processed {target_date_str}. Total flights: {total_flights_loaded}",
            start_time=start_time_job,
            end_time=datetime.now(),
            ip_address=ip_address,
        )
        logger.info(f"Job for {target_date_str} completed successfully.")
        # 13. Close connection
        dblogger.close()

    except Exception as e:
        logger.error(f"Critical error on page {page}: {e}")
        dblogger.write_log(
            LogType.ERROR,
            SERVICE_NAME,
            ACTION_NAME,
            f"FAILED at page {page}: {str(e)}",
            start_time=start_time_job,
            end_time=datetime.now(),
            ip_address=ip_address,
        )
        raise e


def standardize_data(flights):
    standardized_flights = []
    logger.info(type(flights))

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

    return standardized_flights


def validate_data(flight):
    required_fields = [
        "airline",
        "departure_airport",
        "destination_airport",
        "departure_time",
        "destination_time",
        "price",
        "currency",
    ]

    for field in required_fields:
        if field not in flight or flight[field] in (None, ""):
            logger.warning(f"Missing required field: {field} in flight {flight}")
            return False
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

    try:
        price = float(flight["price"])
        if price < 0:
            logger.warning(f"Invalid price: {flight['price']} in flight {flight}")
            return False
    except (ValueError, TypeError):
        logger.warning(f"Price is not a number: {flight['price']} in flight {flight}")
        return False

    if "duration_minutes" in flight and flight["duration_minutes"] is not None:
        try:
            duration = int(flight["duration_minutes"])
            if duration < 0:
                logger.warning(
                    f"Invalid duration_minutes: {flight['duration_minutes']} in flight {flight}"
                )
                return False
        except (ValueError, TypeError):
            logger.warning(
                f"duration_minutes is not an integer: {flight['duration_minutes']} in flight {flight}"
            )
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
    digits = re.findall(r"\d+", price_str)
    if not digits:
        return None
    return int("".join(digits))


def parse_duration(duration_str):
    hours = 0
    minutes = 0
    if "h" in duration_str:
        parts = duration_str.split("h")
        hours = int(parts[0].strip())
        if "m" in parts[1]:
            minutes = int(parts[1].replace("m", "").strip())
    elif "m" in duration_str:
        minutes = int(duration_str.replace("m", "").strip())
    return hours * 60 + minutes


def parse_currency(price_str: str):
    if not price_str:
        return None

    currencies = ["VND", "USD", "EUR", "JPY", "KRW", "THB", "AUD"]

    for cur in currencies:
        if cur in price_str:
            return cur

    match = re.search(r"[A-Z]{2,4}", price_str)
    return match.group(0) if match else None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Đẩy dữ liệu flight vào data warehouse"
    )

    parser.add_argument(
        "-d",
        "--date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.now() + timedelta(days=1),
        help="Ngày bay định dạng YYYY-MM-DD",
    )
    args = parser.parse_args()


    target_date_str = args.date.strftime("%Y-%m-%d")

    logger.info(f"Checking job status for: {target_date_str}...")

    isCompleted = check_if_job_completed(target_date_str)

    if isCompleted:
        logger.info(f"[SKIP] Job for {target_date_str} is already completed. Exiting.")
    else:
        logger.info(f"[START] Starting job for {target_date_str}...")

        transform_and_load_data(target_date_str)
