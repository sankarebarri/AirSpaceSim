"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.routes import airspaces, commands, content, health, runs, scenarios
from .config import get_settings
from .db.session import init_db
from .limits import SlidingWindowRateLimiter
from .middleware import MaxBodySizeMiddleware
from .sessions import SessionRegistry
from .ws import BroadcastHub


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""

    settings = get_settings()
    if settings.environment == "production" and settings.cors_allowed_origins == ["*"]:
        raise RuntimeError(
            "cors_allowed_origins must not be '*' in production; "
            "set AIRSPACESIM_API_CORS_ALLOWED_ORIGINS explicitly."
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

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.auto_create_schema:
            init_db()
        app.state.session_registry = session_registry
        app.state.broadcast_hub = broadcast_hub
        app.state.run_creation_rate_limiter = run_creation_rate_limiter
        yield
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
    app.include_router(content.router, prefix=settings.api_v1_prefix)
    app.include_router(airspaces.router, prefix=settings.api_v1_prefix)
    app.include_router(scenarios.router, prefix=settings.api_v1_prefix)
    app.include_router(runs.router, prefix=settings.api_v1_prefix)
    app.include_router(commands.router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
