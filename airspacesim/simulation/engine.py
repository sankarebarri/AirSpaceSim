import time
from airspacesim.utils.conversions import haversine
from airspacesim.simulation.interpolation import interpolate_position

# def run_simulation(map_renderer, dep_center, waypoints, aircraft_icon, speed_knots, update_interval, arrival_center=None):
#     """
#     Simulate aircraft movement along a route

#     :param map_renderer: MapRenderer instance
#     :param dep_center: Departure airport coordinates[lat, lon]
#     :param arr_center: Destination airport coordinates[lat, lon]
#     :param waypoints: List of waypoints in [lat, lon] format
#     :param aircraft_icon: Icon URL for the aircraft marker.
#     :param speed_knots: Aircraft speed in knots.
#     :param update_interval: Time interval between updates in seconds.
#     """
def run_simulation(map_renderer, gao_center, waypoints, aircraft_icon, speed_knots, update_interval):
    step_distance_nm = speed_knots * update_interval / 3600  # Convert speed to NM per step
    current_position = gao_center

    for i in range(len(waypoints)):
        start = current_position
        end = waypoints[i]
        distance_nm = haversine(start[0], start[1], end[0], end[1])

        # Debugging prints
        print(f"Start: {start}, End: {end}, Distance (NM): {distance_nm}")

        if distance_nm == 0:
            print("Skipping segment: Start and end points are the same.")
            continue

        t = 0

        while t < 1:
            # Dynamically calculate step size
            step_size = max(step_distance_nm / distance_nm, 0.01)
            print(f"Step Size: {step_size}, Updated t: {t}")

            current_position = interpolate_position(start, end, t)
            print(f"Current t: {t}, Current Position: {current_position}")

            map_renderer.add_marker(
                coords=current_position,
                icon_url=aircraft_icon,
                icon_size=[20, 20],
                label_text="Aircraft"
            )
            t += step_size
            time.sleep(update_interval)
