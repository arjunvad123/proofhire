"""Hypothesis/claim generator.

Generates candidate claims based on available evidence that can then
be verified by the proof engine.
"""

from typing import Any

from app.hypothesis.claim_schema import Claim, ClaimSubject, CLAIM_TYPES
from app.db.models import Metric, Artifact, ArtifactType


def generate_claims(
    application_id: str,
    candidate_id: str,
    simulation_run_id: str,
    metrics: list[Metric],
    artifacts: list[Artifact],
    com: dict[str, Any],
) -> list[Claim]:
    """Generate candidate claims based on available evidence.

    This is the hypothesis generator - it proposes claims that the
    proof engine will then attempt to verify.

    Args:
        application_id: The application ID
        candidate_id: The candidate ID
        simulation_run_id: The simulation run ID
        metrics: List of metrics from the simulation run
        artifacts: List of artifacts from the simulation run
        com: Company Operating Model (for context)

    Returns:
        List of claims to be verified
    """
    claims = []
    subject = ClaimSubject(
        candidate_id=candidate_id,
        application_id=application_id,
        simulation_run_id=simulation_run_id,
    )

    # Convert metrics to dict for easier lookup
    metrics_dict = {}
    for m in metrics:
        if m.value_float is not None:
            metrics_dict[m.name] = m.value_float
        elif m.value_bool is not None:
            metrics_dict[m.name] = m.value_bool
        elif m.value_text is not None:
            metrics_dict[m.name] = m.value_text

    # Check artifact types available
    artifact_types = {a.type for a in artifacts}

    # Generate claims based on available evidence

    # 1. Test-related claims
    if "tests_passed" in metrics_dict:
        tests_passed = metrics_dict.get("tests_passed", False)

        if tests_passed:
            # Can claim debugging effective if tests pass
            claims.append(
                Claim(
                    claim_type="debugging_effective",
                    subject=subject,
                    statement="Candidate effectively diagnosed and fixed the bug, as evidenced by passing tests",
                    dimensions=["debugging_method"],
                    confidence=0.8 if tests_passed else 0.0,
                    evidence_requirements=["test_log", "metrics"],
                )
            )

        # Check for added tests
        test_added = metrics_dict.get("test_added", False)
        if test_added or ArtifactType.DIFF in artifact_types:
            claims.append(
                Claim(
                    claim_type="added_regression_test",
                    subject=subject,
                    statement="Candidate added a regression test for the fixed bug",
                    dimensions=["testing_discipline"],
                    confidence=0.7 if test_added else 0.5,
                    evidence_requirements=["diff", "test_log"],
                )
            )

    # 2. Testing discipline claims
    if ArtifactType.COVERAGE in artifact_types or "coverage_percent" in metrics_dict:
        claims.append(
            Claim(
                claim_type="testing_discipline",
                subject=subject,
                statement="Candidate demonstrates good testing practices",
                dimensions=["testing_discipline"],
                confidence=0.6,
                evidence_requirements=["coverage", "test_log"],
            )
        )

    # 3. Time efficiency claims
    if "time_to_green_seconds" in metrics_dict:
        # Time threshold based on COM pace
        pace = com.get("pace", "medium")
        time_threshold = {
            "high": 2400,  # 40 minutes
            "medium": 3000,  # 50 minutes
            "low": 3600,  # 60 minutes
        }.get(pace, 3000)

        claims.append(
            Claim(
                claim_type="time_efficient",
                subject=subject,
                statement="Candidate completed the task within expected time",
                dimensions=["shipping_speed"],
                confidence=0.5,
                evidence_requirements=["metrics"],
            )
        )

    # 4. Communication claims (requires writeup)
    if ArtifactType.WRITEUP in artifact_types:
        claims.append(
            Claim(
                claim_type="communication_clear",
                subject=subject,
                statement="Candidate communicates clearly and thoroughly in their writeup",
                dimensions=["communication"],
                confidence=0.5,  # Needs LLM tagging to increase confidence
                evidence_requirements=["writeup", "llm_tags"],
            )
        )

    # 5. Edge case handling (based on test coverage)
    if "failed_tests_count" in metrics_dict:
        failed = metrics_dict.get("failed_tests_count", 0)
        if failed == 0:
            claims.append(
                Claim(
                    claim_type="handles_edge_cases",
                    subject=subject,
                    statement="Candidate code handles all test cases including edge cases",
                    dimensions=["correctness"],
                    confidence=0.6,
                    evidence_requirements=["test_log"],
                )
            )

    return claims


def prioritize_claims(
    claims: list[Claim],
    rubric: dict[str, Any],
) -> list[Claim]:
    """Prioritize claims based on rubric weights.

    Higher-weighted dimensions should have their claims evaluated first.
    """
    weights = rubric.get("weights", {})

    def claim_priority(claim: Claim) -> float:
        # Sum weights of all dimensions this claim relates to
        total_weight = sum(
            weights.get(dim, 0.1)
            for dim in claim.dimensions
        )
        return total_weight * claim.confidence

    return sorted(claims, key=claim_priority, reverse=True)
