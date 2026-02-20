# simulation/aircraft.py
from airspacesim.utils.conversions import haversine
from airspacesim.simulation.interpolation import interpolate_position
from airspacesim.settings import settings  # To access SIMULATION_SPEED
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
        """
        self.id = id
        self.route = route
        self.waypoints = waypoints
        self.speed = self._sanitize_speed_kt(speed)
        self.callsign = callsign
        self.altitude_ft = float(altitude_ft)
        self.vertical_rate_fpm = float(vertical_rate_fpm)
        self.current_index = 0  # Current waypoint index.
        self.position = waypoints[0]  # Start at the first waypoint.
        self.segment_progress = 0  # Nautical miles travelled along the current segment.

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

        if mode == "off" or speed <= settings.MAX_ABSURD_SPEED_KTS:
            return speed

        if mode == "clamp":
            logger.warning(
                "Aircraft %s speed %.1f kt clamped to %.1f kt.",
                self.id,
                speed,
                settings.MAX_ABSURD_SPEED_KTS,
            )
            return settings.MAX_ABSURD_SPEED_KTS

        raise ValueError(
            f"Aircraft speed {speed:.1f} kt exceeds MAX_ABSURD_SPEED_KTS={settings.MAX_ABSURD_SPEED_KTS:.1f}"
        )

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
        self.altitude_ft = max(0.0, self.altitude_ft + (self.vertical_rate_fpm * effective_time_seconds / 60.0))
        # Horizontal motion in NM:
        # knots = NM / hour, so NM per second = knots / 3600.
        remaining_travel_distance = (self.speed / 3600.0) * effective_time_seconds
        if remaining_travel_distance <= 0:
            return

        # Consume full travel distance, crossing multiple segments if needed.
        while remaining_travel_distance > 0 and self.current_index < len(self.waypoints) - 1:
            start = self.waypoints[self.current_index]
            end = self.waypoints[self.current_index + 1]
            segment_distance = haversine(start[0], start[1], end[0], end[1])
            if segment_distance <= 0:
                # Degenerate segment: skip safely.
                self.current_index += 1
                self.position = end
                self.segment_progress = 0
                continue

            remaining_segment_distance = max(segment_distance - self.segment_progress, 0)
            if remaining_travel_distance < remaining_segment_distance:
                # Advance within the current segment.
                self.segment_progress += remaining_travel_distance
                fraction = self.segment_progress / segment_distance
                self.position = interpolate_position(start, end, fraction)
                remaining_travel_distance = 0
                break

            # Complete segment and carry residual distance to the next segment.
            remaining_travel_distance -= remaining_segment_distance
            self.current_index += 1
            self.position = end
            self.segment_progress = 0
