# database/db_connector.py
import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

def get_db_connection():
    """
    Tạo và trả về một đối tượng kết nối tới cơ sở dữ liệu bằng PyMySQL.
    Hỗ trợ kết nối SSL cho các dịch vụ cloud như TiDB Cloud.
    """
    load_dotenv()

    try:
        # Xây dựng dictionary cấu hình kết nối cho PyMySQL
        config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USERNAME'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'port': int(os.getenv('DB_PORT')),
            'cursorclass': pymysql.cursors.DictCursor, # Để kết quả trả về dạng dictionary
            'charset': 'utf8mb4'
        }

        # Kiểm tra xem có cần sử dụng SSL không
        if os.getenv('DB_USE_SSL', 'false').lower() == 'true':
            ssl_ca_path = os.getenv('DB_SSL_CA')
            if not ssl_ca_path or not os.path.exists(ssl_ca_path):
                print(f"Error: DB_USE_SSL enabled but file not found at DB_SSL_CA: '{ssl_ca_path}'")
                return None
            
            # Thêm các tham số SSL vào config cho PyMySQL
            config['ssl'] = {'ca': ssl_ca_path}
            print("Connecting using SSL/TLS with PyMySQL...")

        # PyMySQL sử dụng pymysql.connect()
        connection = pymysql.connect(**config)

        print("Database connection successful!")
        return connection
            
    except pymysql.Error as e:
        # In ra lỗi chi tiết hơn
        print(f"Error connecting to MySQL with PyMySQL: {e}")
        return None