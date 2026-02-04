"""Brief type definitions."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProvenClaim(BaseModel):
    """A claim that has been proven by evidence."""

    claim_type: str
    statement: str
    dimensions: list[str]
    evidence_refs: list[dict[str, Any]]
    rule_id: str
    confidence: float = 1.0


class UnprovenClaim(BaseModel):
    """A claim that could not be proven."""

    claim_type: str
    statement: str
    dimension: str
    reason: str
    next_step: str = "interview_question"
    suggested_questions: list[str] = Field(default_factory=list)


class RiskFlag(BaseModel):
    """A potential risk or concern identified."""

    flag_type: str
    severity: str  # "low", "medium", "high"
    description: str
    evidence_ref: dict[str, Any] | None = None


class ArtifactReference(BaseModel):
    """Reference to a stored artifact."""

    artifact_id: str
    artifact_type: str
    s3_key: str
    download_url: str | None = None


class CandidateBrief(BaseModel):
    """Complete candidate brief for review.

    This is the main output of the ProofHire system - a structured
    evidence-based summary of what was proven and what needs follow-up.
    """

    # Identifiers
    brief_id: str
    application_id: str
    candidate_id: str
    role_id: str
    org_id: str

    # Candidate info (limited)
    candidate_name: str
    simulation_id: str
    simulation_name: str

    # Timing
    created_at: datetime
    simulation_finished_at: datetime
    time_to_complete_seconds: float

    # Core results
    proven_claims: list[ProvenClaim]
    unproven_claims: list[UnprovenClaim]

    # Additional context
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    artifacts: list[ArtifactReference] = Field(default_factory=list)

    # Summary metrics
    total_claims: int
    proven_count: int
    unproven_count: int
    proof_rate: float  # proven_count / total_claims

    # Dimensions coverage
    dimensions_covered: dict[str, str]  # dimension -> status ("proven", "unproven", "not_evaluated")

    # Interview packet
    suggested_interview_questions: list[str] = Field(default_factory=list)

    # Metadata
    version: str = "1.0"
    com_snapshot: dict[str, Any] = Field(default_factory=dict)  # Company model at time of evaluation


class BriefSummary(BaseModel):
    """Short summary of a brief for list views."""

    brief_id: str
    application_id: str
    candidate_name: str
    simulation_name: str
    created_at: datetime
    proven_count: int
    unproven_count: int
    proof_rate: float
    top_proven_dimensions: list[str]
    top_unproven_dimensions: list[str]
