#utils/calculate_bearing.py

import math

def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate the bearing between two points.

    :param lat1: Latitude of the first point in decimal degrees.
    :param lon1: Longitude of the first point in decimal degrees.
    :param lat2: Latitude of the second point in decimal degrees.
    :param lon2: Longitude of the second point in decimal degrees.
    :return: Initial bearing in degrees.
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.atan2(x, y)
    return (math.degrees(bearing) + 360) % 360