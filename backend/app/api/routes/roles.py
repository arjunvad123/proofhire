"""Role routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import generate_id
from app.db.session import get_db
from app.db.models import Role, RoleStatus, Membership, Application
from app.deps import CurrentUser
from app.company_model.com_builder import build_com_from_interview
from app.company_model.rubric import build_rubric_from_com
from app.company_model.presets import get_evaluation_pack

router = APIRouter()


class RoleInterviewRequest(BaseModel):
    """Role spec interview answers."""

    org_id: str
    title: str
    description: str | None = None
    # Interview questions
    ship_vs_correctness: str  # "ship" | "balanced" | "correctness"
    on_call_first_month: bool
    has_ci: bool
    has_tests: bool
    biggest_risk: str
    failure_by_day_30: str
    # Optional overrides
    pace: str | None = None  # "high" | "medium" | "low"
    quality_bar: str | None = None
    ambiguity: str | None = None


class UpdateRubricRequest(BaseModel):
    """Update role rubric."""

    rubric_json: dict[str, Any] | None = None
    evaluation_pack_json: dict[str, Any] | None = None


class RoleResponse(BaseModel):
    """Role response model."""

    id: str
    org_id: str
    title: str
    description: str | None
    com_json: dict[str, Any]
    rubric_json: dict[str, Any]
    evaluation_pack_json: dict[str, Any]
    status: str
    created_at: str
    application_link: str | None = None

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """Role list item."""

    id: str
    title: str
    status: str
    application_count: int


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: RoleInterviewRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleResponse:
    """Create a new role from interview answers."""
    # Check membership
    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == request.org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    # Build COM from interview
    com = build_com_from_interview(
        ship_vs_correctness=request.ship_vs_correctness,
        on_call=request.on_call_first_month,
        has_ci=request.has_ci,
        has_tests=request.has_tests,
        biggest_risk=request.biggest_risk,
        failure_by_day_30=request.failure_by_day_30,
        pace_override=request.pace,
        quality_override=request.quality_bar,
        ambiguity_override=request.ambiguity,
    )

    # Build rubric from COM
    rubric = build_rubric_from_com(com)

    # Get evaluation pack
    eval_pack = get_evaluation_pack(role_level="founding_backend")

    # Create role
    role = Role(
        id=generate_id(),
        org_id=request.org_id,
        title=request.title,
        description=request.description,
        com_json=com,
        rubric_json=rubric,
        evaluation_pack_json=eval_pack,
        status=RoleStatus.DRAFT,
    )
    db.add(role)
    await db.flush()

    return RoleResponse(
        id=role.id,
        org_id=role.org_id,
        title=role.title,
        description=role.description,
        com_json=role.com_json,
        rubric_json=role.rubric_json,
        evaluation_pack_json=role.evaluation_pack_json,
        status=role.status.value,
        created_at=role.created_at.isoformat(),
    )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleResponse:
    """Get role details."""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Check membership
    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == role.org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    application_link = f"/apply/{role.id}" if role.status == RoleStatus.ACTIVE else None

    return RoleResponse(
        id=role.id,
        org_id=role.org_id,
        title=role.title,
        description=role.description,
        com_json=role.com_json,
        rubric_json=role.rubric_json,
        evaluation_pack_json=role.evaluation_pack_json,
        status=role.status.value,
        created_at=role.created_at.isoformat(),
        application_link=application_link,
    )


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    request: UpdateRubricRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleResponse:
    """Update role rubric or evaluation pack."""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Check membership
    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == role.org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    # Update fields
    if request.rubric_json is not None:
        role.rubric_json = request.rubric_json
    if request.evaluation_pack_json is not None:
        role.evaluation_pack_json = request.evaluation_pack_json

    return RoleResponse(
        id=role.id,
        org_id=role.org_id,
        title=role.title,
        description=role.description,
        com_json=role.com_json,
        rubric_json=role.rubric_json,
        evaluation_pack_json=role.evaluation_pack_json,
        status=role.status.value,
        created_at=role.created_at.isoformat(),
    )


@router.post("/{role_id}/activate", response_model=RoleResponse)
async def activate_role(
    role_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleResponse:
    """Activate a role for accepting applications."""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Check membership
    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == role.org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    role.status = RoleStatus.ACTIVE

    return RoleResponse(
        id=role.id,
        org_id=role.org_id,
        title=role.title,
        description=role.description,
        com_json=role.com_json,
        rubric_json=role.rubric_json,
        evaluation_pack_json=role.evaluation_pack_json,
        status=role.status.value,
        created_at=role.created_at.isoformat(),
        application_link=f"/apply/{role.id}",
    )


@router.get("/{role_id}/applications", response_model=list[dict])
async def list_role_applications(
    role_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """List all applications for a role."""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Check membership
    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == role.org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    # Get applications with candidate info
    from app.db.models import Candidate
    result = await db.execute(
        select(Application, Candidate)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .where(Application.role_id == role_id)
        .order_by(Application.created_at.desc())
    )
    rows = result.all()

    return [
        {
            "id": app.id,
            "candidate_name": candidate.name,
            "candidate_email": candidate.email,
            "status": app.status.value,
            "created_at": app.created_at.isoformat(),
        }
        for app, candidate in rows
    ]
