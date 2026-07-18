import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.config import get_settings
from app.db.session import get_engine, get_session_factory

BASELINE_REVISION = "20260718_0001"
EXPECTED_TABLES = {
    "alembic_version",
    "users",
    "auth_sessions",
    "learning_progress",
    "scenarios",
    "runs",
    "run_commands",
    "run_checkpoints",
}


def _reset_api_caches() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    get_settings.cache_clear()


def _database_urls(tmp_path) -> list[str]:
    urls = [f"sqlite:///{tmp_path / 'airspacesim-api-migrations.db'}"]
    pg_url = os.getenv("AIRSPACESIM_TEST_DATABASE_URL")
    if pg_url:
        urls.append(pg_url)
    return urls


def _build_alembic_config(database_url: str, monkeypatch) -> Config:
    monkeypatch.setenv("AIRSPACESIM_API_DATABASE_URL", database_url)
    monkeypatch.setenv("AIRSPACESIM_API_AUTO_CREATE_SCHEMA", "0")
    _reset_api_caches()

    app_root = Path(__file__).resolve().parents[1]
    alembic_config = Config(str(app_root / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location",
        str(app_root / "app" / "db" / "migrations"),
    )
    alembic_config.set_main_option("prepend_sys_path", str(app_root))
    return alembic_config


def _drop_everything(database_url: str) -> None:
    engine = create_engine(database_url, future=True)
    from app.db.base import Base
    from app.db import models  # noqa: F401

    Base.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    engine.dispose()


def _inspect_database(database_url: str) -> tuple[set[str], str]:
    engine = create_engine(database_url, future=True)
    with engine.connect() as connection:
        table_names = set(inspect(connection).get_table_names())
        current_revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    engine.dispose()
    return table_names, current_revision


def test_baseline_upgrade_creates_full_schema_on_every_database(tmp_path, monkeypatch):
    """The squashed baseline must build the schema from an empty database

    (SQLite always; PostgreSQL too when AIRSPACESIM_TEST_DATABASE_URL is set,
    per decision Q5)."""

    for database_url in _database_urls(tmp_path):
        _drop_everything(database_url)
        alembic_config = _build_alembic_config(database_url, monkeypatch)

        command.upgrade(alembic_config, "head")
        table_names, current_revision = _inspect_database(database_url)
        assert EXPECTED_TABLES.issubset(table_names), database_url
        assert current_revision == BASELINE_REVISION

        # Downgrade returns to an empty database.
        command.downgrade(alembic_config, "base")
        engine = create_engine(database_url, future=True)
        with engine.connect() as connection:
            remaining = set(inspect(connection).get_table_names()) - {"alembic_version"}
        engine.dispose()
        assert remaining == set(), database_url

    _reset_api_caches()


def test_baseline_columns_cover_auth_and_summary_fields(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'columns.db'}"
    alembic_config = _build_alembic_config(database_url, monkeypatch)
    command.upgrade(alembic_config, "head")

    engine = create_engine(database_url, future=True)
    with engine.connect() as connection:
        inspector = inspect(connection)
        run_columns = {column["name"] for column in inspector.get_columns("runs")}
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        progress_columns = {
            column["name"] for column in inspector.get_columns("learning_progress")
        }
    engine.dispose()

    assert {"session_id", "user_id", "summary_json"}.issubset(run_columns)
    assert {"email", "password_hash", "preferred_language"}.issubset(user_columns)
    assert {"user_id", "concept_id", "stage_key", "status"}.issubset(progress_columns)

    _reset_api_caches()
