from airspacesim.utils.conversions import dms_to_decimal, haversine

def process_waypoints(waypoints):
    """
    Process waypoints by converting DMS to decimal degrees and calculating distances.

    :param waypoints: List of waypoints with DMS or distance placeholders.
    :return: List of waypoints with decimal degrees and calculated distances.
    """
    # First Pass: Convert all DMS to decimal degrees
    for wp in waypoints:
        if "coords" in wp:
            lat = dms_to_decimal(*wp["coords"]["lat"])
            lon = dms_to_decimal(*wp["coords"]["lon"])
            wp["dec_coords"] = [lat, lon]

    # Second Pass: Calculate distances if not already provided
    for i, wp in enumerate(waypoints):
        # Skip distance calculation for the last waypoint
        if i == len(waypoints) - 1:
            continue

        # Skip if the current waypoint already has a distance
        if wp.get("distance") is not None:
            continue

        # Ensure the next waypoint has dec_coords
        next_wp = waypoints[i + 1]
        if "dec_coords" in wp and "dec_coords" in next_wp:
            wp["distance"] = haversine(
                wp["dec_coords"][0], wp["dec_coords"][1],  # Current waypoint
                next_wp["dec_coords"][0], next_wp["dec_coords"][1]  # Next waypoint
            )

    return waypoints




def process_route(route):
    """
    Process a single route to calculate all waypoints distances
    
    :param route: Route dictionary with waypoints and radial

    :return: Processed route with updated waypoints.
    """
    route["waypoints"] = process_waypoints(route["waypoints"])
    return route