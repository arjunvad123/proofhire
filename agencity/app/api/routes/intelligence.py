"""
Intelligence System API - V3 Endpoints

The four pillars of network intelligence:
1. Network Activation - Ask network for recommendations
2. Timing Intelligence - Predict who's ready before they know
3. Former Colleague Expansion - Find people who worked WITH your network
4. Company Intelligence - Monitor company events

V3 = Intelligence System (network-driven discovery)
V2 = Network-first search (within existing network)
V1 = API search (external sources)
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import CompanyAuth, get_current_company
from app.intelligence.activation import ReverseReferenceGenerator, ActivationMessageGenerator
from app.intelligence.activation.reverse_reference import RecommendationTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3", tags=["Intelligence System"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ReverseReferenceRequest(BaseModel):
    """Request to generate reverse reference asks."""
    company_id: Optional[UUID] = None
    role_title: str
    required_skills: list[str] = None
    target_person_ids: list[UUID] = None
    limit: int = 50
    save_to_db: bool = False


class ReverseReferenceResponse(BaseModel):
    """Response with generated activation requests."""
    requests_count: int
    requests: list[dict]
    summary: dict


class RecordRecommendationRequest(BaseModel):
    """Request to record a recommendation."""
    company_id: Optional[UUID] = None
    recommender_id: UUID
    activation_request_id: UUID = None
    recommended_name: str
    recommended_linkedin: str = None
    recommended_email: str = None
    recommended_context: str = None
    recommended_current_company: str = None
    recommended_current_title: str = None


class RecordRecommendationResponse(BaseModel):
    """Response after recording a recommendation."""
    recommendation: dict
    intro_request_message: str


class UpdateStatusRequest(BaseModel):
    """Request to update status."""
    status: str


# =============================================================================
# NETWORK ACTIVATION ENDPOINTS (Pillar 1)
# =============================================================================

@router.post("/activate/reverse-reference", response_model=ReverseReferenceResponse)
async def generate_reverse_reference_asks(
    request: ReverseReferenceRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Generate personalized "who would you recommend?" messages.

    This is the highest-ROI move in the intelligence system:
    - Your network has already filtered for quality
    - They've seen the person's actual work
    - Warm intro is built-in

    Example ask:
    "Hey Nikhil, who's the best ML engineer you've ever worked with?"
    """
    try:
        request.company_id = UUID(auth.company_id)
        generator = ReverseReferenceGenerator(request.company_id)

        # Generate requests
        requests = await generator.generate_activation_requests(
            role_title=request.role_title,
            required_skills=request.required_skills,
            target_person_ids=request.target_person_ids,
            limit=request.limit
        )

        # Optionally save to database
        if request.save_to_db and requests:
            requests = await generator.save_activation_requests(requests)

        # Build summary
        by_priority = {"high": 0, "medium": 0, "low": 0}
        for req in requests:
            score = req.get("priority_score", 0)
            if score >= 0.7:
                by_priority["high"] += 1
            elif score >= 0.4:
                by_priority["medium"] += 1
            else:
                by_priority["low"] += 1

        summary = {
            "role": request.role_title,
            "total_requests": len(requests),
            "by_priority": by_priority,
            "top_targets": [
                {
                    "name": r.get("target_name"),
                    "reason": r.get("ask_reason"),
                    "priority": r.get("priority_score")
                }
                for r in requests[:5]
            ]
        }

        return ReverseReferenceResponse(
            requests_count=len(requests),
            requests=requests,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Failed to generate reverse reference asks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations", response_model=RecordRecommendationResponse)
async def record_recommendation(
    request: RecordRecommendationRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Record a recommendation from a network member.

    When someone recommends a person, we:
    1. Store the recommendation
    2. Generate an intro request message
    3. Track the pipeline: recommendation -> intro -> contacted -> converted
    """
    try:
        request.company_id = UUID(auth.company_id)
        tracker = RecommendationTracker(request.company_id)

        result = await tracker.record_recommendation(
            recommender_id=request.recommender_id,
            activation_request_id=request.activation_request_id,
            recommended_name=request.recommended_name,
            recommended_linkedin=request.recommended_linkedin,
            recommended_email=request.recommended_email,
            recommended_context=request.recommended_context,
            recommended_current_company=request.recommended_current_company,
            recommended_current_title=request.recommended_current_title
        )

        intro_message = result.pop("intro_request_message", "")

        return RecordRecommendationResponse(
            recommendation=result,
            intro_request_message=intro_message
        )

    except Exception as e:
        logger.error(f"Failed to record recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{company_id}")
async def get_recommendations(
    company_id: UUID,
    status: str = None,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get all recommendations for a company.

    Status values:
    - new: Just received
    - intro_requested: Asked for intro
    - intro_made: Intro was made
    - contacted: We reached out
    - responded: They responded
    - converted: They joined the pipeline
    - declined: They said no
    """
    try:
        tracker = RecommendationTracker(company_id)
        recommendations = await tracker.get_recommendations(status=status)

        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "status_filter": status
        }

    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{company_id}/stats")
async def get_recommendation_stats(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get recommendation pipeline statistics.

    Returns:
    - Total recommendations
    - Breakdown by status
    - Conversion funnel
    - Conversion rates at each stage
    """
    try:
        tracker = RecommendationTracker(company_id)
        stats = await tracker.get_recommendation_stats()

        return stats

    except Exception as e:
        logger.error(f"Failed to get recommendation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/recommendations/{recommendation_id}/status")
async def update_recommendation_status(
    recommendation_id: UUID,
    request: UpdateStatusRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Update recommendation status.

    Valid statuses:
    - new, intro_requested, intro_made, contacted, responded, converted, declined
    """
    try:
        # Need company_id from the recommendation first
        # For now, just update directly
        from app.services.company_db import company_db

        result = await company_db.update_recommendation(
            recommendation_id=recommendation_id,
            status=request.status
        )

        if not result:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update recommendation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activate/pending/{company_id}")
async def get_pending_activation_requests(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Get all pending activation requests."""
    try:
        generator = ReverseReferenceGenerator(company_id)
        requests = await generator.get_pending_requests()

        return {
            "requests": requests,
            "count": len(requests)
        }

    except Exception as e:
        logger.error(f"Failed to get pending requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/activate/{request_id}/sent")
async def mark_activation_sent(
    request_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Mark an activation request as sent."""
    try:
        from app.services.company_db import company_db
        from datetime import datetime

        result = await company_db.update_activation_request(
            request_id=request_id,
            status="sent",
            sent_at=datetime.utcnow()
        )

        if not result:
            raise HTTPException(status_code=404, detail="Request not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark request as sent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/activate/{request_id}/responded")
async def mark_activation_responded(
    request_id: UUID,
    had_recommendation: bool = False,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Mark an activation request as responded to."""
    try:
        from app.services.company_db import company_db
        from datetime import datetime

        status = "responded_with_rec" if had_recommendation else "responded_no_rec"

        result = await company_db.update_activation_request(
            request_id=request_id,
            status=status,
            responded_at=datetime.utcnow()
        )

        if not result:
            raise HTTPException(status_code=404, detail="Request not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark request as responded: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MESSAGE GENERATION ENDPOINTS
# =============================================================================

class GenerateIntroMessageRequest(BaseModel):
    """Request to generate an intro request message."""
    recommender_name: str
    recommended_name: str
    recommended_context: str = None
    role_title: str = None
    sender_name: str = None


class GenerateReferralPostRequest(BaseModel):
    """Request to generate a referral post."""
    person_name: str
    person_title: str = None
    person_company: str = None
    role_title: str
    required_skills: list[str] = None
    company_name: str = None
    sender_name: str = None
    community_type: str = "slack"


@router.post("/messages/intro-request")
async def generate_intro_request_message(
    request: GenerateIntroMessageRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Generate a message to request an introduction."""
    generator = ActivationMessageGenerator()

    message = generator.generate_intro_request_message(
        recommender_name=request.recommender_name,
        recommended_name=request.recommended_name,
        recommended_context=request.recommended_context,
        role_title=request.role_title,
        sender_name=request.sender_name
    )

    return {"message": message}


@router.post("/messages/referral-post")
async def generate_referral_post(
    request: GenerateReferralPostRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Generate a request for someone to post in their community."""
    generator = ActivationMessageGenerator()

    person = {
        "full_name": request.person_name,
        "current_title": request.person_title,
        "current_company": request.person_company
    }

    result = generator.generate_referral_post_request(
        person=person,
        role_title=request.role_title,
        community_type=request.community_type,
        required_skills=request.required_skills,
        company_name=request.company_name,
        sender_name=request.sender_name
    )

    return result


# =============================================================================
# TIMING INTELLIGENCE ENDPOINTS (Pillar 2)
# =============================================================================

@router.get("/timing/alerts/{company_id}")
async def get_timing_alerts(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get timing-based alerts for the network.

    Identifies people with high readiness signals:
    - Approaching vesting cliff
    - At companies with recent layoffs
    - Title signals indicating availability
    - Recent profile updates

    Returns prioritized list of people to reach out to.
    """
    try:
        from app.intelligence.timing import ReadinessScorer

        scorer = ReadinessScorer(company_id)
        alerts = await scorer.get_timing_alerts()

        return {
            "alerts": alerts,
            "total_alerts": len(alerts)
        }

    except Exception as e:
        logger.error(f"Failed to get timing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timing/network-analysis/{company_id}")
async def analyze_network_readiness(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Analyze readiness across the entire network.

    Returns:
    - Total people scored
    - Breakdown by urgency (immediate, high, medium, low, wait)
    - Top candidates in each urgency category
    """
    try:
        from app.intelligence.timing import ReadinessScorer

        scorer = ReadinessScorer(company_id)
        analysis = await scorer.score_all_network()

        return analysis

    except Exception as e:
        logger.error(f"Failed to analyze network readiness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timing/tenure/{company_id}")
async def analyze_network_tenure(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Analyze tenure patterns across the network.

    Returns:
    - Tenure distribution (0-1, 1-2, 2-3, 3-4, 4-5, 5+ years)
    - People approaching 2-year milestone
    - People approaching 4-year vesting cliff
    """
    try:
        from app.intelligence.timing import TenureTracker

        tracker = TenureTracker(company_id)
        analysis = await tracker.analyze_network_tenure()

        return analysis

    except Exception as e:
        logger.error(f"Failed to analyze network tenure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timing/vesting-cliffs/{company_id}")
async def get_approaching_vesting_cliffs(
    company_id: UUID,
    days_ahead: int = 90,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Find people approaching their vesting cliff.

    Args:
        company_id: The company's network to analyze
        days_ahead: How many days ahead to look (default 90)

    Returns:
        List of people approaching their 4-year vesting cliff
        with recommended outreach timing.
    """
    try:
        from app.intelligence.timing import VestingPredictor

        predictor = VestingPredictor(company_id)
        approaching = await predictor.find_approaching_cliffs(days_ahead=days_ahead)

        return {
            "days_ahead": days_ahead,
            "total_approaching": len(approaching),
            "people": approaching
        }

    except Exception as e:
        logger.error(f"Failed to find approaching vesting cliffs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EXPANSION ENDPOINTS (Pillar 3)
# =============================================================================

@router.get("/expansion/summary/{company_id}")
async def get_expansion_summary(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get summary of expansion potential.

    Shows how many network members have employment history
    and the potential for finding former colleagues.
    """
    try:
        from app.intelligence.expansion import ColleagueExpander

        expander = ColleagueExpander(company_id)
        summary = await expander.get_expansion_summary()

        return summary

    except Exception as e:
        logger.error(f"Failed to get expansion summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ColleagueExpansionRequest(BaseModel):
    """Request for colleague expansion."""
    network_member_ids: list[UUID] = None
    role_filter: str = None
    min_overlap_months: int = 6
    limit: int = 100


@router.post("/expansion/colleagues/{company_id}")
async def find_former_colleagues(
    company_id: UUID,
    request: ColleagueExpansionRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Find former colleagues of network members.

    Returns people who worked at the same company during
    overlapping time periods (they actually know each other).

    Note: Requires employment history data (from PDL enrichment).
    """
    try:
        from app.intelligence.expansion import ColleagueExpander

        expander = ColleagueExpander(company_id)
        result = await expander.find_former_colleagues(
            network_member_ids=request.network_member_ids,
            role_filter=request.role_filter,
            min_overlap_months=request.min_overlap_months,
            limit=request.limit
        )

        return result

    except Exception as e:
        logger.error(f"Failed to find former colleagues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class FindPathsRequest(BaseModel):
    """Request to find warm paths to a candidate."""
    candidate_name: str = None
    candidate_linkedin: str = None
    candidate_company: str = None
    candidate_title: str = None
    employment_history: list[dict] = None
    education: list[dict] = None


@router.post("/expansion/warm-paths/{company_id}")
async def find_warm_paths(
    company_id: UUID,
    request: FindPathsRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Find all warm paths to a specific candidate.

    Provide candidate details and get back all possible
    warm introduction paths through the network:
    - Direct connection (already in network)
    - Former colleague (employment overlap)
    - School connection (education overlap)
    - Recommendation (someone recommended them)
    """
    try:
        from app.intelligence.expansion import WarmPathFinder

        finder = WarmPathFinder(company_id)

        candidate = {
            "full_name": request.candidate_name,
            "linkedin_url": request.candidate_linkedin,
            "current_company": request.candidate_company,
            "current_title": request.candidate_title,
            "employment_history": request.employment_history,
            "education": request.education
        }

        result = await finder.find_all_paths(candidate)

        return result

    except Exception as e:
        logger.error(f"Failed to find warm paths: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COMPANY INTELLIGENCE ENDPOINTS (Pillar 4)
# =============================================================================

@router.get("/company/watched/{company_id}")
async def get_watched_companies(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get companies being watched (where network members work).

    Returns list of companies sorted by number of network members,
    which indicates the potential impact of events at those companies.
    """
    try:
        from app.intelligence.company import CompanyEventMonitor

        monitor = CompanyEventMonitor(company_id)
        watched = await monitor.get_watched_companies()

        return watched

    except Exception as e:
        logger.error(f"Failed to get watched companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/layoffs/{company_id}")
async def get_layoff_exposure(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get network's exposure to companies with recent layoffs.

    Returns breakdown of how many network members are at
    companies that have had layoffs, with urgency levels.
    """
    try:
        from app.intelligence.company import LayoffTracker

        tracker = LayoffTracker(company_id)
        exposure = await tracker.get_network_layoff_exposure()

        return exposure

    except Exception as e:
        logger.error(f"Failed to get layoff exposure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/events/{company_id}")
async def get_company_events(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get all recent events affecting watched companies.

    Returns events grouped by type (layoffs, acquisitions, etc.)
    and sorted by network impact.
    """
    try:
        from app.intelligence.company import CompanyEventMonitor

        monitor = CompanyEventMonitor(company_id)
        events = await monitor.get_all_events()

        return events

    except Exception as e:
        logger.error(f"Failed to get company events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/alerts/{company_id}")
async def get_company_alerts(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get actionable alerts based on company intelligence.

    Prioritized list of actions based on:
    - Urgency (critical > high > medium > low)
    - Network impact (more people = higher priority)
    - Timing (recent events = higher priority)
    """
    try:
        from app.intelligence.company import AlertGenerator

        generator = AlertGenerator(company_id)
        alerts = await generator.generate_all_alerts()

        return alerts

    except Exception as e:
        logger.error(f"Failed to get company alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/digest/{company_id}")
async def get_daily_digest(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get daily digest of company intelligence.

    Summary of what's happening and what actions to take.
    """
    try:
        from app.intelligence.company import AlertGenerator

        generator = AlertGenerator(company_id)
        digest = await generator.get_daily_digest()

        return digest

    except Exception as e:
        logger.error(f"Failed to get daily digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/report/{company_id}/{company_name}")
async def get_company_report(
    company_id: UUID,
    company_name: str,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get intelligence report for a specific company.

    Includes:
    - Network members at the company
    - Recent events
    - Recommended actions
    """
    try:
        from app.intelligence.company import CompanyEventMonitor

        monitor = CompanyEventMonitor(company_id)
        report = await monitor.get_company_intelligence_report(company_name)

        return report

    except Exception as e:
        logger.error(f"Failed to get company report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ScorePersonRequest(BaseModel):
    """Request to score readiness for a specific person."""
    person_id: UUID = None
    person_data: dict = None  # Alternatively, pass person data directly


@router.post("/timing/score-person/{company_id}")
async def score_person_readiness(
    company_id: UUID,
    request: ScorePersonRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Score readiness for a specific person.

    Can either:
    - Pass person_id to look up from database
    - Pass person_data directly for scoring

    Returns detailed readiness breakdown.
    """
    try:
        from app.intelligence.timing import ReadinessScorer
        from app.services.company_db import company_db

        scorer = ReadinessScorer(company_id)

        # Get person data
        if request.person_id:
            person = await company_db.get_person(company_id, request.person_id)
            if not person:
                raise HTTPException(status_code=404, detail="Person not found")
        elif request.person_data:
            person = request.person_data
        else:
            raise HTTPException(status_code=400, detail="Must provide person_id or person_data")

        # Score
        readiness = scorer.calculate_readiness_score(person)

        return {
            "person": {
                "id": str(request.person_id) if request.person_id else None,
                "name": person.get("full_name"),
                "title": person.get("current_title"),
                "company": person.get("current_company")
            },
            "readiness": readiness
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to score person readiness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COMBINED INTELLIGENCE SEARCH
# =============================================================================

class IntelligenceSearchRequest(BaseModel):
    """Request for full intelligence search."""
    company_id: Optional[UUID] = None
    role_title: str
    required_skills: list[str] = None
    locations: list[str] = None
    include_network_search: bool = True
    include_recruiters: bool = True
    include_activation_suggestions: bool = True
    network_limit: int = 50
    activation_limit: int = 20


@router.post("/search")
async def intelligence_search(
    request: IntelligenceSearchRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Full intelligence search combining all sources.

    Returns:
    - Tier 0: Existing recommendations from network
    - Tier 1: Direct network matches
    - Tier 2: Warm path candidates (via employment/school overlap)
    - Tier 3: Recruiters to ask
    - Activation suggestions: Who to ask for recommendations
    """
    try:
        request.company_id = UUID(auth.company_id)
        results = {
            "role": request.role_title,
            "tiers": {}
        }

        # Get existing recommendations (Tier 0)
        tracker = RecommendationTracker(request.company_id)
        recommendations = await tracker.get_recommendations(status="new")
        results["tiers"]["tier_0_recommendations"] = {
            "count": len(recommendations),
            "candidates": recommendations[:10],
            "description": "People recommended by your network"
        }

        # Network search (Tier 1)
        if request.include_network_search:
            from app.search.network_search import NetworkSearch
            network = NetworkSearch(request.company_id)
            network_matches = await network.search(
                role_title=request.role_title,
                required_skills=request.required_skills,
                locations=request.locations,
                limit=request.network_limit
            )
            results["tiers"]["tier_1_network"] = {
                "count": len(network_matches),
                "candidates": network_matches,
                "description": "People in your direct network"
            }

        # Warm paths (Tier 2) - calculated for network matches
        if request.include_network_search:
            from app.search.warm_path import WarmPathCalculator
            warm_calc = WarmPathCalculator(request.company_id)
            # Note: Warm paths are already calculated for network matches
            # This tier would be populated by expansion engine (Phase 3)
            results["tiers"]["tier_2_warm_paths"] = {
                "count": 0,
                "candidates": [],
                "description": "People reachable via warm intro (coming in Phase 3)"
            }

        # Recruiters (Tier 3)
        if request.include_recruiters:
            from app.search.recruiters import RecruiterFinder
            recruiter_finder = RecruiterFinder(request.company_id)
            recruiters = await recruiter_finder.find_recruiters()
            tech_recruiters = [r for r in recruiters if r.get("specialty") == "tech"]
            results["tiers"]["tier_3_recruiters"] = {
                "count": len(recruiters),
                "tech_recruiters": len(tech_recruiters),
                "candidates": recruiters[:10],
                "description": "Recruiters in your network who can refer candidates"
            }

        # Activation suggestions - who to ask for recommendations
        if request.include_activation_suggestions:
            generator = ReverseReferenceGenerator(request.company_id)
            activation_requests = await generator.generate_activation_requests(
                role_title=request.role_title,
                required_skills=request.required_skills,
                limit=request.activation_limit
            )
            results["activation_suggestions"] = {
                "count": len(activation_requests),
                "top_asks": [
                    {
                        "name": r.get("target_name"),
                        "title": r.get("target_title"),
                        "company": r.get("target_company"),
                        "reason": r.get("ask_reason"),
                        "message_preview": r.get("message_content", "")[:200] + "..."
                    }
                    for r in activation_requests[:5]
                ],
                "description": "People to ask 'Who would you recommend?'"
            }

        # Summary
        total_candidates = sum(
            tier.get("count", 0)
            for tier in results["tiers"].values()
        )
        results["summary"] = {
            "total_candidates": total_candidates,
            "highest_signal_action": _get_highest_signal_action(results)
        }

        return results

    except Exception as e:
        logger.error(f"Intelligence search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_highest_signal_action(results: dict) -> str:
    """Determine the highest-signal next action."""
    tiers = results.get("tiers", {})

    # If we have recommendations, use them
    if tiers.get("tier_0_recommendations", {}).get("count", 0) > 0:
        return "Follow up on existing recommendations"

    # If we have network matches, reach out
    if tiers.get("tier_1_network", {}).get("count", 0) > 0:
        return "Message top network matches directly"

    # If we have recruiters, ask them
    if tiers.get("tier_3_recruiters", {}).get("count", 0) > 0:
        return "Ask recruiters in your network for referrals"

    # Default: activate network
    return "Send 'who would you recommend?' asks to network"


# Make the helper function accessible
router._get_highest_signal_action = _get_highest_signal_action
