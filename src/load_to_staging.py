import csv
import argparse
from src.helpper.logger_config import logger
from src.config.sqlite_connector import get_sqlite_connection, clear_flight_metadata
from datetime import datetime
from src.constant.LogType import LogType
from src.config.log_database import DBLogger
from src.helpper.get_Ip import get_ip_address

SERVICE_NAME = "load_to_staging"
ACTION_NAME = "load_csv_to_sqlite"
dblogger = DBLogger()

def load_csv_to_sqlite(file_path):

    #1. Lấy ra địa chỉ ip máy đang thực hiện cào dữ liệu
    ip_address = get_ip_address()

    #2. Xóa dữ liệu cũ
    clear_flight_metadata()
    sqlite_connector = get_sqlite_connection()
    if not sqlite_connector:
        logger.error("Cannot connect to SQLite database. Program terminated.")
        return None
    try:
        start_time = datetime.now()
        #3. Kiểm tra xem trước đó dữ liệu đã được insert hay chưa
        if(dblogger.check_if_job_completed(SERVICE_NAME, ACTION_NAME,start_time)):
            logger.info("Data already inserted. Program terminated.")
            return None
        #4. Mở file csv và insert dữ liệu vào metadata
        with open(file_path, "r", encoding="utf-8") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            rows_to_insert = []

            for row in csv_reader:
                rows_to_insert.append(
                    (
                        row["airline"],
                        row["departure_airport"],
                        row["departure_time"],
                        row["destination_airport"],
                        row["destination_time"],
                        row["duration_time"],
                        row["price"],
                        row["source"],
                        row["crawled_at"],
                    )
                )

            insert_query = """
                               INSERT INTO flights_metadata (
                               airline, departure_airport, departure_time,
                                   destination_airport, destination_time, duration_time, price, source, crawled_at
                               )
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) \
                               """
            # 5. lấy cursor từ metadata và insert dữ liệu 
            cursor = sqlite_connector.cursor()
            cursor.executemany(insert_query, rows_to_insert)
            sqlite_connector.commit()
            end_time = datetime.now()
            # 7. Ghi log khi insert thành công 
            dblogger.write_log(
                LogType.INFO,
                SERVICE_NAME,
                ACTION_NAME,
                f"Inserted {cursor.rowcount} rows into flights_metadata table.",
                start_time,
                end_time,
                ip_address,
            )
            logger.info(f"Inserted {cursor.rowcount} rows into flights_metadata table.")

    except Exception as e:
        # 6. Ghi log khi có lỗi xảy ra
        end_time = datetime.now()
        dblogger.write_log(
            LogType.ERROR,
            SERVICE_NAME,
            ACTION_NAME,
            f"Error reading CSV file: {e}",
            start_time,
            end_time,
            ip_address,
        )
        logger.error(f"Error reading CSV file: {e}")

    finally:
        # 8. Đóng kết nối sau khi hoàn thành 
        sqlite_connector.close()
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load data from CSV to SQLite")
    parser.add_argument(
        "-f", "--file_path", type=str, required=True, help="Path to the CSV file"
    )
    args = parser.parse_args()
    if args.file_path:
        load_csv_to_sqlite(args.file_path)
    else:
        logger.error("No file path provided. Program terminated.")
