import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import logging
import re
import random
from bs4 import BeautifulSoup
import traceback

class TravelScraperV2:
    def __init__(self, source_name, base_url ):
        self.source_name = source_name
        self.base_url = base_url

    def scrape_flights(self, routes, search_date):
        driver = None
        scraped_flights = []

        try:
            driver = self.make_driver(headless=False)

            for r in routes:
                origin = r["origin"]
                destination = r["destination"]
                url = self.build_search_url(origin, destination, search_date)
                logging.info(f"Opening URL: {url}")
                driver.get(url)

                wait = WebDriverWait(driver, 90)
                flight_card_selector = "div[data-testid^='flight-inventory-card-container']"
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, flight_card_selector)))

                self.scroll_page(driver)

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")

                flight_cards = soup.select(flight_card_selector)
                if not flight_cards:
                    raise ValueError("Could not find any flight cards on the page after scrolling.")

                for card in flight_cards:
                    flight_data = self.parse_flight_card(card, search_date)
                    if flight_data:
                        flight_data.update({
                            "departure_airport": origin,
                            "arrival_airport": destination,
                            "currency": "VND",
                            "source": self.source_name,
                            "route": f"{origin}-{destination}",
                        })
                        scraped_flights.append(flight_data)

        except Exception as e:
            logging.error(f"Error occurred while scraping flights: {e}")
        finally:
            if driver:
                driver.quit()
        return scraped_flights

    def make_driver(self, headless=False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.set_window_size(1280, 900)
        return driver

    def build_search_url(self, origin, destination, search_date):
        date_str = search_date.strftime("%d-%m-%Y")
        return f"https://www.traveloka.com/vi-vn/flight/fullsearch?ap={destination}.{origin}&dt={date_str}.NA&ps=1.0.0&sc=ECONOMY"

    def scroll_page(self, driver, max_scrolls=8):
        print("Scrolling page to load all flights...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(max_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2.0, 3.0))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(f"Scrolling stopped at attempt {i+1} as page height did not change.")
                break
            last_height = new_height

    def parse_flight_card(self, card_soup, search_date):

        card_text = card_soup.get_text(" ", strip=True)
        # 1. Trích xuất Hãng bay (Airline)
        airline = None
        # Ưu tiên các tên đầy đủ để tránh nhầm lẫn
        airline_patterns = [
            r"(VietJet Air|Vietjet Air|Vietnam Airlines|Bamboo Airways|Pacific Airlines|Vietravel Airlines)",
            r"(VietJet|Vietjet|Jetstar)",
            r"(VN|VJ|QH|BL|VU)" # Mã hãng bay
        ]
        for pattern in airline_patterns:
            match = re.search(pattern, card_text, re.I)
            if match:
                airline = match.group(1).strip()
                break
        if not airline: return None

        # 2. Trích xuất Giờ bay
        time_matches = re.findall(r"(\d{2}:\d{2})", card_text)
        if len(time_matches) < 2: return None
        departure_time_str, arrival_time_str = time_matches[0], time_matches[1]

        # 3. Trích xuất Giá vé (tìm giá cuối cùng trong thẻ)
        price_matches = re.findall(r"([\d.,]+)\s*VND", card_text)
        if not price_matches: return None
        price = int(re.sub(r'[.,]', '', price_matches[-1]))

        # 4. Xử lý và định dạng dữ liệu
        dep_dt = datetime.strptime(f"{search_date.strftime('%Y-%m-%d')} {departure_time_str}", '%Y-%m-%d %H:%M')
        arr_dt = datetime.strptime(f"{search_date.strftime('%Y-%m-%d')} {arrival_time_str}", '%Y-%m-%d %H:%M')
        if arr_dt < dep_dt:
            arr_dt += timedelta(days=1)
        duration_minutes = int((arr_dt - dep_dt).total_seconds() / 60)
        
        flight_number = f"{airline.split()[0].upper()}-{dep_dt.strftime('%H%M')}"

        return {
            "flight_code": flight_number,
            "airline": airline,
            "departure_time": dep_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "arrival_time": arr_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_minutes": duration_minutes,
            "price": float(price),
            "stops": 0,
        }
