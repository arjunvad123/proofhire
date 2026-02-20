"""
Search API endpoints.

Network-driven people search powered by your connections.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import CompanyAuth, get_current_company
from app.search.engine import SearchEngine
from app.search.models import SearchTarget

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """Request body for search endpoint."""
    role_title: str
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None
    target_companies: list[str] = []
    target_schools: list[str] = []
    preferred_backgrounds: list[str] = []
    anti_patterns: list[str] = []
    locations: list[str] = []
    max_results: int = 50


class CandidateResponse(BaseModel):
    """Candidate in search results."""
    full_name: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    location: Optional[str] = None

    # Scores
    final_score: float
    source_quality_score: float
    network_proximity_score: float
    role_match_score: float

    # Network info
    in_network: bool = False
    pathway_hops: int = 99

    # How we found them
    sources: list[str] = []


class SearchResponse(BaseModel):
    """Response from search endpoint."""
    candidates: list[CandidateResponse]
    total_found: int
    deduplicated_count: int
    pathways_explored: int
    queries_executed: int
    duration_seconds: float
    results_by_source: dict[str, int]


@router.post("/companies/{company_id}/search", response_model=SearchResponse)
async def search_candidates(
    company_id: UUID,
    request: SearchRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Search for candidates using the company's network as pathways.

    This is the main search endpoint. It:
    1. Analyzes your network for high-value gateway nodes
    2. Generates targeted queries for each API (PDL, Google, GitHub, Perplexity)
    3. Executes searches in parallel
    4. Deduplicates and ranks results by relevance + trust
    """
    logger.info(f"Search request for company {company_id}: {request.role_title}")

    try:
        # Create search target
        target = SearchTarget(
            role_title=request.role_title,
            required_skills=request.required_skills,
            preferred_skills=request.preferred_skills,
            experience_years_min=request.experience_years_min,
            experience_years_max=request.experience_years_max,
            target_companies=request.target_companies,
            target_schools=request.target_schools,
            preferred_backgrounds=request.preferred_backgrounds,
            anti_patterns=request.anti_patterns,
            locations=request.locations,
            max_results=request.max_results,
        )

        # Create engine and search
        engine = SearchEngine(company_id)
        results = await engine.search(target)

        # Convert to response format
        candidates = []
        for c in results.candidates:
            candidates.append(CandidateResponse(
                full_name=c.full_name,
                email=c.email,
                linkedin_url=c.linkedin_url,
                github_url=c.github_url,
                current_company=c.current_company,
                current_title=c.current_title,
                location=c.location,
                final_score=round(c.final_score, 3),
                source_quality_score=round(c.source_quality_score, 3),
                network_proximity_score=round(c.network_proximity_score, 3),
                role_match_score=round(c.role_match_score, 3),
                in_network=c.in_network,
                pathway_hops=c.pathway_hops,
                sources=[s.api for s in c.sources],
            ))

        return SearchResponse(
            candidates=candidates,
            total_found=results.total_raw_results,
            deduplicated_count=results.deduplicated_count,
            pathways_explored=results.pathways_explored,
            queries_executed=results.queries_executed,
            duration_seconds=round(results.duration_seconds, 2),
            results_by_source=results.results_by_source,
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/{company_id}/search/explain")
async def explain_search(
    company_id: UUID,
    role_title: str = Query(..., description="Role to search for"),
    required_skills: str = Query("", description="Comma-separated skills"),
    preferred_backgrounds: str = Query("", description="Comma-separated backgrounds"),
    top_k: int = Query(10, description="Number of pathways to explain"),
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Explain how a search would work without executing it.

    Returns the top pathways that would be used, with sample queries.
    Useful for understanding the search strategy before running it.
    """
    logger.info(f"Explain search for company {company_id}: {role_title}")

    try:
        # Parse comma-separated values
        skills = [s.strip() for s in required_skills.split(",") if s.strip()]
        backgrounds = [b.strip() for b in preferred_backgrounds.split(",") if b.strip()]

        target = SearchTarget(
            role_title=role_title,
            required_skills=skills,
            preferred_backgrounds=backgrounds,
        )

        engine = SearchEngine(company_id)
        explanations = await engine.explain_search(target, top_k=top_k)

        return {
            "target": {
                "role_title": role_title,
                "required_skills": skills,
                "preferred_backgrounds": backgrounds,
            },
            "pathways": explanations,
            "sources_configured": [s.name for s in engine.sources],
        }

    except Exception as e:
        logger.error(f"Explain search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/{company_id}/network/stats")
async def get_network_stats(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get statistics about the company's network.

    Shows:
    - Total nodes and their types (founders, VCs, engineers, etc.)
    - Access patterns available
    - Top companies represented
    - Estimated total reach
    """
    logger.info(f"Network stats for company {company_id}")

    try:
        engine = SearchEngine(company_id)
        stats = await engine.get_network_stats()

        return {
            "company_id": str(company_id),
            "network": stats,
        }

    except Exception as e:
        logger.error(f"Network stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/{company_id}/network/gateways")
async def get_top_gateways(
    company_id: UUID,
    n: int = Query(20, description="Number of gateways to return"),
    node_type: Optional[str] = Query(None, description="Filter by node type"),
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Get the top gateway nodes in the network.

    These are the people with the highest potential to connect
    you to relevant candidates based on their role and reach.
    """
    logger.info(f"Top gateways for company {company_id}")

    try:
        from app.search.analyzers.network import NetworkAnalyzer
        from app.search.models import NodeType

        analyzer = NetworkAnalyzer(company_id)

        # Parse node type filter
        node_types = None
        if node_type:
            try:
                node_types = [NodeType(node_type)]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid node_type: {node_type}"
                )

        gateways = await analyzer.get_top_gateways(n=n, node_types=node_types)

        return {
            "company_id": str(company_id),
            "gateways": [
                {
                    "person_id": str(g.person_id),
                    "full_name": g.full_name,
                    "company": g.company,
                    "title": g.title,
                    "node_type": g.node_type.value,
                    "access_patterns": [p.value for p in g.access_patterns],
                    "estimated_reach": g.estimated_reach,
                    "seniority_score": round(g.seniority_score, 2),
                    "linkedin_url": g.linkedin_url,
                }
                for g in gateways
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Top gateways failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
