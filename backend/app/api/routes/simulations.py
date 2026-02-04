"""Simulation catalog routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.company_model.presets import SIMULATIONS

router = APIRouter()


@router.get("", response_model=list[dict[str, Any]])
async def list_simulations() -> list[dict[str, Any]]:
    """List all available simulations."""
    return list(SIMULATIONS.values())


@router.get("/{simulation_id}", response_model=dict[str, Any])
async def get_simulation(simulation_id: str) -> dict[str, Any]:
    """Get simulation details."""
    if simulation_id not in SIMULATIONS:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found",
        )
    return SIMULATIONS[simulation_id]
