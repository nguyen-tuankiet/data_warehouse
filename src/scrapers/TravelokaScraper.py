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
                    logging.warning(f"No flights found for route: {r}")

                for card in flight_cards:
                    flight_data = self.parse_flight_card(card, search_date)
                    scraped_flights.append(flight_data)

        except Exception as e:
            logging.error(f"Error occurred while scraping flights: {e}", exc_info=True)
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

        airline = None
        departure_airport = None
        departure_time = None
        destination_airport = None
        destination_time = None
        price = None
        duration_time = None

        # Get airline
        airline_div = card_soup.select_one("div.css-901oao.css-cens5h.r-uh8wd5.r-majxgm.r-fdjqy7")
        airline = airline_div.get_text(strip=True) if airline_div else None


        depart_block = card_soup.select_one('div.css-1dbjc4n.r-1habvwh.r-eqz5dr.r-9aw3ui.r-knv0ih')
        dest_block = card_soup.select_one('div.css-1dbjc4n.r-obd0qt.r-eqz5dr.r-9aw3ui.r-knv0ih:not(.r-ggk5by)')

        # depart_block
        dep_children = depart_block.find_all("div", recursive=False)
        if len(dep_children) >= 2:
            departure_time = dep_children[0].get_text(strip=True)
            departure_airport = dep_children[1].get_text(strip=True)

        # destination block
        dest_children = dest_block.find_all("div", recursive=False)
        if len(dest_block) >= 2:
            destination_time = dest_children[0].get_text(strip=True)
            destination_airport = dest_children[1].get_text(strip=True)

        # Price
        price_tag = card_soup.select_one('[data-testid="label_fl_inventory_price"]')
        price = price_tag.get_text(strip=True) if price_tag else None

        # Duration time
        duration_tag = card_soup.select_one('div.css-901oao.r-uh8wd5.r-majxgm.r-1p4rafz.r-fdjqy7')
        duration_time = duration_tag.get_text(strip=True) if duration_tag else None


        flight =  {
            "airline": airline,
            "departure_airport": departure_airport,
            "departure_time": departure_time,
            "destination_airport": destination_airport,
            "destination_time": destination_time,
            "price": price,
            "duration_time": duration_time,
        }

        return flight
