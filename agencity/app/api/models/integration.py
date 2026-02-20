"""
Pydantic models for Agencity pipeline endpoints.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class LinkageStatus(str, Enum):
    """Status of a candidate linkage."""
    LINKED = "linked"
    SIMULATION_PENDING = "simulation_pending"
    SIMULATION_IN_PROGRESS = "simulation_in_progress"
    SIMULATION_COMPLETE = "simulation_complete"
    EVALUATED = "evaluated"


class FeedbackAction(str, Enum):
    """Types of feedback actions."""
    HIRED = "hired"
    INTERVIEWED = "interviewed"
    CONTACTED = "contacted"
    SAVED = "saved"
    VIEWED = "viewed"
    REJECTED = "rejected"
    IGNORED = "ignored"


# ============================================================================
# LINKAGE ENDPOINTS
# ============================================================================

class CreateLinkageRequest(BaseModel):
    """Request to create a new candidate linkage."""
    company_id: str = Field(..., description="Company UUID")
    agencity_candidate_id: str = Field(..., description="Agencity candidate UUID")
    agencity_search_id: Optional[str] = Field(None, description="Optional search UUID")
    proofhire_application_id: str = Field(..., description="ProofHire application ID")
    proofhire_role_id: str = Field(..., description="ProofHire role ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_id": "550e8400-e29b-41d4-a716-446655440000",
                "agencity_candidate_id": "123e4567-e89b-12d3-a456-426614174000",
                "proofhire_application_id": "pf-app-001",
                "proofhire_role_id": "pf-role-001"
            }
        }
    )


class UpdateLinkageRequest(BaseModel):
    """Request to update a linkage status."""
    status: LinkageStatus = Field(..., description="New linkage status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "simulation_complete"
            }
        }
    )


class LinkageResponse(BaseModel):
    """Response containing linkage details."""
    id: str
    company_id: str
    agencity_candidate_id: str
    agencity_search_id: Optional[str] = None
    proofhire_application_id: str
    proofhire_role_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LinkageWithCandidateResponse(BaseModel):
    """Response with linkage + candidate info."""
    id: str
    agencity_candidate_id: str
    candidate_name: str
    candidate_email: Optional[str] = None
    proofhire_application_id: str
    proofhire_role_id: str
    status: str
    created_at: datetime


class LinkagesListResponse(BaseModel):
    """Response with multiple linkages."""
    linkages: List[LinkageWithCandidateResponse]
    total: int


# ============================================================================
# FEEDBACK ENDPOINTS
# ============================================================================

class RecordFeedbackRequest(BaseModel):
    """Request to record feedback action."""
    company_id: str = Field(..., description="Company UUID")
    candidate_id: str = Field(..., description="Candidate UUID")
    search_id: Optional[str] = Field(None, description="Optional search UUID")
    action: FeedbackAction = Field(..., description="Feedback action")
    proofhire_score: Optional[int] = Field(None, ge=0, le=100, description="ProofHire score (0-100)")
    proofhire_application_id: Optional[str] = Field(None, description="ProofHire application ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_id": "550e8400-e29b-41d4-a716-446655440000",
                "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
                "action": "hired",
                "proofhire_score": 85,
                "proofhire_application_id": "pf-app-001",
                "notes": "Strong technical skills and great culture fit"
            }
        }
    )


class FeedbackResponse(BaseModel):
    """Response after recording feedback."""
    id: str
    action: str
    recorded_at: datetime


class ProofHireIntegrationStats(BaseModel):
    """Statistics about ProofHire integration."""
    total_invited: int
    total_completed: int
    completion_rate: float
    avg_score: Optional[float] = None


class FeedbackStatsResponse(BaseModel):
    """Response with feedback statistics."""
    total_feedback: int
    by_action: Dict[str, int]
    proofhire_integration: ProofHireIntegrationStats


# ============================================================================
# PIPELINE ENDPOINTS
# ============================================================================

class PipelineStatus(str, Enum):
    """Pipeline status values."""
    SOURCED = "sourced"
    CONTACTED = "contacted"
    SCHEDULED = "scheduled"


class UpdateStatusRequest(BaseModel):
    """Request to update candidate pipeline status."""
    status: PipelineStatus = Field(..., description="New pipeline status")
    notes: Optional[str] = Field(None, description="Optional notes about the status change")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "contacted",
                "notes": "Sent initial outreach email"
            }
        }
    )


class UpdateStatusResponse(BaseModel):
    """Response after updating pipeline status."""
    id: str
    status: str
    contacted_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    updated_at: datetime


class WarmPathInfo(BaseModel):
    """Warm path information."""
    type: str
    description: str


class PipelineCandidate(BaseModel):
    """Candidate in the pipeline - simple 3-stage flow."""
    id: str
    agencity_candidate_id: str
    name: str
    email: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    warmth_score: float
    warmth_level: str
    warm_path: Optional[WarmPathInfo] = None
    status: str  # sourced, contacted, scheduled
    sourced_at: datetime
    contacted_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None


class PipelineResponse(BaseModel):
    """Response with pipeline candidates."""
    candidates: List[PipelineCandidate]
    total: int
    by_status: Dict[str, int]


# ============================================================================
# CURATION CACHE ENDPOINTS
# ============================================================================

class CurationCacheStatus(str, Enum):
    """Curation cache status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    CACHED = "cached"
    FAILED = "failed"


class GenerateCacheRequest(BaseModel):
    """Request to generate cache for a role."""
    role_id: str = Field(..., description="Role UUID")
    force_refresh: bool = Field(False, description="Force refresh even if cache exists")


class CurationCacheResponse(BaseModel):
    """Response with cached curation data."""
    role_id: str
    role_title: str
    status: str
    shortlist: List[Dict[str, Any]]
    total_searched: int
    enriched_count: int
    avg_match_score: float
    generated_at: datetime
    expires_at: datetime
    from_cache: bool = True


class GenerateAllCachesRequest(BaseModel):
    """Request to generate cache for all company roles."""
    force_refresh: bool = Field(False, description="Force refresh all caches")


class CacheStatusResponse(BaseModel):
    """Response with cache status for all roles."""
    total_roles: int
    cached: int
    processing: int
    pending: int
    failed: int
    roles: List[Dict[str, Any]]


# ============================================================================
# PROOFHIRE OPERATIONAL INTEGRATION
# ============================================================================

class InviteToProofHireRequest(BaseModel):
    """Request to create/link a ProofHire application for a candidate."""
    company_id: str = Field(..., description="Company UUID")
    candidate_id: str = Field(..., description="Agencity candidate UUID")
    proofhire_role_id: str = Field(..., description="ProofHire role ID")
    search_id: Optional[str] = Field(None, description="Optional search UUID")


class InviteToProofHireResponse(BaseModel):
    """Response after creating/updating candidate linkage."""
    linkage_id: str
    candidate_id: str
    proofhire_application_id: str
    proofhire_role_id: str
    status: str


class ProofHireRunWebhookRequest(BaseModel):
    """Webhook payload from ProofHire when run state changes."""
    proofhire_application_id: str = Field(..., description="ProofHire application ID")
    run_id: str = Field(..., description="ProofHire simulation run ID")
    success: bool = Field(..., description="Whether run completed successfully")
    proofhire_score: Optional[int] = Field(None, ge=0, le=100, description="Optional score from brief/eval")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Raw webhook payload")


class ProofHireRunWebhookResponse(BaseModel):
    """Acknowledgement response for webhook updates."""
    status: str
    linkage_id: Optional[str] = None


class DecisionPacketResponse(BaseModel):
    """Combined packet for founder decisioning across systems."""
    linkage: LinkageResponse
    candidate: Dict[str, Any]
    feedback: List[Dict[str, Any]]
