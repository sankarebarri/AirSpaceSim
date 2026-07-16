from app.api.v1.routes.health import healthcheck
from app.config import get_settings


def test_healthcheck_returns_ok(db_session):
    response = healthcheck(get_settings(), db_session)

    assert response.status == "ok"
    assert response.database == "ok"
