def interpolate_position(start, end, fraction):
    """
    Interpolate position between two waypoints.

    :param start: Starting waypoint [lat, lon].
    :param end: Ending waypoint [lat, lon].
    :param fraction: Fraction of the distance between start and end (0 to 1).
    :return: New interpolated position [lat, lon].
    """
    new_position = [
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction,
    ]
    print(f"DEBUG: Interpolating: Start={start}, End={end}, Fraction={fraction}, New={new_position}")
    return new_position
