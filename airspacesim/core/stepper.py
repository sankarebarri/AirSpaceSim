"""Adapters that expose stable core stepper interfaces over existing managers."""

from datetime import datetime, timezone

from airspacesim.core.models import TrajectoryTrack


class ManagerStepper:
    """Protocol-friendly adapter around AircraftManager step mechanics."""

    def __init__(self, manager):
        self.manager = manager

    def step(self, time_step_seconds: float):
        self.manager._step_all_aircraft(time_step_seconds)
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        tracks = []
        for ac in self.manager.aircraft_list:
            status = "finished" if hasattr(ac, "finished_time") else "active"
            tracks.append(
                TrajectoryTrack(
                    id=ac.id,
                    route_id=ac.route,
                    position_dd=(float(ac.position[0]), float(ac.position[1])),
                    status=status,
                    updated_utc=now_iso,
                    callsign=ac.callsign,
                    speed_kt=float(ac.speed),
                    altitude_ft=float(ac.altitude_ft),
                    vertical_rate_fpm=float(ac.vertical_rate_fpm),
                )
            )
        return tracks
