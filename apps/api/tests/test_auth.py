"""Phase 6: registration, login, sessions, profile, and guest adoption."""

from fastapi.testclient import TestClient

from app.main import create_app

GUEST_SESSION = "guest-session-auth-tests"


def _client() -> TestClient:
    return TestClient(create_app())


def _register(client: TestClient, email="trainee@example.test", password="training-pass-1"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Trainee"},
        headers={"X-Airspacesim-Session": GUEST_SESSION},
    )


def test_register_login_me_logout_flow(db_session):
    with _client() as client:
        register_response = _register(client)
        assert register_response.status_code == 201
        body = register_response.json()
        assert body["email"] == "trainee@example.test"
        assert body["preferred_language"] == "en"

        set_cookie = register_response.headers["set-cookie"]
        assert "airspacesim_session=" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie
        # Development environment: cookie is not Secure (production sets it).
        assert "Secure" not in set_cookie

        me_response = client.get("/api/v1/auth/me")
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "trainee@example.test"

        logout_response = client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 204
        assert client.get("/api/v1/auth/me").status_code == 401


def test_login_rejects_wrong_password_and_duplicate_registration(db_session):
    with _client() as client:
        assert _register(client).status_code == 201

        duplicate = _register(client)
        assert duplicate.status_code == 409
        assert "already exists" in duplicate.json()["detail"]

        wrong = client.post(
            "/api/v1/auth/login",
            json={"email": "trainee@example.test", "password": "wrong-password"},
        )
        assert wrong.status_code == 401
        assert wrong.json()["detail"] == "Incorrect email or password."

        short = client.post(
            "/api/v1/auth/register",
            json={"email": "second@example.test", "password": "short"},
        )
        assert short.status_code == 422  # schema-level minimum length


def test_login_adopts_guest_runs_onto_the_account(db_session):
    with _client() as client:
        created = client.post(
            "/api/v1/runs",
            json={"name": "Guest Run"},
            headers={"X-Airspacesim-Session": GUEST_SESSION},
        )
        assert created.status_code == 201
        run_id = created.json()["id"]

        assert _register(client).status_code == 201

        # The run is now visible from a *different* browser session because
        # it belongs to the signed-in account.
        listed = client.get(
            "/api/v1/runs",
            headers={"X-Airspacesim-Session": "another-device-session"},
        )
        assert listed.status_code == 200
        assert [item["id"] for item in listed.json()["items"]] == [run_id]

        # And no longer visible to a guest on a fresh session without login.
        client.post("/api/v1/auth/logout")
        guest_listing = client.get(
            "/api/v1/runs",
            headers={"X-Airspacesim-Session": "another-device-session"},
        )
        assert guest_listing.json()["items"] == []


def test_profile_update_saves_language_and_rejects_unknown(db_session):
    with _client() as client:
        assert _register(client).status_code == 201

        updated = client.patch(
            "/api/v1/auth/me",
            json={"preferred_language": "fr", "display_name": "Stagiaire"},
        )
        assert updated.status_code == 200
        assert updated.json()["preferred_language"] == "fr"
        assert updated.json()["display_name"] == "Stagiaire"

        invalid = client.patch("/api/v1/auth/me", json={"preferred_language": "de"})
        assert invalid.status_code == 400
        assert "Supported languages" in invalid.json()["detail"]

        client.post("/api/v1/auth/logout")
        guest_patch = client.patch("/api/v1/auth/me", json={"display_name": "X"})
        assert guest_patch.status_code == 401


def test_runs_created_while_signed_in_are_attributed(db_session):
    with _client() as client:
        assert _register(client).status_code == 201
        created = client.post(
            "/api/v1/runs",
            json={"name": "Signed-in Run"},
            headers={"X-Airspacesim-Session": GUEST_SESSION},
        )
        assert created.status_code == 201
        run_id = created.json()["id"]

        from app.db.models import RunRecord

        stored = db_session.get(RunRecord, run_id)
        assert stored is not None and stored.user_id is not None
