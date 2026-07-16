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
    cors_allowed_origins: list[str] = ["*"]
    cors_allow_credentials: bool = False
    debug: bool = False
    environment: str = "development"
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
