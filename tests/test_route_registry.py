import pytest

from airspacesim.routes.registry import FlightPlan, RouteRegistry, RouteResolutionError


def test_route_registry_stitches_two_routes_on_intersection():
    routes = {
        "UR981": ["NIAMEY", "GAO_VOR", "TAVIL"],
        "UA612": ["BAMAKO", "GAO_VOR", "ETRUL"],
    }
    registry = RouteRegistry(routes)
    plan = FlightPlan(
        departure_id="NIAMEY",
        destination_id="BAMAKO",
        route_ids=("UR981", "UA612"),
    )

    resolved = registry.resolve_flight_plan(plan)
    assert resolved == ["NIAMEY", "GAO_VOR", "BAMAKO"]


def test_route_registry_raises_when_consecutive_routes_do_not_intersect():
    routes = {
        "R1": ["A", "B", "C"],
        "R2": ["X", "Y", "Z"],
    }
    registry = RouteRegistry(routes)
    plan = FlightPlan(departure_id="A", destination_id="Z", route_ids=("R1", "R2"))

    with pytest.raises(RouteResolutionError):
        registry.resolve_flight_plan(plan)


def test_route_registry_multiple_intersections_picks_deterministic_join():
    routes = {
        "R1": ["A", "B", "C", "D"],
        "R2": ["X", "B", "C", "Y"],
    }
    registry = RouteRegistry(routes)
    plan = FlightPlan(departure_id="A", destination_id="Y", route_ids=("R1", "R2"))

    # Both B and C intersect; deterministic policy chooses earliest viable join on current route.
    resolved = registry.resolve_flight_plan(plan)
    assert resolved == ["A", "B", "C", "Y"]
