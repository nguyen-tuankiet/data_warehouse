# scrapers/scraper_manager.py
from typing import List, Dict, Any
from datetime import datetime
import logging

from .booking_api_scraper import BookingApiScraper
from .agoda_scraper_v2 import AgodaScraperV2
from .traveloka_scraper_v2 import TravelokaScraperV2
from .field_mapper import FieldMapper

class ScraperManager:
    """Manager class để điều phối các scraper khác nhau"""
    
    def __init__(self):
        self.scrapers = {
            'BookingApiScraper': BookingApiScraper(),
            'AgodaScraperV2': AgodaScraperV2(),
            'TravelokaScraperV2': TravelokaScraperV2()
        }
        self.logger = logging.getLogger(__name__)
    
    def get_scraper(self, scraper_class: str):
        """Lấy scraper instance theo class name"""
        return self.scrapers.get(scraper_class)
    
    def scrape_all_sources(self, configs: List[Dict], routes: List[Dict], search_date: datetime) -> List[Dict]:
        """Scrape từ tất cả các nguồn được cấu hình"""
        all_flights = []
        
        for config in configs:
            source_name = config['source_name']
            scraper_class = config.get('scraper_class', '')
            
            if not scraper_class:
                self.logger.warning(f"No scraper class defined for {source_name}")
                continue
                
            scraper = self.get_scraper(scraper_class)
            if not scraper:
                self.logger.error(f"Scraper class {scraper_class} not found")
                continue
            
            # Scrape cho từng route
            for route in routes:
                origin = route['origin']
                destination = route['destination']
                
                try:
                    self.logger.info(f"Scraping {source_name} for route {origin}-{destination}")
                    flights = scraper.scrape_flights(origin, destination, search_date)
                    
                    if flights:
                        all_flights.extend(flights)
                        self.logger.info(f"Found {len(flights)} flights from {source_name} for {origin}-{destination}")
                    else:
                        self.logger.warning(f"No flights found from {source_name} for {origin}-{destination}")
                        
                except Exception as e:
                    self.logger.error(f"Error scraping {source_name} for {origin}-{destination}: {e}")
                    continue
        
        return all_flights
    
    def scrape_single_source(self, source_name: str, scraper_class: str, origin: str, destination: str, search_date: datetime) -> List[Dict]:
        """Scrape từ một nguồn cụ thể"""
        scraper = self.get_scraper(scraper_class)
        if not scraper:
            self.logger.error(f"Scraper class {scraper_class} not found")
            return []
        
        try:
            self.logger.info(f"Scraping {source_name} for route {origin}-{destination}")
            flights = scraper.scrape_flights(origin, destination, search_date)
            self.logger.info(f"Found {len(flights)} flights from {source_name}")
            return flights
        except Exception as e:
            self.logger.error(f"Error scraping {source_name}: {e}")
            return []
    
    def validate_flight_data(self, flight_data: Dict) -> bool:
        """Validate flight data trước khi lưu vào database"""
        required_fields = ['flight_code', 'airline', 'departure_airport', 'arrival_airport', 'departure_time', 'arrival_time', 'price', 'source']
        
        for field in required_fields:
            if not flight_data.get(field):
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate price
        if not isinstance(flight_data.get('price'), (int, float)) or flight_data.get('price', 0) <= 0:
            self.logger.warning(f"Invalid price: {flight_data.get('price')}")
            return False
        
        # Validate datetime format
        try:
            datetime.strptime(flight_data.get('departure_time', ''), '%Y-%m-%d %H:%M:%S')
            datetime.strptime(flight_data.get('arrival_time', ''), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            self.logger.warning(f"Invalid datetime format")
            return False
        
        return True
    
    def clean_flight_data(self, flights: List[Dict]) -> List[Dict]:
        """Làm sạch và validate flight data"""
        cleaned_flights = []
        
        for flight in flights:
            if self.validate_flight_data(flight):
                # Ensure all fields have default values
                flight.setdefault('currency', 'VND')
                flight.setdefault('stops', 0)
                flight.setdefault('aircraft_type', '')
                flight.setdefault('baggage_info', '')
                flight.setdefault('meal_info', '')
                flight.setdefault('seat_class', '')
                flight.setdefault('booking_url', '')
                
                cleaned_flights.append(flight)
            else:
                self.logger.warning(f"Skipping invalid flight data: {flight.get('flight_code', 'Unknown')}")
        
        return cleaned_flights
    
    def get_scraper_status(self) -> Dict[str, bool]:
        """Lấy trạng thái của các scraper"""
        status = {}
        for name, scraper in self.scrapers.items():
            try:
                # Simple test to check if scraper is working
                status[name] = hasattr(scraper, 'scrape_flights')
            except:
                status[name] = False
        return status

