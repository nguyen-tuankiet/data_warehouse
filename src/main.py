import csv
import logging
import os
from datetime import datetime, timedelta
from src.config.db_manager import get_active_configs, log_message
from src.scrapers.ScraperManager import ScraperManager
from src.config.db_connector import get_db_connection
from src.config.sqlite_connector import get_sqlite_connection, clear_sqlite_db
from src.constant.DataSource import DataSource
from src.config.db_manager import get_airport
from src.helpper.hepper import buidl_origin_destination
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


def main():
    connection = get_db_connection()
    logger = logging.getLogger(__name__)

    # Tìm kiếm cho những ngày tới
    search_date = datetime.now() + timedelta(days=2)

    if not connection:
        logger.error("Cannot connect to database. Program terminated.")
        return
    try:
        # build routes
        airport_code = get_airport(connection)
        search_routes = buidl_origin_destination(airport_code)

        logger.info("Starting multi-source flight data scraping process.")

        # Lấy configs từ database
        configs = get_active_configs(connection)
        if not configs:
            logger.error("No active data sources found in config table.")
            return

        logger.info(f"Found {len(configs)} active data sources to scrape.")

        # Khởi tạo scraper manager
        scraper_manager = ScraperManager()

        # Kiểm tra trạng thái scrapers
        scraper_status = scraper_manager.get_scraper_status()
        logger.info(f"Scraper status: {scraper_status}")

        # Scrape từ tất cả các nguồn
        all_scraped_flights = scraper_manager.scrape_all_sources(configs, search_routes, search_date)

        # Làm sạch dữ liệu
        cleaned_flights = scraper_manager.clean_flight_data(all_scraped_flights)

        if cleaned_flights:
            # Log summary
            sources_summary = {}
            for flight in cleaned_flights:
                source = flight['source']
                sources_summary[source] = sources_summary.get(source, 0) + 1

            logger.info("Scraping summary:")
            for source, count in sources_summary.items():
                logger.info(f"  {source}: {count} flights")
                log_message(connection, "INFO", f"Scraped {count} flights from {source}", source_name=source)
        else:
            logger.warning("No valid flight data to insert into database.")
            log_message(connection, "WARNING", "No valid flight data scraped from any source.")

        log_message(connection, "INFO", "Multi-source flight data scraping process completed.")

    except Exception as e:
        error_msg = f"Critical error in main process: {e}"
        logger.error(error_msg)
        log_message(connection, "ERROR", error_msg)

    finally:
        try:
            connection.close()
            logger.info("Database connection closed.")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

def scrape_single_source(data_src: DataSource):
    connection = get_db_connection()
    if not connection:
        logger.error("Cannot connect to database. Program terminated.")
        return None
    search_date = datetime.now() + timedelta(days=1)
    airport_code = get_airport(connection)
    routes = buidl_origin_destination(airport_code)
    configs = get_active_configs(connection)

    for config in configs:
        if config.get('source_name') == data_src.value:
            scraperManager = ScraperManager()
            flights = scraperManager.scrape_single_source(config, routes, search_date)
            csv_path=  save_to_csv(flights, data_src.value)
            load_csv_to_sqlite(csv_path)


    return None


def save_to_csv(flights, file_name, base_folder="data"):
    if not flights:
        logger.warning("No flights to save to CSV.")
        return

    today_str = datetime.now().strftime("%Y%m%d")
    folder_name= f"scrap_{today_str}"
    folder_path = os.path.join(base_folder, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    file_name = f"{file_name}.csv"
    file_path = os.path.join(folder_path, file_name)

    column = flights[0].keys()
    with open(file_path, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, column)
        writer.writeheader()
        writer.writerows(flights)

    logger.info(f"Saved {len(flights)} flights to CSV file: {file_name}")
    return file_path

def load_csv_to_sqlite(file_path):

    sqlite_connector = get_sqlite_connection()
    if not sqlite_connector:
        logger.error("Cannot connect to SQLite database. Program terminated.")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            rows_to_insert = []

            for row in csv_reader:
                duration = int(row['duration_minutes']) if row['duration_minutes'] else None
                price = float(row['price']) if row['price'] else None
                stops = int(row['stops']) if row['stops'] else None

                rows_to_insert.append((
                    row['flight_code'],
                    row['airline'],
                    row['departure_time'],
                    row['arrival_time'],
                    duration,
                    price,
                    stops,
                    row['departure_airport'],
                    row['arrival_airport'],
                    row['currency'],
                    row['source'],
                    row['route']
                ))

            insert_query = """
                               INSERT INTO flights_metadata (flight_code, airline, departure_time, arrival_time, \
                                                             duration_minutes, price, stops, \
                                                             departure_airport, arrival_airport, \
                                                             currency, source, route)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                               """

            cursor = sqlite_connector.cursor()
            cursor.executemany(insert_query, rows_to_insert)
            sqlite_connector.commit()

    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")

    finally:
        sqlite_connector.close()
        logger.info("SQLite connection closed.")


if __name__ == "__main__":
    clear_sqlite_db()
    scrape_single_source(DataSource.TRAVELOKA_DATA_SRC)
