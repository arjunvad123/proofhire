"""Simulation run routes."""

from typing import Annotated, Any
import json

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.ids import generate_id
from app.core.time import utc_now
from app.config import get_settings
from app.db.session import get_db
from app.db.models import (
    Application,
    ApplicationStatus,
    SimulationRun,
    SimulationRunStatus,
    Artifact,
    ArtifactType,
)
from app.company_model.presets import SIMULATIONS

router = APIRouter()
settings = get_settings()


class StartRunRequest(BaseModel):
    """Request to start a simulation run."""

    simulation_id: str


class SubmitRunRequest(BaseModel):
    """Request to submit a simulation run."""

    writeup: dict[str, str]  # prompt -> answer


class RunResponse(BaseModel):
    """Simulation run response."""

    id: str
    application_id: str
    simulation_id: str
    status: str
    started_at: str | None
    finished_at: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.post("/applications/{application_id}/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def start_simulation_run(
    application_id: str,
    request: StartRunRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RunResponse:
    """Start a new simulation run for an application."""
    # Verify application exists
    result = await db.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    # Verify simulation exists
    if request.simulation_id not in SIMULATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid simulation ID",
        )

    # Check for existing incomplete run
    result = await db.execute(
        select(SimulationRun)
        .where(
            SimulationRun.application_id == application_id,
            SimulationRun.simulation_id == request.simulation_id,
            SimulationRun.status.in_([SimulationRunStatus.QUEUED, SimulationRunStatus.RUNNING]),
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A run for this simulation is already in progress",
        )

    # Create run
    run = SimulationRun(
        id=generate_id(),
        application_id=application_id,
        simulation_id=request.simulation_id,
        status=SimulationRunStatus.QUEUED,
    )
    db.add(run)

    # Update application status
    application.status = ApplicationStatus.IN_SIMULATION

    await db.flush()

    # Do not enqueue here; the runner needs submission payload from /submit.

    return RunResponse(
        id=run.id,
        application_id=run.application_id,
        simulation_id=run.simulation_id,
        status=run.status.value,
        started_at=run.started_at.isoformat() if run.started_at else None,
        finished_at=run.finished_at.isoformat() if run.finished_at else None,
        created_at=run.created_at.isoformat(),
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RunResponse:
    """Get simulation run status."""
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    return RunResponse(
        id=run.id,
        application_id=run.application_id,
        simulation_id=run.simulation_id,
        status=run.status.value,
        started_at=run.started_at.isoformat() if run.started_at else None,
        finished_at=run.finished_at.isoformat() if run.finished_at else None,
        created_at=run.created_at.isoformat(),
    )


@router.get("/{run_id}/status")
async def get_run_status(
    run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get detailed run status including progress."""
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Get artifact count for progress indication
    result = await db.execute(
        select(Artifact).where(Artifact.simulation_run_id == run_id)
    )
    artifacts = result.scalars().all()

    return {
        "id": run.id,
        "status": run.status.value,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "artifact_count": len(artifacts),
        "runner_metadata": run.runner_metadata_json,
    }


@router.post("/{run_id}/submit")
async def submit_run(
    run_id: str,
    code: UploadFile = File(...),
    writeup: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Submit code and writeup for a simulation run."""
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if run.status not in [SimulationRunStatus.QUEUED, SimulationRunStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run is not accepting submissions",
        )

    # Parse writeup JSON
    try:
        writeup_data = json.loads(writeup)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid writeup JSON",
        )

    # Read code file
    code_content = await code.read()

    # Store submission (in production, upload to S3)
    from app.core.hashing import hash_data

    # Store code artifact
    code_artifact = Artifact(
        id=generate_id(),
        simulation_run_id=run_id,
        type=ArtifactType.SOURCE_BUNDLE,
        s3_key=f"runs/{run_id}/submission.tar.gz",  # Would be uploaded to S3
        sha256=hash_data(code_content),
        metadata_json={"filename": code.filename, "size": len(code_content)},
    )
    db.add(code_artifact)

    # Store writeup artifact
    writeup_bytes = json.dumps(writeup_data).encode()
    writeup_artifact = Artifact(
        id=generate_id(),
        simulation_run_id=run_id,
        type=ArtifactType.WRITEUP,
        s3_key=f"runs/{run_id}/writeup.json",
        sha256=hash_data(writeup_bytes),
        metadata_json={"prompts": list(writeup_data.keys())},
    )
    db.add(writeup_artifact)

    # Update run status
    run.status = SimulationRunStatus.RUNNING
    run.started_at = utc_now()

    # Trigger grading job with the submission payload the runner can execute.
    try:
        r = redis.from_url(settings.redis_url)
        candidate_code = code_content.decode("utf-8", errors="ignore")
        candidate_writeup = (
            writeup_data.get("content")
            if isinstance(writeup_data, dict) and isinstance(writeup_data.get("content"), str)
            else json.dumps(writeup_data)
        )
        job = {
            "type": "simulation",
            "run_id": run_id,
            "simulation_id": run.simulation_id,
            "application_id": run.application_id,
            "candidate_code": candidate_code,
            "candidate_writeup": candidate_writeup,
        }
        await r.lpush("proofhire:jobs", json.dumps(job))
        await r.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to enqueue job for run {run_id}: {e}")

    return {"status": "submitted", "run_id": run_id}


@router.get("/{run_id}/artifacts")
async def get_run_artifacts(
    run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict[str, Any]]:
    """Get artifacts for a simulation run (candidate-limited view)."""
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    result = await db.execute(
        select(Artifact).where(Artifact.simulation_run_id == run_id)
    )
    artifacts = result.scalars().all()

    # Candidate can only see certain artifact types
    allowed_types = {ArtifactType.TEST_LOG, ArtifactType.COVERAGE}

    return [
        {
            "id": a.id,
            "type": a.type.value,
            "created_at": a.created_at.isoformat(),
        }
        for a in artifacts
        if a.type in allowed_types
    ]
