import socket
from src.helpper.logger_config import logger


def get_ip_address():
    try:
        host_name = socket.gethostname()
        ip_by_host = socket.gethostbyname(host_name)
    except Exception as e:
        logger.error(f"Lỗi cách Hostname: {e}")
        return "127.0.0.1"

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        return ip
    except Exception as e:
        logger.error(f"Lỗi cách Hostname: {e}")
        return "127.0.0.1"
    finally:
        s.close()
