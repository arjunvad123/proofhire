"""Organization routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.ids import generate_id
from app.db.session import get_db
from app.db.models import Org, Membership, MembershipRole
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
