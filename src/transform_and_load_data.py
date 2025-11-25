import argparse
from datetime import datetime, timedelta

from src.config.data_warehouse_connector import insert_flights
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
    # Lấy IP một lần ở đầu hàm
    ip_address = get_ip_address()  # Đảm bảo bạn đã import hàm này
    start_time_job = datetime.now()

    # --- Giai đoạn 1: Tiền xử lý ---
    try:
        # Nên truyền ngày vào để biết xử lý dữ liệu nào
        process_missing_data()
        process_duplicate_data()
    except Exception as e:
        logger.error(f"Error processing pre-data: {e}")
        return  # Dừng nếu lỗi ngay từ đầu

    # --- Giai đoạn 2: Cập nhật Dimension (Chỉ làm 1 lần) ---
    # Log vào DB nhưng dùng action khác để không bị hàm check hiểu nhầm
    updated_airline_count = update_dim_airline()
    if updated_airline_count > 0:
        dblogger.write_log(
            LogType.INFO,
            SERVICE_NAME,
            "UPDATE_DIM_AIRLINE",
            f"Updated {updated_airline_count}",
            ip_address=ip_address,
        )

    updated_airport_count = update_dim_airport()
    if updated_airport_count > 0:
        dblogger.write_log(
            LogType.INFO,
            SERVICE_NAME,
            "UPDATE_DIM_AIRPORT",
            f"Updated {updated_airport_count}",
            ip_address=ip_address,
        )

    # --- Giai đoạn 3: Vòng lặp xử lý chính ---
    page = 0
    total_flights_loaded = 0

    try:
        while True:
            # Truyền ngày vào get_batch để lấy đúng dữ liệu ngày đó
            flights = get_batch(page)

            if not flights:
                break

            standardized_flights = standardize_data(flights)

            # Load to data_warehouse
            count = insert_flights(standardized_flights)

            if count > 0:
                total_flights_loaded += count
                logger.info(f"Page {page}: Loaded {count} flights")

                # OPTIONAL: Ghi log DB chi tiết từng batch (nhưng đổi Action Name)
                # Dùng action="BATCH_INSERT" để hàm check_completed KHÔNG bắt dính cái này
                dblogger.write_log(
                    LogType.INFO,
                    SERVICE_NAME,
                    "BATCH_INSERT",  # <--- KHÁC ACTION_NAME CHÍNH
                    f"Page {page}: Loaded {count} flights",
                    ip_address=ip_address,
                )

            page += 1

        # --- QUAN TRỌNG NHẤT: GHI LOG HOÀN TẤT ---
        # Chỉ khi thoát vòng lặp thành công mới ghi dòng này.
        # Đây là dòng mà check_if_job_completed sẽ tìm kiếm.
        dblogger.write_log(
            LogType.INFO,
            SERVICE_NAME,
            ACTION_NAME,  # <--- Đây là "TRANSFORM_AND_LOAD"
            f"SUCCESS: Processed {target_date_str}. Total flights: {total_flights_loaded}",
            start_time=start_time_job,
            end_time=datetime.now(),
            ip_address=ip_address,
        )
        print(f"Job for {target_date_str} completed successfully.")

    except Exception as e:
        # Nếu lỗi giữa chừng, ghi log ERROR
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
        raise e  # Ném lỗi ra để main biết mà dừng


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
        # Lưu ý: Giữ nguyên logic parse này là tốt để validate định dạng đầu vào
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.now() + timedelta(days=1),
        help="Ngày bay định dạng YYYY-MM-DD",
    )
    args = parser.parse_args()

    # --- BƯỚC SỬA 1: Chuyển datetime object về string chuẩn 'YYYY-MM-DD' ---
    # Vì hàm check DB và hàm xử lý đều cần string cho dễ thao tác
    target_date_str = args.date.strftime("%Y-%m-%d")

    print(f"Checking job status for: {target_date_str}...")

    # Gọi hàm check
    isCompleted = dblogger.check_if_job_completed(
        SERVICE_NAME, ACTION_NAME, target_date_str
    )

    if isCompleted:
        print(f"[SKIP] Job for {target_date_str} is already completed. Exiting.")
    else:
        print(f"[START] Starting job for {target_date_str}...")

        transform_and_load_data(target_date_str)
