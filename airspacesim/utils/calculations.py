"""Small reusable calculation helpers."""

from airspacesim.utils.conversions import haversine


def route_distance_nm(points):
    """Compute total route distance in NM for [[lat, lon], ...] points."""
    if not points or len(points) < 2:
        return 0.0
    distance = 0.0
    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]
        distance += haversine(start[0], start[1], end[0], end[1])
    return distance
