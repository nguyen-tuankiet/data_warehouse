import sqlite3
from src.config.sqlite_connector import get_sqlite_connection
from src.constant.LogType import LogType


class DBLogger:
    def __init__(self):
        """
        Khởi tạo kết nối và gán vào self.connection
        """
        self.connection = get_sqlite_connection()

        if not self.connection:
            print("Error: Cannot connect to SQLite database.")
            return

        # Tự động tạo bảng ngay khi khởi tạo
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            level VARCHAR(20) NOT NULL,
            service_name VARCHAR(100),
            action VARCHAR(100),
            message TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Lỗi tạo bảng: {e}")

    def write_log(
        self,
        level: LogType,
        service_name,
        action,
        message,
        start_time=None,
        end_time=None,
        ip_address=None,
    ):
        query = """
        INSERT INTO logs (level, service_name, action, message, start_time, end_time, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                query,
                (
                    level.value,
                    service_name,
                    action,
                    message,
                    start_time,
                    end_time,
                    ip_address,
                ),
            )
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Lỗi ghi log: {e}")
            return None

    def check_if_job_completed(self, service_name, action, date_check: str):
        query = """
        SELECT COUNT(*) FROM logs 
        WHERE service_name = ? 
        AND action = ? 
        AND level = ? 
        AND date(start_time) = date(?)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                query, (service_name, action, LogType.INFO.value, date_check)
            )
            count = cursor.fetchone()[0]
            return count > 0
        except sqlite3.Error as e:
            print(f"Lỗi kiểm tra log: {e}")
            return False

    def close(self):
        if self.connection:
            self.connection.close()
