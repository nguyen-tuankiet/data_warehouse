# scraper/base_scraper.py
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException, NoSuchElementException
from datetime import datetime, timedelta
import logging

# --- HÀM DỌN DẸP POP-UP CHUYÊN DỤNG ---
def clear_popups(driver, wait):
    """
    Tìm và đóng tất cả các loại pop-up, banner quảng cáo có thể xuất hiện.
    """
    print("Checking and cleaning up pop-ups...")
    
    # Chờ một vài giây để mọi thứ kịp hiện ra
    time.sleep(3)
    
    # Danh sách các selector cho pop-up và close button
    popup_selectors = [
        '//div[@role="dialog"]',
        '//div[contains(@class, "modal")]',
        '//div[contains(@class, "popup")]',
        '//div[contains(@class, "overlay")]',
        '//div[contains(@class, "banner")]'
    ]
    
    close_button_selectors = [
        './/button[contains(@aria-label, "close") or contains(@aria-label, "Close")]',
        './/button[contains(@class, "close")]',
        './/div[@aria-label="close" or @aria-label="Close"]',
        './/span[contains(@class, "close")]',
        './/i[contains(@class, "close")]',
        './/*[text()="×"]',
        './/*[text()="✕"]'
    ]
    
    popups_closed = 0
    
    # Tìm và đóng các pop-up
    for popup_selector in popup_selectors:
        try:
            popups = driver.find_elements(By.XPATH, popup_selector)
            for popup in popups:
                if popup.is_displayed():
                    # Thử tìm và click nút đóng
                    for close_selector in close_button_selectors:
                        try:
                            close_button = popup.find_element(By.XPATH, close_selector)
                            if close_button.is_displayed():
                                driver.execute_script("arguments[0].click();", close_button)
                                print(f" -> Closed pop-up with close button.")
                                popups_closed += 1
                                time.sleep(0.5)
                                break
                        except:
                            continue
                    
                    # Nếu không tìm thấy nút đóng, thử click vào overlay
                    try:
                        driver.execute_script("arguments[0].click();", popup)
                        print(" -> Tried to close pop-up by clicking overlay.")
                        time.sleep(0.5)
                    except:
                        pass
                        
        except Exception as e:
            continue
    
    # Thử đóng bằng phím Escape
    try:
        from selenium.webdriver.common.keys import Keys
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        print(" -> Tried to close pop-up with Escape key.")
        time.sleep(0.5)
    except:
        pass
    
    # Xóa các cookie banner nếu có
    try:
        cookie_selectors = [
            '//div[contains(@class, "cookie")]//button[contains(text(), "Accept")]',
            '//div[contains(@class, "cookie")]//button[contains(text(), "Đồng ý")]',
            '//button[contains(text(), "Accept All")]',
            '//button[contains(text(), "Accept cookies")]'
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_button = driver.find_element(By.XPATH, selector)
                if cookie_button.is_displayed():
                    cookie_button.click()
                    print(" -> Accepted cookies.")
                    time.sleep(0.5)
                    break
            except:
                continue
    except:
        pass

    print(f"Finished cleaning up pop-ups. Closed {popups_closed} pop-ups.")


# ----- CÁC HÀM HỖ TRỢ (Giữ nguyên) -----
def parse_price(price_text):
    try:
        return int("".join(filter(str.isdigit, price_text)))
    except (ValueError, TypeError): return None

def parse_duration(duration_text):
    try:
        parts = duration_text.replace(' ', '').split('h')
        hours = int(parts[0]) if parts[0] else 0
        minutes = int(parts[1].replace('m', '')) if len(parts) > 1 and parts[1] else 0
        return hours * 60 + minutes
    except (ValueError, IndexError): return None

# ----- HÀM SCRAPING CHÍNH (Phiên bản cải tiến) -----
def scrape_flights(url, source_name, origin, destination, search_date):
    print(f"Starting data scraping from: {source_name}")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    driver = None
    scraped_flights = []
    
    try:
        # Cấu hình Chrome với các tùy chọn tối ưu hơn
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--log-level=3")
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        # options.add_argument("--disable-images")  # Commented out - may break some sites
        # options.add_argument("--disable-javascript")  # Commented out - Traveloka needs JS
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Not supported
        # options.add_experimental_option('useAutomationExtension', False)  # Not supported
        # options.add_experimental_option("detach", True)  # Not supported in this version
        
        # Khởi tạo driver với Chrome version 140 (tương thích với Chrome hiện tại)
        try:
            driver = uc.Chrome(options=options, use_subprocess=True, version_main=140)
            logger.info("Chrome driver initialized successfully with version 140")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver with version 140: {e}")
            # Fallback: try auto-detection
            try:
                driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
                logger.info("Chrome driver initialized successfully with auto-detection")
            except Exception as e2:
                logger.error(f"Failed to initialize Chrome driver: {e2}")
                return []
            
        wait = WebDriverWait(driver, 30)
        
        print(f"Opening page: {url}")
        driver.get(url)
        time.sleep(3)  # Chờ trang load

        # IMPORTANT STEP: CLEAN UP INTERFACE
        clear_popups(driver, wait)

        print(f"Filling search information: {origin} -> {destination}, date {search_date.strftime('%Y-%m-%d')}")
        
        # Tìm và điền form với nhiều selector alternatives
        try:
            # 1. Nhập điểm đi - thử nhiều selector
            origin_selectors = [
                '//input[@placeholder="Từ đâu?"]',
                '//input[@aria-label="Origin"]',
                '//input[@data-testid="origin-input"]',
                '//input[contains(@class, "origin")]'
            ]
            
            origin_input = None
            for selector in origin_selectors:
                try:
                    origin_input = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    break
                except TimeoutException:
                    continue
                    
            if not origin_input:
                raise Exception("Could not find origin input field")
                
            origin_input.clear()
            origin_input.send_keys(origin)
            time.sleep(1)
            
            # Click vào suggestion
            suggestion_selectors = [
                f'//div[contains(@class, "suggestion") and contains(text(), "{origin}")]',
                f'//div[contains(@class, "dropdown")]//div[contains(text(), "{origin}")]',
                f'//li[contains(text(), "{origin}")]'
            ]
            
            for selector in suggestion_selectors:
                try:
                    suggestion = driver.find_element(By.XPATH, selector)
                    suggestion.click()
                    break
                except NoSuchElementException:
                    continue

            # 2. Nhập điểm đến
            dest_selectors = [
                '//input[@placeholder="Đến đâu?"]',
                '//input[@aria-label="Destination"]',
                '//input[@data-testid="destination-input"]',
                '//input[contains(@class, "destination")]'
            ]
            
            dest_input = None
            for selector in dest_selectors:
                try:
                    dest_input = driver.find_element(By.XPATH, selector)
                    break
                except NoSuchElementException:
                    continue
                    
            if not dest_input:
                raise Exception("Could not find destination input field")
                
            dest_input.clear()
            dest_input.send_keys(destination)
            time.sleep(1)
            
            # Click vào suggestion destination
            for selector in suggestion_selectors:
                try:
                    suggestion = driver.find_element(By.XPATH, selector.replace(origin, destination))
                    suggestion.click()
                    break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            logger.error(f"Error filling search form: {e}")
            raise
            
        # 3. Chọn ngày đi
        try:
            day_str = str(search_date.day)
            date_selectors = [
                f'//div[@role="button" and starts-with(@aria-label, "{day_str} ") and @aria-disabled="false"]',
                f'//td[contains(@class, "date") and text()="{day_str}"]',
                f'//div[contains(@class, "date") and text()="{day_str}"]'
            ]
            
            date_clicked = False
            for selector in date_selectors:
                try:
                    date_element = driver.find_element(By.XPATH, selector)
                    date_element.click()
                    date_clicked = True
                    break
                except NoSuchElementException:
                    continue
                    
            if not date_clicked:
                logger.warning("Could not select date, using default date")
                
        except Exception as e:
            logger.warning(f"Error selecting date: {e}")

        # 4. Nhấn nút Tìm kiếm
        search_selectors = [
            '//button[contains(text(), "Tìm kiếm")]',
            '//button[contains(text(), "Search")]',
            '//div[@role="button" and .//div[text()="Tìm kiếm"]]',
            '//input[@type="submit"]'
        ]
        
        search_clicked = False
        for selector in search_selectors:
            try:
                search_button = driver.find_element(By.XPATH, selector)
                search_button.click()
                search_clicked = True
                break
            except NoSuchElementException:
                continue
                
        if not search_clicked:
            raise Exception("Could not find search button")
            
        print("Search button clicked. Waiting for results page...")
        time.sleep(5)

        # --- TRÍCH XUẤT DỮ LIỆU với selectors cải tiến ---
        result_selectors = [
            '//div[contains(@class, "flight-result")]',
            '//div[contains(@class, "flight-card")]',
            '//div[contains(@class, "result-item")]',
            '//div[@data-testid="flight-card"]'
        ]
        
        flight_cards = []
        for selector in result_selectors:
            try:
                flight_cards = driver.find_elements(By.XPATH, selector)
                if flight_cards:
                    break
            except:
                continue
                
        if not flight_cards:
            # Thử tìm với selector cũ
            try:
                flight_cards = driver.find_elements(By.XPATH, '//div[@class="css-1dbjc4n r-14l270h r-156s2ag"]/div[contains(@class, "r-1loqt21")]')
            except:
                pass
                
        print(f"Found {len(flight_cards)} flights on the page.")

        if not flight_cards:
            driver.save_screenshot(f"debug_no_flights_{origin}_{destination}.png")
            logger.warning("No flights found")

        for idx, card in enumerate(flight_cards[:10], 1):  # Giới hạn 10 chuyến đầu tiên
            try:
                # Trích xuất dữ liệu với error handling tốt hơn
                flight_data = extract_flight_data(card, search_date, source_name)
                if flight_data:
                    scraped_flights.append(flight_data)
                    print(f"  [{idx}] Đã cào: {flight_data['airline']} | {flight_data['price']} VND")
            except Exception as e:
                logger.warning(f"Error extracting flight data {idx}: {e}")
                continue

    except Exception as e:
        error_msg = f"Serious error during scraping: {e}"
        print(error_msg)
        logger.error(error_msg)
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if driver:
                driver.save_screenshot(f"error_{origin}_{destination}_{timestamp}.png")
                print(f"Saved error screenshot: error_{origin}_{destination}_{timestamp}.png")
        except Exception as screenshot_error:
            logger.error(f"Could not save screenshot: {screenshot_error}")
            
    finally:
        # Đảm bảo driver được đóng đúng cách
        if driver:
            try:
                driver.quit()
                logger.info("Chrome driver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing Chrome driver: {e}")
                
        print(f"Completed scraping from {source_name}. Found {len(scraped_flights)} flights.")
        
    return scraped_flights


def extract_flight_data(card, search_date, source_name):
    """Trích xuất dữ liệu từ một thẻ chuyến bay"""
    try:
        # Thử nhiều selector cho airline
        airline_selectors = [
            './/div[contains(@class, "airline")]',
            './/span[contains(@class, "airline")]',
            './/div[contains(@class, "carrier")]',
            './/div[@class="css-1dbjc4n r-1awozwy r-18u37iz r-1wtj0ep"]/div[1]'
        ]
        
        airline = None
        for selector in airline_selectors:
            try:
                airline = card.find_element(By.XPATH, selector).text.strip()
                if airline:
                    break
            except:
                continue
                
        if not airline:
            return None
            
        # Thử nhiều selector cho thời gian
        time_selectors = [
            './/div[contains(@class, "time")]',
            './/span[contains(@class, "time")]',
            './/div[contains(@class, "departure")]',
            './/div[@class="css-1dbjc4n r-1e081e0"]/div[@class="css-1dbjc4n"]'
        ]
        
        departure_time_str = None
        arrival_time_str = None
        
        for selector in time_selectors:
            try:
                time_elements = card.find_elements(By.XPATH, selector)
                if len(time_elements) >= 2:
                    departure_time_str = time_elements[0].text.strip()
                    arrival_time_str = time_elements[1].text.strip()
                    break
            except:
                continue
                
        if not departure_time_str or not arrival_time_str:
            return None
            
        # Thử nhiều selector cho giá
        price_selectors = [
            './/div[contains(@class, "price")]//span',
            './/span[contains(@class, "price")]',
            './/div[contains(@class, "cost")]',
            './/div[contains(@class, "r-1jkjb")]/span'
        ]
        
        price_text = None
        for selector in price_selectors:
            try:
                price_element = card.find_element(By.XPATH, selector)
                price_text = price_element.text.strip()
                if price_text:
                    break
            except:
                continue
                
        if not price_text:
            return None
            
        # Tạo flight data
        departure_dt = datetime.strptime(f"{search_date.strftime('%Y-%m-%d')} {departure_time_str}", '%Y-%m-%d %H:%M')
        arrival_dt_temp = datetime.strptime(f"{search_date.strftime('%Y-%m-%d')} {arrival_time_str}", '%Y-%m-%d %H:%M')
        arrival_dt = (arrival_dt_temp + timedelta(days=1)) if arrival_dt_temp < departure_dt else arrival_dt_temp

        return {
            "flight_code": f"{airline.split(' ')[0].upper()}-{departure_time_str.replace(':', '')}",
            "airline": airline,
            "departure_airport": origin,
            "arrival_airport": destination,
            "departure_time": departure_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "arrival_time": arrival_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_minutes": None,  # Có thể thêm logic parse duration sau
            "price": parse_price(price_text),
            "source": source_name
        }
        
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error extracting flight data: {e}")
        return None