"""Orchestration service for processing completed simulation runs.

This service coordinates the entire flow from run completion to brief generation:
1. Store metrics and artifact references
2. Generate claims from evidence
3. Evaluate claims using proof engine
4. Store claim results
5. Generate interview questions for unproven claims
6. Build and store the candidate brief
7. Update application status
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.core.ids import generate_id
from app.core.time import utc_now
from app.db.models import (
    Application,
    ApplicationStatus,
    SimulationRun,
    Artifact,
    ArtifactType,
    Metric,
    Claim as ClaimModel,
    ClaimStatus,
    Brief,
    Role,
    Candidate,
)
from app.hypothesis.generator import generate_claims, prioritize_claims
from app.hypothesis.claim_schema import Claim, ProofResult
from app.proof.engine import get_proof_engine
from app.briefs.interview_packet import generate_full_interview_packet
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def process_completed_run(
    run_id: str,
    metrics: dict[str, Any],
    artifact_urls: dict[str, str],
) -> None:
    """
    Process a completed simulation run through the full evaluation pipeline.

    This is called as a background task after the runner notifies completion.

    Args:
        run_id: The simulation run ID
        metrics: Dict of metric name -> value from the runner
        artifact_urls: Dict of artifact name -> S3 presigned URL
    """
    logger.info(f"Starting orchestration for run {run_id}")

    # Create a new database session for the background task
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # 1. Fetch the run and related data
            result = await db.execute(
                select(SimulationRun).where(SimulationRun.id == run_id)
            )
            run = result.scalar_one_or_none()

            if not run:
                logger.error(f"Run {run_id} not found")
                return

            # Get application and role
            result = await db.execute(
                select(Application).where(Application.id == run.application_id)
            )
            application = result.scalar_one_or_none()

            if not application:
                logger.error(f"Application {run.application_id} not found")
                return

            result = await db.execute(
                select(Role).where(Role.id == application.role_id)
            )
            role = result.scalar_one_or_none()

            result = await db.execute(
                select(Candidate).where(Candidate.id == application.candidate_id)
            )
            candidate = result.scalar_one_or_none()

            if not role or not candidate:
                logger.error(f"Role or candidate not found for application {application.id}")
                return

            # Get COM from role
            com = role.com_json or {}
            rubric = role.rubric_json or {}

            # 2. Store metrics in database
            metric_records = []
            for name, value in metrics.items():
                metric = Metric(
                    id=generate_id(),
                    simulation_run_id=run_id,
                    name=name,
                )
                # Store in appropriate column based on type
                if isinstance(value, bool):
                    metric.value_bool = value
                elif isinstance(value, (int, float)):
                    metric.value_float = float(value)
                else:
                    metric.value_text = str(value)

                db.add(metric)
                metric_records.append(metric)

            await db.flush()

            # 3. Store artifact references
            artifact_records = []
            artifact_type_map = {
                "metrics.json": ArtifactType.METRICS_JSON,
                "testlog.txt": ArtifactType.TEST_LOG,
                "coverage.xml": ArtifactType.COVERAGE,
                "diff.patch": ArtifactType.DIFF,
                "grader_output.json": ArtifactType.METRICS_JSON,
            }

            for name, url in artifact_urls.items():
                artifact_type = artifact_type_map.get(name, ArtifactType.METRICS_JSON)
                # Extract S3 key from URL (everything after bucket name)
                s3_key = f"runs/{run_id}/{name}"

                artifact = Artifact(
                    id=generate_id(),
                    simulation_run_id=run_id,
                    type=artifact_type,
                    s3_key=s3_key,
                    sha256="pending",  # Would compute from actual content
                    metadata_json={"url": url, "filename": name},
                )
                db.add(artifact)
                artifact_records.append(artifact)

            await db.flush()

            # 4. Generate claims from evidence
            claims = generate_claims(
                application_id=application.id,
                candidate_id=candidate.id,
                simulation_run_id=run_id,
                metrics=metric_records,
                artifacts=artifact_records,
                com=com,
            )

            # Prioritize claims based on rubric
            claims = prioritize_claims(claims, rubric)

            logger.info(f"Generated {len(claims)} claims for run {run_id}")

            # 5. Evaluate claims using proof engine
            proof_engine = get_proof_engine()
            proof_results: list[ProofResult] = proof_engine.evaluate_all(
                claims=claims,
                metrics=metric_records,
                artifacts=artifact_records,
                llm_tags=None,  # TODO: Add LLM tagging for writeup analysis
                com=com,
            )

            # 6. Store claim results in database
            proved_claims = []
            unproved_claims = []

            for result in proof_results:
                claim_model = ClaimModel(
                    id=generate_id(),
                    application_id=application.id,
                    claim_type=result.claim.claim_type,
                    claim_json=result.claim.model_dump(),
                    status=ClaimStatus.PROVED if result.status == "PROVED" else ClaimStatus.UNPROVED,
                    evidence_refs_json={
                        "refs": [ref.model_dump() for ref in result.evidence_refs],
                        "reason": result.reason,
                    },
                    rule_id=result.rule_id,
                )
                db.add(claim_model)

                if result.status == "PROVED":
                    proved_claims.append(result)
                else:
                    unproven_claims.append((result.claim, result.reason))

            await db.flush()

            logger.info(
                f"Evaluated claims: {len(proved_claims)} proved, {len(unproven_claims)} unproved"
            )

            # 7. Generate interview questions for unproven claims
            interview_questions = []
            if unproven_claims:
                interview_questions = generate_full_interview_packet(
                    unproven_claims=unproven_claims,
                    com=com,
                    max_questions=10,
                )

            # 8. Build the brief
            brief_content = {
                "candidate": {
                    "id": candidate.id,
                    "name": candidate.name,
                    "email": candidate.email,
                },
                "role": {
                    "id": role.id,
                    "title": role.title,
                },
                "simulation": {
                    "id": run.simulation_id,
                    "run_id": run_id,
                    "completed_at": run.finished_at.isoformat() if run.finished_at else None,
                },
                "proof_rate": len(proved_claims) / len(proof_results) if proof_results else 0,
                "proven_claims": [
                    {
                        "claim_type": r.claim.claim_type,
                        "statement": r.claim.statement,
                        "dimensions": r.claim.dimensions,
                        "evidence": [ref.model_dump() for ref in r.evidence_refs],
                        "rule_id": r.rule_id,
                        "reason": r.reason,
                    }
                    for r in proved_claims
                ],
                "unproven_claims": [
                    {
                        "claim_type": claim.claim_type,
                        "statement": claim.statement,
                        "dimensions": claim.dimensions,
                        "reason": reason,
                    }
                    for claim, reason in unproven_claims
                ],
                "interview_questions": interview_questions,
                "risk_flags": _identify_risk_flags(metrics, proof_results),
                "dimensions_coverage": _compute_dimensions_coverage(proof_results, rubric),
            }

            # Store the brief
            brief = Brief(
                id=generate_id(),
                application_id=application.id,
                brief_json=brief_content,
                version=1,
            )
            db.add(brief)

            # 9. Update application status to COMPLETE
            application.status = ApplicationStatus.COMPLETE

            await db.commit()

            logger.info(
                f"Orchestration complete for run {run_id}",
                application_id=application.id,
                brief_id=brief.id,
                proof_rate=brief_content["proof_rate"],
            )

        except Exception as e:
            logger.exception(f"Orchestration failed for run {run_id}: {e}")
            await db.rollback()
            raise

        finally:
            await engine.dispose()


def _identify_risk_flags(
    metrics: dict[str, Any],
    proof_results: list[ProofResult],
) -> list[dict[str, Any]]:
    """Identify risk flags based on metrics and proof results."""
    flags = []

    # Check for test failures
    if metrics.get("failed_tests_count", 0) > 0:
        flags.append({
            "severity": "high",
            "type": "test_failures",
            "message": f"{metrics['failed_tests_count']} test(s) failed",
        })

    # Check for low proof rate
    proved = sum(1 for r in proof_results if r.status == "PROVED")
    if len(proof_results) > 0 and proved / len(proof_results) < 0.3:
        flags.append({
            "severity": "medium",
            "type": "low_proof_rate",
            "message": "Less than 30% of claims could be proven",
        })

    # Check for missing coverage
    if metrics.get("coverage_percent", 100) < 50:
        flags.append({
            "severity": "medium",
            "type": "low_coverage",
            "message": f"Test coverage at {metrics.get('coverage_percent', 0):.1f}%",
        })

    # Check for timeout
    if metrics.get("timed_out", False):
        flags.append({
            "severity": "high",
            "type": "timeout",
            "message": "Candidate did not complete within time limit",
        })

    return flags


def _compute_dimensions_coverage(
    proof_results: list[ProofResult],
    rubric: dict[str, Any],
) -> dict[str, str]:
    """Compute coverage status for each evaluation dimension."""
    # Get all dimensions from rubric
    weights = rubric.get("weights", {})
    dimensions = set(weights.keys())

    # Also add dimensions from claims
    for result in proof_results:
        dimensions.update(result.claim.dimensions)

    coverage = {}
    for dim in dimensions:
        # Check if any proved claim covers this dimension
        proved_for_dim = any(
            dim in r.claim.dimensions and r.status == "PROVED"
            for r in proof_results
        )
        unproved_for_dim = any(
            dim in r.claim.dimensions and r.status == "UNPROVED"
            for r in proof_results
        )

        if proved_for_dim:
            coverage[dim] = "covered"
        elif unproved_for_dim:
            coverage[dim] = "partial"
        else:
            coverage[dim] = "uncovered"

    return coverage
