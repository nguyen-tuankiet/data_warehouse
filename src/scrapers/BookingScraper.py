#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import random
import logging
import re
from datetime import datetime, timedelta
import json

class BookingApiScraper:
    def __init__(self):
        self.source_name = "Booking.com"
        self.base_url = "https://flights.booking.com/api/flights/"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        
    def fetch_json(self, url: str, retries: int = 3, backoff: float = 2.0, timeout: float = 30.0):
        """Fetch JSON data từ API với retry logic"""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        
        for attempt in range(retries):
            try:
                logging.info(f"Requesting Booking API (try {attempt+1}): {url}")
                resp = requests.get(url, headers=headers, timeout=timeout)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    logging.warning(f"HTTP {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logging.error(f"Error fetching Booking API: {e}")
            time.sleep(backoff * (2**attempt) + random.random())
        return None

    def build_search_url(self, origin, destination, dep_date, trip_type="ONEWAY", adults=1, cabin="ECONOMY"):
        """Xây dựng URL tìm kiếm cho Booking API"""
        # Chuyển đổi mã sân bay thành format Booking
        origin_formatted = f"{origin}.AIRPORT"
        dest_formatted = f"{destination}.AIRPORT"
        
        # Xác định country codes (simplified)
        country_mapping = {
            "SGN": "VN", "HAN": "VN", "DAD": "VN", "CXR": "VN", "PQC": "VN",
            "BKK": "TH", "DMK": "TH", "CNX": "TH", "HKT": "TH",
            "SIN": "SG", "KUL": "MY", "CGK": "ID", "MNL": "PH"
        }
        
        from_country = country_mapping.get(origin, "VN")
        to_country = country_mapping.get(destination, "VN")
        
        url = (f"{self.base_url}?type={trip_type}&adults={adults}&cabinClass={cabin}"
               f"&children=&from={origin_formatted}&to={dest_formatted}"
               f"&fromCountry={from_country}&toCountry={to_country}"
               f"&depart={dep_date.strftime('%Y-%m-%d')}")
        
        if trip_type.upper() == "ROUNDTRIP":
            return_date = dep_date + timedelta(days=7)  # Default return after 7 days
            url += f"&return={return_date.strftime('%Y-%m-%d')}"
        
        url += "&sort=BEST&travelPurpose=leisure"
        return url

    def parse_booking_data(self, json_data):
        """Parse dữ liệu từ Booking API response"""
        flights = []
        
        if not json_data:
            return flights
            
        offers = json_data.get("flightOffers", [])
        if not offers:
            return flights

        for idx, offer in enumerate(offers, 1):
            try:
                # Lấy thông tin giá
                price_block = offer.get("priceBreakdown", {}).get("total", {})
                price = price_block.get("units")
                currency = price_block.get("currencyCode", "USD")

                # Lấy segments
                segments = offer.get("segments", [])
                for seg in segments:
                    legs = seg.get("legs", [])
                    for leg in legs:
                        # Thông tin sân bay
                        dep_airport = leg.get("departureAirport", {}).get("code", "")
                        arr_airport = leg.get("arrivalAirport", {}).get("code", "")
                        dep_time = leg.get("departureTime", "")
                        arr_time = leg.get("arrivalTime", "")

                        # Thông tin chuyến bay
                        flight_info = leg.get("flightInfo", {})
                        flight_number = flight_info.get("flightNumber", "")
                        carrier_info = flight_info.get("carrierInfo", {})
                        airline_code = carrier_info.get("marketingCarrier", "")

                        # Tên hãng hàng không
                        carriers_data = leg.get("carriersData", [])
                        airline_name = carriers_data[0].get("name") if carriers_data else airline_code

                        # Parse thời gian
                        departure_dt = None
                        arrival_dt = None
                        
                        try:
                            if dep_time:
                                departure_dt = datetime.fromisoformat(dep_time.replace('Z', '+00:00'))
                            if arr_time:
                                arrival_dt = datetime.fromisoformat(arr_time.replace('Z', '+00:00'))
                        except:
                            pass

                        # Tạo flight data
                        flight_data = {
                            "flight_code": f"{airline_code}{flight_number}",
                            "airline": airline_name or airline_code,
                            "departure_airport": dep_airport,
                            "arrival_airport": arr_airport,
                            "departure_time": departure_dt.strftime('%Y-%m-%d %H:%M:%S') if departure_dt else "",
                            "arrival_time": arrival_dt.strftime('%Y-%m-%d %H:%M:%S') if arrival_dt else "",
                            "duration_minutes": leg.get("totalTime", ""),
                            "price": price,
                            "currency": currency,
                            "source": self.source_name,
                            "route": f"{dep_airport}-{arr_airport}",
                            "stops": leg.get("stops", 0),
                            "aircraft_type": "",
                            "baggage_info": "",
                            "meal_info": "",
                            "seat_class": "ECONOMY",
                            "booking_url": ""
                        }
                        
                        flights.append(flight_data)
                        
            except Exception as e:
                logging.error(f"Error parsing Booking offer {idx}: {e}")
                continue
                
        return flights

    def scrape_flights(self, origin, destination, search_date):

        try:
            # Try multiple sort modes to increase coverage
            flights = []
            sort_modes = ["BEST", "CHEAPEST", "FASTEST"]
            for sort in sort_modes:
                url = self.build_search_url(origin, destination, search_date)
                url = url.replace("sort=BEST", f"sort={sort}")
                logging.info(f"Booking API URL: {url}")
                data = self.fetch_json(url)
                if not data:
                    continue
                flights.extend(self.parse_booking_data(data))
            # Deduplicate by flight_code + departure_time
            dedup = {}
            for f in flights:
                key = (f.get("flight_code"), f.get("departure_time"))
                dedup[key] = f
            flights = list(dedup.values())
            
            # Log results
            for flight in flights:
                print(f"  -> {flight['airline']} | {flight['price']} {flight['currency']} | {flight['departure_time']}")
                
            return flights
            
        except Exception as e:
            return []
