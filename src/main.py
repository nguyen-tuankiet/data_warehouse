import csv
import os
from datetime import datetime, timedelta

from src.config.sqlite_connector import get_sqlite_connection, clear_flight_metadata, \
    get_source_by_name, get_airport, load_dim_date
from src.helpper.hepper import buidl_origin_destination
import argparse
from src.helpper.logger_config import logger
from src.scrapers.ScraperManager import ScraperManager
from src.transform.transform_and_load_data import transform_and_load_data


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
    load_csv_to_sqlite(csv_path)


    # load_csv_to_sqlite("data/scrap_20251029/Traveloka.com.csv")

    transform_and_load_data()
    #         TODO: Create log


    return None


def save_to_csv(flights, source_name, base_folder="data"):
    if not flights:
        logger.warning("No flights to save to CSV.")
        return

    today_str = datetime.now().strftime("%Y%m%d")
    folder_name= f"scrap_{today_str}"
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
    with open(file_path, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, column)
        writer.writeheader()
        writer.writerows(flights)

    logger.info(f"Saved {len(flights)} flights to CSV file: {file_name}")
    return file_path

def load_csv_to_sqlite(file_path):
    clear_flight_metadata()
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
                    row['duration_time'],
                    row['price'],
                    row['source'],
                    row['crawled_at'],

                ))

            insert_query = """
                               INSERT INTO flights_metadata (
                               airline, departure_airport, departure_time,
                                   destination_airport, destination_time, duration_time, price, source, crawled_at
                               )
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) \
                               """

            cursor = sqlite_connector.cursor()
            cursor.executemany(insert_query, rows_to_insert)
            sqlite_connector.commit()
            logger.info(f"Inserted {cursor.rowcount} rows into flights_metadata table.")
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")

    finally:
        sqlite_connector.close()
        return None


if __name__ == "__main__":


    parser = argparse.ArgumentParser(description='Scrape and transform data from multiple sources')
    parser.add_argument('-s', '--source', type=str, help='Source name to scrape', required=False)
    parser.add_argument('-d', '--date',  type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
                        help='Date to scrape', required= False, default=datetime.now() + timedelta(days=1))
    parser.add_argument('--load-dim-date', action='store_true', help='Run load_dim_date ETL process')


    args = parser.parse_args()
    source = args.source
    date = args.date
    load_dim_flag = args.load_dim_date

    if load_dim_flag:
        path = "data/date_dim.csv"
        load_dim_date(path)
    else:
        scrape_single_source(source, date)
