"""
Unified Search API

ONE endpoint that does everything:
- Network search
- External search (Clado/PDL)
- Warm path finding
- Timing intelligence
- Deep research

Replaces: /v1/curation, /v2/search, /v3/search, /v3/intelligence
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.unified_search import unified_search, SearchResult, Candidate


router = APIRouter(prefix="/search", tags=["unified-search"])


# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================

class SearchRequest(BaseModel):
    """Unified search request."""

    company_id: str
    role_title: str
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    location: Optional[str] = None
    years_experience: Optional[int] = None

    # Feature flags (all ON by default)
    include_external: bool = True      # Search beyond network
    include_timing: bool = True        # Add timing/urgency signals
    deep_research: bool = True         # Research top candidates

    limit: int = 20


class CandidateResponse(BaseModel):
    """Simplified candidate for API response."""

    id: str
    full_name: str
    current_title: Optional[str]
    current_company: Optional[str]
    location: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]

    # Scores (0-100)
    fit_score: float
    warmth_score: float
    timing_score: float
    combined_score: float

    # Classification
    tier: int                           # 1=network, 2=warm, 3=cold
    tier_label: str                     # "Network", "Warm Intro", "Cold"
    source: str                         # "network" or "external"
    timing_urgency: str                 # "high", "medium", "low"

    # Warm path (if exists)
    has_warm_path: bool
    warm_path_type: Optional[str]       # "company_overlap", "school_overlap"
    warm_path_connector: Optional[str]  # Name of connector
    warm_path_relationship: Optional[str]
    intro_message: Optional[str]

    # Context
    why_consider: list[str]
    unknowns: list[str]
    research_highlights: list[str]


class SearchResponse(BaseModel):
    """Unified search response."""

    # Query info
    role_title: str
    query_used: str
    search_duration_seconds: float

    # Network stats
    network_size: int
    network_companies: int

    # Summary
    total_found: int
    tier_1_network: int
    tier_2_warm: int
    tier_3_cold: int
    high_urgency: int

    # Features used
    external_enabled: bool
    timing_enabled: bool
    research_enabled: bool
    deep_researched: int

    # Results
    candidates: list[CandidateResponse]


def _to_response(c: Candidate) -> CandidateResponse:
    """Convert internal Candidate to API response."""

    tier_labels = {1: "Network", 2: "Warm Intro", 3: "Cold"}

    return CandidateResponse(
        id=c.id,
        full_name=c.full_name,
        current_title=c.current_title,
        current_company=c.current_company,
        location=c.location,
        linkedin_url=c.linkedin_url,
        github_url=c.github_url,
        fit_score=round(c.fit_score, 1),
        warmth_score=round(c.warmth_score, 1),
        timing_score=round(c.timing_score, 1),
        combined_score=round(c.combined_score, 1),
        tier=c.tier,
        tier_label=tier_labels.get(c.tier, "Unknown"),
        source=c.source,
        timing_urgency=c.timing_urgency,
        has_warm_path=c.warm_path is not None,
        warm_path_type=c.warm_path.path_type if c.warm_path else None,
        warm_path_connector=c.warm_path.connector.full_name if c.warm_path else None,
        warm_path_relationship=c.warm_path.relationship if c.warm_path else None,
        intro_message=c.intro_message,
        why_consider=c.why_consider,
        unknowns=c.unknowns,
        research_highlights=c.research_highlights
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    🔍 UNIFIED SEARCH

    One endpoint that does everything:
    - Searches your network (Tier 1)
    - Searches external databases with warm path finding (Tier 2-3)
    - Adds timing/urgency signals
    - Deep researches top candidates

    All features ON by default. Disable with flags:
    - include_external: false  → Network only
    - include_timing: false    → Skip timing signals
    - deep_research: false     → Skip Perplexity research

    Returns candidates ranked by: fit (50%) + warmth (30%) + timing (20%)
    """
    try:
        result = await unified_search.search(
            company_id=request.company_id,
            role_title=request.role_title,
            required_skills=request.required_skills,
            preferred_skills=request.preferred_skills,
            location=request.location,
            years_experience=request.years_experience,
            include_external=request.include_external,
            include_timing=request.include_timing,
            deep_research=request.deep_research,
            limit=request.limit
        )

        return SearchResponse(
            role_title=result.role_title,
            query_used=result.query_used,
            search_duration_seconds=result.search_duration_seconds,
            network_size=result.network_size,
            network_companies=result.network_companies,
            total_found=result.total_found,
            tier_1_network=result.tier_1_count,
            tier_2_warm=result.tier_2_count,
            tier_3_cold=result.tier_3_count,
            high_urgency=result.high_urgency_count,
            external_enabled=request.include_external,
            timing_enabled=result.timing_enabled,
            research_enabled=result.research_enabled,
            deep_researched=result.deep_researched_count,
            candidates=[_to_response(c) for c in result.candidates]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/network-only", response_model=SearchResponse)
async def search_network_only(request: SearchRequest):
    """
    Search ONLY the founder's network.
    Equivalent to: include_external=false, include_timing=true, deep_research=true
    """
    request.include_external = False
    return await search(request)


@router.post("/quick", response_model=SearchResponse)
async def quick_search(request: SearchRequest):
    """
    Quick search - network + external, no research.
    Faster but less detailed.
    """
    request.deep_research = False
    return await search(request)


@router.get("/health")
async def health():
    """Check search service health."""
    return {
        "status": "healthy",
        "unified_search": True,
        "features": {
            "network_search": True,
            "external_search": True,
            "warm_path_finding": True,
            "timing_intelligence": True,
            "deep_research": bool(settings.perplexity_api_key)
        }
    }


# Import settings for health check
from app.config import settings
