"""Brief routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Brief, Application, Role, Membership
from app.deps import CurrentUser

router = APIRouter()


@router.get("/{brief_id}")
async def get_brief(
    brief_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get a brief by ID (founder only)."""
    result = await db.execute(select(Brief).where(Brief.id == brief_id))
    brief = result.scalar_one_or_none()

    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brief not found",
        )

    # Get application and role to verify access
    result = await db.execute(select(Application).where(Application.id == brief.application_id))
    application = result.scalar_one_or_none()

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

    return {
        "id": brief.id,
        "application_id": brief.application_id,
        "version": brief.version,
        "created_at": brief.created_at.isoformat(),
        "brief": brief.brief_json,
    }
