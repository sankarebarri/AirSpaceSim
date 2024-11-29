def interpolate_position(start, end, t):
    # print(1)
    """
    Interpolate between two points based on t (0 <= t <= 1)

    :param start: [lat, lon] of the start point
    :param end: [lat, lon] of the end point
    :param t:  Parameter (0 <= t <= 1).

    :return: Interpolated position [lat, lon]
    """
    return [
        start[0] + (end[0] - start[0]) * t,
        start[1] + (end[1] - start[1]) * t
    ]