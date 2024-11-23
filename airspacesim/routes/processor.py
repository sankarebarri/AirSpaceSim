from airspacesim.utils.conversions import dms_to_decimal, haversine

def process_waypoints(waypoints):
    """
    Process waypoints by converting DMS to decimal degrees and calculating distances.

    :param waypoints: List of waypoints with DMS or distance placeholders.
    :return: List of waypoints with decimal degrees and calculated distances.
    """
    processed_waypoints = []
    for i, wp in enumerate(waypoints):
        if "coords" in wp:
            lat = dms_to_decimal(*wp["coords"]["lat"])
            lon = dms_to_decimal(*wp["coords"]["lon"])
            wp["coords"] = [lat, lon]

        if "distance" not in wp or wp["distance"] is None:
            if i < len(waypoints) - 1 and "coords" in wp and "coords" in waypoints[i + 1]:
                wp["distance"] = haversine(
                    wp["coords"][0], wp["coords"][1],
                    waypoints[i + 1]["coords"][0], waypoints[i + 1]["coords"][1]
                )
        processed_waypoints.append(wp)
    return processed_waypoints

def process_route(route):
    """
    Process a single route to calculate all waypoints distances
    
    :param route: Route dictionary with waypoints and radial

    :return: Processed route with updated waypoints.
    """
    route["waypoints"] = process_waypoints(route["waypoints"])
    return route