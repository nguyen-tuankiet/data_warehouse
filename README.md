# Flight Scraper System

Hệ thống cào dữ liệu chuyến bay từ 3 website chính: **Booking.com**, **Agoda**, và **Traveloka** với khả năng mapping field linh hoạt và lưu trữ trong MySQL database.

## 🚀 Tính năng chính

- **Multi-source scraping**: Cào dữ liệu từ 3 website khác nhau
- **Flexible field mapping**: Mapping field linh hoạt cho từng website
- **Database integration**: Lưu trữ dữ liệu trong MySQL với schema mở rộng
- **Configurable system**: Cấu hình dễ dàng qua database và JSON
- **Comprehensive logging**: Hệ thống log chi tiết
- **Error handling**: Xử lý lỗi và retry mechanism
- **Data validation**: Validate dữ liệu trước khi lưu

## 📋 Yêu cầu hệ thống

- Python 3.8+
- Chrome browser
- MySQL database
- Internet connection

## 🛠️ Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd flight-scraper
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình database

Tạo file `.env` trong thư mục gốc:

```env
DB_HOST=localhost
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_NAME=flight_scraper
DB_PORT=4000
DB_SSL_CA=
DB_USE_SSL=false
```
### 4. Tải file isrgrootx1.pem lưu trong thư mục góc

### 5. Cách chạy project: 
```bash
python src/main.py
python -m src.main

```

