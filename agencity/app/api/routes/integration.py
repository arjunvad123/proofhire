"""
Integration API routes for Agencity ↔ ProofHire.

Endpoints for managing candidate linkages, feedback actions, and pipeline view.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from postgrest.exceptions import APIError

from app.core.database import get_supabase_client
from app.api.models.integration import (
    CreateLinkageRequest,
    UpdateLinkageRequest,
    LinkageResponse,
    LinkageWithCandidateResponse,
    LinkagesListResponse,
    RecordFeedbackRequest,
    FeedbackResponse,
    FeedbackStatsResponse,
    ProofHireIntegrationStats,
    PipelineResponse,
    PipelineCandidate,
    ProofHireLinkageInfo,
    WarmPathInfo,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# LINKAGE ENDPOINTS
# ============================================================================

@router.post("/linkages", response_model=LinkageResponse, status_code=201)
async def create_linkage(request: CreateLinkageRequest):
    """
    Create a new candidate linkage between Agencity and ProofHire.

    This is called when a founder clicks "Invite to ProofHire" in the Agencity UI.
    """
    supabase = get_supabase_client()

    try:
        # Validate that company and candidate exist
        company = supabase.table("companies").select("id").eq("id", request.company_id).execute()
        if not company.data:
            raise HTTPException(status_code=404, detail="Company not found")

        candidate = supabase.table("people").select("id").eq("id", request.agencity_candidate_id).execute()
        if not candidate.data:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Check if linkage already exists for this candidate
        existing = supabase.table("candidate_linkages").select("*").eq(
            "agencity_candidate_id", request.agencity_candidate_id
        ).execute()

        if existing.data:
            raise HTTPException(
                status_code=409,
                detail="Linkage already exists for this candidate"
            )

        # Create linkage
        linkage_data = {
            "company_id": request.company_id,
            "agencity_candidate_id": request.agencity_candidate_id,
            "agencity_search_id": request.agencity_search_id,
            "proofhire_application_id": request.proofhire_application_id,
            "proofhire_role_id": request.proofhire_role_id,
            "status": "linked",
        }

        result = supabase.table("candidate_linkages").insert(linkage_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create linkage")

        logger.info(
            f"Created linkage: candidate={request.agencity_candidate_id}, "
            f"application={request.proofhire_application_id}"
        )

        return LinkageResponse(**result.data[0])

    except APIError as e:
        logger.error(f"Supabase error creating linkage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/linkages/candidate/{candidate_id}", response_model=LinkageResponse)
async def get_linkage_by_candidate(candidate_id: str):
    """
    Get linkage for a specific Agencity candidate.

    Returns 404 if no linkage exists.
    """
    supabase = get_supabase_client()

    try:
        result = supabase.table("candidate_linkages").select("*").eq(
            "agencity_candidate_id", candidate_id
        ).execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="No linkage found for this candidate"
            )

        return LinkageResponse(**result.data[0])

    except APIError as e:
        logger.error(f"Supabase error getting linkage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/linkages/application/{application_id}", response_model=LinkageResponse)
async def get_linkage_by_application(application_id: str):
    """
    Get linkage by ProofHire application ID.

    Used for webhook handlers to update linkage status.
    """
    supabase = get_supabase_client()

    try:
        result = supabase.table("candidate_linkages").select("*").eq(
            "proofhire_application_id", application_id
        ).execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="No linkage found for this application"
            )

        return LinkageResponse(**result.data[0])

    except APIError as e:
        logger.error(f"Supabase error getting linkage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/linkages/company/{company_id}", response_model=LinkagesListResponse)
async def get_company_linkages(
    company_id: str,
    status: Optional[str] = Query(None, description="Filter by status (all if not specified)")
):
    """
    Get all linkages for a company, optionally filtered by status.
    """
    supabase = get_supabase_client()

    try:
        # Build query
        query = supabase.table("candidate_linkages").select(
            "id, agencity_candidate_id, proofhire_application_id, proofhire_role_id, "
            "status, created_at, people!inner(full_name, email)"
        ).eq("company_id", company_id)

        if status and status != "all":
            query = query.eq("status", status)

        result = query.order("created_at", desc=True).execute()

        # Format response
        linkages = []
        for row in result.data:
            linkages.append(LinkageWithCandidateResponse(
                id=row["id"],
                agencity_candidate_id=row["agencity_candidate_id"],
                candidate_name=row["people"]["full_name"],
                candidate_email=row["people"].get("email"),
                proofhire_application_id=row["proofhire_application_id"],
                proofhire_role_id=row["proofhire_role_id"],
                status=row["status"],
                created_at=row["created_at"]
            ))

        return LinkagesListResponse(
            linkages=linkages,
            total=len(linkages)
        )

    except APIError as e:
        logger.error(f"Supabase error getting company linkages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/linkages/{linkage_id}", response_model=LinkageResponse)
async def update_linkage(linkage_id: str, request: UpdateLinkageRequest):
    """
    Update linkage status.

    Called when simulation status changes (e.g., via webhook from ProofHire).
    """
    supabase = get_supabase_client()

    try:
        result = supabase.table("candidate_linkages").update({
            "status": request.status.value
        }).eq("id", linkage_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Linkage not found")

        logger.info(f"Updated linkage {linkage_id} to status: {request.status}")

        return LinkageResponse(**result.data[0])

    except APIError as e:
        logger.error(f"Supabase error updating linkage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FEEDBACK ENDPOINTS
# ============================================================================

@router.post("/feedback/action", response_model=FeedbackResponse, status_code=201)
async def record_feedback(request: RecordFeedbackRequest):
    """
    Record a feedback action for reinforcement learning.

    Called when founder makes a hiring decision (hired, rejected, etc.).
    """
    supabase = get_supabase_client()

    try:
        # Validate company and candidate exist
        company = supabase.table("companies").select("id").eq("id", request.company_id).execute()
        if not company.data:
            raise HTTPException(status_code=404, detail="Company not found")

        candidate = supabase.table("people").select("id").eq("id", request.candidate_id).execute()
        if not candidate.data:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Create feedback record
        feedback_data = {
            "company_id": request.company_id,
            "candidate_id": request.candidate_id,
            "search_id": request.search_id,
            "action": request.action.value,
            "proofhire_score": request.proofhire_score,
            "proofhire_application_id": request.proofhire_application_id,
            "notes": request.notes,
            "metadata": request.metadata,
        }

        result = supabase.table("feedback_actions").insert(feedback_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to record feedback")

        logger.info(
            f"Recorded feedback: candidate={request.candidate_id}, "
            f"action={request.action}, score={request.proofhire_score}"
        )

        return FeedbackResponse(
            id=result.data[0]["id"],
            action=result.data[0]["action"],
            recorded_at=result.data[0]["created_at"]
        )

    except APIError as e:
        logger.error(f"Supabase error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/stats/{company_id}", response_model=FeedbackStatsResponse)
async def get_feedback_stats(company_id: str):
    """
    Get feedback statistics for a company.

    Returns breakdown by action type and ProofHire integration metrics.
    """
    supabase = get_supabase_client()

    try:
        # Get all feedback for company
        result = supabase.table("feedback_actions").select(
            "action, proofhire_score, proofhire_application_id"
        ).eq("company_id", company_id).execute()

        total_feedback = len(result.data)

        # Count by action
        by_action = {}
        for row in result.data:
            action = row["action"]
            by_action[action] = by_action.get(action, 0) + 1

        # ProofHire integration stats
        proofhire_feedback = [
            row for row in result.data
            if row.get("proofhire_application_id")
        ]

        total_invited = len(proofhire_feedback)
        completed = [row for row in proofhire_feedback if row.get("proofhire_score") is not None]
        total_completed = len(completed)

        completion_rate = total_completed / total_invited if total_invited > 0 else 0.0

        avg_score = None
        if completed:
            avg_score = sum(row["proofhire_score"] for row in completed) / len(completed)

        proofhire_stats = ProofHireIntegrationStats(
            total_invited=total_invited,
            total_completed=total_completed,
            completion_rate=completion_rate,
            avg_score=avg_score
        )

        return FeedbackStatsResponse(
            total_feedback=total_feedback,
            by_action=by_action,
            proofhire_integration=proofhire_stats
        )

    except APIError as e:
        logger.error(f"Supabase error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PIPELINE ENDPOINT
# ============================================================================

@router.get("/pipeline/{company_id}", response_model=PipelineResponse)
async def get_pipeline(
    company_id: str,
    status: str = Query("all", description="Filter by status"),
    sort: str = Query("date", description="Sort by: date, score, status"),
    limit: int = Query(50, ge=1, le=200, description="Max results")
):
    """
    Get all candidates in the pipeline for a company.

    Includes candidates from search results with their linkage status and ProofHire data.
    """
    supabase = get_supabase_client()

    try:
        # Get all people for this company with optional linkage data
        query = supabase.table("people").select(
            "id, full_name, email, current_title, current_company, "
            "trust_score, is_from_network, first_seen, "
            "candidate_linkages(id, proofhire_application_id, proofhire_role_id, status)"
        ).eq("company_id", company_id)

        result = query.order("first_seen", desc=True).limit(limit).execute()

        candidates = []
        status_counts = {
            "sourced": 0,
            "contacted": 0,
            "invited": 0,
            "in_simulation": 0,
            "reviewed": 0
        }

        for person in result.data:
            # Determine candidate status
            linkage = person.get("candidate_linkages")
            if linkage and len(linkage) > 0:
                linkage = linkage[0]
                linkage_status = linkage["status"]

                # Map linkage status to pipeline status
                if linkage_status == "linked":
                    candidate_status = "invited"
                elif linkage_status in ["simulation_pending", "simulation_in_progress"]:
                    candidate_status = "in_simulation"
                elif linkage_status in ["simulation_complete", "evaluated"]:
                    candidate_status = "reviewed"
                else:
                    candidate_status = "sourced"

                proofhire_info = ProofHireLinkageInfo(
                    application_id=linkage["proofhire_application_id"],
                    role_id=linkage["proofhire_role_id"],
                    simulation_status=linkage_status,
                    brief_available=(linkage_status == "evaluated")
                )
            else:
                candidate_status = "sourced"
                proofhire_info = None

            # Warmth level
            warmth_score = person.get("trust_score", 0.5)
            warmth_level = "network" if person.get("is_from_network") else "cold"

            # Warm path info (simplified for now)
            warm_path = None
            if person.get("is_from_network"):
                warm_path = WarmPathInfo(
                    type="network",
                    description="From founder's network"
                )

            status_counts[candidate_status] += 1

            candidates.append(PipelineCandidate(
                id=person["id"],
                agencity_candidate_id=person["id"],
                name=person["full_name"],
                email=person.get("email"),
                title=person.get("current_title"),
                company=person.get("current_company"),
                warmth_score=warmth_score,
                warmth_level=warmth_level,
                warm_path=warm_path,
                status=candidate_status,
                sourced_at=person["first_seen"],
                contacted_at=None,  # TODO: Track this separately
                invited_at=linkage["created_at"] if linkage else None,
                proofhire_linkage=proofhire_info
            ))

        # Apply status filter
        if status != "all":
            candidates = [c for c in candidates if c.status == status]

        # Apply sorting
        if sort == "score":
            candidates.sort(key=lambda c: c.warmth_score, reverse=True)
        elif sort == "status":
            candidates.sort(key=lambda c: c.status)
        # Default is already by date (first_seen)

        return PipelineResponse(
            candidates=candidates,
            total=len(candidates),
            by_status=status_counts
        )

    except APIError as e:
        logger.error(f"Supabase error getting pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))
