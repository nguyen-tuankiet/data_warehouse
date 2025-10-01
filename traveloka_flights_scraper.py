"""
Scraper nâng cao cho Traveloka Flights (vi-vn) - Phiên bản cải tiến
- Nhận tham số (sân bay, ngày bay) từ command-line.
- Có thể chạy cho một khoảng ngày (date range).
- Cấu trúc lại để dễ dàng tích hợp vào hệ thống tự động.
- Ghi log ra console thay vì chỉ print.
- Tên file output tự động theo ngày và chặng bay.
"""

import argparse
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import random
import pandas as pd
import re
from datetime import datetime, timedelta
from dateutil import tz
import os

# Cấu hình logging cơ bản
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------- CONFIG mặc định (có thể bị ghi đè bởi command-line) ----------------
DEFAULT_ADULTS = 1
DEFAULT_CHILDREN = 0
DEFAULT_INFANTS = 0
DEFAULT_SEAT_CLASS = "ECONOMY"
MAX_SCROLLS = 8
HEADLESS = True  # Nên để True khi chạy tự động
TIMEZONE = "Asia/Ho_Chi_Minh"
# -----------------------------------------------------------------------------------

def make_driver(headless=False):
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.set_window_size(1280, 900)
    return driver

def build_flight_search_url(dep_city, arr_city, dep_date, adults, children, infants, seat_class):
    dep_dt_str = dep_date.strftime("%d-%m-%Y")
    ap = f"{arr_city}.{dep_city}"
    dt = f"{dep_dt_str}.NA"
    ps = f"{adults}.{children}.{infants}"
    sc = seat_class
    base = "https://www.traveloka.com/vi-vn/flight/fullsearch?"
    url = f"{base}ap={ap}&dt={dt}&ps={ps}&sc={sc}"
    return url

def rand_sleep(a=0.8, b=1.8):
    time.sleep(random.uniform(a, b))

def scroll_page(driver, max_scrolls=6, pause_min=1.0, pause_max=2.0):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(pause_min, pause_max))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            time.sleep(1.0)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logging.info(f"Dừng scroll ở lần thứ {i+1} vì đã hết trang.")
                break
        last_height = new_height

def parse_flight_card(card, scraped_date):
    def safe_text(el):
        return el.get_text(" ", strip=True) if el else ""

    flight_data = {
        "airline": "", "flight_number": "", "departure_airport": "", "arrival_airport": "",
        "departure_time": "", "arrival_time": "", "duration": "", "price": None, "currency": "",
        "aircraft_type": "", "baggage_info": "", "meal_info": "", "seat_class": "", "stops": 0,
        "last_scraped": scraped_date
    }
    
    card_text = safe_text(card)
    
    airline_patterns = [
        r"(VietJet|Vietjet|Vietnam Airlines|Bamboo Airways|Jetstar|Pacific Airlines|Vietravel Airlines)",
        r"(VN|VJ|QH|BL|VU)"
    ]
    for pattern in airline_patterns:
        match = re.search(pattern, card_text, re.I)
        if match:
            flight_data["airline"] = match.group(1)
            break
            
    flight_num_match = re.search(r"([A-Z]{2,3}\s*\d{3,4})", card_text)
    if flight_num_match:
        flight_data["flight_number"] = flight_num_match.group(1).replace(" ", "")
        
    time_matches = re.findall(r"(\d{1,2}:\d{2})", card_text)
    if len(time_matches) >= 2:
        flight_data["departure_time"] = time_matches[0]
        flight_data["arrival_time"] = time_matches[1]
        
    airport_matches = re.findall(r"\(([A-Z]{3})\)", card_text)
    if len(airport_matches) >= 2:
        flight_data["departure_airport"] = airport_matches[0]
        flight_data["arrival_airport"] = airport_matches[1]

    duration_match = re.search(r"(\d{1,2}h\s*\d{0,2}m|\d{1,2}g\s*\d{0,2}p)", card_text, re.I)
    if duration_match:
        flight_data["duration"] = duration_match.group(1)

    price_matches = re.findall(r"([\d,.]+)\s*(₫|VND)", card_text)
    if price_matches:
        price_str, currency_symbol = price_matches[-1]
        try:
            price = int(re.sub(r'[.,]', '', price_str))
            flight_data["price"] = price
            flight_data["currency"] = "VND"
        except ValueError:
            logging.warning(f"Không thể chuyển đổi giá: '{price_str}'")

    if "nonstop" in card_text.lower() or "bay thẳng" in card_text.lower():
        flight_data["stops"] = 0
    elif "1 stop" in card_text.lower() or "1 điểm dừng" in card_text.lower():
        flight_data["stops"] = 1
        
    return flight_data

def extract_flight_data_from_html(html):
    soup = BeautifulSoup(html, "lxml")
    flights = []
    flight_cards = soup.find_all("div", attrs={"data-testid": re.compile(r"^flight-inventory-card-container")})
    logging.info(f"Số thẻ flight tìm được với data-testid: {len(flight_cards)}")
    
    scraped_time_iso = datetime.now(tz=tz.gettz(TIMEZONE)).isoformat()

    for idx, card in enumerate(flight_cards):
        try:
            flight_data = parse_flight_card(card, scraped_time_iso)
            if flight_data and flight_data.get("airline"):
                flights.append(flight_data)
        except Exception as e:
            logging.error(f"Lỗi khi xử lý thẻ flight {idx}: {e}")
            continue
    return flights

def scrape_single_day(dep_city, arr_city, dep_date, args):
    driver = make_driver(HEADLESS)
    flights = []
    
    try:
        search_url = build_flight_search_url(
            dep_city, arr_city, dep_date,
            args.adults, args.children, args.infants, args.seat_class
        )
        logging.info(f"Mở URL cho ngày {dep_date.strftime('%Y-%m-%d')}: {search_url}")
        driver.get(search_url)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        rand_sleep(3.0, 5.0)

        logging.info("Scrolling để load thêm chuyến bay...")
        scroll_page(driver, max_scrolls=MAX_SCROLLS, pause_min=2.0, pause_max=3.0)

        html = driver.page_source
        daily_flights = extract_flight_data_from_html(html)
        
        # Thêm thông tin ngày bay vào mỗi record
        for flight in daily_flights:
            flight['flight_date'] = dep_date.strftime('%Y-%m-%d')

        logging.info(f"Tìm thấy {len(daily_flights)} chuyến bay cho ngày {dep_date.strftime('%Y-%m-%d')}.")
        flights.extend(daily_flights)

    except Exception as e:
        logging.error(f"Lỗi trong quá trình scrape ngày {dep_date.strftime('%Y-%m-%d')}: {e}")
    finally:
        driver.quit()

    return flights

def main(args):
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        if start_date > end_date:
            raise ValueError("Ngày bắt đầu không được lớn hơn ngày kết thúc.")
    except ValueError as e:
        logging.error(f"Lỗi định dạng ngày: {e}. Sử dụng format YYYY-MM-DD.")
        return

    all_flights = []
    current_date = start_date
    while current_date <= end_date:
        daily_flights = scrape_single_day(args.departure_city, args.arrival_city, current_date, args)
        all_flights.extend(daily_flights)
        current_date += timedelta(days=1)
        if current_date <= end_date:
            logging.info("Nghỉ một lát trước khi scrape ngày tiếp theo...")
            rand_sleep(5, 10)

    if not all_flights:
        logging.warning("Không tìm thấy dữ liệu chuyến bay nào.")
        return

    # Gán ID và lưu file
    for i, flight in enumerate(all_flights, start=1):
        flight["id"] = i
    
    df = pd.DataFrame(all_flights)
    
    # Sắp xếp lại các cột
    columns = [
        "id", "flight_date", "airline", "flight_number", "departure_airport", "arrival_airport",
        "departure_time", "arrival_time", "duration", "price", "currency",
        "aircraft_type", "baggage_info", "meal_info", "seat_class", "stops", "last_scraped"
    ]
    df = df.reindex(columns=columns, fill_value="")
    
    # Tạo tên file output động
    output_dir = "flight_data"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{args.departure_city}-{args.arrival_city}_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.csv"
    output_path = os.path.join(output_dir, filename)

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logging.info(f"Đã lưu file: {output_path}")
    logging.info(f"Tổng số records: {len(df)}")
    
    logging.info("\nSample data:")
    print(df.head(3).to_string())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Traveloka Flight Scraper")
    parser.add_argument("departure_city", help="Mã sân bay đi (VD: HAN)")
    parser.add_argument("arrival_city", help="Mã sân bay đến (VD: SGN)")
    parser.add_argument("start_date", help="Ngày bắt đầu lấy dữ liệu (YYYY-MM-DD)")
    parser.add_argument("end_date", help="Ngày kết thúc lấy dữ liệu (YYYY-MM-DD)")
    
    parser.add_argument("--adults", type=int, default=DEFAULT_ADULTS, help="Số người lớn")
    parser.add_argument("--children", type=int, default=DEFAULT_CHILDREN, help="Số trẻ em")
    parser.add_argument("--infants", type=int, default=DEFAULT_INFANTS, help="Số em bé")
    parser.add_argument("--seat-class", default=DEFAULT_SEAT_CLASS, help="Hạng ghế (ECONOMY, BUSINESS, ...)")
    
    args = parser.parse_args()
    main(args)
