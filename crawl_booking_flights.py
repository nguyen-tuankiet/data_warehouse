#!/usr/bin/env python3
"""
Crawl Booking Flights API -> CSV
Usage:
  python crawl_booking_api.py \
    ROUNDTRIP 1 ECONOMY SGN.AIRPORT CEB.AIRPORT VN PH 2025-11-01 2025-11-08
"""

import argparse
import logging
import requests
import time
import random
import pandas as pd
import re
from datetime import datetime
import os
import sys

# ---------- Config ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

BASE_URL = "https://flights.booking.com/api/flights/"

# ---------- Helpers ----------
def fetch_json(url: str, retries: int = 3, backoff: float = 2.0, timeout: float = 30.0):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }
    for attempt in range(retries):
        try:
            logging.info(f"Requesting (try {attempt+1}): {url}")
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            else:
                logging.warning(f"HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logging.error(f"Error: {e}")
        time.sleep(backoff * (2**attempt) + random.random())
    return None

def parse_price(it):
    price = None
    currency = None
    if isinstance(it, dict):
        price_block = it.get("price") or it.get("pricing") or {}
        if isinstance(price_block, dict):
            price = price_block.get("total") or price_block.get("amount")
            currency = price_block.get("currency") or price_block.get("currencyCode")
    return price, currency

def extract_segments(it):
    segs = []
    if not isinstance(it, dict):
        return segs
    itineraries = it.get("itineraries") or it.get("legs") or []
    if isinstance(itineraries, dict):
        itineraries = [itineraries]
    for itin in itineraries:
        segments = itin.get("segments") if isinstance(itin, dict) else []
        for s in segments:
            dep = s.get("departure") or {}
            arr = s.get("arrival") or {}
            segs.append({
                "airline": s.get("carrier", {}).get("name") if isinstance(s.get("carrier"), dict) else s.get("carrier", ""),
                "flight_number": s.get("flightNumber") or "",
                "depart_time": dep.get("at") or "",
                "depart_airport": dep.get("iataCode") or "",
                "arrive_time": arr.get("at") or "",
                "arrive_airport": arr.get("iataCode") or "",
                "duration": s.get("duration") or "",
            })
    return segs

def format_duration(seconds: int) -> str:
    """Convert seconds to 3h05m format"""
    if not seconds or not isinstance(seconds, (int, float)):
        return ""
    h, m = divmod(int(seconds) // 60, 60)
    return f"{h}h{m:02d}m"

def build_rows(json_data):
    rows = []
    offers = json_data.get("flightOffers", [])
    if not offers:
        return rows

    for idx, offer in enumerate(offers, 1):
        price_block = offer.get("priceBreakdown", {}).get("total", {})
        price = price_block.get("units")
        currency = price_block.get("currencyCode")

        segments = offer.get("segments", [])
        for seg in segments:
            legs = seg.get("legs", [])
            for leg in legs:
                dep_airport = leg.get("departureAirport", {}).get("code", "")
                arr_airport = leg.get("arrivalAirport", {}).get("code", "")
                dep_time = leg.get("departureTime", "")
                arr_time = leg.get("arrivalTime", "")

                flight_info = leg.get("flightInfo", {})
                flight_number = flight_info.get("flightNumber", "")
                carrier_info = flight_info.get("carrierInfo", {})
                airline_code = carrier_info.get("marketingCarrier", "")

                carriers_data = leg.get("carriersData", [])
                airline_name = carriers_data[0].get("name") if carriers_data else airline_code

                rows.append({
                    "offer": idx,
                    "airline": airline_name,
                    "flight_number": f"{airline_code}{flight_number}",
                    "depart_time": dep_time,
                    "depart_airport": dep_airport,
                    "arrive_time": arr_time,
                    "arrive_airport": arr_airport,
                    "duration": leg.get("totalTime", ""),
                    "price": price,
                    "currency": currency
                })
    return rows

def main():
    parser = argparse.ArgumentParser(description="Crawl Booking Flights API to CSV")
    parser.add_argument("type", help="Trip type: ONEWAY or ROUNDTRIP")
    parser.add_argument("adults", type=int, help="Number of adults")
    parser.add_argument("cabin", help="Cabin class: ECONOMY, BUSINESS, etc.")
    parser.add_argument("origin", help="Origin airport code (e.g. SGN.AIRPORT)")
    parser.add_argument("destination", help="Destination airport code (e.g. CEB.AIRPORT)")
    parser.add_argument("from_country", help="Origin country code (e.g. VN)")
    parser.add_argument("to_country", help="Destination country code (e.g. PH)")
    parser.add_argument("depart", help="Departure date YYYY-MM-DD")
    parser.add_argument("return_date", nargs="?", default="", help="Return date YYYY-MM-DD (if ROUNDTRIP)")
    parser.add_argument("--outdir", default="flight_data", help="Output folder")
    args = parser.parse_args()

    # build url
    url = (f"{BASE_URL}?type={args.type}&adults={args.adults}&cabinClass={args.cabin}"
           f"&children=&from={args.origin}&to={args.destination}"
           f"&fromCountry={args.from_country}&toCountry={args.to_country}"
           f"&depart={args.depart}")
    if args.type.upper() == "ROUNDTRIP" and args.return_date:
        url += f"&return={args.return_date}"
    url += "&sort=BEST&travelPurpose=leisure"

    data = fetch_json(url)
    if not data:
        logging.error("Không lấy được dữ liệu.")
        sys.exit(1)
    rows = build_rows(data)
    if not rows:
        logging.error("Không có chuyến bay trong kết quả.")
        sys.exit(1)

    df = pd.DataFrame(rows)
    os.makedirs(args.outdir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{args.origin}_{args.destination}_{args.depart}{'_'+args.return_date if args.return_date else ''}_{ts}.csv"
    path = os.path.join(args.outdir, fname)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logging.info(f"Đã lưu {len(df)} dòng vào {path}")
    print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
