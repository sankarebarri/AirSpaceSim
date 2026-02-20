"""Strict validators for AirSpaceSim v1 JSON contracts."""

from datetime import datetime

CANONICAL_DATA_DOMAINS = {
    "scenario": {
        "airspacesim.scenario_airspace",
        "airspacesim.scenario_aircraft",
        "airspacesim.scenario",
    },
    "aircraft_state": {
        "airspacesim.aircraft_state",
        "airspacesim.aircraft_data",
    },
    "aircraft_events": {
        "airspacesim.inbox_events",
    },
    "trajectory_output": {
        "airspacesim.trajectory",
    },
}


class ValidationError(ValueError):
    """Raised when a contract payload fails strict validation."""


def _fail(message):
    raise ValidationError(message)


def _require(condition, message):
    if not condition:
        _fail(message)


def _require_dict(value, name):
    _require(isinstance(value, dict), f"{name} must be an object")


def _require_list(value, name):
    _require(isinstance(value, list), f"{name} must be an array")


def _is_iso8601_utc(value):
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def build_envelope(schema_name, source, data, generated_utc=None, schema_version="1.0"):
    """Build a standard v1 envelope used by canonical runtime contracts."""
    if generated_utc is None:
        generated_utc = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return {
        "schema": {
            "name": schema_name,
            "version": schema_version,
        },
        "metadata": {
            "source": source,
            "generated_utc": generated_utc,
        },
        "data": data,
    }


def contract_domain(schema_name):
    """Return canonical data domain for a schema name, or None when unknown."""
    for domain, schema_names in CANONICAL_DATA_DOMAINS.items():
        if schema_name in schema_names:
            return domain
    return None


def _require_lat_lon(coords, name):
    _require_list(coords, name)
    _require(len(coords) == 2, f"{name} must contain exactly [lat, lon]")
    _require(
        all(isinstance(v, (int, float)) for v in coords),
        f"{name} values must be numeric",
    )
    _require(-90 <= coords[0] <= 90, f"{name}[0] latitude out of range")
    _require(-180 <= coords[1] <= 180, f"{name}[1] longitude out of range")


def validate_envelope(payload, schema_name, schema_version="1.0"):
    _require_dict(payload, "payload")
    _require_dict(payload.get("schema"), "schema")
    _require(
        payload["schema"].get("name") == schema_name,
        f"schema.name must be '{schema_name}'",
    )
    _require(
        payload["schema"].get("version") == schema_version,
        f"schema.version must be '{schema_version}'",
    )
    _require_dict(payload.get("metadata"), "metadata")
    _require(
        isinstance(payload["metadata"].get("source"), str),
        "metadata.source must be a string",
    )
    _require(
        _is_iso8601_utc(payload["metadata"].get("generated_utc")),
        "metadata.generated_utc must be ISO-8601",
    )
    _require_dict(payload.get("data"), "data")
    return payload


def validate_scenario_v01(payload):
    validate_envelope(payload, "airspacesim.scenario", schema_version="0.1")
    data = payload["data"]
    _require_dict(data.get("airspace"), "data.airspace")
    _require_dict(data.get("aircraft"), "data.aircraft")

    scenario_airspace_payload = {
        "schema": {"name": "airspacesim.scenario_airspace", "version": "1.0"},
        "metadata": payload["metadata"],
        "data": data["airspace"],
    }
    validate_scenario_airspace(scenario_airspace_payload)

    route_ids = {route["id"] for route in data["airspace"]["routes"]}
    scenario_aircraft_payload = {
        "schema": {"name": "airspacesim.scenario_aircraft", "version": "1.0"},
        "metadata": payload["metadata"],
        "data": data["aircraft"],
    }
    validate_scenario_aircraft(scenario_aircraft_payload, route_ids=route_ids)
    return payload


def validate_trajectory_v01(payload):
    validate_envelope(payload, "airspacesim.trajectory", schema_version="0.1")
    data = payload["data"]
    tracks = data.get("tracks")
    _require_list(tracks, "data.tracks")
    for idx, item in enumerate(tracks):
        _require_dict(item, f"data.tracks[{idx}]")
        _require(
            isinstance(item.get("id"), str) and item["id"],
            f"data.tracks[{idx}].id required",
        )
        _require_lat_lon(item.get("position_dd"), f"data.tracks[{idx}].position_dd")
        _require(
            isinstance(item.get("route_id"), str),
            f"data.tracks[{idx}].route_id must be string",
        )
        _require(
            isinstance(item.get("status"), str),
            f"data.tracks[{idx}].status must be string",
        )
        if "speed_kt" in item:
            _require(
                isinstance(item.get("speed_kt"), (int, float))
                and item["speed_kt"] >= 0,
                f"data.tracks[{idx}].speed_kt must be >= 0",
            )
        if "altitude_ft" in item:
            _require(
                isinstance(item.get("altitude_ft"), (int, float))
                and item["altitude_ft"] >= 0,
                f"data.tracks[{idx}].altitude_ft must be >= 0",
            )
        if "vertical_rate_fpm" in item:
            _require(
                isinstance(item.get("vertical_rate_fpm"), (int, float)),
                f"data.tracks[{idx}].vertical_rate_fpm must be numeric",
            )
        _require(
            _is_iso8601_utc(item.get("updated_utc")),
            f"data.tracks[{idx}].updated_utc must be ISO-8601",
        )
    return payload


def validate_scenario_airspace(payload):
    validate_envelope(payload, "airspacesim.scenario_airspace")
    data = payload["data"]

    points = data.get("points")
    routes = data.get("routes")
    airspaces = data.get("airspaces")

    _require_dict(points, "data.points")
    _require_list(routes, "data.routes")
    _require_list(airspaces, "data.airspaces")

    for point_id, point in points.items():
        _require(
            isinstance(point_id, str) and point_id,
            "point keys must be non-empty strings",
        )
        _require_dict(point, f"data.points.{point_id}")
        _require(
            isinstance(point.get("type"), str),
            f"points.{point_id}.type must be a string",
        )
        _require_dict(point.get("coord"), f"points.{point_id}.coord")
        _require_lat_lon(point["coord"].get("dd"), f"points.{point_id}.coord.dd")

    route_ids = set()
    for idx, route in enumerate(routes):
        _require_dict(route, f"data.routes[{idx}]")
        route_id = route.get("id")
        _require(
            isinstance(route_id, str) and route_id,
            f"data.routes[{idx}].id must be a non-empty string",
        )
        _require(route_id not in route_ids, f"duplicate route id: {route_id}")
        route_ids.add(route_id)
        waypoint_ids = route.get("waypoint_ids")
        _require_list(waypoint_ids, f"data.routes[{idx}].waypoint_ids")
        _require(
            len(waypoint_ids) >= 2,
            f"route {route_id} must contain at least 2 waypoint_ids",
        )
        for waypoint_id in waypoint_ids:
            _require(
                isinstance(waypoint_id, str),
                f"route {route_id} waypoint_ids must contain strings",
            )
            _require(
                waypoint_id in points,
                f"route {route_id} references unknown point: {waypoint_id}",
            )

    for idx, airspace in enumerate(airspaces):
        _require_dict(airspace, f"data.airspaces[{idx}]")
        _require(
            isinstance(airspace.get("id"), str),
            f"data.airspaces[{idx}].id must be a string",
        )
        center_point_id = airspace.get("center_point_id")
        _require(
            isinstance(center_point_id, str) and center_point_id in points,
            f"data.airspaces[{idx}].center_point_id must reference an existing point",
        )
        _require(
            isinstance(airspace.get("radius_nm"), (int, float)),
            f"data.airspaces[{idx}].radius_nm must be numeric",
        )

    return payload


def validate_scenario_aircraft(payload, route_ids=None):
    validate_envelope(payload, "airspacesim.scenario_aircraft")
    data = payload["data"]
    aircraft = data.get("aircraft")
    _require_list(aircraft, "data.aircraft")

    seen_ids = set()
    for idx, item in enumerate(aircraft):
        _require_dict(item, f"data.aircraft[{idx}]")
        ac_id = item.get("id")
        _require(
            isinstance(ac_id, str) and ac_id,
            f"data.aircraft[{idx}].id must be non-empty string",
        )
        _require(ac_id not in seen_ids, f"duplicate aircraft id: {ac_id}")
        seen_ids.add(ac_id)
        route_id = item.get("route_id")
        _require(
            isinstance(route_id, str) and route_id,
            f"data.aircraft[{idx}].route_id must be non-empty string",
        )
        if route_ids is not None:
            _require(
                route_id in route_ids,
                f"aircraft {ac_id} references unknown route_id: {route_id}",
            )
        _require(
            isinstance(item.get("speed_kt"), (int, float)) and item["speed_kt"] > 0,
            f"data.aircraft[{idx}].speed_kt must be > 0",
        )
        if "altitude_ft" in item:
            _require(
                isinstance(item.get("altitude_ft"), (int, float))
                and item["altitude_ft"] >= 0,
                f"data.aircraft[{idx}].altitude_ft must be >= 0",
            )
        if "vertical_rate_fpm" in item:
            _require(
                isinstance(item.get("vertical_rate_fpm"), (int, float)),
                f"data.aircraft[{idx}].vertical_rate_fpm must be numeric",
            )
    return payload


def validate_inbox_events(payload):
    validate_envelope(payload, "airspacesim.inbox_events")
    data = payload["data"]
    events = data.get("events")
    _require_list(events, "data.events")

    allowed_types = {
        "ADD_AIRCRAFT",
        "SET_SPEED",
        "REMOVE_AIRCRAFT",
        "REROUTE",
        "SET_VERTICAL_RATE",
    }
    for idx, event in enumerate(events):
        _require_dict(event, f"data.events[{idx}]")
        _require(
            isinstance(event.get("event_id"), str) and event["event_id"],
            f"data.events[{idx}].event_id required",
        )
        _require(
            event.get("type") in allowed_types, f"data.events[{idx}].type unsupported"
        )
        _require(
            _is_iso8601_utc(event.get("created_utc")),
            f"data.events[{idx}].created_utc must be ISO-8601",
        )
        _require_dict(event.get("payload"), f"data.events[{idx}].payload")
        if "sequence" in event:
            _require(
                isinstance(event["sequence"], int),
                f"data.events[{idx}].sequence must be integer",
            )

    return payload


def validate_aircraft_state(payload):
    validate_envelope(payload, "airspacesim.aircraft_state")
    data = payload["data"]
    aircraft = data.get("aircraft")
    _require_list(aircraft, "data.aircraft")

    for idx, item in enumerate(aircraft):
        _require_dict(item, f"data.aircraft[{idx}]")
        _require(
            isinstance(item.get("id"), str) and item["id"],
            f"data.aircraft[{idx}].id required",
        )
        _require_lat_lon(item.get("position_dd"), f"data.aircraft[{idx}].position_dd")
        _require(
            isinstance(item.get("status"), str),
            f"data.aircraft[{idx}].status must be string",
        )
        if "altitude_ft" in item:
            _require(
                isinstance(item.get("altitude_ft"), (int, float))
                and item["altitude_ft"] >= 0,
                f"data.aircraft[{idx}].altitude_ft must be >= 0",
            )
        if "vertical_rate_fpm" in item:
            _require(
                isinstance(item.get("vertical_rate_fpm"), (int, float)),
                f"data.aircraft[{idx}].vertical_rate_fpm must be numeric",
            )
        _require(
            _is_iso8601_utc(item.get("updated_utc")),
            f"data.aircraft[{idx}].updated_utc must be ISO-8601",
        )

    return payload


def validate_render_profile(payload):
    validate_envelope(payload, "airspacesim.render_profile")
    data = payload["data"]
    map_cfg = data.get("map")
    layers = data.get("layers")
    _require_dict(map_cfg, "data.map")
    _require_list(layers, "data.layers")
    _require(isinstance(map_cfg.get("zoom"), int), "data.map.zoom must be integer")
    return payload


def validate_map_config(payload):
    """
    Validate map config contract.

    Accepted shapes:
    - legacy (unversioned): root-level config fields
    - versioned: airspacesim.map_config envelope with data object
    """
    if isinstance(payload, dict) and "schema" in payload:
        validate_envelope(payload, "airspacesim.map_config")
        cfg = payload["data"]
        prefix = "data"
    else:
        _require_dict(payload, "payload")
        cfg = payload
        prefix = "payload"

    has_center = isinstance(cfg.get("center"), list)
    render_center = cfg.get("render", {}).get("map", {}).get("center")
    has_render_center = isinstance(render_center, dict) and isinstance(
        render_center.get("point_id"), str
    )
    _require(
        has_center or has_render_center,
        f"{prefix}.center or {prefix}.render.map.center.point_id is required",
    )
    if has_center:
        _require_lat_lon(cfg.get("center"), f"{prefix}.center")

    _require(
        isinstance(cfg.get("zoom"), int)
        or isinstance(cfg.get("render", {}).get("map", {}).get("zoom"), int),
        f"{prefix}.zoom or {prefix}.render.map.zoom must be integer",
    )

    tile_layer = cfg.get("tile_layer") or cfg.get("render", {}).get("map", {}).get(
        "tile_layer"
    )
    _require_dict(tile_layer, f"{prefix}.tile_layer")
    _require(
        isinstance(tile_layer.get("url"), str) and tile_layer["url"],
        f"{prefix}.tile_layer.url must be a non-empty string",
    )
    _require(
        isinstance(tile_layer.get("attribution"), str),
        f"{prefix}.tile_layer.attribution must be a string",
    )

    elements = cfg.get("elements")
    _require_list(elements, f"{prefix}.elements")
    for idx, element in enumerate(elements):
        _require_dict(element, f"{prefix}.elements[{idx}]")
        _require(
            element.get("type") in {"polyline", "circle", "marker"},
            f"{prefix}.elements[{idx}].type must be one of polyline/circle/marker",
        )
    return payload


def validate_aircraft_data(payload):
    """
    Validate legacy aircraft_data contract.

    Accepted shapes:
    - legacy (unversioned): {"aircraft_data": [...]}
    - versioned: airspacesim.aircraft_data envelope with data.aircraft_data
    """
    if isinstance(payload, dict) and "schema" in payload:
        validate_envelope(payload, "airspacesim.aircraft_data")
        root = payload["data"]
        prefix = "data"
    else:
        _require_dict(payload, "payload")
        root = payload
        prefix = "payload"

    aircraft_data = root.get("aircraft_data")
    _require_list(aircraft_data, f"{prefix}.aircraft_data")
    seen_ids = set()
    for idx, item in enumerate(aircraft_data):
        _require_dict(item, f"{prefix}.aircraft_data[{idx}]")
        ac_id = item.get("id")
        _require(
            isinstance(ac_id, str) and ac_id,
            f"{prefix}.aircraft_data[{idx}].id must be non-empty string",
        )
        _require(ac_id not in seen_ids, f"duplicate aircraft id: {ac_id}")
        seen_ids.add(ac_id)
        if "position" in item:
            _require_lat_lon(
                item.get("position"), f"{prefix}.aircraft_data[{idx}].position"
            )
        if "callsign" in item:
            _require(
                isinstance(item.get("callsign"), str),
                f"{prefix}.aircraft_data[{idx}].callsign must be string",
            )
        if "speed" in item:
            _require(
                isinstance(item.get("speed"), (int, float)) and item["speed"] >= 0,
                f"{prefix}.aircraft_data[{idx}].speed must be >= 0",
            )
    return payload
