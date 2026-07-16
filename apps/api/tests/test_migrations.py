from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.config import get_settings
from app.db.session import get_engine, get_session_factory


def _reset_api_caches() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    get_settings.cache_clear()


def _build_alembic_config(tmp_path, monkeypatch) -> tuple[Config, str]:
    db_path = tmp_path / "airspacesim-api-migrations.db"
    database_url = f"sqlite:///{db_path}"
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
    return alembic_config, database_url


def _inspect_database(database_url: str) -> tuple[set[str], str]:
    engine = create_engine(database_url, future=True)
    with engine.connect() as connection:
        table_names = set(inspect(connection).get_table_names())
        current_revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    engine.dispose()
    return table_names, current_revision


def test_alembic_upgrade_creates_expected_schema(tmp_path, monkeypatch):
    alembic_config, database_url = _build_alembic_config(tmp_path, monkeypatch)

    command.upgrade(alembic_config, "head")

    table_names, current_revision = _inspect_database(database_url)

    assert {
        "alembic_version",
        "run_checkpoints",
        "run_commands",
        "runs",
        "scenarios",
    }.issubset(table_names)
    assert current_revision == "20260708_0003"

    _reset_api_caches()


def test_alembic_upgrade_adds_session_scoping_columns(tmp_path, monkeypatch):
    alembic_config, database_url = _build_alembic_config(tmp_path, monkeypatch)

    command.upgrade(alembic_config, "20260511_0002")
    engine = create_engine(database_url, future=True)
    with engine.connect() as connection:
        run_columns = {column["name"] for column in inspect(connection).get_columns("runs")}
        scenario_columns = {
            column["name"] for column in inspect(connection).get_columns("scenarios")
        }
    engine.dispose()
    assert "session_id" not in run_columns
    assert "session_id" not in scenario_columns

    command.upgrade(alembic_config, "head")
    engine = create_engine(database_url, future=True)
    with engine.connect() as connection:
        run_columns = {column["name"] for column in inspect(connection).get_columns("runs")}
        scenario_columns = {
            column["name"] for column in inspect(connection).get_columns("scenarios")
        }
    engine.dispose()
    assert "session_id" in run_columns
    assert "session_id" in scenario_columns

    command.downgrade(alembic_config, "20260511_0002")
    engine = create_engine(database_url, future=True)
    with engine.connect() as connection:
        run_columns = {column["name"] for column in inspect(connection).get_columns("runs")}
    engine.dispose()
    assert "session_id" not in run_columns

    _reset_api_caches()


def test_alembic_upgrade_path_supports_incremental_revisions(tmp_path, monkeypatch):
    alembic_config, database_url = _build_alembic_config(tmp_path, monkeypatch)

    command.upgrade(alembic_config, "20260511_0001")

    table_names, current_revision = _inspect_database(database_url)
    assert {
        "alembic_version",
        "run_commands",
        "runs",
        "scenarios",
    }.issubset(table_names)
    assert "run_checkpoints" not in table_names
    assert current_revision == "20260511_0001"

    command.upgrade(alembic_config, "head")

    table_names, current_revision = _inspect_database(database_url)
    assert "run_checkpoints" in table_names
    assert current_revision == "20260708_0003"

    _reset_api_caches()


def test_alembic_downgrade_removes_checkpoint_revision(tmp_path, monkeypatch):
    alembic_config, database_url = _build_alembic_config(tmp_path, monkeypatch)

    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "20260511_0001")

    table_names, current_revision = _inspect_database(database_url)
    assert {
        "alembic_version",
        "run_commands",
        "runs",
        "scenarios",
    }.issubset(table_names)
    assert "run_checkpoints" not in table_names
    assert current_revision == "20260511_0001"

    _reset_api_caches()
