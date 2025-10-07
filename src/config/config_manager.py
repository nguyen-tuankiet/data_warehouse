# config/config_manager.py
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class ConfigManager:
    """Manager class để quản lý cấu hình cho các website scraping"""
    
    def __init__(self, config_file: str = "provider_configs.json"):
        self.config_file = config_file
        self.configs = self._load_configs()
    
    def _load_configs(self) -> Dict[str, Any]:
        """Load cấu hình từ file JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_configs()
        except Exception as e:
            print(f"Error loading config file: {e}")
            return self._get_default_configs()
    
    def _get_default_configs(self) -> Dict[str, Any]:
        """Lấy cấu hình mặc định cho 3 website"""
        return {
            "booking": {
                "provider_name": "Booking.com",
                "base_url": "https://www.booking.com/flights",
                "scraper_class": "BookingScraper",
                "is_active": True,
                "request_config": {
                    "max_retries": 3,
                    "retry_delay": 5,
                    "timeout": 30,
                    "request_delay": {
                        "min": 2,
                        "max": 5
                    }
                },
                "selectors": {
                    "flight_card": "[data-testid='flight-card']",
                    "airline_name": ".airline-name",
                    "flight_number": ".flight-number",
                    "departure_time": ".departure-time",
                    "arrival_time": ".arrival-time",
                    "duration": ".duration",
                    "price": ".price",
                    "stops": ".stops-info"
                },
                "field_mappings": {
                    "airline": {
                        "selectors": ['.//div[@data-testid="airline-name"]', './/span[contains(@class, "airline")]'],
                        "required": True,
                        "type": "text"
                    },
                    "flight_number": {
                        "selectors": ['.//div[@data-testid="flight-number"]', './/span[contains(@class, "flight-number")]'],
                        "required": False,
                        "type": "text"
                    },
                    "departure_time": {
                        "selectors": ['.//div[@data-testid="departure-time"]', './/span[contains(@class, "time")]'],
                        "required": True,
                        "type": "datetime"
                    },
                    "arrival_time": {
                        "selectors": ['.//div[@data-testid="arrival-time"]', './/span[contains(@class, "time")]'],
                        "required": True,
                        "type": "datetime"
                    },
                    "price": {
                        "selectors": ['.//div[@data-testid="price"]', './/span[contains(@class, "price")]'],
                        "required": True,
                        "type": "price"
                    }
                }
            },
            "agoda": {
                "provider_name": "Agoda.com",
                "base_url": "https://www.agoda.com/flights",
                "scraper_class": "AgodaScraper",
                "is_active": True,
                "request_config": {
                    "max_retries": 3,
                    "retry_delay": 5,
                    "timeout": 30,
                    "request_delay": {
                        "min": 2,
                        "max": 5
                    }
                },
                "selectors": {
                    "flight_card": "[data-testid='flight-card']",
                    "airline_name": ".airline-name",
                    "flight_number": ".flight-number",
                    "departure_time": ".departure-time",
                    "arrival_time": ".arrival-time",
                    "duration": ".duration",
                    "price": ".price",
                    "stops": ".stops-info"
                },
                "field_mappings": {
                    "airline": {
                        "selectors": ['.//div[@data-testid="airline-name"]', './/span[contains(@class, "airline")]'],
                        "required": True,
                        "type": "text"
                    },
                    "flight_number": {
                        "selectors": ['.//div[@data-testid="flight-number"]', './/span[contains(@class, "flight-number")]'],
                        "required": False,
                        "type": "text"
                    },
                    "departure_time": {
                        "selectors": ['.//div[@data-testid="departure-time"]', './/span[contains(@class, "time")]'],
                        "required": True,
                        "type": "datetime"
                    },
                    "arrival_time": {
                        "selectors": ['.//div[@data-testid="arrival-time"]', './/span[contains(@class, "time")]'],
                        "required": True,
                        "type": "datetime"
                    },
                    "price": {
                        "selectors": ['.//div[@data-testid="price"]', './/span[contains(@class, "price")]'],
                        "required": True,
                        "type": "price"
                    }
                }
            },
            "traveloka": {
                "provider_name": "Traveloka.com",
                "base_url": "https://www.traveloka.com/vi-vn/flight",
                "scraper_class": "TravelokaScraper",
                "is_active": True,
                "request_config": {
                    "max_retries": 3,
                    "retry_delay": 5,
                    "timeout": 30,
                    "request_delay": {
                        "min": 2,
                        "max": 5
                    }
                },
                "selectors": {
                    "flight_card": "div[class*='flight-result']",
                    "airline_name": ".airline-name",
                    "flight_number": ".flight-number",
                    "departure_time": ".departure-time",
                    "arrival_time": ".arrival-time",
                    "duration": ".duration",
                    "price": ".price",
                    "stops": ".stops-info"
                },
                "field_mappings": {
                    "airline": {
                        "selectors": ['.//div[contains(@class, "airline")]', './/span[contains(@class, "airline")]'],
                        "required": True,
                        "type": "text"
                    },
                    "flight_number": {
                        "selectors": ['.//div[@data-testid="flight-number"]', './/span[contains(@class, "flight-number")]'],
                        "required": False,
                        "type": "text"
                    },
                    "departure_time": {
                        "selectors": ['.//span[contains(@class, "time")]', './/div[contains(@class, "time")]'],
                        "required": True,
                        "type": "datetime"
                    },
                    "arrival_time": {
                        "selectors": ['.//span[contains(@class, "time")]', './/div[contains(@class, "time")]'],
                        "required": True,
                        "type": "datetime"
                    },
                    "price": {
                        "selectors": ['.//div[contains(@class, "price")]//span', './/span[contains(@class, "price")]'],
                        "required": True,
                        "type": "price"
                    }
                }
            }
        }
    
    def get_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """Lấy cấu hình cho một provider cụ thể"""
        return self.configs.get(provider)
    
    def get_all_configs(self) -> Dict[str, Any]:
        """Lấy tất cả cấu hình"""
        return self.configs
    
    def get_active_configs(self) -> List[Dict[str, Any]]:
        """Lấy danh sách các config đang active"""
        active_configs = []
        for provider, config in self.configs.items():
            if config.get('is_active', True):
                active_configs.append({
                    'provider': provider,
                    'config': config
                })
        return active_configs
    
    def update_config(self, provider: str, config_data: Dict[str, Any]) -> bool:
        """Cập nhật cấu hình cho một provider"""
        try:
            self.configs[provider] = config_data
            self._save_configs()
            return True
        except Exception as e:
            print(f"Error updating config for {provider}: {e}")
            return False
    
    def update_field_mapping(self, provider: str, field_name: str, mapping_data: Dict[str, Any]) -> bool:
        """Cập nhật field mapping cho một provider"""
        try:
            if provider not in self.configs:
                return False
            
            if 'field_mappings' not in self.configs[provider]:
                self.configs[provider]['field_mappings'] = {}
            
            self.configs[provider]['field_mappings'][field_name] = mapping_data
            self._save_configs()
            return True
        except Exception as e:
            print(f"Error updating field mapping for {provider}.{field_name}: {e}")
            return False
    
    def set_provider_status(self, provider: str, is_active: bool) -> bool:
        """Set trạng thái active/inactive cho provider"""
        try:
            if provider in self.configs:
                self.configs[provider]['is_active'] = is_active
                self._save_configs()
                return True
            return False
        except Exception as e:
            print(f"Error setting status for {provider}: {e}")
            return False
    
    def _save_configs(self) -> bool:
        """Lưu cấu hình vào file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config file: {e}")
            return False
    
    def get_scraper_class(self, provider: str) -> Optional[str]:
        """Lấy scraper class cho provider"""
        config = self.get_config(provider)
        return config.get('scraper_class') if config else None
    
    def get_base_url(self, provider: str) -> Optional[str]:
        """Lấy base URL cho provider"""
        config = self.get_config(provider)
        return config.get('base_url') if config else None
    
    def get_request_config(self, provider: str) -> Dict[str, Any]:
        """Lấy cấu hình request cho provider"""
        config = self.get_config(provider)
        return config.get('request_config', {}) if config else {}
    
    def get_selectors(self, provider: str) -> Dict[str, str]:
        """Lấy selectors cho provider"""
        config = self.get_config(provider)
        return config.get('selectors', {}) if config else {}
    
    def get_field_mappings(self, provider: str) -> Dict[str, Dict[str, Any]]:
        """Lấy field mappings cho provider"""
        config = self.get_config(provider)
        return config.get('field_mappings', {}) if config else {}
    
    def validate_config(self, provider: str) -> List[str]:
        """Validate cấu hình cho provider"""
        errors = []
        config = self.get_config(provider)
        
        if not config:
            errors.append(f"Provider {provider} not found")
            return errors
        
        required_fields = ['provider_name', 'base_url', 'scraper_class']
        for field in required_fields:
            if not config.get(field):
                errors.append(f"Missing required field: {field}")
        
        if not config.get('is_active'):
            errors.append("Provider is inactive")
        
        return errors
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Lấy summary của tất cả configs"""
        summary = {
            'total_providers': len(self.configs),
            'active_providers': 0,
            'inactive_providers': 0,
            'providers': {}
        }
        
        for provider, config in self.configs.items():
            is_active = config.get('is_active', True)
            if is_active:
                summary['active_providers'] += 1
            else:
                summary['inactive_providers'] += 1
            
            summary['providers'][provider] = {
                'name': config.get('provider_name', provider),
                'is_active': is_active,
                'scraper_class': config.get('scraper_class', 'Unknown'),
                'base_url': config.get('base_url', 'Unknown'),
                'field_mappings_count': len(config.get('field_mappings', {}))
            }
        
        return summary

