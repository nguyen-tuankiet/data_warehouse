# test_scrapers.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from config.db_connector import get_db_connection
from config.db_manager import setup_database, get_active_configs
from config.config_manager import ConfigManager
from scrapers.ScraperManager import ScraperManager
from scrapers.BookingScraper import BookingApiScraper
from scrapers.AgodaScraper import AgodaScraperV2
from scrapers.TravelokaScraper import TravelScraperV2

def test_database_connection():
    """Test kết nối database"""
    print("=== Testing Database Connection ===")
    connection = get_db_connection()
    if connection:
        print("✓ Database connection successful")
        connection.close()
        return True
    else:
        print("✗ Database connection failed")
        return False

def test_database_setup():
    """Test setup database tables"""
    print("\n=== Testing Database Setup ===")
    connection = get_db_connection()
    if not connection:
        print("✗ Cannot connect to database")
        return False
    
    try:
        setup_database(connection)
        print("✓ Database setup completed")
        
        # Test get configs
        configs = get_active_configs(connection)
        print(f"✓ Found {len(configs)} active configs")
        for config in configs:
            print(f"  - {config['source_name']}: {config['scraper_class']}")
        
        return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False
    finally:
        connection.close()

def test_config_manager():
    """Test config manager"""
    print("\n=== Testing Config Manager ===")
    try:
        config_manager = ConfigManager()
        
        # Test get all configs
        all_configs = config_manager.get_all_configs()
        print(f"✓ Loaded {len(all_configs)} provider configs")
        
        # Test get active configs
        active_configs = config_manager.get_active_configs()
        print(f"✓ Found {len(active_configs)} active providers")
        
        # Test get specific config
        for provider in ['booking', 'agoda', 'traveloka']:
            config = config_manager.get_config(provider)
            if config:
                print(f"✓ {provider}: {config['provider_name']} - {config['scraper_class']}")
            else:
                print(f"✗ {provider}: Config not found")
        
        # Test config summary
        summary = config_manager.get_config_summary()
        print(f"✓ Config summary: {summary['active_providers']}/{summary['total_providers']} active")
        
        return True
    except Exception as e:
        print(f"✗ Config manager test failed: {e}")
        return False

def test_scraper_initialization():
    """Test khởi tạo các scraper"""
    print("\n=== Testing Scraper Initialization ===")
    try:
        scrapers = {
            'BookingApiScraper': BookingApiScraper(),
            'AgodaScraperV2': AgodaScraperV2(),
            'TravelokaScraperV2': TravelScraperV2()
        }
        
        for name, scraper in scrapers.items():
            if hasattr(scraper, 'scrape_flights'):
                print(f"✓ {name}: Initialized successfully")
            else:
                print(f"✗ {name}: Missing scrape_flights method")
        
        # Test scraper manager
        scraper_manager = ScraperManager()
        status = scraper_manager.get_scraper_status()
        print(f"✓ Scraper Manager: {status}")
        
        return True
    except Exception as e:
        print(f"✗ Scraper initialization test failed: {e}")
        return False

def test_single_scraper(scraper_name: str, origin: str = "SGN", destination: str = "HAN"):
    """Test một scraper cụ thể"""
    print(f"\n=== Testing {scraper_name} ===")
    
    search_date = datetime.now() + timedelta(days=2)
    
    try:
        if scraper_name == "BookingApiScraper":
            scraper = BookingApiScraper()
        elif scraper_name == "AgodaScraperV2":
            scraper = AgodaScraperV2()
        elif scraper_name == "TravelokaScraperV2":
            scraper = TravelScraperV2()
        else:
            print(f"✗ Unknown scraper: {scraper_name}")
            return False
        
        print(f"Testing {scraper_name} for route {origin} -> {destination}")
        print("Note: This will open a browser window for testing...")
        
        # Uncomment the line below to actually test scraping
        # flights = scraper.scrape_flights(origin, destination, search_date)
        # print(f"✓ Found {len(flights)} flights")
        
        print("✓ Scraper test completed (browser test skipped)")
        return True
        
    except Exception as e:
        print(f"✗ {scraper_name} test failed: {e}")
        return False

def test_field_mappings():
    """Test field mappings"""
    print("\n=== Testing Field Mappings ===")
    try:
        from src.etl.field_mapper import FieldMapper
        
        for source in ['Booking.com', 'Agoda', 'Traveloka']:
            mapper = FieldMapper(source)
            
            # Test get selectors
            airline_selectors = mapper.get_selectors('airline')
            print(f"✓ {source} airline selectors: {len(airline_selectors)} found")
            
            # Test field type
            price_type = mapper.get_field_type('price')
            print(f"✓ {source} price type: {price_type}")
            
            # Test required field
            airline_required = mapper.is_required('airline')
            print(f"✓ {source} airline required: {airline_required}")
        
        return True
    except Exception as e:
        print(f"✗ Field mappings test failed: {e}")
        return False

def run_all_tests():
    """Chạy tất cả tests"""
    print("Starting Flight Scraper System Tests...")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Database Setup", test_database_setup),
        ("Config Manager", test_config_manager),
        ("Scraper Initialization", test_scraper_initialization),
        ("Field Mappings", test_field_mappings),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! System is ready.")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    return passed == total

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            run_all_tests()
        elif command == "test-booking":
            test_single_scraper("BookingApiScraper")
        elif command == "test-agoda":
            test_single_scraper("AgodaScraperV2")
        elif command == "test-traveloka":
            test_single_scraper("TravelokaScraperV2")
        elif command == "db":
            test_database_connection()
            test_database_setup()
        elif command == "config":
            test_config_manager()
        else:
            print("Unknown command. Available commands:")
            print("  test - Run all tests")
            print("  test-booking - Test Booking scraper")
            print("  test-agoda - Test Agoda scraper")
            print("  test-traveloka - Test Traveloka scraper")
            print("  db - Test database only")
            print("  config - Test config manager only")
    else:
        run_all_tests()

if __name__ == "__main__":
    main()

