
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