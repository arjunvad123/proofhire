"""Application routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import generate_id
from app.db.session import get_db
from app.db.models import (
    Application,
    ApplicationStatus,
    Candidate,
    Role,
    RoleStatus,
    SimulationRun,
    Membership,
)
from app.deps import CurrentUser

router = APIRouter()


class ApplyRequest(BaseModel):
    """Application request from candidate."""

    email: EmailStr
    name: str
    github_url: str | None = None
    consent: bool  # Must be True


class PrescreenRequest(BaseModel):
    """Prescreen data for an application."""

    answers: dict[str, Any]


class ApplicationResponse(BaseModel):
    """Application response model."""

    id: str
    role_id: str
    candidate_id: str
    status: str
    created_at: str

    class Config:
        from_attributes = True


class ApplicationDetailResponse(ApplicationResponse):
    """Detailed application response with simulations."""

    simulations: list[dict[str, Any]]
    prescreen_json: dict[str, Any] | None


# Public endpoint - candidate applies
@router.post("/roles/{role_id}/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_role(
    role_id: str,
    request: ApplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApplicationResponse:
    """Apply to a role as a candidate."""
    # Verify consent
    if not request.consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent is required to apply",
        )

    # Get role
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    if role.status != RoleStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role is not accepting applications",
        )

    # Find or create candidate
    result = await db.execute(select(Candidate).where(Candidate.email == request.email))
    candidate = result.scalar_one_or_none()

    if not candidate:
        candidate = Candidate(
            id=generate_id(),
            email=request.email,
            name=request.name,
            github_url=request.github_url,
        )
        db.add(candidate)
        await db.flush()

    # Check for existing application
    result = await db.execute(
        select(Application)
        .where(Application.role_id == role_id, Application.candidate_id == candidate.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already applied to this role",
        )

    # Create application
    application = Application(
        id=generate_id(),
        role_id=role_id,
        candidate_id=candidate.id,
        status=ApplicationStatus.APPLIED,
        consent_version="v1.0",
    )
    db.add(application)
    await db.flush()

    return ApplicationResponse(
        id=application.id,
        role_id=application.role_id,
        candidate_id=application.candidate_id,
        status=application.status.value,
        created_at=application.created_at.isoformat(),
    )


@router.get("/{application_id}", response_model=ApplicationDetailResponse)
async def get_application(
    application_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApplicationDetailResponse:
    """Get application details (candidate view - limited info)."""
    result = await db.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    # Get role for simulation info
    result = await db.execute(select(Role).where(Role.id == application.role_id))
    role = result.scalar_one_or_none()

    simulations = role.evaluation_pack_json.get("simulations", []) if role else []

    # Get simulation runs
    result = await db.execute(
        select(SimulationRun).where(SimulationRun.application_id == application_id)
    )
    runs = result.scalars().all()

    # Mark which simulations are completed
    completed_sims = {run.simulation_id for run in runs if run.status.value == "succeeded"}
    for sim in simulations:
        sim["completed"] = sim["id"] in completed_sims

    return ApplicationDetailResponse(
        id=application.id,
        role_id=application.role_id,
        candidate_id=application.candidate_id,
        status=application.status.value,
        created_at=application.created_at.isoformat(),
        simulations=simulations,
        prescreen_json=application.prescreen_json,
    )


@router.post("/{application_id}/prescreen", response_model=ApplicationResponse)
async def submit_prescreen(
    application_id: str,
    request: PrescreenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApplicationResponse:
    """Submit prescreen answers."""
    result = await db.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    application.prescreen_json = request.answers
    application.status = ApplicationStatus.PRESCREENED

    return ApplicationResponse(
        id=application.id,
        role_id=application.role_id,
        candidate_id=application.candidate_id,
        status=application.status.value,
        created_at=application.created_at.isoformat(),
    )


@router.get("/{application_id}/brief")
async def get_application_brief(
    application_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get the proof brief for an application (founder only)."""
    result = await db.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    # Get role and verify membership
    result = await db.execute(select(Role).where(Role.id == application.role_id))
    role = result.scalar_one_or_none()

    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == role.org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this brief",
        )

    # Get latest brief
    from app.db.models import Brief
    result = await db.execute(
        select(Brief)
        .where(Brief.application_id == application_id)
        .order_by(Brief.version.desc())
        .limit(1)
    )
    brief = result.scalar_one_or_none()

    if not brief:
        return {
            "application_id": application_id,
            "status": "pending",
            "message": "Brief not yet generated - candidate may still be completing simulations",
        }

    return brief.brief_json
