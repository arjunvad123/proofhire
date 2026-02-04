"""Candidate routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import generate_id
from app.db.session import get_db
from app.db.models import Candidate

router = APIRouter()


class CandidateResponse(BaseModel):
    """Candidate response model."""

    id: str
    email: str
    name: str
    github_url: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CandidateResponse:
    """Get candidate by ID."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    return CandidateResponse(
        id=candidate.id,
        email=candidate.email,
        name=candidate.name,
        github_url=candidate.github_url,
        created_at=candidate.created_at.isoformat(),
    )
