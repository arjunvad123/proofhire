"""
Pipeline API routes for Agencity.

Endpoints for managing candidate pipeline status and feedback actions.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from postgrest.exceptions import APIError

from app.auth import CompanyAuth, get_current_company
from app.core.database import get_supabase_client
from app.api.models.integration import (
    CreateLinkageRequest,
    UpdateLinkageRequest,
    LinkageStatus,
    LinkageResponse,
    LinkageWithCandidateResponse,
    LinkagesListResponse,
    RecordFeedbackRequest,
    FeedbackAction,
    FeedbackResponse,
    FeedbackStatsResponse,
    ProofHireIntegrationStats,
    PipelineResponse,
    PipelineCandidate,
    WarmPathInfo,
    UpdateStatusRequest,
    UpdateStatusResponse,
    PipelineStatus,
    CurationCacheResponse,
    CacheStatusResponse,
    GenerateCacheRequest,
    GenerateAllCachesRequest,
    CurationCacheStatus,
    InviteToProofHireRequest,
    InviteToProofHireResponse,
    ProofHireRunWebhookRequest,
    ProofHireRunWebhookResponse,
    DecisionPacketResponse,
)
from app.config import settings
from app.services.proofhire_client import proofhire_client
from app.services.external_search.clado_client import clado_client
from app.services.external_search.apollo_client import apollo_client
from app.services.external_search.firecrawl_client import firecrawl_client

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# LINKAGE ENDPOINTS (DEPRECATED - ProofHire integration removed)
# ============================================================================
# These endpoints are kept for backwards compatibility but will be removed in future versions

@router.post("/linkages", response_model=LinkageResponse, status_code=201, deprecated=True)
async def create_linkage(
    request: CreateLinkageRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Create a new candidate linkage between Agencity and ProofHire.

    This is called when a founder clicks "Invite to ProofHire" in the Agencity UI.
    """
    request.company_id = auth.company_id
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


@router.get("/linkages/candidate/{candidate_id}", response_model=LinkageResponse, deprecated=True)
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


@router.get("/linkages/application/{application_id}", response_model=LinkageResponse, deprecated=True)
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


@router.get("/linkages/company/{company_id}", response_model=LinkagesListResponse, deprecated=True)
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


@router.patch("/linkages/{linkage_id}", response_model=LinkageResponse, deprecated=True)
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
# PROOFHIRE OPERATIONAL ENDPOINTS
# ============================================================================

@router.post("/proofhire/invite", response_model=InviteToProofHireResponse, status_code=201)
async def invite_candidate_to_proofhire(
    request: InviteToProofHireRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Create a ProofHire application and persist candidate linkage.

    This is the operational replacement for deprecated linkage flow.
    """
    request.company_id = auth.company_id
    supabase = get_supabase_client()

    try:
        company = supabase.table("companies").select("id").eq("id", request.company_id).execute()
        if not company.data:
            raise HTTPException(status_code=404, detail="Company not found")

        candidate_result = (
            supabase.table("people")
            .select("id, company_id, full_name, email, github_url")
            .eq("id", request.candidate_id)
            .eq("company_id", request.company_id)
            .execute()
        )
        if not candidate_result.data:
            raise HTTPException(status_code=404, detail="Candidate not found for company")

        candidate = candidate_result.data[0]
        if not candidate.get("email"):
            raise HTTPException(
                status_code=400,
                detail="Candidate is missing email and cannot be invited to ProofHire",
            )

        try:
            app_payload = await proofhire_client.create_application(
                proofhire_role_id=request.proofhire_role_id,
                candidate_name=candidate.get("full_name") or "Candidate",
                candidate_email=candidate["email"],
                github_url=candidate.get("github_url"),
            )
        except Exception as exc:
            logger.exception("ProofHire application creation failed")
            raise HTTPException(
                status_code=502,
                detail=f"ProofHire application creation failed: {exc}",
            ) from exc

        proofhire_application_id = app_payload.get("id")
        if not proofhire_application_id:
            raise HTTPException(status_code=502, detail="ProofHire response missing application id")

        existing = (
            supabase.table("candidate_linkages")
            .select("id")
            .eq("agencity_candidate_id", request.candidate_id)
            .execute()
        )

        linkage_data = {
            "company_id": request.company_id,
            "agencity_candidate_id": request.candidate_id,
            "agencity_search_id": request.search_id,
            "proofhire_application_id": proofhire_application_id,
            "proofhire_role_id": request.proofhire_role_id,
            "status": LinkageStatus.SIMULATION_PENDING.value,
        }

        if existing.data:
            linkage = (
                supabase.table("candidate_linkages")
                .update(linkage_data)
                .eq("id", existing.data[0]["id"])
                .execute()
            )
        else:
            linkage = supabase.table("candidate_linkages").insert(linkage_data).execute()

        if not linkage.data:
            raise HTTPException(status_code=500, detail="Failed to persist candidate linkage")

        linkage_row = linkage.data[0]
        return InviteToProofHireResponse(
            linkage_id=linkage_row["id"],
            candidate_id=request.candidate_id,
            proofhire_application_id=linkage_row["proofhire_application_id"],
            proofhire_role_id=linkage_row["proofhire_role_id"],
            status=linkage_row["status"],
        )

    except HTTPException:
        raise
    except APIError as e:
        logger.error("Supabase error inviting candidate to ProofHire: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proofhire/webhooks/run-complete", response_model=ProofHireRunWebhookResponse)
async def proofhire_run_complete_webhook(
    request: ProofHireRunWebhookRequest,
    x_internal_key: Optional[str] = Header(None),
):
    """Update linkage status when ProofHire run completes."""
    supabase = get_supabase_client()

    if settings.proofhire_internal_api_key:
        if not proofhire_client.verify_internal_key(x_internal_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid internal API key",
            )

    try:
        linkage_result = (
            supabase.table("candidate_linkages")
            .select("*")
            .eq("proofhire_application_id", request.proofhire_application_id)
            .execute()
        )

        if not linkage_result.data:
            return ProofHireRunWebhookResponse(status="ignored_no_linkage")

        linkage = linkage_result.data[0]
        linkage_id = linkage["id"]
        # Linkage tracks milestone completion (not score quality), so both pass/fail
        # terminal run events are marked complete.
        new_status = LinkageStatus.SIMULATION_COMPLETE.value

        supabase.table("candidate_linkages").update({"status": new_status}).eq("id", linkage_id).execute()

        if request.proofhire_score is not None:
            supabase.table("feedback_actions").insert(
                {
                    "company_id": linkage["company_id"],
                    "candidate_id": linkage["agencity_candidate_id"],
                    "action": FeedbackAction.INTERVIEWED.value if request.success else FeedbackAction.IGNORED.value,
                    "proofhire_application_id": request.proofhire_application_id,
                    "proofhire_score": request.proofhire_score,
                    "metadata": {
                        "run_id": request.run_id,
                        "success": request.success,
                        "webhook_metadata": request.metadata or {},
                    },
                }
            ).execute()

        return ProofHireRunWebhookResponse(status="ok", linkage_id=linkage_id)

    except APIError as e:
        logger.error("Supabase error handling ProofHire webhook: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proofhire/decision-packet/{proofhire_application_id}", response_model=DecisionPacketResponse)
async def get_decision_packet(proofhire_application_id: str):
    """Return founder-facing decision packet data for one application."""
    supabase = get_supabase_client()

    try:
        linkage_result = (
            supabase.table("candidate_linkages")
            .select("*")
            .eq("proofhire_application_id", proofhire_application_id)
            .execute()
        )
        if not linkage_result.data:
            raise HTTPException(status_code=404, detail="Linkage not found")

        linkage_row = linkage_result.data[0]
        candidate_result = (
            supabase.table("people")
            .select("id, full_name, email, linkedin_url, github_url, current_title, current_company")
            .eq("id", linkage_row["agencity_candidate_id"])
            .execute()
        )
        candidate = candidate_result.data[0] if candidate_result.data else {}

        feedback_result = (
            supabase.table("feedback_actions")
            .select("id, action, proofhire_score, notes, metadata, created_at")
            .eq("proofhire_application_id", proofhire_application_id)
            .order("created_at", desc=True)
            .execute()
        )

        return DecisionPacketResponse(
            linkage=LinkageResponse(**linkage_row),
            candidate=candidate,
            feedback=feedback_result.data or [],
        )

    except HTTPException:
        raise
    except APIError as e:
        logger.error("Supabase error building decision packet: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/health", response_model=Dict[str, Any])
async def get_external_providers_health():
    """Health snapshot for external dependencies used in search/integration."""
    clado_health, firecrawl_health, apollo_health, proofhire_health = await asyncio.gather(
        clado_client.health_check(),
        firecrawl_client.health_check(),
        apollo_client.health_check(),
        proofhire_client.health_check(),
    )
    search_providers = [clado_health, firecrawl_health, apollo_health]
    all_providers = search_providers + [proofhire_health]
    active_search = sum(1 for p in search_providers if p.get("ok"))
    return {
        "ok": active_search > 0,  # OK if at least one search provider works
        "active_search_providers": active_search,
        "total_search_providers": len(search_providers),
        "providers": all_providers,
    }


# ============================================================================
# FEEDBACK ENDPOINTS
# ============================================================================

@router.post("/feedback/action", response_model=FeedbackResponse, status_code=201)
async def record_feedback(
    request: RecordFeedbackRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Record a feedback action for reinforcement learning.

    Called when founder makes a hiring decision (hired, rejected, etc.).
    """
    request.company_id = auth.company_id
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
async def get_feedback_stats(
    company_id: str,
    auth: CompanyAuth = Depends(get_current_company),
):
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
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get all candidates in the pipeline for a company.

    Simple 3-stage pipeline: sourced, contacted, scheduled
    """
    supabase = get_supabase_client()

    try:
        # Get all people for this company who are in the pipeline
        query = supabase.table("people").select(
            "id, full_name, email, current_title, current_company, "
            "trust_score, is_from_network, first_seen, pipeline_status, "
            "contacted_at, scheduled_at"
        ).eq("company_id", company_id).not_.is_("pipeline_status", "null")

        result = query.order("first_seen", desc=True).limit(limit).execute()

        candidates = []
        status_counts = {
            "sourced": 0,
            "contacted": 0,
            "scheduled": 0
        }

        for person in result.data:
            # Get pipeline status from database
            candidate_status = person.get("pipeline_status")
            if not candidate_status:
                continue


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
                contacted_at=person.get("contacted_at"),
                scheduled_at=person.get("scheduled_at")
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


@router.patch("/candidates/{candidate_id}/status", response_model=UpdateStatusResponse)
async def update_candidate_status(
    candidate_id: str,
    request: UpdateStatusRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Update candidate pipeline status.

    Updates the pipeline_status field and sets appropriate timestamps:
    - contacted: Sets contacted_at
    - scheduled: Sets scheduled_at
    """
    supabase = get_supabase_client()

    try:
        # Verify candidate exists
        candidate = supabase.table("people").select("id, pipeline_status").eq(
            "id", candidate_id
        ).execute()

        if not candidate.data:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Prepare update data
        update_data = {
            "pipeline_status": request.status.value,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Set/Clear timestamps based on status
        if request.status == PipelineStatus.CONTACTED:
            update_data["contacted_at"] = datetime.utcnow().isoformat()
            update_data["scheduled_at"] = None  # Clear later stage if moving back
        elif request.status == PipelineStatus.SCHEDULED:
            update_data["scheduled_at"] = datetime.utcnow().isoformat()
            # contacted_at should already be set, but we ensure it's not cleared
        elif request.status == PipelineStatus.SOURCED:
            update_data["contacted_at"] = None
            update_data["scheduled_at"] = None

        # Update the candidate
        result = supabase.table("people").update(update_data).eq(
            "id", candidate_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update candidate status")

        updated_candidate = result.data[0]

        logger.info(
            f"Updated candidate {candidate_id} to status: {request.status.value}"
            + (f" with notes: {request.notes}" if request.notes else "")
        )

        return UpdateStatusResponse(
            id=updated_candidate["id"],
            status=updated_candidate["pipeline_status"],
            contacted_at=updated_candidate.get("contacted_at"),
            scheduled_at=updated_candidate.get("scheduled_at"),
            updated_at=updated_candidate["updated_at"]
        )

    except APIError as e:
        logger.error(f"Supabase error updating candidate status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CURATION CACHE ENDPOINTS
# ============================================================================

@router.get("/curation/cache/{company_id}/{role_id}", response_model=CurationCacheResponse)
async def get_curation_cache(
    company_id: UUID,
    role_id: UUID,
    force_refresh: bool = Query(False, description="Force refresh cache"),
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get cached curated candidates for a role.

    Returns cached results if available and not expired.
    If cache is expired or force_refresh=True, returns 404.
    """
    supabase = get_supabase_client()

    try:
        # Check cache
        if not force_refresh:
            cache_result = supabase.table("curation_cache").select(
                "id, role_id, shortlist, metadata, total_searched, enriched_count, "
                "avg_match_score, generated_at, expires_at"
            ).eq("company_id", str(company_id)).eq("role_id", str(role_id)).gt(
                "expires_at", datetime.utcnow().isoformat()
            ).execute()

            if cache_result.data:
                cache = cache_result.data[0]

                # Get role title
                role_result = supabase.table("roles").select("title").eq("id", str(role_id)).execute()
                role_title = role_result.data[0]["title"] if role_result.data else "Unknown Role"

                logger.info(f"Cache hit for role {role_id}")

                return CurationCacheResponse(
                    role_id=str(role_id),
                    role_title=role_title,
                    status="cached",
                    shortlist=cache["shortlist"],
                    total_searched=cache["total_searched"],
                    enriched_count=cache["enriched_count"],
                    avg_match_score=cache["avg_match_score"],
                    generated_at=cache["generated_at"],
                    expires_at=cache["expires_at"],
                    from_cache=True
                )

        # Cache miss or force refresh
        raise HTTPException(
            status_code=404,
            detail="Cache not found or expired. Use POST /curation/cache/generate to create cache."
        )

    except HTTPException:
        raise
    except APIError as e:
        logger.error(f"Supabase error getting cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/curation/cache/generate/{company_id}", response_model=Dict[str, str])
async def generate_curation_cache(
    company_id: str,
    request: GenerateCacheRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Generate/refresh cached curated candidates for a role.

    This triggers a background job to:
    1. Run curation for the role
    2. Store results in cache
    3. Update role curation_status

    Returns immediately with job ID.
    """
    supabase = get_supabase_client()

    try:
        # Verify role exists
        role = supabase.table("roles").select("id, title").eq(
            "id", request.role_id
        ).eq("company_id", company_id).execute()

        if not role.data:
            raise HTTPException(status_code=404, detail="Role not found")

        # Update role status to 'processing'
        supabase.table("roles").update({
            "curation_status": "processing"
        }).eq("id", request.role_id).execute()

        # NOTE: In production, this should trigger a background job (Celery, RQ, etc.)
        # For now, we'll mark it as pending and return
        # The actual curation should be done by a background worker

        logger.info(f"Curation job queued for role {request.role_id}")

        return {
            "status": "queued",
            "role_id": request.role_id,
            "message": "Curation job queued. Results will be cached when complete."
        }

    except HTTPException:
        raise
    except APIError as e:
        logger.error(f"Supabase error generating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/curation/cache/generate-all/{company_id}", response_model=Dict[str, Any])
async def generate_all_curation_caches(
    company_id: str,
    request: GenerateAllCachesRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Generate/refresh cached curated candidates for ALL company roles.

    This triggers background jobs for all active roles.
    Returns immediately with status.
    """
    supabase = get_supabase_client()

    try:
        # Get all active roles
        roles_result = supabase.table("roles").select("id, title, status").eq(
            "company_id", company_id
        ).eq("status", "active").execute()

        if not roles_result.data:
            return {
                "status": "no_roles",
                "message": "No active roles found",
                "queued_count": 0
            }

        # Update all roles to 'processing'
        role_ids = [r["id"] for r in roles_result.data]

        for role_id in role_ids:
            supabase.table("roles").update({
                "curation_status": "processing"
            }).eq("id", role_id).execute()

        logger.info(f"Curation jobs queued for {len(role_ids)} roles")

        return {
            "status": "queued",
            "queued_count": len(role_ids),
            "role_ids": role_ids,
            "message": f"Curation jobs queued for {len(role_ids)} roles"
        }

    except APIError as e:
        logger.error(f"Supabase error generating all caches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/curation/cache-status/{company_id}", response_model=CacheStatusResponse)
async def get_cache_status(
    company_id: str,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get curation cache status for all company roles.

    Returns counts and details for each role's cache status.
    """
    supabase = get_supabase_client()

    try:
        # Get all roles with their curation status
        roles_result = supabase.table("roles").select(
            "id, title, status, curation_status, last_curated_at"
        ).eq("company_id", company_id).execute()

        if not roles_result.data:
            return CacheStatusResponse(
                total_roles=0,
                cached=0,
                processing=0,
                pending=0,
                failed=0,
                roles=[]
            )

        # Count by status
        cached = sum(1 for r in roles_result.data if r.get("curation_status") == "cached")
        processing = sum(1 for r in roles_result.data if r.get("curation_status") == "processing")
        pending = sum(1 for r in roles_result.data if r.get("curation_status") == "pending")
        failed = sum(1 for r in roles_result.data if r.get("curation_status") == "failed")

        return CacheStatusResponse(
            total_roles=len(roles_result.data),
            cached=cached,
            processing=processing,
            pending=pending,
            failed=failed,
            roles=roles_result.data
        )

    except APIError as e:
        logger.error(f"Supabase error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
