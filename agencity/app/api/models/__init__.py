"""
API models package.
"""

from app.api.models.integration import (
    CreateLinkageRequest,
    UpdateLinkageRequest,
    LinkageResponse,
    LinkageWithCandidateResponse,
    LinkagesListResponse,
    RecordFeedbackRequest,
    FeedbackResponse,
    FeedbackStatsResponse,
    PipelineResponse,
    PipelineCandidate,
)

__all__ = [
    "CreateLinkageRequest",
    "UpdateLinkageRequest",
    "LinkageResponse",
    "LinkageWithCandidateResponse",
    "LinkagesListResponse",
    "RecordFeedbackRequest",
    "FeedbackResponse",
    "FeedbackStatsResponse",
    "PipelineResponse",
    "PipelineCandidate",
]
