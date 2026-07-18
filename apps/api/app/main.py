"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.routes import (
    airspaces,
    auth,
    commands,
    content,
    health,
    progress,
    runs,
    scenarios,
)
from .config import get_settings
from .db.session import get_session_factory, init_db
from .limits import SlidingWindowRateLimiter
from .middleware import MaxBodySizeMiddleware
from .services.retention import RetentionSweeper
from .sessions import SessionRegistry
from .ws import BroadcastHub


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""

    settings = get_settings()
    if settings.environment == "production":
        insecure_origins = [
            origin
            for origin in settings.cors_allowed_origins
            if origin == "*" or "localhost" in origin or "127.0.0.1" in origin
        ]
        if insecure_origins:
            raise RuntimeError(
                "Production requires explicit non-localhost CORS origins "
                f"(found {insecure_origins}); set "
                "AIRSPACESIM_API_CORS_ALLOWED_ORIGINS explicitly."
            )
    broadcast_hub = BroadcastHub()
    session_registry = SessionRegistry(
        broadcast_hub=broadcast_hub,
        checkpoint_retention_per_run=settings.checkpoint_retention_per_run,
    )
    run_creation_rate_limiter = SlidingWindowRateLimiter(
        max_requests=settings.rate_limit_run_creates_per_minute,
        window_seconds=60.0,
    )

    retention_sweeper = RetentionSweeper(
        get_session_factory(),
        retention_days=settings.anonymous_run_retention_days,
        interval_seconds=settings.retention_sweep_interval_seconds,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.auto_create_schema:
            init_db()
        app.state.session_registry = session_registry
        app.state.broadcast_hub = broadcast_hub
        app.state.run_creation_rate_limiter = run_creation_rate_limiter
        app.state.retention_sweeper = retention_sweeper
        retention_sweeper.start()
        yield
        retention_sweeper.stop()
        session_registry.shutdown()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        MaxBodySizeMiddleware, max_bytes=settings.max_request_body_bytes
    )
    app.state.session_registry = session_registry
    app.state.broadcast_hub = broadcast_hub
    app.state.run_creation_rate_limiter = run_creation_rate_limiter

    app.include_router(health.router)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(progress.router, prefix=settings.api_v1_prefix)
    app.include_router(content.router, prefix=settings.api_v1_prefix)
    app.include_router(airspaces.router, prefix=settings.api_v1_prefix)
    app.include_router(scenarios.router, prefix=settings.api_v1_prefix)
    app.include_router(runs.router, prefix=settings.api_v1_prefix)
    app.include_router(commands.router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
