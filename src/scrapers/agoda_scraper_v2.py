#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
import logging
import re
import random
from bs4 import BeautifulSoup
import traceback

class AgodaScraperV2:
    def __init__(self):
        self.source_name = "Agoda.com"
        self.base_url = "https://www.agoda.com/flights"

    def make_driver(self, headless=False):
        """Sử dụng webdriver-manager để tự động quản lý driver."""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Bypass detection
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        return driver

    def build_search_url(self, origin, destination, search_date):
        """Xây dựng URL tìm kiếm cho Agoda."""
        dep_dt_str = search_date.strftime("%Y-%m-%d")
        return (f"https://www.agoda.com/flights/results?departureFrom={origin}&departureFromType=1"
                f"&arrivalTo={destination}&arrivalToType=1&departDate={dep_dt_str}"
                f"&searchType=1&cabinType=Economy&adults=1&sort=8")

    def wait_and_scroll(self, driver, wait):
        """Chờ và scroll với chiến lược tích cực"""
        print("Waiting for page to load and scrolling...")
        
        # Chờ một chút để trang bắt đầu render
        time.sleep(8)
        
        # Scroll nhiều lần để load content
        last_height = driver.execute_script("return document.body.scrollHeight")
        scrolls_without_change = 0
        
        for i in range(20):  # Tăng số lần scroll
            # Scroll xuống
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"Scroll {i+1}/20...")
            
            # Chờ content load
            time.sleep(2.5)
            
            # Kiểm tra height
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                scrolls_without_change += 1
                if scrolls_without_change >= 3:
                    break
            else:
                scrolls_without_change = 0
                last_height = new_height
            
            # Scroll lên một chút
            if i % 3 == 0:
                driver.execute_script("window.scrollBy(0, -300);")
                time.sleep(1)
        
        # Scroll về đầu
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)

    def debug_page_structure(self, driver):
        """Phân tích cấu trúc trang để tìm patterns"""
        print("\n=== DEBUG: Analyzing page structure ===")
        
        # Lấy tất cả các div elements
        all_divs = driver.find_elements(By.TAG_NAME, "div")
        print(f"Total DIV elements: {len(all_divs)}")
        
        # Tìm elements có chứa giá
        price_patterns = ["VND", "₫", "đ", "1,", "2,", "3,", "4,", "5,"]
        price_elements = []
        
        for div in all_divs[:500]:  # Giới hạn để không quá lâu
            try:
                text = div.text.strip()
                if any(pattern in text for pattern in price_patterns) and len(text) < 100:
                    price_elements.append(div)
            except:
                continue
        
        print(f"Elements containing price indicators: {len(price_elements)}")
        
        # Phân tích class patterns
        class_patterns = {}
        for elem in price_elements[:20]:
            try:
                classes = elem.get_attribute("class")
                if classes:
                    for cls in classes.split():
                        if cls:
                            class_patterns[cls] = class_patterns.get(cls, 0) + 1
            except:
                continue
        
        # In ra top classes
        sorted_classes = sorted(class_patterns.items(), key=lambda x: x[1], reverse=True)
        print("\nTop common classes in price elements:")
        for cls, count in sorted_classes[:10]:
            print(f"  {cls}: {count}")
        
        # Tìm parent elements
        print("\nAnalyzing parent structures...")
        parent_tags = {}
        for elem in price_elements[:20]:
            try:
                parent = elem.find_element(By.XPATH, "..")
                tag = parent.tag_name
                parent_class = parent.get_attribute("class") or "no-class"
                key = f"{tag}.{parent_class[:50]}"
                parent_tags[key] = parent_tags.get(key, 0) + 1
            except:
                continue
        
        sorted_parents = sorted(parent_tags.items(), key=lambda x: x[1], reverse=True)
        print("Top parent structures:")
        for structure, count in sorted_parents[:10]:
            print(f"  {structure}: {count}")
        
        print("=== END DEBUG ===\n")

    def find_flight_elements_dynamic(self, driver):
        """Tìm flight elements bằng cách phân tích động"""
        print("Attempting to find flight elements dynamically...")
        
        # Chiến lược 1: Tìm theo text chứa thời gian và giá
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Tìm tất cả elements chứa pattern giờ (HH:MM)
        time_pattern = re.compile(r'\d{2}:\d{2}')
        elements_with_time = []
        
        for elem in soup.find_all(['div', 'span']):
            text = elem.get_text(strip=True)
            if time_pattern.search(text):
                elements_with_time.append(elem)
        
        print(f"Found {len(elements_with_time)} elements with time pattern")
        
        # Tìm parent chung chứa cả time và price
        flight_candidates = []
        
        for time_elem in elements_with_time:
            parent = time_elem.parent
            # Đi lên 3-4 cấp để tìm container
            for _ in range(4):
                if parent:
                    parent_text = parent.get_text(strip=True)
                    # Check if parent contains both time and price indicators
                    if (time_pattern.search(parent_text) and 
                        ('VND' in parent_text or '₫' in parent_text or 'đ' in parent_text)):
                        
                        # Check if we haven't added this parent yet
                        if parent not in flight_candidates:
                            flight_candidates.append(parent)
                            break
                    parent = parent.parent
        
        print(f"Found {len(flight_candidates)} flight candidate containers")
        return flight_candidates

    def parse_flight_from_element(self, element, search_date):
        """Parse flight data từ element bất kỳ"""
        try:
            text = element.get_text(" ", strip=True)
            
            # Tìm airline
            airline_patterns = [
                r"(Vietnam Airlines|VietJet Air|Vietjet Air|Bamboo Airways|Pacific Airlines|Vietravel Airlines)",
                r"(VN|VJ|QH|BL|VU)\s*\d+"
            ]
            airline = None
            for pattern in airline_patterns:
                match = re.search(pattern, text, re.I)
                if match:
                    airline = match.group(1).strip()
                    break
            
            if not airline:
                return None
            
            # Tìm times
            time_matches = re.findall(r'(\d{2}:\d{2})', text)
            if len(time_matches) < 2:
                return None
            
            departure_time_str = time_matches[0]
            arrival_time_str = time_matches[1]
            
            # Tìm price
            price_patterns = [
                r'đ\s*([\d,.]+)',
                r'([\d,.]+)\s*VND',
                r'([\d,.]+)\s*₫',
            ]
            
            price = None
            for pattern in price_patterns:
                match = re.search(pattern, text)
                if match:
                    price = int(re.sub(r'[.,]', '', match.group(1)))
                    break
            
            if not price:
                return None
            
            # Parse datetime
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
            
        except Exception as e:
            return None

    def scrape_flights(self, origin, destination, search_date):
        print(f"\n{'='*60}")
        print(f"Starting Agoda V2 scraping: {origin} -> {destination}")
        print(f"{'='*60}\n")
        
        driver = None
        scraped_flights = []

        try:
            driver = self.make_driver(headless=False)
            url = self.build_search_url(origin, destination, search_date)
            print(f"Opening URL: {url}")
            driver.get(url)

            wait = WebDriverWait(driver, 60)
            
            # Chờ và scroll
            self.wait_and_scroll(driver, wait)
            
            # Debug page structure
            self.debug_page_structure(driver)
            
            # Tìm flight elements động
            flight_elements = self.find_flight_elements_dynamic(driver)
            
            if not flight_elements:
                print("⚠ No flight elements found with dynamic detection")
                
                # Lưu debug files
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"debug_agoda_{origin}_{destination}_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")
                
                html_path = f"debug_agoda_{origin}_{destination}_{timestamp}.html"
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"HTML saved: {html_path}")
                
                return scraped_flights
            
            # Parse flights
            print(f"\nParsing {len(flight_elements)} potential flight containers...")
            seen_flights = set()
            
            for idx, element in enumerate(flight_elements, 1):
                try:
                    flight_data = self.parse_flight_from_element(element, search_date)
                    if flight_data:
                        # Tránh duplicate
                        key = f"{flight_data['flight_code']}-{flight_data['price']}"
                        if key not in seen_flights:
                            seen_flights.add(key)
                            
                            flight_data.update({
                                "departure_airport": origin,
                                "arrival_airport": destination,
                                "currency": "VND",
                                "source": self.source_name,
                                "route": f"{origin}-{destination}",
                            })
                            scraped_flights.append(flight_data)
                            print(f"  [{len(scraped_flights)}] ✓ {flight_data['airline']} - {flight_data['departure_time'][11:16]} → {flight_data['arrival_time'][11:16]} - {flight_data['price']:,.0f} VND")
                except Exception as e:
                    continue

        except Exception as e:
            print(f"\n❌ Error during scraping: {e}")
            traceback.print_exc()
            
        finally:
            if driver:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"final_agoda_{origin}_{destination}_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                print(f"\nFinal screenshot: {screenshot_path}")
                driver.quit()
        
        print(f"\n{'='*60}")
        print(f"✓ Scraping completed: Found {len(scraped_flights)} flights")
        print(f"{'='*60}\n")
        
        return scraped_flights