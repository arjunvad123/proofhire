"""Company Operating Model type definitions."""

from typing import Literal
from pydantic import BaseModel


class CompanyOperatingModel(BaseModel):
    """Company Operating Model (COM) structure.

    Captures the operating context that influences evaluation priorities.
    """

    stage: Literal["pre-seed", "seed", "series-a", "growth"] = "seed"
    pace: Literal["high", "medium", "low"] = "high"
    quality_bar: Literal["high", "medium", "low"] = "high"
    ambiguity: Literal["high", "medium", "low"] = "high"
    on_call: bool = True
    stack: list[str] = ["python", "fastapi", "postgres"]
    priorities: list[str] = ["ship_v1"]
    risk_intolerance: list[str] = ["data_loss", "security"]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump()
