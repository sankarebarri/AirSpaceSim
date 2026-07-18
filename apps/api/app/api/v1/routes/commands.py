"""Operator command routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from ....db.repositories import (
    RunCheckpointRepository,
    RunCommandRepository,
    RunRepository,
)
from ....dependencies import (
    BroadcastHubDependency,
    DbSessionDependency,
    OptionalUserDependency,
    SessionIdDependency,
    SessionRegistryDependency,
)
from ....schemas.commands import (
    CommandResultItem,
    RunCommandCreateRequest,
    RunCommandResponse,
    RunCommandResultResponse,
    RunCommandSubmissionResponse,
)
from ....services import missing_runtime_detail, record_run_command

router = APIRouter(prefix="/runs/{run_id}/commands", tags=["commands"])


def _build_command_result_payload(
    result: dict,
    *,
    default_state: str,
) -> RunCommandResultResponse:
    applied = list(result.get("applied", []))
    skipped = [
        CommandResultItem(command_id=item[0], reason=item[1])
        for item in result.get("skipped", [])
    ]
    rejected = [
        CommandResultItem(command_id=item[0], reason=item[1])
        for item in result.get("rejected", [])
    ]

    if rejected:
        state = "rejected"
    elif skipped:
        state = "skipped"
    elif applied:
        state = "applied"
    else:
        state = default_state
    return RunCommandResultResponse(
        state=state,
        applied=applied,
        skipped=skipped,
        rejected=rejected,
    )


def _reject_command(
    *,
    command,
    db: DbSessionDependency,
    reason: str,
) -> RunCommandSubmissionResponse:
    command.status = "rejected"
    command = RunCommandRepository(db).update(command)
    return RunCommandSubmissionResponse(
        command=RunCommandResponse.model_validate(command),
        result=RunCommandResultResponse(
            state="rejected",
            rejected=[CommandResultItem(command_id=command.id, reason=reason)],
        ),
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RunCommandSubmissionResponse,
)
def submit_command(
    run_id: str,
    payload: RunCommandCreateRequest,
    db: DbSessionDependency,
    session_registry: SessionRegistryDependency,
    broadcast_hub: BroadcastHubDependency,
    session_id: SessionIdDependency,
    user: OptionalUserDependency = None,
) -> RunCommandSubmissionResponse:
    """Persist an operator command against an existing run."""

    run = RunRepository(db).get(
        run_id, session_id=session_id, user_id=user.id if user else None
    )
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run not found: {run_id}",
        )
    command = record_run_command(
        db,
        run=run,
        command_type=payload.command_type,
        payload=payload.payload,
    )
    runtime_session = session_registry.get(run_id)
    checkpoint = RunCheckpointRepository(db).latest_for_run(run_id)
    if runtime_session is None and run.status != "draft":
        response_payload = _reject_command(
            command=command,
            db=db,
            reason=missing_runtime_detail(
                run,
                has_checkpoint=checkpoint is not None,
            ),
        )
        broadcast_hub.publish_command_result(
            run_id,
            {
                "command": response_payload.command.model_dump(mode="json"),
                "result": response_payload.result.model_dump(mode="json"),
            },
        )
        return response_payload

    result_payload = RunCommandResultResponse(state="queued")
    if runtime_session is not None:
        result = runtime_session.apply_command(
            command_id=command.id,
            command_type=payload.command_type,
            payload=payload.payload,
        )
        result_payload = _build_command_result_payload(result, default_state="queued")
        if result["applied"]:
            command.status = "applied"
            command.applied_at = datetime.now(timezone.utc)
            if payload.command_type == "SET_SIMULATION_SPEED":
                run.sim_rate = runtime_session.sim_rate
                RunRepository(db).update(run)
        elif result["rejected"]:
            command.status = "rejected"
        elif result["skipped"]:
            command.status = "skipped"
        command = RunCommandRepository(db).update(command)
    response_payload = RunCommandSubmissionResponse(
        command=RunCommandResponse.model_validate(command),
        result=result_payload,
    )
    broadcast_hub.publish_command_result(
        run_id,
        {
            "command": response_payload.command.model_dump(mode="json"),
            "result": response_payload.result.model_dump(mode="json"),
        },
    )
    return response_payload
