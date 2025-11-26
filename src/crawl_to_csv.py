# crawl_to_csv.py
import argparse
from datetime import datetime, timedelta
from src.config.sqlite_connector import get_source_by_name, get_airport
from src.helpper.hepper import buidl_origin_destination
from src.scrapers.ScraperManager import ScraperManager
from src.main import save_to_csv  # Reuse hàm lưu CSV có sẵn
from src.helpper.logger_config import logger
from src.config.log_database import DBLogger
from src.helpper.get_Ip import get_ip_address
from src.constant.LogType import LogType

SERVICE_NAME = "crawl_to_csv"
ACTION_NAME = "crawl_to_csv"
dblogger = DBLogger()


# Process 1. Crawl_Data_And_Save_To_CSV:
def crawl_and_save_to_csv(source_name: str, search_date: datetime):
    ip_address = get_ip_address()
    start_time = datetime.now()
    logger.info(
        f"Bắt đầu crawl dữ liệu từ {source_name} cho ngày {search_date.strftime('%Y-%m-%d')}"
    )
    dblogger.write_log(
        LogType.INFO,
        SERVICE_NAME,
        ACTION_NAME,
        f"Bắt đầu crawl dữ liệu từ {source_name} cho ngày {search_date.strftime('%Y-%m-%d')}",
        start_time,
        datetime.now(),
        ip_address,
    )

    # 1.1. Lấy cấu hình source từ bảng source trong SQLite
    # Gọi hàm get_source_by_name() từ src.config.sqlite_connector
    web_source = get_source_by_name(source_name)
    # 1.1.1. Kiểm tra source có tồn tại và đang active
    if not web_source:
        # 1.1.1.1. Không tìm thấy source → dừng toàn bộ
        logger.error(f"Không tìm thấy source '{source_name}' trong database!")
        dblogger.write_log(
            LogType.ERROR,
            SERVICE_NAME,
            ACTION_NAME,
            f"Không tìm thấy source '{source_name}' trong database!",
            start_time,
            datetime.now(),
            ip_address,
        )
        return

    # 1.2. Kiểm tra ngày tìm kiếm không được là quá khứ
    if search_date.date() < datetime.now().date():
        # 1.2.1. Ngày không hợp lệ → dừng
        logger.error("Không được chọn ngày trong quá khứ!")
        dblogger.write_log(
            LogType.ERROR,
            SERVICE_NAME,
            ACTION_NAME,
            "Không được chọn ngày trong quá khứ!",
            start_time,
            datetime.now(),
            ip_address,
        )
        return

    # 1.3. Lấy danh sách sân bay gốc từ bảng dim_airport
    # Gọi hàm get_airport() từ sqlite_connector.py
    airport_codes = get_airport()
    # 1.3.1. Kiểm tra có dữ liệu sân bay không
    if not airport_codes:
        # 1.3.1.1. Không có sân bay → không tạo được route
        logger.error("Không lấy được danh sách sân bay từ bảng dim_airport!")
        dblogger.write_log(
            LogType.ERROR,
            SERVICE_NAME,
            ACTION_NAME,
            "Không lấy được danh sách sân bay từ bảng dim_airport!",
            start_time,
            datetime.now(),
            ip_address,
        )
        return

    # 1.4. Tạo tất cả các chặng bay (origin → destination, khác nhau)
    # Gọi hàm buidl_origin_destination() từ src.helpper.hepper
    routes = buidl_origin_destination(airport_codes)
    # 1.4.1. Log số lượng chặng bay được tạo
    logger.info(f"Đã tạo {len(routes)} chặng bay từ {len(airport_codes)} sân bay")

    # 1.5. Khởi tạo ScraperManager để điều phối scraper theo source
    scraper_manager = ScraperManager()

    # 1.6. Gọi hàm scrape_single_source() từ ScraperManager.py
    flights = scraper_manager.scrape_single_source(web_source, routes, search_date)

    # 1.7. Kiểm tra kết quả crawl
    if not flights:
        # 1.7.1. Không có dữ liệu → kết thúc sớm
        logger.warning("Không tìm thấy chuyến bay nào!")
        dblogger.write_log(
            LogType.WARNING,
            SERVICE_NAME,
            ACTION_NAME,
            "Không tìm thấy chuyến bay nào!",
            start_time,
            datetime.now(),
            ip_address,
        )
        return

    # 1.8. Lưu dữ liệu vào file CSV
    csv_path = save_to_csv(flights, source_name)

    # 1.8.1. Kiểm tra việc lưu file thành công
    if csv_path:
        logger.info(f"HOÀN TẤT! Đã lưu {len(flights)} chuyến bay → {csv_path}")
        dblogger.write_log(
            LogType.INFO,
            SERVICE_NAME,
            ACTION_NAME,
            f"HOÀN TẤT! Đã lưu {len(flights)} chuyến bay → {csv_path}",
            start_time,
            datetime.now(),
            ip_address,
        )
    else:
        logger.error("Lưu file CSV thất bại!")
        dblogger.write_log(
            LogType.ERROR,
            SERVICE_NAME,
            ACTION_NAME,
            "Lưu file CSV thất bại!",
            start_time,
            datetime.now(),
            ip_address,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chỉ crawl và lưu ra CSV (không load DB)"
    )
    parser.add_argument(
        "-s", "--source", type=str, required=True, help="Tên source: Traveloka.com"
    )
    parser.add_argument(
        "-d",
        "--date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.now() + timedelta(days=1),
        help="Ngày bay định dạng YYYY-MM-DD (mặc định: ngày mai)",
    )

    args = parser.parse_args()

    crawl_and_save_to_csv(args.source, args.date)
