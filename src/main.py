import csv
import os
from datetime import datetime, timedelta

from src.config.sqlite_connector import (
    get_source_by_name,
    get_airport,
    load_dim_date,
    update_dim_airline,
    update_dim_airport,
)
from src.helpper.hepper import buidl_origin_destination
import argparse
from src.helpper.logger_config import logger
from src.scrapers.ScraperManager import ScraperManager
from src.transform_and_load_data import transform_and_load_data
from src.load_to_staging import load_csv_to_sqlite


def scrape_single_source(source_name, search_date):
    logger.info(f"Scraping data from {source_name}...")
    # Load config
    airport_code = get_airport()
    web_source = get_source_by_name(source_name)

    if web_source is None:
        logger.error("Source name not found in database. Program terminated.")
        return None
    if search_date < datetime.now():
        logger.error("Date cannot be in the past. Program terminated.")
        return None

    routes = buidl_origin_destination(airport_code)

    scraperManager = ScraperManager()
    flights = scraperManager.scrape_single_source(web_source, routes, search_date)
    if not flights:
        logger.warning("No flights found.")
        return None
    csv_path = save_to_csv(flights, source_name)
    if not csv_path:
        logger.warning("No CSV file generated.")
        return None
    load_csv_to_sqlite(csv_path)

    transform_and_load_data(search_date.strftime("%Y-%m-%d"))

    return None


# Process 1. Crawl_Data_And_Save_To_CSV:
# 1.8. Lưu dữ liệu vào file CSV
# 1.8.1.Gọi hàm save_to_csv() → tạo thư mục scrap_YYYYMMDD + thêm cột crawled_at, source
def save_to_csv(flights, source_name, base_folder="data"):
    if not flights:
        logger.warning("No flights to save to CSV.")
        return

    today_str = datetime.now().strftime("%Y%m%d")
    folder_name = f"scrap_{today_str}"
    folder_path = os.path.join(base_folder, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    file_name = f"{source_name}.csv"
    file_path = os.path.join(folder_path, file_name)

    # Thêm ngày giờ và source vào từng dòng flight
    saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for flight in flights:
        flight["crawled_at"] = saved_at
        flight["source"] = source_name

    column = flights[0].keys()
    with open(file_path, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, column)
        writer.writeheader()
        writer.writerows(flights)

    logger.info(f"Saved {len(flights)} flights to CSV file: {file_name}")
    return file_path


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Scrape and transform data from multiple sources"
    )

    parser.add_argument(
        "-s", "--source", type=str, help="Source name to scrape", required=False
    )

    parser.add_argument(
        "-d",
        "--date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        help="Date to scrape",
        required=False,
        default=datetime.now() + timedelta(days=1),
    )

    parser.add_argument(
        "--load-dim-date", action="store_true", help="Run load_dim_date ETL process"
    )

    parser.add_argument(
        "--update-airline", action="store_true", help="Run check and update dim_airline"
    )

    parser.add_argument(
        "--update-airport", action="store_true", help="Run check and update dim_airport"
    )
    

    args = parser.parse_args()

    if args.load_dim_date:
        path = "data/date_dim.csv"
        load_dim_date(path)

    elif args.update_airline:
        update_dim_airline()

    elif args.update_airport:
        update_dim_airport()

    #     Mặc đinh sẽ cho crawl data
    else:
        date = args.date
        source = args.source
        scrape_single_source(source, date)
