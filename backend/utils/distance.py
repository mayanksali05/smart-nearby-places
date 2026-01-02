import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points on Earth (in kilometers)
    """

    # convert degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [
        lat1, lon1, lat2, lon2
    ])

    # haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + \
        math.cos(lat1) * math.cos(lat2) * \
        math.sin(dlon / 2) ** 2

    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in km
    r = 6371

    return round(c * r, 2)
