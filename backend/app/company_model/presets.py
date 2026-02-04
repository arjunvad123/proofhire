"""Evaluation pack presets for different role types."""

from typing import Any


# Simulation configurations
SIMULATIONS = {
    "bugfix_v1": {
        "id": "bugfix_v1",
        "name": "Bug Fix Simulation",
        "description": "Diagnose and fix a bug, add regression test, explain root cause",
        "duration_minutes": 60,
        "skills_assessed": ["debugging", "testing", "communication"],
    },
    "feature_migration_v1": {
        "id": "feature_migration_v1",
        "name": "Feature + Migration Simulation",
        "description": "Add endpoint, schema migration, handle edge cases, provide rollback notes",
        "duration_minutes": 90,
        "skills_assessed": ["feature_development", "database", "system_design", "communication"],
    },
}


def get_evaluation_pack(
    role_level: str = "founding_backend",
    custom_simulations: list[str] | None = None,
) -> dict[str, Any]:
    """Get the evaluation pack (enabled simulations) for a role level.

    Args:
        role_level: The role level (founding_backend, senior_backend, etc.)
        custom_simulations: Optional list of specific simulation IDs to include

    Returns:
        Evaluation pack configuration
    """
    if custom_simulations:
        enabled_sims = [
            SIMULATIONS[sim_id]
            for sim_id in custom_simulations
            if sim_id in SIMULATIONS
        ]
    else:
        # Default simulations by role level
        if role_level == "founding_backend":
            enabled_sims = [SIMULATIONS["bugfix_v1"]]
        elif role_level == "senior_backend":
            enabled_sims = [SIMULATIONS["bugfix_v1"], SIMULATIONS["feature_migration_v1"]]
        else:
            enabled_sims = [SIMULATIONS["bugfix_v1"]]

    return {
        "role_level": role_level,
        "simulations": enabled_sims,
        "total_duration_minutes": sum(s["duration_minutes"] for s in enabled_sims),
        "writeup_prompts": [
            "What was the root cause of the bug?",
            "What tradeoffs did you consider?",
            "How would you monitor this in production?",
        ],
    }
