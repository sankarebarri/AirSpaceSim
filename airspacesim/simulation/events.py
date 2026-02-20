"""Canonical event application for simulation runtime."""

from airspacesim.utils.conversions import dms_to_decimal


def _route_to_decimal_waypoints(route_waypoints):
    output = []
    for waypoint in route_waypoints:
        if "dec_coords" in waypoint:
            output.append(waypoint["dec_coords"])
        else:
            output.append(
                [
                    dms_to_decimal(*waypoint["coords"]["lat"]),
                    dms_to_decimal(*waypoint["coords"]["lon"]),
                ]
            )
    return output


def _find_aircraft(manager, aircraft_id):
    for aircraft in manager.aircraft_list:
        if aircraft.id == aircraft_id:
            return aircraft
    return None


def apply_events_idempotent(manager, events):
    """Apply validated canonical events to an AircraftManager."""
    applied = []
    skipped = []
    rejected = []

    for event in events:
        event_type = event["type"]
        payload = event["payload"]
        event_id = event["event_id"]
        try:
            if event_type == "ADD_AIRCRAFT":
                aircraft_id = payload.get("aircraft_id") or payload.get("id")
                route_id = payload.get("route_id")
                if not aircraft_id or not route_id:
                    rejected.append((event_id, "missing aircraft_id or route_id"))
                    continue
                manager.add_aircraft(
                    id=aircraft_id,
                    route_name=route_id,
                    callsign=payload.get("callsign", aircraft_id),
                    speed=payload.get("speed_kt"),
                    altitude_ft=payload.get("altitude_ft", 0.0),
                    vertical_rate_fpm=payload.get("vertical_rate_fpm", 0.0),
                )
                applied.append(event_id)
            elif event_type == "SET_SPEED":
                aircraft_id = payload.get("aircraft_id")
                speed_kt = payload.get("speed_kt")
                aircraft = _find_aircraft(manager, aircraft_id)
                if not aircraft:
                    skipped.append((event_id, "aircraft not found"))
                    continue
                if not isinstance(speed_kt, (int, float)) or speed_kt <= 0:
                    rejected.append((event_id, "invalid speed_kt"))
                    continue
                aircraft.speed = speed_kt
                manager.save_aircraft_data()
                applied.append(event_id)
            elif event_type == "REMOVE_AIRCRAFT":
                aircraft_id = payload.get("aircraft_id")
                if not aircraft_id:
                    rejected.append((event_id, "missing aircraft_id"))
                    continue
                manager.delete_aircraft(aircraft_id)
                manager.save_aircraft_data()
                applied.append(event_id)
            elif event_type == "REROUTE":
                aircraft_id = payload.get("aircraft_id")
                route_id = payload.get("route_id")
                aircraft = _find_aircraft(manager, aircraft_id)
                if not aircraft:
                    skipped.append((event_id, "aircraft not found"))
                    continue
                if route_id not in manager.routes:
                    rejected.append((event_id, "unknown route_id"))
                    continue
                new_waypoints = _route_to_decimal_waypoints(manager.routes[route_id])
                aircraft.route = route_id
                aircraft.waypoints = new_waypoints
                aircraft.current_index = 0
                aircraft.segment_progress = 0
                aircraft.position = new_waypoints[0]
                manager.save_aircraft_data()
                applied.append(event_id)
            elif event_type == "SET_VERTICAL_RATE":
                aircraft_id = payload.get("aircraft_id")
                vertical_rate_fpm = payload.get("vertical_rate_fpm")
                aircraft = _find_aircraft(manager, aircraft_id)
                if not aircraft:
                    skipped.append((event_id, "aircraft not found"))
                    continue
                if not isinstance(vertical_rate_fpm, (int, float)):
                    rejected.append((event_id, "invalid vertical_rate_fpm"))
                    continue
                aircraft.vertical_rate_fpm = vertical_rate_fpm
                manager.save_aircraft_data()
                applied.append(event_id)
            else:
                rejected.append((event_id, "unsupported type"))
        except Exception as exc:
            rejected.append((event_id, str(exc)))

    return {
        "applied": applied,
        "skipped": skipped,
        "rejected": rejected,
    }
