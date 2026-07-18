"""Phase 6: protected learning-progress persistence."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_progress_requires_authentication(db_session):
    with TestClient(create_app()) as client:
        response = client.put(
            "/api/v1/progress",
            json={"concept_id": "traffic_relationships", "stage_key": "tr_same_track"},
        )
        assert response.status_code == 401
        assert client.get("/api/v1/progress").status_code == 401


def test_progress_upsert_and_listing_for_signed_in_user(db_session):
    with TestClient(create_app()) as client:
        register = client.post(
            "/api/v1/auth/register",
            json={"email": "learner@example.test", "password": "training-pass-1"},
        )
        assert register.status_code == 201

        first = client.put(
            "/api/v1/progress",
            json={"concept_id": "traffic_relationships", "stage_key": "tr_same_track"},
        )
        assert first.status_code == 200
        assert first.json()["status"] == "completed"

        # Upserting the same stage does not duplicate it.
        client.put(
            "/api/v1/progress",
            json={"concept_id": "traffic_relationships", "stage_key": "tr_same_track"},
        )
        client.put(
            "/api/v1/progress",
            json={
                "concept_id": "traffic_relationships",
                "stage_key": "tr_reciprocal_track",
            },
        )

        listed = client.get("/api/v1/progress")
        assert listed.status_code == 200
        stages = sorted(item["stage_key"] for item in listed.json()["items"])
        assert stages == ["tr_reciprocal_track", "tr_same_track"]
