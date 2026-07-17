"""Simulation run routes."""

import asyncio
from queue import Empty

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import Response

from airspacesim.io import build_envelope, serialize_trajectory_payload_to_csv

from ....db.repositories import RunCheckpointRepository, RunRepository
from ....dependencies import (
    BroadcastHubDependency,
    DbSessionDependency,
    RunCreationRateLimitDependency,
    SessionIdDependency,
    SessionRegistryDependency,
    SettingsDependency,
)
from ....schemas.runs import (
    PracticeRunCreateRequest,
    RunCreateRequest,
    RunListResponse,
    RunResponse,
    RunStateResponse,
    RunTrajectoryResponse,
)
from ....services import (
    create_run,
    missing_runtime_detail,
    pause_run as pause_run_service,
    resume_run as resume_run_service,
    start_run as start_run_service,
    stop_run as stop_run_service,
)
from ....services.practice_runs import create_practice_run

router = APIRouter(prefix="/runs", tags=["runs"])


def _enforce_run_capacity(
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    session_id: str,
    settings: SettingsDependency,
) -> None:
    if len(session_registry.list_sessions()) >= settings.max_concurrent_runs_global:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The service is at capacity. Try again shortly.",
        )
    active_for_session = RunRepository(db).count_active_for_session(session_id)
    if active_for_session >= settings.max_concurrent_runs_per_session:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"You already have {active_for_session} active runs "
                f"(limit: {settings.max_concurrent_runs_per_session})."
            ),
        )


def _get_run_or_404(run_id: str, db: DbSessionDependency, session_id: str):
    run = RunRepository(db).get(run_id, session_id=session_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run not found: {run_id}",
        )
    return run


def _stop_previous_lesson_practice_runs(
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    *,
    session_id: str,
    airspace_id: str,
    lesson_id: str | None,
) -> None:
    if not lesson_id:
        return

    for run in RunRepository(db).list(session_id=session_id):
        if run.status not in {"running", "paused"} or run.scenario is None:
            continue
        metadata = run.scenario.metadata_payload or {}
        if (
            metadata.get("source") != "airspacesim.api.practice_runs"
            or metadata.get("airspace_id") != airspace_id
            or metadata.get("lesson_id") != lesson_id
        ):
            continue
        session_registry.stop(run.id)
        stop_run_service(db, run)


def _build_inactive_state(run) -> RunStateResponse:
    return RunStateResponse(
        run=RunResponse.model_validate(run),
        runtime_status="inactive",
        sim_rate=float(run.sim_rate),
        updated_utc=None,
        source="database_only",
        last_error=None,
        aircraft=[],
        metrics={
            "aircraft_count": 0,
            "active_aircraft_count": 0,
            "finished_aircraft_count": 0,
        },
    )


def _checkpoint_updated_utc(checkpoint) -> str:
    return checkpoint.snapshot.get("updated_utc") or checkpoint.created_at.isoformat()


def _checkpoint_metrics(snapshot: dict) -> dict:
    metrics = snapshot.get("metrics")
    if isinstance(metrics, dict):
        return metrics

    aircraft = snapshot.get("aircraft", [])
    active_count = sum(1 for item in aircraft if item.get("status") == "active")
    finished_count = len(aircraft) - active_count
    return {
        "aircraft_count": len(aircraft),
        "active_aircraft_count": active_count,
        "finished_aircraft_count": finished_count,
    }


def _build_checkpoint_state(run, checkpoint) -> RunStateResponse:
    snapshot = checkpoint.snapshot or {}
    return RunStateResponse(
        run=RunResponse.model_validate(run),
        runtime_status=checkpoint.runtime_status,
        sim_rate=float(checkpoint.sim_rate),
        updated_utc=_checkpoint_updated_utc(checkpoint),
        source="checkpoint",
        last_error=snapshot.get("last_error"),
        time_seconds=snapshot.get("time_seconds"),
        aircraft=snapshot.get("aircraft", []),
        separation=snapshot.get("separation"),
        summary=snapshot.get("summary"),
        metrics=_checkpoint_metrics(snapshot),
    )


def _build_checkpoint_trajectory(run_id: str, checkpoint) -> RunTrajectoryResponse:
    snapshot = checkpoint.snapshot or {}
    tracks = []
    updated_utc = _checkpoint_updated_utc(checkpoint)
    for item in snapshot.get("aircraft", []):
        tracks.append(
            {
                "id": item["id"],
                "route_id": item["route_id"],
                "position_dd": item["position_dd"],
                "status": item["status"],
                "updated_utc": item.get("updated_utc") or updated_utc,
                "callsign": item.get("callsign"),
                "speed_kt": item.get("speed_kt"),
                "flight_level": item.get("flight_level"),
                "altitude_ft": item.get("altitude_ft"),
                "vertical_rate_fpm": item.get("vertical_rate_fpm"),
            }
        )
    return RunTrajectoryResponse(
        run_id=run_id,
        runtime_status=checkpoint.runtime_status,
        updated_utc=updated_utc,
        tracks=tracks,
    )


def _build_run_trajectory(
    run_id: str,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    session_id: str,
) -> RunTrajectoryResponse:
    _get_run_or_404(run_id, db, session_id)
    runtime_session = session_registry.get(run_id)
    if runtime_session is not None:
        snapshot = runtime_session.trajectory_snapshot()
        return RunTrajectoryResponse(
            run_id=run_id,
            runtime_status=snapshot["runtime_status"],
            updated_utc=snapshot["updated_utc"],
            tracks=snapshot["tracks"],
        )

    checkpoint = RunCheckpointRepository(db).latest_for_run(run_id)
    if checkpoint is not None:
        return _build_checkpoint_trajectory(run_id, checkpoint)

    return RunTrajectoryResponse(
        run_id=run_id,
        runtime_status="inactive",
        updated_utc=None,
        tracks=[],
    )


def _build_run_state(
    run,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
) -> RunStateResponse:
    runtime_session = session_registry.get(run.id)
    if runtime_session is not None:
        snapshot = runtime_session.state_snapshot()
        return RunStateResponse(
            run=RunResponse.model_validate(run),
            runtime_status=snapshot["runtime_status"],
            sim_rate=float(snapshot["sim_rate"]),
            updated_utc=snapshot["updated_utc"],
            source="runtime_session",
            last_error=snapshot["last_error"],
            time_seconds=snapshot.get("time_seconds"),
            aircraft=snapshot["aircraft"],
            separation=snapshot.get("separation"),
            summary=snapshot.get("summary"),
            metrics=snapshot["metrics"],
        )

    checkpoint = RunCheckpointRepository(db).latest_for_run(run.id)
    if checkpoint is not None:
        return _build_checkpoint_state(run, checkpoint)

    return _build_inactive_state(run)


def _build_state_event(
    run,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
) -> dict:
    state = _build_run_state(run, db, session_registry)
    return {
        "type": "run_state.snapshot",
        "run_id": run.id,
        "data": state.model_dump(mode="json"),
    }


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RunResponse)
def create_run_route(
    payload: RunCreateRequest,
    db: DbSessionDependency,
    session_id: SessionIdDependency,
    _rate_limit: RunCreationRateLimitDependency = None,
) -> RunResponse:
    """Create and persist a run shell."""

    run = create_run(
        db, session_id=session_id, scenario_id=payload.scenario_id, name=payload.name
    )
    return RunResponse.model_validate(run)


@router.post("/practice", status_code=status.HTTP_201_CREATED, response_model=RunResponse)
def create_practice_run_route(
    payload: PracticeRunCreateRequest,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    session_id: SessionIdDependency,
    settings: SettingsDependency,
    _rate_limit: RunCreationRateLimitDependency = None,
) -> RunResponse:
    """Create and start a live practice run from an airspace package."""

    _stop_previous_lesson_practice_runs(
        db,
        session_registry,
        session_id=session_id,
        airspace_id=payload.airspace_id,
        lesson_id=payload.lesson_id,
    )
    _enforce_run_capacity(db, session_registry, session_id, settings)
    run = create_practice_run(
        db,
        session_id=session_id,
        airspace_id=payload.airspace_id,
        scenario_id=payload.scenario_id,
        lesson_id=payload.lesson_id,
        name=payload.name,
    )
    run = start_run_service(db, run)
    try:
        session_registry.start(run=run, scenario=run.scenario)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return RunResponse.model_validate(run)


@router.get("", response_model=RunListResponse)
def list_runs(db: DbSessionDependency, session_id: SessionIdDependency) -> RunListResponse:
    """List durable runs from SQLite."""

    items = RunRepository(db).list(session_id=session_id)
    return RunListResponse(items=[RunResponse.model_validate(item) for item in items])


@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: str, db: DbSessionDependency, session_id: SessionIdDependency) -> RunResponse:
    """Fetch a persisted run by id."""

    return RunResponse.model_validate(_get_run_or_404(run_id, db, session_id))


@router.post("/{run_id}/start", response_model=RunResponse)
def start_run(
    run_id: str,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    session_id: SessionIdDependency,
    settings: SettingsDependency,
) -> RunResponse:
    """Transition a draft run into running state."""

    run = _get_run_or_404(run_id, db, session_id)
    _enforce_run_capacity(db, session_registry, session_id, settings)
    run = start_run_service(db, run)
    try:
        session_registry.start(run=run, scenario=run.scenario)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return RunResponse.model_validate(run)


@router.post("/{run_id}/pause", response_model=RunResponse)
def pause_run(
    run_id: str,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    session_id: SessionIdDependency,
) -> RunResponse:
    """Transition a running run into paused state."""

    run = _get_run_or_404(run_id, db, session_id)
    try:
        runtime_session = session_registry.pause(run_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    if runtime_session is None:
        checkpoint = RunCheckpointRepository(db).latest_for_run(run_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=missing_runtime_detail(
                run,
                has_checkpoint=checkpoint is not None,
            ),
        )
    run = pause_run_service(db, run)
    return RunResponse.model_validate(run)


@router.post("/{run_id}/resume", response_model=RunResponse)
def resume_run(
    run_id: str,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    session_id: SessionIdDependency,
) -> RunResponse:
    """Resume a paused run."""

    run = _get_run_or_404(run_id, db, session_id)
    try:
        runtime_session = session_registry.resume(run_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    if runtime_session is None:
        checkpoint = RunCheckpointRepository(db).latest_for_run(run_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=missing_runtime_detail(
                run,
                has_checkpoint=checkpoint is not None,
            ),
        )
    run = resume_run_service(db, run)
    return RunResponse.model_validate(run)


@router.post("/{run_id}/stop", response_model=RunResponse)
def stop_run(
    run_id: str,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    session_id: SessionIdDependency,
) -> RunResponse:
    """Stop a draft, running, or paused run."""

    session_registry.stop(run_id)
    run = stop_run_service(db, _get_run_or_404(run_id, db, session_id))
    return RunResponse.model_validate(run)


@router.get("/{run_id}/state", response_model=RunStateResponse)
def get_run_state(
    run_id: str,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    session_id: SessionIdDependency,
) -> RunStateResponse:
    """Return the current live state or the latest checkpointed state."""

    run = _get_run_or_404(run_id, db, session_id)
    return _build_run_state(run, db, session_registry)


@router.get("/{run_id}/trajectory", response_model=RunTrajectoryResponse)
def get_run_trajectory(
    run_id: str,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    session_id: SessionIdDependency,
) -> RunTrajectoryResponse:
    """Return live trajectory tracks or the latest checkpointed tracks."""

    return _build_run_trajectory(run_id, db, session_registry, session_id)


@router.websocket("/{run_id}/stream")
async def stream_run(
    websocket: WebSocket,
    run_id: str,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    broadcast_hub: BroadcastHubDependency,
    session_id: SessionIdDependency,
) -> None:
    """Stream run state and command events for one run."""

    run = RunRepository(db).get(run_id, session_id=session_id)
    if run is None:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    subscriber = broadcast_hub.subscribe(run_id)
    try:
        await websocket.send_json(_build_state_event(run, db, session_registry))
        while True:
            try:
                event = subscriber.queue.get_nowait()
            except Empty:
                await asyncio.sleep(0.05)
                continue
            await websocket.send_json(event)
    except WebSocketDisconnect:
        return
    finally:
        broadcast_hub.unsubscribe(subscriber)


@router.get(
    "/{run_id}/export.csv",
)
def export_run_csv(
    run_id: str,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    session_id: SessionIdDependency,
) -> Response:
    """Export the latest run trajectory snapshot as CSV."""

    trajectory = _build_run_trajectory(run_id, db, session_registry, session_id)
    payload = build_envelope(
        "airspacesim.trajectory",
        source="airspacesim-api",
        data={
            "tracks": [
                track.model_dump(mode="json")
                for track in trajectory.tracks
            ]
        },
        generated_utc=trajectory.updated_utc,
        schema_version="0.1",
    )
    csv_text = serialize_trajectory_payload_to_csv(payload)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="run-{run_id}-trajectory.csv"'
            )
        },
    )
