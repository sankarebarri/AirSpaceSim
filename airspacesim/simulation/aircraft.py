# simulation/aircraft.py
import math

from airspacesim.utils.conversions import haversine
from airspacesim.simulation.interpolation import interpolate_position
from airspacesim.simulation.performance_database import (
    hold_speed_kt,
    max_flight_level,
    speed_limits_kt,
    turn_rate_deg_per_sec,
)
from airspacesim.settings import settings  # To access SIMULATION_SPEED
from airspacesim.utils.calculate_bearing import calculate_bearing
from airspacesim.utils.logging_config import default_logger as logger


class Aircraft:
    def __init__(
        self,
        id,
        route,
        waypoints,
        speed=400,
        callsign=None,
        altitude_ft=0.0,
        vertical_rate_fpm=0.0,
        flight_level=None,
        aircraft_type="UNKNOWN",
        waypoint_ids=None,
    ):
        """
        Initialize the aircraft.

        :param id: Unique identifier for the aircraft.
        :param route: Route name associated with the aircraft.
        :param waypoints: List of waypoints in decimal degrees [(lat, lon), ...].
        :param speed: Speed of the aircraft in knots. Defaults to 400.
        :param callsign: Optional callsign for the aircraft.
        :param altitude_ft: Initial altitude in feet.
        :param vertical_rate_fpm: Climb(+)/descent(-) rate in feet per minute.
        :param flight_level: Optional metadata flight level (FL). No physics impact.
        :param aircraft_type: Aircraft performance key, for example B737 or A320.
        """
        self.id = id
        self.route = route
        self.waypoints = waypoints
        self.waypoint_ids = list(
            waypoint_ids or [str(index) for index in range(len(waypoints))]
        )
        self.callsign = callsign
        self.aircraft_type = self._sanitize_aircraft_type(aircraft_type)
        self.speed = self._sanitize_speed_kt(speed)
        self.vertical_rate_fpm = float(vertical_rate_fpm)
        sanitized_flight_level = self._sanitize_flight_level(flight_level, altitude_ft)
        self.altitude_ft = self._resolve_initial_altitude_ft(
            altitude_ft,
            flight_level,
            sanitized_flight_level,
        )
        self.flight_level = int(round(self.altitude_ft / 100.0))
        self.target_flight_level = (
            sanitized_flight_level if flight_level is not None else None
        )
        self.current_index = 0  # Current waypoint index.
        self.position = waypoints[0]  # Start at the first waypoint.
        self.segment_progress = 0  # Nautical miles travelled along the current segment.
        self.lateral_mode = "route"
        self.heading_deg = self._resolve_initial_heading_deg()
        self.assigned_heading_deg = None
        self.assigned_radial_deg = None
        self.radial_deviation_deg = None
        self.radial_anchor_dd = None
        self.radial_cross_track_nm = None
        self.radial_capture_tolerance_nm = 1.0
        self.radial_intercept_angle_deg = 30.0
        self.direct_to_fix_id = None
        self.direct_to_target_index = None
        self.waypoint_capture_tolerance_nm = 3.0
        self.hold_fix_id = None
        self.hold_fix_position = None
        self.hold_turn_direction = "right"
        self.pre_hold_speed_kt = None

    def _sanitize_aircraft_type(self, aircraft_type):
        value = str(aircraft_type or "UNKNOWN").strip().upper()
        return value or "UNKNOWN"

    def _resolve_initial_altitude_ft(
        self,
        altitude_ft,
        requested_flight_level,
        sanitized_flight_level,
    ):
        altitude = float(altitude_ft)
        if altitude < 0:
            raise ValueError(f"Altitude must be >= 0 ft, got {altitude_ft}")
        if requested_flight_level is not None and altitude == 0:
            return float(sanitized_flight_level) * 100.0
        return altitude

    def _sanitize_speed_kt(self, speed_kt):
        """Validate configured speed in knots and apply configured guardrails."""
        speed = float(speed_kt)
        if speed <= 0:
            raise ValueError(f"Aircraft speed must be > 0 kt, got {speed_kt}")

        if speed > settings.REALISTIC_ENROUTE_SPEED_WARNING_KTS:
            logger.warning(
                "Aircraft %s speed %.1f kt exceeds realistic en-route threshold %.1f kt.",
                self.id,
                speed,
                settings.REALISTIC_ENROUTE_SPEED_WARNING_KTS,
            )

        mode = settings.SPEED_GUARDRAIL_MODE
        if mode not in {"reject", "clamp", "off"}:
            raise ValueError(f"Unsupported SPEED_GUARDRAIL_MODE: {mode}")

        if mode == "off":
            return speed

        if self.aircraft_type == "UNKNOWN" and speed <= settings.MAX_ABSURD_SPEED_KTS:
            return speed

        lower_limit, upper_limit = speed_limits_kt(self.aircraft_type)
        if lower_limit <= speed <= upper_limit and speed <= settings.MAX_ABSURD_SPEED_KTS:
            return speed

        if mode == "clamp":
            clamped_speed = min(max(speed, lower_limit), upper_limit)
            clamped_speed = min(clamped_speed, settings.MAX_ABSURD_SPEED_KTS)
            logger.warning(
                "Aircraft %s speed %.1f kt clamped to %.1f kt for %s performance limits.",
                self.id,
                speed,
                clamped_speed,
                self.aircraft_type,
            )
            return clamped_speed

        if speed < lower_limit or speed > upper_limit:
            raise ValueError(
                f"Aircraft speed {speed:.1f} kt outside {self.aircraft_type} "
                f"performance range {lower_limit:.1f}-{upper_limit:.1f} kt"
            )

        raise ValueError(
            f"Aircraft speed {speed:.1f} kt exceeds MAX_ABSURD_SPEED_KTS={settings.MAX_ABSURD_SPEED_KTS:.1f}"
        )

    def _sanitize_flight_level(self, flight_level, altitude_ft):
        """
        Normalize FL metadata.
        If no explicit FL is provided, derive display FL from altitude_ft.
        """
        if flight_level is None:
            altitude = float(altitude_ft)
            if altitude < 0:
                altitude = 0.0
            sanitized = int(round(altitude / 100.0))
            if getattr(self, "aircraft_type", "UNKNOWN") == "UNKNOWN":
                return sanitized
            limit = max_flight_level(getattr(self, "aircraft_type", "B737"))
            if sanitized > limit:
                raise ValueError(
                    f"Altitude {altitude:.1f} ft exceeds {self.aircraft_type} max FL{limit}"
                )
            return sanitized

        value = float(flight_level)
        if value < 0:
            raise ValueError(f"Flight level must be >= 0, got {flight_level}")
        sanitized = int(round(value))
        if getattr(self, "aircraft_type", "UNKNOWN") == "UNKNOWN":
            return sanitized
        limit = max_flight_level(getattr(self, "aircraft_type", "B737"))
        if sanitized > limit:
            raise ValueError(
                f"Flight level FL{sanitized} exceeds {self.aircraft_type} max FL{limit}"
            )
        return sanitized

    def _resolve_initial_heading_deg(self):
        if len(self.waypoints) < 2:
            return 0.0
        start = self.waypoints[0]
        end = self.waypoints[1]
        return float(calculate_bearing(start[0], start[1], end[0], end[1]))

    def update_position(self, time_step):
        """
        Update the aircraft's position based on its speed and elapsed time.
        This version processes only one update step per call, so that any change in the
        simulation speed is applied on the next tick to all aircraft.

        :param time_step: Time elapsed in seconds since the last update.
        """
        if self.current_index >= len(self.waypoints) - 1:
            return

        # `time_step` is real elapsed seconds; simulation speed scales simulated seconds.
        effective_time_seconds = float(time_step) * float(settings.SIMULATION_SPEED)
        # Vertical profile update is independent from horizontal segment progression.
        self._update_vertical_profile(effective_time_seconds)
        # Horizontal motion in NM:
        # knots = NM / hour, so NM per second = knots / 3600.
        remaining_travel_distance = (self.speed / 3600.0) * effective_time_seconds
        if remaining_travel_distance <= 0:
            return
        if getattr(self, "lateral_mode", "route") == "heading":
            self._update_heading_assignment(effective_time_seconds)
            self.position = self._destination_point(
                self.position,
                self.heading_deg,
                remaining_travel_distance,
            )
            return
        if getattr(self, "lateral_mode", "route") == "radial_intercept":
            self._update_radial_intercept(effective_time_seconds)
            self.position = self._destination_point(
                self.position,
                self.heading_deg,
                remaining_travel_distance,
            )
            self._advance_route_reference_if_needed()
            return
        if getattr(self, "lateral_mode", "route") == "radial":
            self._update_radial_tracking(effective_time_seconds)
            self.position = self._destination_point(
                self.position,
                self.heading_deg,
                remaining_travel_distance,
            )
            self._advance_route_reference_if_needed()
            return
        if getattr(self, "lateral_mode", "route") == "route_intercept":
            self._update_route_intercept(effective_time_seconds)
            self.position = self._destination_point(
                self.position,
                self.heading_deg,
                remaining_travel_distance,
            )
            self._advance_route_reference_if_needed()
            return
        if getattr(self, "lateral_mode", "route") == "direct_to":
            self._update_direct_to(effective_time_seconds)
            self.position = self._destination_point(
                self.position,
                self.heading_deg,
                remaining_travel_distance,
            )
            self._capture_direct_to_target_if_needed()
            return
        if getattr(self, "lateral_mode", "route") == "hold_entry":
            self._update_direct_to(effective_time_seconds)
            self.position = self._destination_point(
                self.position,
                self.heading_deg,
                remaining_travel_distance,
            )
            self._capture_hold_fix_if_needed()
            return
        if getattr(self, "lateral_mode", "route") == "hold":
            self._update_hold(effective_time_seconds)
            self.position = self._destination_point(
                self.position,
                self.heading_deg,
                remaining_travel_distance,
            )
            return

        # Consume full travel distance, crossing multiple segments if needed.
        while (
            remaining_travel_distance > 0
            and self.current_index < len(self.waypoints) - 1
        ):
            start = self.waypoints[self.current_index]
            end = self.waypoints[self.current_index + 1]
            segment_distance = haversine(start[0], start[1], end[0], end[1])
            if segment_distance <= 0:
                # Degenerate segment: skip safely.
                self.current_index += 1
                self.position = end
                self.segment_progress = 0
                continue

            remaining_segment_distance = max(
                segment_distance - self.segment_progress, 0
            )
            if remaining_travel_distance < remaining_segment_distance:
                # Advance within the current segment.
                self.segment_progress += remaining_travel_distance
                fraction = self.segment_progress / segment_distance
                self.position = interpolate_position(start, end, fraction)
                self.heading_deg = float(
                    calculate_bearing(start[0], start[1], end[0], end[1])
                )
                remaining_travel_distance = 0
                break

            # Complete segment and carry residual distance to the next segment.
            remaining_travel_distance -= remaining_segment_distance
            self.current_index += 1
            self.position = end
            self.segment_progress = 0
            if self.current_index < len(self.waypoints) - 1:
                next_point = self.waypoints[self.current_index + 1]
                self.heading_deg = float(
                    calculate_bearing(end[0], end[1], next_point[0], next_point[1])
                )

    def _update_vertical_profile(self, effective_time_seconds):
        if self.vertical_rate_fpm == 0:
            self.flight_level = int(round(self.altitude_ft / 100.0))
            return

        previous_altitude_ft = self.altitude_ft
        next_altitude_ft = max(
            0.0,
            previous_altitude_ft
            + (self.vertical_rate_fpm * effective_time_seconds / 60.0),
        )
        target_flight_level = getattr(self, "target_flight_level", None)
        if target_flight_level is not None:
            target_altitude_ft = float(target_flight_level) * 100.0
            crossed_target = (
                previous_altitude_ft <= target_altitude_ft <= next_altitude_ft
                if self.vertical_rate_fpm > 0
                else next_altitude_ft <= target_altitude_ft <= previous_altitude_ft
            )
            if crossed_target:
                self.altitude_ft = target_altitude_ft
                self.flight_level = int(round(float(target_flight_level)))
                self.vertical_rate_fpm = 0.0
                return

        self.altitude_ft = next_altitude_ft
        self.flight_level = int(round(self.altitude_ft / 100.0))

    def assign_heading(self, heading_deg):
        heading = float(heading_deg) % 360.0
        self.assigned_heading_deg = heading
        self.assigned_radial_deg = None
        self.lateral_mode = "heading"
        self.radial_deviation_deg = None
        self.radial_anchor_dd = None
        self.radial_cross_track_nm = None

    def assign_radial(self, radial_deg):
        radial = float(radial_deg) % 360.0
        self.assigned_radial_deg = radial
        self.assigned_heading_deg = radial
        self.radial_anchor_dd = self._active_route_anchor()
        self.radial_deviation_deg = self._signed_heading_delta(
            self._active_route_bearing_deg(),
            radial,
        )
        self.radial_cross_track_nm = self._radial_cross_track_nm()
        self.lateral_mode = "radial_intercept"

    def assign_radial_deviation(self, deviation_deg):
        route_heading = self._active_route_bearing_deg()
        self.assign_radial(route_heading + float(deviation_deg))

    def resume_route(self):
        self.assigned_heading_deg = None
        self.assigned_radial_deg = None
        self.radial_deviation_deg = None
        self.radial_anchor_dd = None
        self.radial_cross_track_nm = None
        self.direct_to_fix_id = None
        self.direct_to_target_index = None
        self.lateral_mode = "route_intercept"

    def direct_to(self, fix_id):
        normalized_fix_id = str(fix_id).strip()
        if not normalized_fix_id:
            raise ValueError("Direct-to fix id is required")
        waypoint_lookup = {
            str(waypoint_id).upper(): index
            for index, waypoint_id in enumerate(self.waypoint_ids)
        }
        target_index = waypoint_lookup.get(normalized_fix_id.upper())
        if target_index is None:
            raise ValueError(f"Fix '{fix_id}' is not on route {self.route}")
        if target_index <= self.current_index and self.current_index < len(self.waypoints) - 1:
            raise ValueError(f"Fix '{fix_id}' is behind current route progress")
        self.direct_to_fix_id = self.waypoint_ids[target_index]
        self.direct_to_target_index = target_index
        self.assigned_heading_deg = None
        self.assigned_radial_deg = None
        self.radial_deviation_deg = None
        self.radial_anchor_dd = None
        self.radial_cross_track_nm = None
        self.lateral_mode = "direct_to"

    def hold_at_fix(self, fix_id, turn_direction="right"):
        normalized_fix_id = str(fix_id).strip()
        if not normalized_fix_id:
            raise ValueError("Hold fix id is required")
        waypoint_lookup = {
            str(waypoint_id).upper(): index
            for index, waypoint_id in enumerate(self.waypoint_ids)
        }
        target_index = waypoint_lookup.get(normalized_fix_id.upper())
        if target_index is None:
            raise ValueError(f"Fix '{fix_id}' is not on route {self.route}")
        normalized_turn = str(turn_direction or "right").strip().lower()
        if normalized_turn not in {"left", "right"}:
            raise ValueError("Hold turn_direction must be left or right")
        self.hold_fix_id = self.waypoint_ids[target_index]
        self.hold_fix_position = self.waypoints[target_index]
        self.hold_turn_direction = normalized_turn
        if self.pre_hold_speed_kt is None:
            self.pre_hold_speed_kt = self.speed
        self.speed = min(self.speed, hold_speed_kt(self.aircraft_type))
        self.direct_to_target_index = target_index
        self.direct_to_fix_id = self.hold_fix_id
        self.assigned_heading_deg = None
        self.assigned_radial_deg = None
        self.radial_deviation_deg = None
        self.radial_anchor_dd = None
        self.radial_cross_track_nm = None
        self.lateral_mode = "hold_entry"

    def exit_hold(self):
        if self.pre_hold_speed_kt is not None:
            self.speed = self.pre_hold_speed_kt
        self.pre_hold_speed_kt = None
        self.hold_fix_id = None
        self.hold_fix_position = None
        self.direct_to_fix_id = None
        self.direct_to_target_index = None
        self.resume_route()

    def _update_heading_assignment(self, effective_time_seconds):
        target_heading = getattr(self, "assigned_heading_deg", None)
        if target_heading is None:
            return
        current_heading = float(getattr(self, "heading_deg", 0.0)) % 360.0
        delta = self._signed_heading_delta(current_heading, target_heading)
        max_turn = (
            turn_rate_deg_per_sec(self.aircraft_type, self.speed)
            * effective_time_seconds
        )
        if abs(delta) <= max_turn:
            self.heading_deg = target_heading
            return
        turn_step = max_turn if delta > 0 else -max_turn
        self.heading_deg = (current_heading + turn_step) % 360.0

    def _update_radial_intercept(self, effective_time_seconds):
        target_heading = (
            float(self.assigned_radial_deg)
            if self.assigned_radial_deg is not None
            else float(self.heading_deg)
        ) % 360.0
        cross_track_nm = self._radial_cross_track_nm()
        self.radial_cross_track_nm = cross_track_nm
        if cross_track_nm is not None and abs(cross_track_nm) <= self.radial_capture_tolerance_nm:
            self.lateral_mode = "radial"
            self.assigned_heading_deg = target_heading
            self._update_heading_assignment(effective_time_seconds)
            return
        if cross_track_nm is not None:
            intercept_direction = 1.0 if cross_track_nm > 0 else -1.0
            target_heading = (
                target_heading
                + (intercept_direction * self.radial_intercept_angle_deg)
            ) % 360.0
        self.assigned_heading_deg = target_heading
        self._update_heading_assignment(effective_time_seconds)

    def _update_radial_tracking(self, effective_time_seconds):
        target_heading = (
            float(self.assigned_radial_deg)
            if self.assigned_radial_deg is not None
            else float(self.heading_deg)
        ) % 360.0
        cross_track_nm = self._radial_cross_track_nm()
        self.radial_cross_track_nm = cross_track_nm
        if cross_track_nm is not None:
            correction_deg = max(min(cross_track_nm * 2.5, 12.0), -12.0)
            target_heading = (target_heading + correction_deg) % 360.0
        self.assigned_heading_deg = target_heading
        self.radial_deviation_deg = self._signed_heading_delta(
            self._active_route_bearing_deg(),
            (
                float(self.assigned_radial_deg)
                if self.assigned_radial_deg is not None
                else target_heading
            ),
        )
        self._update_heading_assignment(effective_time_seconds)

    def _update_route_intercept(self, effective_time_seconds):
        target_heading = self._bearing_to_active_route_target()
        self.assigned_heading_deg = target_heading
        self._update_heading_assignment(effective_time_seconds)

    def _update_direct_to(self, effective_time_seconds):
        target_index = self.direct_to_target_index
        if target_index is None or target_index >= len(self.waypoints):
            self.resume_route()
            return
        target = self.waypoints[target_index]
        self.assigned_heading_deg = float(
            calculate_bearing(
                self.position[0],
                self.position[1],
                target[0],
                target[1],
            )
        )
        self._update_heading_assignment(effective_time_seconds)

    def _bearing_to_active_route_target(self):
        if self.current_index >= len(self.waypoints) - 1:
            return float(getattr(self, "heading_deg", 0.0)) % 360.0
        target = self.waypoints[self.current_index + 1]
        return float(
            calculate_bearing(
                self.position[0],
                self.position[1],
                target[0],
                target[1],
            )
        )

    def _signed_heading_delta(self, current_heading, target_heading):
        return ((float(target_heading) - float(current_heading) + 540.0) % 360.0) - 180.0

    def _active_route_bearing_deg(self):
        if self.current_index >= len(self.waypoints) - 1:
            return float(getattr(self, "heading_deg", 0.0)) % 360.0
        start = self.waypoints[self.current_index]
        end = self.waypoints[self.current_index + 1]
        return float(calculate_bearing(start[0], start[1], end[0], end[1]))

    def _active_route_anchor(self):
        if self.current_index >= len(self.waypoints):
            return self.position
        return self.waypoints[self.current_index]

    def _radial_cross_track_nm(self):
        if self.radial_anchor_dd is None or self.assigned_radial_deg is None:
            return None
        anchor_lat, anchor_lon = self.radial_anchor_dd
        current_lat, current_lon = self.position
        mean_lat_rad = math.radians((float(anchor_lat) + float(current_lat)) / 2.0)
        north_nm = (float(current_lat) - float(anchor_lat)) * 60.0
        east_nm = (
            (float(current_lon) - float(anchor_lon))
            * 60.0
            * max(math.cos(mean_lat_rad), 0.2)
        )
        course_rad = math.radians(float(self.assigned_radial_deg))
        course_east = math.sin(course_rad)
        course_north = math.cos(course_rad)
        return (course_east * north_nm) - (course_north * east_nm)

    def _advance_route_reference_if_needed(self):
        if self.current_index >= len(self.waypoints) - 1:
            return
        next_waypoint = self.waypoints[self.current_index + 1]
        distance_to_next = haversine(
            self.position[0],
            self.position[1],
            next_waypoint[0],
            next_waypoint[1],
        )
        if distance_to_next <= 3.0:
            self.current_index += 1
            self.segment_progress = 0
            if self.lateral_mode == "route_intercept":
                self.lateral_mode = "route"
                self.assigned_heading_deg = None

    def _capture_direct_to_target_if_needed(self):
        target_index = self.direct_to_target_index
        if target_index is None or target_index >= len(self.waypoints):
            return
        target = self.waypoints[target_index]
        distance_to_target = haversine(
            self.position[0],
            self.position[1],
            target[0],
            target[1],
        )
        if distance_to_target > self.waypoint_capture_tolerance_nm:
            return
        self.position = target
        self.current_index = target_index
        self.segment_progress = 0
        self.direct_to_target_index = None
        self.direct_to_fix_id = None
        self.assigned_heading_deg = None
        if self.current_index < len(self.waypoints) - 1:
            next_point = self.waypoints[self.current_index + 1]
            self.heading_deg = float(
                calculate_bearing(target[0], target[1], next_point[0], next_point[1])
            )
            self.lateral_mode = "route"
        else:
            self.lateral_mode = "route"

    def _capture_hold_fix_if_needed(self):
        target_index = self.direct_to_target_index
        if target_index is None or target_index >= len(self.waypoints):
            return
        target = self.waypoints[target_index]
        distance_to_target = haversine(
            self.position[0],
            self.position[1],
            target[0],
            target[1],
        )
        if distance_to_target > self.waypoint_capture_tolerance_nm:
            return
        self.position = target
        self.current_index = target_index
        self.segment_progress = 0
        self.direct_to_target_index = None
        self.direct_to_fix_id = None
        self.lateral_mode = "hold"

    def _update_hold(self, effective_time_seconds):
        turn_rate = turn_rate_deg_per_sec(self.aircraft_type, self.speed)
        if self.hold_turn_direction == "left":
            turn_rate *= -1.0
        self.heading_deg = (
            float(self.heading_deg) + (turn_rate * effective_time_seconds)
        ) % 360.0
        self.assigned_heading_deg = self.heading_deg

    def _destination_point(self, start, heading_deg, distance_nm):
        earth_radius_nm = 3440.065
        lat1 = math.radians(float(start[0]))
        lon1 = math.radians(float(start[1]))
        bearing = math.radians(float(heading_deg))
        angular_distance = float(distance_nm) / earth_radius_nm

        lat2 = math.asin(
            math.sin(lat1) * math.cos(angular_distance)
            + math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing)
        )
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
            math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2),
        )
        lon2 = (lon2 + (3 * math.pi)) % (2 * math.pi) - math.pi
        return [math.degrees(lat2), math.degrees(lon2)]
