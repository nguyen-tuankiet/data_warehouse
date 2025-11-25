# Process 1. Crawl_Data_And_Save_To_CSV:
#  1.4. Tạo tất cả các chặng bay (origin → destination, khác nhau)
def buidl_origin_destination(airports):
    routes =[]
    for origin in airports:
        for destination in airports:
            if origin != destination:
                routes.append(
                    {
                        "origin": origin,
                        "destination": destination
                    }
                )

    return routes

import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip