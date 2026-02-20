"""Deterministic route registry and flight-plan waypoint stitching."""

from dataclasses import dataclass

from airspacesim.utils.logging_config import default_logger as logger


class RouteResolutionError(ValueError):
    """Raised when a flight plan cannot be resolved into an ordered waypoint path."""


@dataclass(frozen=True)
class FlightPlan:
    """Minimal route-driven flight plan contract."""

    departure_id: str
    destination_id: str
    route_ids: tuple[str, ...]


class RouteRegistry:
    """Stores airway definitions and resolves route chains into waypoint paths."""

    def __init__(self, routes):
        self.routes = {
            route_id: list(waypoint_ids) for route_id, waypoint_ids in routes.items()
        }

    def resolve_flight_plan(self, plan):
        if not plan.route_ids:
            raise RouteResolutionError("flight plan must include at least one route id")
        for route_id in plan.route_ids:
            if route_id not in self.routes:
                raise RouteResolutionError(f"unknown route_id '{route_id}'")

        first_route = self.routes[plan.route_ids[0]]
        if plan.departure_id in first_route:
            start_candidates = [plan.departure_id]
            prefix = []
        else:
            start_candidates = [first_route[0], first_route[-1]]
            prefix = [plan.departure_id]

        best = None
        for start_wp in start_candidates:
            resolved = self._resolve_from_route(
                route_ids=list(plan.route_ids),
                route_idx=0,
                start_wp=start_wp,
                destination_id=plan.destination_id,
            )
            if resolved is None:
                continue
            candidate = prefix + resolved
            key = (len(candidate), tuple(candidate))
            if best is None or key < best[0]:
                best = (key, candidate)

        if best is None:
            raise RouteResolutionError(
                f"could not resolve flight plan departure={plan.departure_id} routes={list(plan.route_ids)} "
                f"destination={plan.destination_id}"
            )
        return best[1]

    def _resolve_from_route(self, route_ids, route_idx, start_wp, destination_id):
        route_id = route_ids[route_idx]
        route = self.routes[route_id]

        if route_idx == len(route_ids) - 1:
            end_candidates = (
                [destination_id] if destination_id in route else [route[0], route[-1]]
            )
            best = None
            for end_wp in end_candidates:
                segment = self._segment_between(route, start_wp, end_wp)
                if not segment:
                    continue
                candidate = list(segment)
                if destination_id not in route:
                    candidate.append(destination_id)
                key = (len(candidate), tuple(candidate))
                if best is None or key < best[0]:
                    best = (key, candidate)
            return best[1] if best else None

        next_route = self.routes[route_ids[route_idx + 1]]
        intersections = sorted(set(route) & set(next_route))
        if not intersections:
            raise RouteResolutionError(
                f"routes '{route_id}' and '{route_ids[route_idx + 1]}' do not intersect"
            )

        candidates = []
        for join_wp in intersections:
            segment = self._segment_between(route, start_wp, join_wp)
            if not segment:
                continue
            remainder = self._resolve_from_route(
                route_ids=route_ids,
                route_idx=route_idx + 1,
                start_wp=join_wp,
                destination_id=destination_id,
            )
            if not remainder:
                continue
            full = segment + remainder[1:]
            candidates.append((join_wp, full))

        if not candidates:
            raise RouteResolutionError(
                f"no valid forward stitching from route '{route_id}' at waypoint '{start_wp}'"
            )

        # Deterministic choice: shortest path, then lexicographic path, then join id.
        ranked = sorted(
            candidates, key=lambda item: (len(item[1]), tuple(item[1]), item[0])
        )
        chosen_join, chosen_path = ranked[0]
        if len(candidates) > 1:
            logger.info(
                "Multiple intersections between %s and %s: %s; selected %s",
                route_id,
                route_ids[route_idx + 1],
                intersections,
                chosen_join,
            )
        return chosen_path

    @staticmethod
    def _segment_between(route, start_wp, end_wp):
        if start_wp not in route or end_wp not in route:
            return None
        start_idx = route.index(start_wp)
        end_idx = route.index(end_wp)
        if start_idx <= end_idx:
            return route[start_idx : end_idx + 1]
        return list(reversed(route[end_idx : start_idx + 1]))
