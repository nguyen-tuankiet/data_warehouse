# scrapers/field_mapper.py
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class FieldMapper:
    """Class để mapping và xử lý dữ liệu từ các website khác nhau"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.mappings = self._get_default_mappings()
    
    def _get_default_mappings(self) -> Dict[str, Dict]:
        """Lấy default field mappings cho từng website"""
        return {
            'Booking.com': {
                'airline': {
                    'selectors': ['.//div[@data-testid="airline-name"]', './/span[contains(@class, "airline")]'],
                    'required': True,
                    'type': 'text'
                },
                'flight_number': {
                    'selectors': ['.//div[@data-testid="flight-number"]', './/span[contains(@class, "flight-number")]'],
                    'required': False,
                    'type': 'text'
                },
                'departure_time': {
                    'selectors': ['.//div[@data-testid="departure-time"]', './/span[contains(@class, "time")]'],
                    'required': True,
                    'type': 'datetime'
                },
                'arrival_time': {
                    'selectors': ['.//div[@data-testid="arrival-time"]', './/span[contains(@class, "time")]'],
                    'required': True,
                    'type': 'datetime'
                },
                'price': {
                    'selectors': ['.//div[@data-testid="price"]', './/span[contains(@class, "price")]'],
                    'required': True,
                    'type': 'price'
                },
                'duration': {
                    'selectors': ['.//div[@data-testid="duration"]', './/span[contains(@class, "duration")]'],
                    'required': False,
                    'type': 'duration'
                },
                'stops': {
                    'selectors': ['.//div[@data-testid="stops"]', './/span[contains(@class, "stops")]'],
                    'required': False,
                    'type': 'stops'
                }
            },
            'Agoda': {
                'airline': {
                    'selectors': ['.//div[@data-testid="airline-name"]', './/span[contains(@class, "airline")]'],
                    'required': True,
                    'type': 'text'
                },
                'flight_number': {
                    'selectors': ['.//div[@data-testid="flight-number"]', './/span[contains(@class, "flight-number")]'],
                    'required': False,
                    'type': 'text'
                },
                'departure_time': {
                    'selectors': ['.//div[@data-testid="departure-time"]', './/span[contains(@class, "time")]'],
                    'required': True,
                    'type': 'datetime'
                },
                'arrival_time': {
                    'selectors': ['.//div[@data-testid="arrival-time"]', './/span[contains(@class, "time")]'],
                    'required': True,
                    'type': 'datetime'
                },
                'price': {
                    'selectors': ['.//div[@data-testid="price"]', './/span[contains(@class, "price")]'],
                    'required': True,
                    'type': 'price'
                },
                'duration': {
                    'selectors': ['.//div[@data-testid="duration"]', './/span[contains(@class, "duration")]'],
                    'required': False,
                    'type': 'duration'
                },
                'stops': {
                    'selectors': ['.//div[@data-testid="stops"]', './/span[contains(@class, "stops")]'],
                    'required': False,
                    'type': 'stops'
                }
            },
            'Traveloka': {
                'airline': {
                    'selectors': ['.//div[contains(@class, "airline")]', './/span[contains(@class, "airline")]'],
                    'required': True,
                    'type': 'text'
                },
                'flight_number': {
                    'selectors': ['.//div[@data-testid="flight-number"]', './/span[contains(@class, "flight-number")]'],
                    'required': False,
                    'type': 'text'
                },
                'departure_time': {
                    'selectors': ['.//span[contains(@class, "time")]', './/div[contains(@class, "time")]'],
                    'required': True,
                    'type': 'datetime'
                },
                'arrival_time': {
                    'selectors': ['.//span[contains(@class, "time")]', './/div[contains(@class, "time")]'],
                    'required': True,
                    'type': 'datetime'
                },
                'price': {
                    'selectors': ['.//div[contains(@class, "price")]//span', './/span[contains(@class, "price")]'],
                    'required': True,
                    'type': 'price'
                },
                'duration': {
                    'selectors': ['.//div[contains(@class, "duration")]', './/span[contains(@class, "duration")]'],
                    'required': False,
                    'type': 'duration'
                },
                'stops': {
                    'selectors': ['.//div[contains(@class, "stops")]', './/span[contains(@class, "stops")]'],
                    'required': False,
                    'type': 'stops'
                }
            }
        }
    
    def get_selectors(self, field_name: str) -> list:
        """Lấy danh sách selectors cho một field"""
        if self.source_name in self.mappings and field_name in self.mappings[self.source_name]:
            return self.mappings[self.source_name][field_name]['selectors']
        return []
    
    def is_required(self, field_name: str) -> bool:
        """Kiểm tra field có bắt buộc không"""
        if self.source_name in self.mappings and field_name in self.mappings[self.source_name]:
            return self.mappings[self.source_name][field_name]['required']
        return False
    
    def get_field_type(self, field_name: str) -> str:
        """Lấy kiểu dữ liệu của field"""
        if self.source_name in self.mappings and field_name in self.mappings[self.source_name]:
            return self.mappings[self.source_name][field_name]['type']
        return 'text'
    
    def parse_field_value(self, field_name: str, raw_value: str, search_date: datetime = None) -> Any:
        """Parse giá trị field theo kiểu dữ liệu"""
        if not raw_value:
            return None
            
        field_type = self.get_field_type(field_name)
        
        if field_type == 'text':
            return raw_value.strip()
        elif field_type == 'number':
            return self._parse_number(raw_value)
        elif field_type == 'datetime':
            return self._parse_datetime(raw_value, search_date)
        elif field_type == 'price':
            return self._parse_price(raw_value)
        elif field_type == 'duration':
            return self._parse_duration(raw_value)
        elif field_type == 'stops':
            return self._parse_stops(raw_value)
        else:
            return raw_value.strip()
    
    def _parse_number(self, value: str) -> Optional[int]:
        """Parse số từ text"""
        try:
            return int(re.sub(r'[^\d]', '', value))
        except:
            return None
    
    def _parse_price(self, value: str) -> Optional[int]:
        """Parse giá từ text"""
        try:
            # Remove currency symbols and extract numbers
            price_clean = re.sub(r'[^\d,]', '', value)
            price_clean = price_clean.replace(',', '')
            return int(price_clean) if price_clean else None
        except:
            return None
    
    def _parse_datetime(self, value: str, search_date: datetime = None) -> Optional[str]:
        """Parse thời gian từ text"""
        try:
            if not search_date:
                search_date = datetime.now()
                
            # Parse time format (HH:MM)
            time_match = re.search(r'(\d{1,2}):(\d{2})', value)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                dt = datetime.combine(search_date.date(), datetime.min.time().replace(hour=hour, minute=minute))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        return None
    
    def _parse_duration(self, value: str) -> Optional[int]:
        """Parse thời lượng bay từ text (trả về phút)"""
        try:
            # Parse format like "2h 30m" or "2h30m" or "150 minutes"
            value = value.lower().replace(' ', '')
            
            # Check for hours and minutes format
            hour_match = re.search(r'(\d+)h', value)
            minute_match = re.search(r'(\d+)m', value)
            
            hours = int(hour_match.group(1)) if hour_match else 0
            minutes = int(minute_match.group(1)) if minute_match else 0
            
            return hours * 60 + minutes
        except:
            return None
    
    def _parse_stops(self, value: str) -> Optional[int]:
        """Parse số điểm dừng từ text"""
        try:
            value = value.lower()
            if 'direct' in value or 'non-stop' in value or 'không dừng' in value:
                return 0
            elif 'stop' in value or 'dừng' in value:
                # Extract number from text
                numbers = re.findall(r'\d+', value)
                return int(numbers[0]) if numbers else 1
            return 0
        except:
            return None
    
    def create_flight_data(self, extracted_data: Dict[str, Any], origin: str, destination: str, search_date: datetime) -> Dict[str, Any]:
        """Tạo flight data object từ extracted data"""
        route = f"{origin}-{destination}"
        
        # Parse times
        departure_time = self.parse_field_value('departure_time', extracted_data.get('departure_time', ''), search_date)
        arrival_time = self.parse_field_value('arrival_time', extracted_data.get('arrival_time', ''), search_date)
        
        # Calculate duration if not provided
        duration_minutes = self.parse_field_value('duration', extracted_data.get('duration', ''))
        if not duration_minutes and departure_time and arrival_time:
            try:
                dep_dt = datetime.strptime(departure_time, '%Y-%m-%d %H:%M:%S')
                arr_dt = datetime.strptime(arrival_time, '%Y-%m-%d %H:%M:%S')
                if arr_dt < dep_dt:
                    arr_dt += timedelta(days=1)
                duration_minutes = int((arr_dt - dep_dt).total_seconds() / 60)
            except:
                duration_minutes = None
        
        # Generate flight code if not provided
        flight_code = extracted_data.get('flight_number', '')
        if not flight_code:
            airline = extracted_data.get('airline', 'UNKNOWN')
            airline_code = airline.split(' ')[0].upper() if airline else 'UNK'
            time_str = departure_time.replace(':', '').replace('-', '').replace(' ', '')[:6] if departure_time else '000000'
            flight_code = f"{airline_code}-{time_str}"
        
        return {
            "flight_code": flight_code,
            "airline": self.parse_field_value('airline', extracted_data.get('airline', '')),
            "departure_airport": origin,
            "arrival_airport": destination,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "duration_minutes": duration_minutes,
            "price": self.parse_field_value('price', extracted_data.get('price', '')),
            "currency": "VND",
            "source": self.source_name,
            "route": route,
            "stops": self.parse_field_value('stops', extracted_data.get('stops', '0')),
            "aircraft_type": extracted_data.get('aircraft_type', ''),
            "baggage_info": extracted_data.get('baggage_info', ''),
            "meal_info": extracted_data.get('meal_info', ''),
            "seat_class": extracted_data.get('seat_class', ''),
            "booking_url": extracted_data.get('booking_url', '')
        }

