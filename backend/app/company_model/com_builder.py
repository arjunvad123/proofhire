"""Build Company Operating Model from interview answers."""

from typing import Any


def build_com_from_interview(
    ship_vs_correctness: str,
    on_call: bool,
    has_ci: bool,
    has_tests: bool,
    biggest_risk: str,
    failure_by_day_30: str,
    pace_override: str | None = None,
    quality_override: str | None = None,
    ambiguity_override: str | None = None,
) -> dict[str, Any]:
    """Build a Company Operating Model from role spec interview answers.

    Args:
        ship_vs_correctness: "ship" | "balanced" | "correctness"
        on_call: Whether engineer will be on-call in first month
        has_ci: Whether company has CI
        has_tests: Whether company has tests
        biggest_risk: Description of biggest engineering risk
        failure_by_day_30: What failure looks like
        pace_override: Optional explicit pace setting
        quality_override: Optional explicit quality bar
        ambiguity_override: Optional explicit ambiguity level

    Returns:
        COM dictionary
    """
    # Determine pace from ship_vs_correctness
    if pace_override:
        pace = pace_override
    elif ship_vs_correctness == "ship":
        pace = "high"
    elif ship_vs_correctness == "correctness":
        pace = "low"
    else:
        pace = "medium"

    # Determine quality bar
    if quality_override:
        quality_bar = quality_override
    elif has_ci and has_tests:
        quality_bar = "high"
    elif has_ci or has_tests:
        quality_bar = "medium"
    else:
        quality_bar = "low"

    # Determine ambiguity
    if ambiguity_override:
        ambiguity = ambiguity_override
    else:
        # Startups typically have high ambiguity
        ambiguity = "high"

    # Build priorities from risk and failure descriptions
    priorities = []
    risk_lower = biggest_risk.lower()
    failure_lower = failure_by_day_30.lower()

    if "ship" in risk_lower or "launch" in risk_lower or "deadline" in failure_lower:
        priorities.append("ship_v1")
    if "bug" in risk_lower or "quality" in failure_lower or "incident" in failure_lower:
        priorities.append("stabilize_uptime")
    if "scale" in risk_lower or "performance" in risk_lower:
        priorities.append("scale_infrastructure")
    if "security" in risk_lower or "data" in risk_lower:
        priorities.append("security_compliance")

    if not priorities:
        priorities = ["ship_v1"]  # Default

    # Build risk intolerance
    risk_intolerance = []
    if "data" in risk_lower or "privacy" in risk_lower:
        risk_intolerance.append("data_loss")
    if "security" in risk_lower or "auth" in risk_lower:
        risk_intolerance.append("security")
    if "downtime" in risk_lower or "availability" in risk_lower:
        risk_intolerance.append("downtime")

    if not risk_intolerance:
        risk_intolerance = ["data_loss"]  # Default

    return {
        "stage": "seed",  # Default for v1 niche
        "pace": pace,
        "quality_bar": quality_bar,
        "ambiguity": ambiguity,
        "on_call": on_call,
        "stack": ["python", "fastapi", "postgres"],  # Default for v1
        "priorities": priorities,
        "risk_intolerance": risk_intolerance,
    }
