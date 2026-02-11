"""
Search API V2 - Network-First Search Endpoints

These endpoints use the improved V2 search engine that actually
leverages the network for warm introductions.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.search.engine_v2 import SearchEngineV2, SearchResultsV2

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/search", tags=["search-v2"])


class SearchRequestV2(BaseModel):
    """Search request for V2 API."""
    company_id: UUID
    role_title: str
    required_skills: list[str] = []
    preferred_backgrounds: list[str] = []
    locations: list[str] = []
    max_results: int = 50
    include_cold: bool = True  # Whether to include Tier 4 results


class NetworkSummaryResponse(BaseModel):
    """Response for network summary endpoint."""
    network_stats: dict
    recruiter_summary: dict
    recommendations: list[str]


@router.post("", response_model=SearchResultsV2)
async def search_v2(request: SearchRequestV2):
    """
    Execute a network-first search.

    This endpoint searches in the following order:
    1. Tier 1: People in your network who match the role
    2. Tier 2: People reachable via warm introductions
    3. Tier 3: Recruiters in your network to contact
    4. Tier 4: External search results (cold)

    Returns tiered results with warmth scores and recommended actions.
    """
    try:
        engine = SearchEngineV2(request.company_id)

        results = await engine.search(
            role_title=request.role_title,
            required_skills=request.required_skills,
            preferred_backgrounds=request.preferred_backgrounds,
            locations=request.locations,
            max_results=request.max_results,
            include_cold=request.include_cold
        )

        return results

    except Exception as e:
        logger.error(f"V2 search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network-summary/{company_id}", response_model=NetworkSummaryResponse)
async def get_network_summary(company_id: UUID):
    """
    Get a summary of the company's network.

    Returns statistics about the network, recruiter info, and recommendations.
    """
    try:
        engine = SearchEngineV2(company_id)
        summary = await engine.get_network_summary()
        return NetworkSummaryResponse(**summary)

    except Exception as e:
        logger.error(f"Network summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/{company_id}")
async def search_network_only(
    company_id: UUID,
    role_title: str = Query(..., description="Role to search for"),
    skills: Optional[str] = Query(None, description="Comma-separated skills"),
    location: Optional[str] = Query(None, description="Location filter"),
    limit: int = Query(50, description="Max results")
):
    """
    Search only within the network (Tier 1).

    This is a faster search that only looks at direct connections.
    Use this when you want to see who in the network matches a role.
    """
    try:
        from app.search.network_search import NetworkSearch
        from app.search.readiness import ReadinessScorer

        network_search = NetworkSearch(company_id)
        readiness_scorer = ReadinessScorer()

        # Parse skills
        required_skills = [s.strip() for s in skills.split(",")] if skills else []
        locations = [location] if location else []

        # Search
        matches = await network_search.search(
            role_title=role_title,
            required_skills=required_skills,
            locations=locations,
            limit=limit
        )

        # Add readiness scores
        scored = readiness_scorer.batch_score(matches)

        # Sort by combined score
        for m in scored:
            m["combined_score"] = (
                m.get("match_score", 0) * 0.5 +
                m.get("readiness_score", 0) * 0.5
            )

        scored.sort(key=lambda x: x["combined_score"], reverse=True)

        return {
            "count": len(scored),
            "candidates": scored,
            "message": f"Found {len(scored)} matches in your network"
        }

    except Exception as e:
        logger.error(f"Network search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recruiters/{company_id}")
async def get_recruiters(
    company_id: UUID,
    specialty: Optional[str] = Query(None, description="Filter by specialty: tech, finance, sales, etc.")
):
    """
    Get recruiters in the network.

    Recruiters are the highest-signal contacts for finding candidates.
    One conversation with a recruiter can yield 5-10 qualified candidates.
    """
    try:
        from app.search.recruiters import RecruiterFinder

        finder = RecruiterFinder(company_id)
        recruiters = await finder.find_recruiters(specialty=specialty)
        summary = await finder.get_recruiter_summary()

        return {
            "count": len(recruiters),
            "recruiters": recruiters,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Recruiter search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warm-path")
async def find_warm_path(
    company_id: UUID,
    candidate_linkedin_url: Optional[str] = None,
    candidate_name: Optional[str] = None,
    candidate_company: Optional[str] = None
):
    """
    Find the warmest introduction path to a specific candidate.

    Provide either LinkedIn URL or name+company to identify the candidate.
    Returns the best path through your network to reach them.
    """
    try:
        from app.search.warm_path import WarmPathCalculator

        calculator = WarmPathCalculator(company_id)

        candidate = {
            "linkedin_url": candidate_linkedin_url,
            "full_name": candidate_name,
            "current_company": candidate_company
        }

        path = await calculator.find_warm_path(candidate)

        if path:
            return {
                "found": True,
                "path": path,
                "message": f"Warm path found via {path.get('via_person', {}).get('name', 'connection')}"
            }
        else:
            return {
                "found": False,
                "path": None,
                "message": "No warm path found. This would be a cold outreach."
            }

    except Exception as e:
        logger.error(f"Warm path search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{company_id}")
async def get_network_stats(company_id: UUID):
    """
    Get detailed statistics about the network.

    Returns breakdown by role type, companies, locations, etc.
    """
    try:
        from app.search.network_search import NetworkSearch

        network_search = NetworkSearch(company_id)
        stats = await network_search.get_network_stats()

        return stats

    except Exception as e:
        logger.error(f"Stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
