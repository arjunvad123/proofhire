"""Organization routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.ids import generate_id
from app.db.session import get_db
from app.db.models import Org, Membership, MembershipRole, Role, RoleStatus
from app.deps import CurrentUser

router = APIRouter()


class CreateOrgRequest(BaseModel):
    """Create organization request."""

    name: str


class OrgResponse(BaseModel):
    """Organization response model."""

    id: str
    name: str
    created_at: str

    class Config:
        from_attributes = True


class OrgWithRoleResponse(OrgResponse):
    """Organization with user's role."""

    role: str


@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_org(
    request: CreateOrgRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrgResponse:
    """Create a new organization and make current user the owner."""
    # Create org
    org = Org(
        id=generate_id(),
        name=request.name,
    )
    db.add(org)
    await db.flush()

    # Create owner membership
    membership = Membership(
        id=generate_id(),
        org_id=org.id,
        user_id=current_user.id,
        role=MembershipRole.OWNER,
    )
    db.add(membership)

    return OrgResponse(
        id=org.id,
        name=org.name,
        created_at=org.created_at.isoformat(),
    )


@router.get("", response_model=list[OrgWithRoleResponse])
async def list_orgs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[OrgWithRoleResponse]:
    """List all organizations the current user belongs to."""
    result = await db.execute(
        select(Org, Membership.role)
        .join(Membership, Org.id == Membership.org_id)
        .where(Membership.user_id == current_user.id)
    )
    rows = result.all()

    return [
        OrgWithRoleResponse(
            id=org.id,
            name=org.name,
            created_at=org.created_at.isoformat(),
            role=role.value,
        )
        for org, role in rows
    ]


@router.get("/{org_id}", response_model=OrgResponse)
async def get_org(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrgResponse:
    """Get organization details."""
    # Check membership
    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    # Get org
    result = await db.execute(select(Org).where(Org.id == org_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return OrgResponse(
        id=org.id,
        name=org.name,
        created_at=org.created_at.isoformat(),
    )


# Role endpoints under /orgs/{org_id}/roles

class CreateRoleRequest(BaseModel):
    """Simple role creation request."""

    title: str
    interview_answers: dict[str, Any] | None = None


class RoleListResponse(BaseModel):
    """Role response model."""

    id: str
    org_id: str
    title: str
    status: str
    com: dict[str, Any]
    rubric: dict[str, Any]
    simulation_ids: list[str]
    created_at: str

    class Config:
        from_attributes = True


@router.post("/{org_id}/roles", response_model=RoleListResponse, status_code=status.HTTP_201_CREATED)
async def create_org_role(
    org_id: str,
    request: CreateRoleRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleListResponse:
    """Create a new role for an organization."""
    # Check membership
    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    # Build COM from interview answers (simplified for MVP)
    answers = request.interview_answers or {}
    com = {
        "pace": "medium",
        "quality_bar": "medium",
        "ambiguity": "medium",
        "priorities": answers.get("priorities", []),
    }

    # Map interview answers to COM
    pace_answer = answers.get("pace", "")
    if "High" in pace_answer:
        com["pace"] = "high"
    elif "Low" in pace_answer:
        com["pace"] = "low"

    quality_answer = answers.get("quality_bar", "")
    if "High" in quality_answer:
        com["quality_bar"] = "high"
    elif "Pragmatic" in quality_answer:
        com["quality_bar"] = "low"

    ambiguity_answer = answers.get("ambiguity", "")
    if "High" in ambiguity_answer:
        com["ambiguity"] = "high"
    elif "Low" in ambiguity_answer:
        com["ambiguity"] = "low"

    # Build rubric from COM (simplified)
    rubric = {
        "dimensions": {
            "correctness": {"weight": 0.3, "threshold": 0.7},
            "testing": {"weight": 0.25, "threshold": 0.6},
            "code_quality": {"weight": 0.25, "threshold": 0.6},
            "communication": {"weight": 0.2, "threshold": 0.5},
        },
        "passing_threshold": 0.65,
    }

    # Adjust weights based on COM
    if com["quality_bar"] == "high":
        rubric["dimensions"]["correctness"]["weight"] = 0.35
        rubric["dimensions"]["testing"]["weight"] = 0.3
    elif com["quality_bar"] == "low":
        rubric["dimensions"]["correctness"]["weight"] = 0.25
        rubric["passing_threshold"] = 0.55

    # Create role
    role = Role(
        id=generate_id(),
        org_id=org_id,
        title=request.title,
        com_json=com,
        rubric_json=rubric,
        evaluation_pack_json={"simulation_ids": ["bugfix_v1"]},
        status=RoleStatus.ACTIVE,  # Auto-activate for MVP
    )
    db.add(role)
    await db.flush()

    return RoleListResponse(
        id=role.id,
        org_id=role.org_id,
        title=role.title,
        status=role.status.value,
        com=role.com_json,
        rubric=role.rubric_json,
        simulation_ids=role.evaluation_pack_json.get("simulation_ids", []),
        created_at=role.created_at.isoformat(),
    )


@router.get("/{org_id}/roles", response_model=list[RoleListResponse])
async def list_org_roles(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RoleListResponse]:
    """List all roles for an organization."""
    # Check membership
    result = await db.execute(
        select(Membership)
        .where(Membership.org_id == org_id, Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    # Get roles
    result = await db.execute(
        select(Role).where(Role.org_id == org_id).order_by(Role.created_at.desc())
    )
    roles = result.scalars().all()

    return [
        RoleListResponse(
            id=role.id,
            org_id=role.org_id,
            title=role.title,
            status=role.status.value,
            com=role.com_json,
            rubric=role.rubric_json,
            simulation_ids=role.evaluation_pack_json.get("simulation_ids", []),
            created_at=role.created_at.isoformat(),
        )
        for role in roles
    ]
