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
