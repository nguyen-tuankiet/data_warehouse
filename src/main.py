import csv
import logging
import os
from datetime import datetime, timedelta
from src.config.db_manager import get_active_configs, log_message
from src.scrapers.ScraperManager import ScraperManager
from src.config.db_connector import get_db_connection
from src.config.sqlite_connector import get_sqlite_connection, clear_sqlite_db, init_sqlite_db
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

    #         TODO: Create log


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
                rows_to_insert.append((
                    row['airline'],
                    row['departure_airport'],
                    row['departure_time'],
                    row['destination_airport'],
                    row['destination_time'],
                    row['price'],
                    row['duration_time']
                ))

            insert_query = """
                               INSERT INTO flights_metadata (
                               airline, departure_airport, departure_time,
                                   destination_airport, destination_time, duration_time, price,
                               )
                               VALUES (?, ?, ?, ?, ?, ?, ?) \
                               """

            cursor = sqlite_connector.cursor()
            cursor.executemany(insert_query, rows_to_insert)
            sqlite_connector.commit()

    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")

    finally:
        sqlite_connector.close()
        return None


if __name__ == "__main__":
    init_sqlite_db()
    clear_sqlite_db()
    scrape_single_source(DataSource.TRAVELOKA_DATA_SRC)
