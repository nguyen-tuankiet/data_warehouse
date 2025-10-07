# main.py
import logging
import sys
import argparse
from datetime import datetime, timedelta
from config.db_connector import get_db_connection
from config.db_manager import setup_database, get_active_configs, log_message, insert_flights_data
from scrapers.scraper_manager import ScraperManager

# Ensure console uses UTF-8 to avoid encoding errors on Windows consoles
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Setup logging (UTF-8 for file handler)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flight_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def main():
    """
    Hàm chính điều phối toàn bộ quy trình ETL cho 3 website
    """
    logger = logging.getLogger(__name__)
    
    # ----- CẤU HÌNH TÌM KIẾM -----
    search_routes = [
        {"origin": "SGN", "destination": "HAN"},
        # {"origin": "SGN", "destination": "DAD"},
        # {"origin": "HAN", "destination": "SGN"},
        # {"origin": "DAD", "destination": "SGN"},
    ]
    
    # Tìm kiếm cho những ngày tới
    search_date = datetime.now() + timedelta(days=2)
    # ----------------------------

    connection = get_db_connection()
    if not connection:
        logger.error("Cannot connect to database. Program terminated.")
        return

    try:
        # Setup database và tables
        setup_database(connection)
        log_message(connection, "INFO", "Starting multi-source flight data scraping process.")

        # Lấy configs từ database
        configs = get_active_configs(connection)
        if not configs:
            log_message(connection, "WARNING", "No active URL configurations found in config table.")
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
            logger.info(f"Total scraped {len(cleaned_flights)} valid flights. Inserting into database...")
            
            # Insert vào database
            insert_flights_data(connection, cleaned_flights)
            
            log_message(connection, "INFO", f"Successfully inserted/updated {len(cleaned_flights)} flight records into database.")
            logger.info("Database insertion completed.")
            
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

def scrape_single_source(source_name: str, origin: str, destination: str, search_date: datetime = None):
    """
    Hàm để scrape từ một nguồn cụ thể (dùng cho testing)
    """
    if not search_date:
        search_date = datetime.now() + timedelta(days=2)
    
    logger = logging.getLogger(__name__)
    
    connection = get_db_connection()
    if not connection:
        logger.error("Cannot connect to database.")
        return []
    
    try:
        configs = get_active_configs(connection)
        target_config = None
        
        for config in configs:
            if config['source_name'] == source_name:
                target_config = config
                break
        
        if not target_config:
            logger.error(f"Source {source_name} not found in active configs")
            return []
        
        scraper_manager = ScraperManager()
        flights = scraper_manager.scrape_single_source(
            source_name, 
            target_config['scraper_class'], 
            origin, 
            destination, 
            search_date
        )
        
        cleaned_flights = scraper_manager.clean_flight_data(flights)
        
        if cleaned_flights:
            insert_flights_data(connection, cleaned_flights)
            logger.info(f"Inserted {len(cleaned_flights)} flights from {source_name}")
        
        return cleaned_flights
        
    finally:
        connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flight scrapers runner")
    parser.add_argument("--source", dest="source", type=str, default=None,
                        help="Run a single source by name (e.g. Booking.com, Agoda.com, Traveloka.com)")
    parser.add_argument("--origin", dest="origin", type=str, default="SGN",
                        help="Origin IATA code, default SGN")
    parser.add_argument("--destination", dest="destination", type=str, default="HAN",
                        help="Destination IATA code, default HAN")
    parser.add_argument("--date", dest="date", type=str, default=None,
                        help="Departure date YYYY-MM-DD; default is today+2 days")

    args = parser.parse_args()

    if args.source:
        # Single-source mode
        try:
            if args.date:
                from datetime import datetime
                dep_date = datetime.strptime(args.date, "%Y-%m-%d")
            else:
                dep_date = None
            scrape_single_source(args.source, args.origin, args.destination, dep_date)
        except Exception as _:
            # Fall back to multi-source if parsing failed
            main()
    else:
        # Multi-source (default)
        main()