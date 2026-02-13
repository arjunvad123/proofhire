"""
V3 Hybrid Search API

Combines network search with external people databases (Clado/PDL)
and adds warm path intelligence.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.search_orchestrator import search_orchestrator, HybridSearchResult
from app.services.network_index import network_index_service
from app.services.warm_path_finder import warm_path_finder, CandidateWithWarmth


router = APIRouter(prefix="/v3/search", tags=["search-v3"])


class HybridSearchRequest(BaseModel):
    """Request for hybrid search."""

    company_id: str
    role_title: str
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    location: Optional[str] = None
    years_experience: Optional[int] = None
    limit: int = 20


class CandidateResponse(BaseModel):
    """Simplified candidate for API response."""

    id: str
    full_name: str
    headline: Optional[str]
    location: Optional[str]
    current_title: Optional[str]
    current_company: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]

    # Scores
    match_score: float
    warmth_score: float
    combined_score: float

    # Warm path info
    is_in_network: bool
    warm_path_type: Optional[str]
    warm_path_connector: Optional[str]
    warm_path_relationship: Optional[str]
    intro_message: Optional[str]


class TierResponse(BaseModel):
    """Response for one search tier."""

    tier_name: str
    tier_number: int
    count: int
    candidates: list[CandidateResponse]


class HybridSearchResponse(BaseModel):
    """Full hybrid search response."""

    role_title: str
    query_used: str
    total_candidates: int

    # Network stats
    network_size: int
    unique_companies: int
    unique_schools: int

    # Results by tier
    tier_1_network: TierResponse
    tier_2_warm: TierResponse
    tier_3_cold: TierResponse

    # Combined shortlist
    shortlist: list[CandidateResponse]


def _to_candidate_response(c: CandidateWithWarmth) -> CandidateResponse:
    """Convert internal model to API response."""
    return CandidateResponse(
        id=c.id,
        full_name=c.full_name,
        headline=c.headline,
        location=c.location,
        current_title=c.current_title,
        current_company=c.current_company,
        linkedin_url=c.linkedin_url,
        github_url=c.github_url,
        match_score=c.match_score,
        warmth_score=c.warmth_score,
        combined_score=c.combined_score,
        is_in_network=c.is_in_network,
        warm_path_type=c.best_path.path_type if c.best_path else None,
        warm_path_connector=c.best_path.connector.full_name if c.best_path else None,
        warm_path_relationship=c.best_path.relationship if c.best_path else None,
        intro_message=c.best_path.suggested_message if c.best_path else None
    )


@router.post("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """
    Execute hybrid search across network + external databases.

    Returns candidates from:
    - Tier 1: Direct network (warmth = 1.0)
    - Tier 2: External with warm paths (warmth = 0.3-0.8)
    - Tier 3: External cold (warmth = 0.0)

    Each candidate includes warm path information when available.
    """
    try:
        result = await search_orchestrator.search(
            company_id=request.company_id,
            role_title=request.role_title,
            required_skills=request.required_skills,
            preferred_skills=request.preferred_skills,
            location=request.location,
            years_experience=request.years_experience,
            limit=request.limit
        )

        return HybridSearchResponse(
            role_title=result.role_title,
            query_used=result.query_used,
            total_candidates=result.total_candidates,
            network_size=result.network_stats['total_contacts'],
            unique_companies=result.network_stats['unique_companies'],
            unique_schools=result.network_stats['unique_schools'],
            tier_1_network=TierResponse(
                tier_name=result.tier_1_network.tier_name,
                tier_number=1,
                count=result.tier_1_network.count,
                candidates=[_to_candidate_response(c) for c in result.tier_1_network.candidates[:10]]
            ),
            tier_2_warm=TierResponse(
                tier_name=result.tier_2_warm.tier_name,
                tier_number=2,
                count=result.tier_2_warm.count,
                candidates=[_to_candidate_response(c) for c in result.tier_2_warm.candidates[:10]]
            ),
            tier_3_cold=TierResponse(
                tier_name=result.tier_3_cold.tier_name,
                tier_number=3,
                count=result.tier_3_cold.count,
                candidates=[_to_candidate_response(c) for c in result.tier_3_cold.candidates[:10]]
            ),
            shortlist=[_to_candidate_response(c) for c in result.shortlist]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network-index/{company_id}")
async def get_network_index(company_id: str):
    """
    Get the network index for a company.

    Returns statistics about the network:
    - Total contacts
    - Unique companies (with counts)
    - Unique schools (with counts)
    - Top companies and schools
    """
    try:
        index = await network_index_service.build_index(company_id)
        stats = network_index_service.get_network_stats(index)

        return {
            "company_id": company_id,
            "total_contacts": stats['total_contacts'],
            "unique_companies": stats['unique_companies'],
            "unique_schools": stats['unique_schools'],
            "unique_skills": stats['unique_skills'],
            "top_companies": stats['top_companies'],
            "top_schools": stats['top_schools'],
            "indexed": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warm-paths/{company_id}")
async def find_warm_paths_for_linkedin(
    company_id: str,
    linkedin_urls: list[str]
):
    """
    Find warm paths for specific LinkedIn profiles.

    Useful when you have candidate profiles and want to
    check if there are warm intro paths in the network.
    """
    try:
        from app.services.external_search.clado_client import clado_client

        index = await network_index_service.build_index(company_id)
        results = []

        for url in linkedin_urls[:10]:  # Limit to 10
            # Enrich via Clado
            profile = await clado_client.enrich_profile(url)
            if profile:
                with_warmth = await warm_path_finder.find_warm_paths(profile, index)
                results.append(_to_candidate_response(with_warmth))
            else:
                results.append({
                    "linkedin_url": url,
                    "error": "Could not enrich profile"
                })

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
