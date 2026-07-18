"""Runtime configuration for the FastAPI service."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service configuration loaded from environment variables."""

    app_name: str = "AirSpaceSim API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./var/airspacesim-api.db"
    database_echo: bool = False
    auto_create_schema: bool = True
    checkpoint_retention_per_run: int = 25
    # Cookie-based auth requires credentialed CORS, which forbids the "*"
    # wildcard — defaults cover the local dev frontends; production must set
    # its own explicit origins (enforced in create_app).
    cors_allowed_origins: list[str] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ]
    cors_allow_credentials: bool = True
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"
    auth_cookie_name: str = "airspacesim_session"
    auth_session_ttl_days: int = 30
    anonymous_run_retention_days: int = 14
    retention_sweep_interval_seconds: float = 3600.0
    max_concurrent_runs_per_session: int = 100
    max_concurrent_runs_global: int = 500
    rate_limit_run_creates_per_minute: int = 300
    max_request_body_bytes: int = 256_000

    model_config = SettingsConfigDict(
        env_prefix="AIRSPACESIM_API_",
        env_file=".env",
        extra="ignore",
    )

    @property
    def database_path(self) -> Path | None:
        """Return the local file path when using a SQLite file URL."""

        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            return None
        raw_path = self.database_url.removeprefix(prefix)
        if raw_path == ":memory:":
            return None
        return Path(raw_path)


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for app startup and request wiring."""

    return Settings()
