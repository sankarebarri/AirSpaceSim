# utils/conversions.py

from math import radians, sin, cos, sqrt, atan2


def dms_to_decimal(degrees, minutes, seconds, direction):
    """
    Convert DMS(Degrees, Minutes, Seconds) to decimal degrees

    :param degrees: Degrees component.
    :param minutes: Minutes component.
    :param seconds: Seconds component.
    :param direction: Direction ('N', 'S', 'E', 'W').

    :return: Decimal degree representation.
    """
    decimal = degrees + (minutes / 60) + (seconds / 3600)
    if direction in ["S", "W"]:
        decimal = -decimal
    return decimal


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth using haversine formula

    :param lat1: Latitude of the first point in decimal degrees.
    :param lon1: Longitude of the first point in decimal degrees.
    :param lat2: Latitude of the second point in decimal degrees.
    :param lon2: Longitude of the second point in decimal degrees.

    :return: Distance in nautical miles (NM).
    """
    R = 6371  # Earth's radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c * 0.539957  # Convert kilometers to nautical miles


# print(haversine(16.5, -0.083333, 16.7, -0.15))  # Example for WP1 to WP2
