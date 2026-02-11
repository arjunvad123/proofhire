"""
Shortlist API routes.

Handles shortlist retrieval and candidate feedback.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.search_engine import SearchEngine
from app.models.blueprint import RoleBlueprint
from app.models.evaluation import Shortlist

router = APIRouter(prefix="/shortlists", tags=["shortlists"])

# In-memory storage for MVP
shortlists: dict[str, Shortlist] = {}

# Engine instance
search_engine = SearchEngine()


class SearchRequest(BaseModel):
    """Request to search for candidates."""

    blueprint: dict


class CandidateFeedback(BaseModel):
    """Feedback on a candidate."""

    candidate_id: str
    decision: str  # "interested", "pass", "hired"
    reason: str | None = None


class CandidateDisplayResponse(BaseModel):
    """Candidate formatted for display."""

    id: str
    name: str
    tagline: str
    known_facts: list[str]
    observed_signals: list[str]
    unknown: list[str]
    why_consider: str
    next_step: str


class ShortlistResponse(BaseModel):
    """Shortlist response for frontend."""

    id: str
    conversation_id: str
    candidates: list[CandidateDisplayResponse]
    sources_searched: list[str]
    total_searched: int


@router.post("/search", response_model=ShortlistResponse)
async def search_candidates(request: SearchRequest):
    """
    Search for candidates matching a blueprint.

    This is typically triggered after a conversation,
    but can be called directly with a blueprint.
    """
    try:
        blueprint = RoleBlueprint(**request.blueprint)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid blueprint: {e}")

    # Run search
    shortlist = await search_engine.search(blueprint, limit=5)

    # Generate ID and store
    import uuid
    shortlist_id = str(uuid.uuid4())

    # Format for response
    candidates = []
    for ec in shortlist.candidates:
        summary = ec.summary_for_display()
        candidates.append(CandidateDisplayResponse(
            id=ec.candidate.id or "",
            name=summary["name"],
            tagline=summary["tagline"],
            known_facts=summary["known_facts"],
            observed_signals=summary["observed_signals"],
            unknown=summary["unknown"],
            why_consider=summary["why_consider"],
            next_step=summary["next_step"],
        ))

    return ShortlistResponse(
        id=shortlist_id,
        conversation_id=shortlist.conversation_id,
        candidates=candidates,
        sources_searched=shortlist.search_sources,
        total_searched=shortlist.total_searched,
    )


@router.get("/{shortlist_id}", response_model=ShortlistResponse)
async def get_shortlist(shortlist_id: str):
    """Get a shortlist by ID."""
    shortlist = shortlists.get(shortlist_id)
    if not shortlist:
        raise HTTPException(status_code=404, detail="Shortlist not found")

    # Format for response (same as above)
    candidates = []
    for ec in shortlist.candidates:
        summary = ec.summary_for_display()
        candidates.append(CandidateDisplayResponse(
            id=ec.candidate.id or "",
            name=summary["name"],
            tagline=summary["tagline"],
            known_facts=summary["known_facts"],
            observed_signals=summary["observed_signals"],
            unknown=summary["unknown"],
            why_consider=summary["why_consider"],
            next_step=summary["next_step"],
        ))

    return ShortlistResponse(
        id=shortlist_id,
        conversation_id=shortlist.conversation_id,
        candidates=candidates,
        sources_searched=shortlist.search_sources,
        total_searched=shortlist.total_searched,
    )


@router.post("/{shortlist_id}/feedback")
async def submit_feedback(shortlist_id: str, feedback: CandidateFeedback):
    """
    Submit feedback on a candidate.

    This feedback is used to improve future rankings.
    """
    shortlist = shortlists.get(shortlist_id)
    if not shortlist:
        raise HTTPException(status_code=404, detail="Shortlist not found")

    # Validate decision
    valid_decisions = ["interested", "pass", "hired"]
    if feedback.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision. Must be one of: {valid_decisions}"
        )

    # TODO: Store feedback for learning
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"Feedback received: {feedback.candidate_id} -> {feedback.decision} "
        f"(reason: {feedback.reason})"
    )

    return {"status": "ok", "message": "Feedback recorded"}


@router.get("/demo/candidates")
async def get_demo_candidates():
    """
    Get top candidates for demo purposes.

    Returns the most impressive candidates with rich data.
    """
    from app.sources.network import NetworkSource

    source = NetworkSource()
    candidates = await source.get_demo_candidates(limit=5)

    results = []
    for c in candidates:
        results.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "school": c.school,
            "github_username": c.github_username,
            "github_url": c.github_url,
            "skills": c.skills[:10],  # Top 10 skills
            "github_repos": [
                {
                    "name": r.name,
                    "description": r.description,
                    "language": r.language,
                    "stars": r.stars,
                }
                for r in c.github_repos[:5]
            ],
        })

    return {"candidates": results, "count": len(results)}
