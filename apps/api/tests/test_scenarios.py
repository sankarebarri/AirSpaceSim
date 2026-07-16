from app.api.v1.routes.scenarios import (
    create_scenario_route,
    get_scenario,
    list_scenarios,
    update_scenario_route,
)
from app.schemas.scenarios import ScenarioCreateRequest, ScenarioUpdateRequest

SESSION_ID = "test-session-a"


def test_scenario_crud_roundtrip(db_session):
    created = create_scenario_route(
        ScenarioCreateRequest(
            name="Demo Scenario",
            description="Baseline hosted scenario",
            metadata_payload={"seed": "demo"},
        ),
        db_session,
        SESSION_ID,
    )
    assert created.slug == "demo-scenario"
    assert created.airspace_payload["schema"]["name"] == "airspacesim.scenario_airspace"
    assert created.aircraft_payload["schema"]["name"] == "airspacesim.scenario_aircraft"

    list_response = list_scenarios(db_session, SESSION_ID)
    assert len(list_response.items) == 1

    fetch_response = get_scenario(created.id, db_session, SESSION_ID)
    assert fetch_response.name == "Demo Scenario"

    updated = update_scenario_route(
        created.id,
        ScenarioUpdateRequest(
            description="Updated description",
            metadata_payload={"seed": "updated"},
        ),
        db_session,
        SESSION_ID,
    )
    assert updated.description == "Updated description"
    assert updated.metadata_payload == {"seed": "updated"}


def test_scenarios_are_isolated_per_session(db_session):
    create_scenario_route(
        ScenarioCreateRequest(name="Session A Scenario"),
        db_session,
        SESSION_ID,
    )

    other_session_id = "test-session-b"
    list_response = list_scenarios(db_session, other_session_id)
    assert list_response.items == []
