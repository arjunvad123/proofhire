"""Rubric type definitions and building logic."""

from typing import Any, Literal
from pydantic import BaseModel


class RubricWeights(BaseModel):
    """Weights for evaluation dimensions."""

    shipping_speed: float = 0.25
    correctness: float = 0.25
    testing_discipline: float = 0.20
    debugging_method: float = 0.20
    communication: float = 0.10


class RubricThresholds(BaseModel):
    """Thresholds for pass/fail criteria."""

    must_pass_tests: bool = True
    min_coverage_delta: float = 0.0


class Rubric(BaseModel):
    """Evaluation rubric structure."""

    weights: RubricWeights = RubricWeights()
    thresholds: RubricThresholds = RubricThresholds()
    role_level: Literal["founding_backend", "senior_backend", "staff_backend"] = "founding_backend"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


def build_rubric_from_com(com: dict[str, Any]) -> dict[str, Any]:
    """Build a rubric based on the Company Operating Model.

    Adjusts weights based on company priorities and pace.
    """
    weights = RubricWeights()

    # Adjust based on pace
    pace = com.get("pace", "high")
    if pace == "high":
        weights.shipping_speed = 0.30
        weights.correctness = 0.20
    elif pace == "low":
        weights.shipping_speed = 0.15
        weights.correctness = 0.30

    # Adjust based on quality bar
    quality = com.get("quality_bar", "high")
    if quality == "high":
        weights.testing_discipline = 0.25
        weights.correctness = weights.correctness + 0.05
        # Rebalance
        weights.shipping_speed = max(0.15, weights.shipping_speed - 0.05)

    # Check for specific priorities
    priorities = com.get("priorities", [])
    if "stabilize_uptime" in priorities:
        weights.debugging_method = 0.25
        weights.shipping_speed = max(0.15, weights.shipping_speed - 0.05)

    # Normalize weights to sum to 1.0
    total = (
        weights.shipping_speed
        + weights.correctness
        + weights.testing_discipline
        + weights.debugging_method
        + weights.communication
    )
    weights.shipping_speed /= total
    weights.correctness /= total
    weights.testing_discipline /= total
    weights.debugging_method /= total
    weights.communication /= total

    thresholds = RubricThresholds(
        must_pass_tests=True,
        min_coverage_delta=0.0 if quality != "high" else 5.0,
    )

    rubric = Rubric(weights=weights, thresholds=thresholds)
    return rubric.to_dict()
