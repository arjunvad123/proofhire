"""Brief builder - assembles proven/unproven claims into candidate briefs."""

from datetime import datetime
from typing import Any

from app.briefs.brief_types import (
    ArtifactReference,
    CandidateBrief,
    ProvenClaim,
    RiskFlag,
    UnprovenClaim,
)
from app.briefs.interview_packet import generate_interview_questions
from app.db.models import Application, Artifact, Brief, Candidate, Claim, Role, SimulationRun
from app.hypothesis.claim_schema import ProofResult
from app.logging_config import get_logger

logger = get_logger(__name__)


class BriefBuilder:
    """Build candidate briefs from proof results."""

    # Dimensions we track
    ALL_DIMENSIONS = [
        "debugging_method",
        "testing_discipline",
        "correctness",
        "shipping_speed",
        "communication",
    ]

    @staticmethod
    def _get_run_duration_seconds(simulation_run: SimulationRun) -> float | None:
        """Return run duration when start/end datetimes are available."""
        started_at = getattr(simulation_run, "started_at", None)
        finished_at = getattr(simulation_run, "finished_at", None)
        if not isinstance(finished_at, datetime):
            finished_at = getattr(simulation_run, "completed_at", None)

        if isinstance(started_at, datetime) and isinstance(finished_at, datetime):
            return (finished_at - started_at).total_seconds()

        return None

    def build(
        self,
        application: Application,
        candidate: Candidate,
        role: Role,
        simulation_run: SimulationRun,
        proof_results: list[ProofResult],
        artifacts: list[Artifact],
        com: dict[str, Any],
    ) -> CandidateBrief:
        """Build a complete candidate brief.

        Args:
            application: The job application
            candidate: The candidate
            role: The role applied to
            simulation_run: The completed simulation run
            proof_results: Results from proof engine
            artifacts: Stored artifacts from the run
            com: Company Operating Model

        Returns:
            CandidateBrief ready for review
        """
        from app.core.ids import generate_id

        brief_id = generate_id()

        # Separate proven and unproven claims
        proven_claims = []
        unproven_claims = []

        for result in proof_results:
            if result.status == "PROVED":
                proven_claims.append(
                    ProvenClaim(
                        claim_type=result.claim.claim_type,
                        statement=result.claim.statement,
                        dimensions=result.claim.dimensions,
                        evidence_refs=[ref.model_dump() for ref in result.evidence_refs],
                        rule_id=result.rule_id,
                        confidence=result.claim.confidence,
                    )
                )
            else:
                # Generate interview questions for unproven claims
                questions = generate_interview_questions(
                    claim=result.claim,
                    reason=result.reason,
                    com=com,
                )
                unproven_claims.append(
                    UnprovenClaim(
                        claim_type=result.claim.claim_type,
                        statement=result.claim.statement,
                        dimension=result.claim.dimensions[0] if result.claim.dimensions else "unknown",
                        reason=result.reason,
                        suggested_questions=questions,
                    )
                )

        # Compute dimensions coverage
        dimensions_covered = self._compute_dimensions_coverage(proven_claims, unproven_claims)

        # Identify risk flags
        risk_flags = self._identify_risk_flags(proof_results, simulation_run)

        # Build artifact references
        artifact_refs = [
            ArtifactReference(
                artifact_id=str(a.id),
                artifact_type=a.type.value if hasattr(a.type, 'value') else str(a.type),
                s3_key=a.s3_key,
            )
            for a in artifacts
        ]

        # Compute timing
        time_to_complete = self._get_run_duration_seconds(simulation_run) or 0.0

        # Gather all suggested questions
        all_questions = []
        for claim in unproven_claims:
            all_questions.extend(claim.suggested_questions)

        total_claims = len(proof_results)
        proven_count = len(proven_claims)
        unproven_count = len(unproven_claims)
        proof_rate = proven_count / total_claims if total_claims > 0 else 0.0

        logger.info(
            "Brief built",
            brief_id=brief_id,
            application_id=str(application.id),
            proven_count=proven_count,
            unproven_count=unproven_count,
            proof_rate=round(proof_rate, 2),
        )

        return CandidateBrief(
            brief_id=brief_id,
            application_id=str(application.id),
            candidate_id=str(candidate.id),
            role_id=str(role.id),
            org_id=str(role.org_id),
            candidate_name=candidate.name,
            simulation_id=simulation_run.simulation_id,
            simulation_name=simulation_run.simulation_id,  # Could map to display name
            created_at=datetime.utcnow(),
            simulation_finished_at=simulation_run.finished_at or datetime.utcnow(),
            time_to_complete_seconds=time_to_complete,
            proven_claims=proven_claims,
            unproven_claims=unproven_claims,
            risk_flags=risk_flags,
            artifacts=artifact_refs,
            total_claims=total_claims,
            proven_count=proven_count,
            unproven_count=unproven_count,
            proof_rate=proof_rate,
            dimensions_covered=dimensions_covered,
            suggested_interview_questions=all_questions[:10],  # Limit to top 10
            com_snapshot=com,
        )

    def _compute_dimensions_coverage(
        self,
        proven: list[ProvenClaim],
        unproven: list[UnprovenClaim],
    ) -> dict[str, str]:
        """Compute coverage status for each dimension."""
        coverage = {}

        # Initialize all dimensions as not_evaluated
        for dim in self.ALL_DIMENSIONS:
            coverage[dim] = "not_evaluated"

        # Mark proven dimensions
        for claim in proven:
            for dim in claim.dimensions:
                coverage[dim] = "proven"

        # Mark unproven dimensions (only if not already proven)
        for claim in unproven:
            if claim.dimension in coverage and coverage[claim.dimension] != "proven":
                coverage[claim.dimension] = "unproven"

        return coverage

    def _identify_risk_flags(
        self,
        proof_results: list[ProofResult],
        simulation_run: SimulationRun,
    ) -> list[RiskFlag]:
        """Identify potential risk flags from the results."""
        flags = []

        # Check for skipped tests
        for result in proof_results:
            if result.claim.claim_type == "testing_discipline" and result.status == "UNPROVED":
                if "skipped" in result.reason.lower():
                    flags.append(
                        RiskFlag(
                            flag_type="skipped_tests",
                            severity="medium",
                            description="Candidate introduced skipped tests",
                        )
                    )

        # Check for timeout/long completion
        duration = self._get_run_duration_seconds(simulation_run)
        if duration is not None and duration > 3600:  # Over 1 hour
            flags.append(
                RiskFlag(
                    flag_type="long_completion_time",
                    severity="low",
                    description=f"Simulation took {int(duration/60)} minutes to complete",
                )
            )

        # Check if tests never passed
        tests_passed = False
        for result in proof_results:
            for ref in result.evidence_refs:
                if ref.id == "tests_passed" and ref.value is True:
                    tests_passed = True
                    break

        if not tests_passed:
            flags.append(
                RiskFlag(
                    flag_type="tests_never_passed",
                    severity="high",
                    description="Tests did not pass after candidate submission",
                )
            )

        return flags


# Convenience function
def build_brief(
    application: Application,
    candidate: Candidate,
    role: Role,
    simulation_run: SimulationRun,
    proof_results: list[ProofResult],
    artifacts: list[Artifact],
    com: dict[str, Any],
) -> CandidateBrief:
    """Build a candidate brief."""
    builder = BriefBuilder()
    return builder.build(
        application=application,
        candidate=candidate,
        role=role,
        simulation_run=simulation_run,
        proof_results=proof_results,
        artifacts=artifacts,
        com=com,
    )
