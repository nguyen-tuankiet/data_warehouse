
-- dim airport
CREATE TABLE IF NOT EXISTS dim_airport (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL ,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(100) DEFAULT 'Unknow',
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Việt Nam',
    timezone VARCHAR(50) DEFAULT 'Asia/Ho_Chi_Minh',
    effective_date DATE DEFAULT '2020-01-01',
    end_date DATE DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE
);


INSERT INTO dim_airport (id, code, name, city, country, timezone, effective_date, end_date, is_active) VALUES
(1, 'HAN', 'Sân bay Quốc tế Nội Bài', 'Hà Nội', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(2, 'SGN', 'Sân bay Quốc tế Tân Sơn Nhất', 'Hồ Chí Minh', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(3, 'DAD', 'Sân bay Quốc tế Đà Nẵng', 'Đà Nẵng', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(4, 'VDO', 'Sân bay Quốc tế Vân Đồn', 'Quảng Ninh', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(5, 'HPH', 'Sân bay Quốc tế Cát Bi', 'Hải Phòng', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(6, 'VII', 'Sân bay Quốc tế Vinh', 'Nghệ An', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(7, 'HUI', 'Sân bay Quốc tế Phú Bài', 'Huế', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(8, 'CXR', 'Sân bay Quốc tế Cam Ranh', 'Khánh Hòa', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(9, 'DLI', 'Sân bay Quốc tế Liên Khương', 'Lâm Đồng', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(10, 'UIH', 'Sân bay Quốc tế Phù Cát', 'Bình Định', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(11, 'VCA', 'Sân bay Quốc tế Cần Thơ', 'Cần Thơ', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(12, 'PQC', 'Sân bay Quốc tế Phú Quốc', 'Kiên Giang', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(13, 'DIN', 'Sân bay Điện Biên Phủ', 'Điện Biên', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(14, 'THD', 'Sân bay Thọ Xuân', 'Thanh Hóa', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(15, 'VDH', 'Sân bay Đồng Hới', 'Quảng Bình', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(16, 'VCL', 'Sân bay Chu Lai', 'Quảng Nam', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(17, 'TBB', 'Sân bay Tuy Hòa', 'Phú Yên', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(18, 'PXU', 'Sân bay Pleiku', 'Gia Lai', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(19, 'BMV', 'Sân bay Buôn Mê Thuột', 'Đắk Lăk', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(20, 'VKG', 'Sân bay Rạch Giá', 'Kiên Giang', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(21, 'CAH', 'Sân bay Cà Mau', 'Cà Mau', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE),
(22, 'VCS', 'Sân bay Côn Đảo', 'Bà Rịa – Vũng Tàu', 'Việt Nam', 'Asia/Ho_Chi_Minh', '2020-01-01', NULL, TRUE);




-- dim airline
CREATE TABLE IF NOT EXISTS dim_airline (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    airline_code VARCHAR(10) DEFAULT 'Unknow',
    airline_name VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    alliance VARCHAR(50),
    effective_date DATE DEFAULT '2020-01-01',
    end_date DATE DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE
);


INSERT INTO dim_airline (id, airline_code, airline_name, country, alliance, effective_date, end_date, is_active) VALUES
(1, 'VN', 'Vietnam Airlines', 'Việt Nam', 'SkyTeam', '2020-01-01', NULL, TRUE),
(2, 'VJ', 'VietJet Air', 'Việt Nam', NULL, '2020-01-01', NULL, TRUE),
(3, 'QH', 'Bamboo Airways', 'Việt Nam', NULL, '2020-01-01', NULL, TRUE),
(4, 'VU', 'Vietravel Airlines', 'Việt Nam', NULL, '2020-01-01', NULL, TRUE),
(5, 'BL', 'Pacific Airlines', 'Việt Nam', 'SkyTeam', '2020-01-01', NULL, TRUE),

(6, 'SQ', 'Singapore Airlines', 'Singapore', 'Star Alliance', '2020-01-01', NULL, TRUE),
(7, 'TG', 'Thai Airways', 'Thái Lan', 'Star Alliance', '2020-01-01', NULL, TRUE),
(8, 'CX', 'Cathay Pacific', 'Hồng Kông', 'oneworld', '2020-01-01', NULL, TRUE),
(9, 'KE', 'Korean Air', 'Hàn Quốc', 'SkyTeam', '2020-01-01', NULL, TRUE),
(10, 'JL', 'Japan Airlines', 'Nhật Bản', 'oneworld', '2020-01-01', NULL, TRUE),
(11, 'NH', 'All Nippon Airways (ANA)', 'Nhật Bản', 'Star Alliance', '2020-01-01', NULL, TRUE),
(12, 'CI', 'China Airlines', 'Đài Loan', 'SkyTeam', '2020-01-01', NULL, TRUE),
(13, 'BR', 'EVA Air', 'Đài Loan', 'Star Alliance', '2020-01-01', NULL, TRUE),
(14, 'CX', 'Cathay Dragon', 'Hồng Kông', 'oneworld', '2020-01-01', NULL, FALSE),
(15, 'QR', 'Qatar Airways', 'Qatar', 'oneworld', '2020-01-01', NULL, TRUE),
(16, 'EK', 'Emirates', 'UAE', NULL, '2020-01-01', NULL, TRUE),
(17, 'MH', 'Malaysia Airlines', 'Malaysia', 'oneworld', '2020-01-01', NULL, TRUE),
(18, 'GA', 'Garuda Indonesia', 'Indonesia', 'SkyTeam', '2020-01-01', NULL, TRUE),
(19, 'CZ', 'China Southern Airlines', 'Trung Quốc', 'SkyTeam', '2020-01-01', NULL, TRUE),
(20, 'CA', 'Air China', 'Trung Quốc', 'Star Alliance', '2020-01-01', NULL, TRUE),
(21, 'TR', 'Scoot', 'Singapore', NULL, '2020-01-01', NULL, TRUE),
(22, 'AK', 'AirAsia', 'Malaysia', NULL, '2020-01-01', NULL, TRUE),
(23, 'FD', 'Thai AirAsia', 'Thái Lan', NULL, '2020-01-01', NULL, TRUE),
(24, '5J', 'Cebu Pacific', 'Philippines', NULL, '2020-01-01', NULL, TRUE),
(25, 'PR', 'Philippine Airlines', 'Philippines', 'Star Alliance', '2020-01-01', NULL, TRUE);




-- dim date
CREATE TABLE IF NOT EXISTS dim_date (
    date_id INTEGER PRIMARY KEY,
    full_date TEXT NOT NULL,
    day_of_year INTEGER NOT NULL,
    month_of_year INTEGER NOT NULL,
    year_num INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    quarter_num INTEGER NOT NULL,
    is_holiday TEXT DEFAULT 'Non-Holiday',
    is_weekend TEXT DEFAULT 'Weekday'
);




-- config
CREATE TABLE IF NOT EXISTS source (
    source_name VARCHAR(255) NOT NULL PRIMARY KEY ,
    url VARCHAR(1024) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    scraper_class VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO source (source_name, url, is_active, scraper_class) VALUES
   ('Booking.com', 'https://flights.booking.com/api/flights/', TRUE, 'BookingApiScraper'),
   ('Agoda.com', 'https://www.agoda.com/flights', TRUE, 'AgodaScraperV2'),
   ('Traveloka.com', 'https://www.traveloka.com/vi-vn/flight', TRUE, 'TravelokaScraperV2');





-- Logs
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER  PRIMARY KEY AUTOINCREMENT,
    start_time TIMESTAMP ,
    end_time TIMESTAMP ,
    level VARCHAR(20) NOT NULL,                     -- Mức độ log (INFO, WARN, ERROR, DEBUG, TRACE)
    service_name VARCHAR(100),                      -- Tên service/module sinh ra log
    action VARCHAR(100),                            -- Hành động hoặc sự kiện cụ thể (VD: USER_LOGIN, TASK_DELETE)
    message TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- flight raw 
CREATE TABLE IF NOT EXISTS flights_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline TEXT,
    departure_airport TEXT,
    departure_time TEXT,
    destination_airport TEXT,
    destination_time TEXT,
    duration_time INTEGER,
    price REAL,
    source TEXT,
    crawled_at TIMESTAMP
    );



SELECT  * FROM source
    WHERE source_name = 'Traveloka.com' AND is_active = TRUE
