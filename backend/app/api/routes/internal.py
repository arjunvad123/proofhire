"""Internal API routes for runner callbacks.

These endpoints are called by the runner service to notify the backend
of job completion. They are protected by an internal API key.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Header, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.db.models import SimulationRun, SimulationRunStatus
from app.core.time import utc_now

router = APIRouter()
settings = get_settings()


class RunCompleteRequest(BaseModel):
    """Request body from runner when a simulation run completes."""

    success: bool
    metrics: dict[str, Any] = {}
    artifact_urls: dict[str, str] = {}
    duration_seconds: float = 0.0


class RunCompleteResponse(BaseModel):
    """Response to runner after processing completion."""

    status: str
    message: str


def verify_internal_key(x_internal_key: str = Header(...)) -> str:
    """Verify the internal API key from the runner."""
    if x_internal_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )
    return x_internal_key


@router.post(
    "/runs/{run_id}/complete",
    response_model=RunCompleteResponse,
    dependencies=[Depends(verify_internal_key)],
)
async def run_complete(
    run_id: str,
    request: RunCompleteRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RunCompleteResponse:
    """
    Handle simulation run completion from runner.

    This endpoint:
    1. Updates the run status to SUCCEEDED or FAILED
    2. Stores artifact URLs and metrics
    3. Triggers the orchestration pipeline in the background
    """
    # Find the run
    result = await db.execute(
        select(SimulationRun).where(SimulationRun.id == run_id)
    )
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Update run status
    run.status = SimulationRunStatus.SUCCEEDED if request.success else SimulationRunStatus.FAILED
    run.finished_at = utc_now()
    run.runner_metadata_json = {
        "duration_seconds": request.duration_seconds,
        "artifact_urls": request.artifact_urls,
        "metrics": request.metrics,
    }

    await db.commit()

    # Trigger orchestration in background
    # Import here to avoid circular imports
    from app.services.orchestrator import process_completed_run

    background_tasks.add_task(
        process_completed_run,
        run_id=run_id,
        metrics=request.metrics,
        artifact_urls=request.artifact_urls,
    )

    return RunCompleteResponse(
        status="accepted",
        message=f"Run {run_id} marked as {'succeeded' if request.success else 'failed'}. Processing in background.",
    )
