"""Canonical event application for simulation runtime."""

from airspacesim.utils.conversions import dms_to_decimal
from airspacesim.utils.logging_config import default_logger as logger


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


def _find_callsign_matches(manager, callsign):
    return [aircraft for aircraft in manager.aircraft_list if aircraft.callsign == callsign]


def apply_events_idempotent(manager, events):
    """Apply validated canonical events to an AircraftManager."""
    applied = []
    skipped = []
    rejected = []

    for event in events:
        event_type = event["type"]
        payload = event["payload"]
        event_id = event["event_id"]
        logger.info(
            "[EVENT] received id=%s type=%s payload=%s",
            event_id,
            event_type,
            payload,
        )
        try:
            if event_type == "ADD_AIRCRAFT":
                aircraft_id = payload.get("aircraft_id") or payload.get("id")
                route_id = payload.get("route_id")
                if not aircraft_id or not route_id:
                    rejected.append((event_id, "missing aircraft_id or route_id"))
                    logger.warning(
                        "[EVENT] rejected id=%s reason=%s",
                        event_id,
                        "missing aircraft_id or route_id",
                    )
                    continue
                if _find_aircraft(manager, aircraft_id):
                    skipped.append((event_id, "aircraft_id already exists"))
                    logger.warning(
                        "[EVENT] skipped id=%s reason=%s aircraft_id=%s",
                        event_id,
                        "aircraft_id already exists",
                        aircraft_id,
                    )
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
                logger.info(
                    "[EVENT] applied id=%s action=ADD_AIRCRAFT aircraft_id=%s route_id=%s",
                    event_id,
                    aircraft_id,
                    route_id,
                )
            elif event_type == "SET_SPEED":
                aircraft_id = payload.get("aircraft_id")
                speed_kt = payload.get("speed_kt")
                aircraft = _find_aircraft(manager, aircraft_id)
                if not aircraft:
                    callsign_matches = (
                        _find_callsign_matches(manager, aircraft_id)
                        if isinstance(aircraft_id, str) and aircraft_id
                        else []
                    )
                    if len(callsign_matches) == 1:
                        reason = (
                            f"aircraft not found by id; payload.aircraft_id matched callsign "
                            f"'{aircraft_id}'. use aircraft id '{callsign_matches[0].id}'"
                        )
                    elif len(callsign_matches) > 1:
                        reason = (
                            f"aircraft not found by id; payload.aircraft_id matched multiple callsigns "
                            f"'{aircraft_id}'. use aircraft id"
                        )
                    else:
                        reason = "aircraft not found (payload.aircraft_id must be aircraft id, not callsign)"

                    skipped.append((event_id, reason))
                    logger.warning(
                        "[EVENT] skipped id=%s reason=%s aircraft_id=%s",
                        event_id,
                        reason,
                        aircraft_id,
                    )
                    continue
                if not isinstance(speed_kt, (int, float)) or speed_kt <= 0:
                    rejected.append((event_id, "invalid speed_kt"))
                    logger.warning(
                        "[EVENT] rejected id=%s reason=%s speed_kt=%s",
                        event_id,
                        "invalid speed_kt",
                        speed_kt,
                    )
                    continue
                if hasattr(aircraft, "_sanitize_speed_kt"):
                    aircraft.speed = aircraft._sanitize_speed_kt(speed_kt)
                else:
                    aircraft.speed = float(speed_kt)
                manager.save_aircraft_data()
                applied.append(event_id)
                logger.info(
                    "[EVENT] applied id=%s action=SET_SPEED aircraft_id=%s speed_kt=%s",
                    event_id,
                    aircraft_id,
                    aircraft.speed,
                )
            elif event_type == "REMOVE_AIRCRAFT":
                aircraft_id = payload.get("aircraft_id")
                if not aircraft_id:
                    rejected.append((event_id, "missing aircraft_id"))
                    logger.warning(
                        "[EVENT] rejected id=%s reason=%s",
                        event_id,
                        "missing aircraft_id",
                    )
                    continue
                manager.delete_aircraft(aircraft_id)
                manager.save_aircraft_data()
                applied.append(event_id)
                logger.info(
                    "[EVENT] applied id=%s action=REMOVE_AIRCRAFT aircraft_id=%s",
                    event_id,
                    aircraft_id,
                )
            elif event_type == "REROUTE":
                aircraft_id = payload.get("aircraft_id")
                route_id = payload.get("route_id")
                aircraft = _find_aircraft(manager, aircraft_id)
                if not aircraft:
                    skipped.append((event_id, "aircraft not found"))
                    logger.warning(
                        "[EVENT] skipped id=%s reason=%s aircraft_id=%s",
                        event_id,
                        "aircraft not found",
                        aircraft_id,
                    )
                    continue
                if route_id not in manager.routes:
                    rejected.append((event_id, "unknown route_id"))
                    logger.warning(
                        "[EVENT] rejected id=%s reason=%s route_id=%s",
                        event_id,
                        "unknown route_id",
                        route_id,
                    )
                    continue
                new_waypoints = _route_to_decimal_waypoints(manager.routes[route_id])
                aircraft.route = route_id
                aircraft.waypoints = new_waypoints
                aircraft.current_index = 0
                aircraft.segment_progress = 0
                aircraft.position = new_waypoints[0]
                manager.save_aircraft_data()
                applied.append(event_id)
                logger.info(
                    "[EVENT] applied id=%s action=REROUTE aircraft_id=%s route_id=%s",
                    event_id,
                    aircraft_id,
                    route_id,
                )
            elif event_type == "SET_VERTICAL_RATE":
                aircraft_id = payload.get("aircraft_id")
                vertical_rate_fpm = payload.get("vertical_rate_fpm")
                aircraft = _find_aircraft(manager, aircraft_id)
                if not aircraft:
                    skipped.append((event_id, "aircraft not found"))
                    logger.warning(
                        "[EVENT] skipped id=%s reason=%s aircraft_id=%s",
                        event_id,
                        "aircraft not found",
                        aircraft_id,
                    )
                    continue
                if not isinstance(vertical_rate_fpm, (int, float)):
                    rejected.append((event_id, "invalid vertical_rate_fpm"))
                    logger.warning(
                        "[EVENT] rejected id=%s reason=%s vertical_rate_fpm=%s",
                        event_id,
                        "invalid vertical_rate_fpm",
                        vertical_rate_fpm,
                    )
                    continue
                aircraft.vertical_rate_fpm = vertical_rate_fpm
                manager.save_aircraft_data()
                applied.append(event_id)
                logger.info(
                    "[EVENT] applied id=%s action=SET_VERTICAL_RATE aircraft_id=%s vertical_rate_fpm=%s",
                    event_id,
                    aircraft_id,
                    vertical_rate_fpm,
                )
            elif event_type == "SET_SIMULATION_SPEED":
                sim_rate = payload.get("sim_rate")
                if not isinstance(sim_rate, (int, float)) or sim_rate <= 0:
                    rejected.append((event_id, "invalid sim_rate"))
                    logger.warning(
                        "[EVENT] rejected id=%s reason=%s sim_rate=%s",
                        event_id,
                        "invalid sim_rate",
                        sim_rate,
                    )
                    continue
                manager.set_simulation_speed(float(sim_rate))
                applied.append(event_id)
                logger.info(
                    "[EVENT] applied id=%s action=SET_SIMULATION_SPEED sim_rate=%s",
                    event_id,
                    sim_rate,
                )
            else:
                rejected.append((event_id, "unsupported type"))
                logger.warning(
                    "[EVENT] rejected id=%s reason=%s type=%s",
                    event_id,
                    "unsupported type",
                    event_type,
                )
        except Exception as exc:
            rejected.append((event_id, str(exc)))
            logger.exception("[EVENT] exception id=%s type=%s", event_id, event_type)

    if events:
        logger.info(
            "[EVENT] batch summary applied=%d skipped=%d rejected=%d",
            len(applied),
            len(skipped),
            len(rejected),
        )

    return {
        "applied": applied,
        "skipped": skipped,
        "rejected": rejected,
    }
