"""
API endpoints for candidate curation.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.models.curation import (
    CurationRequest,
    CurationResponse,
    CuratedCandidate,
    AISummary,
    RegenerateSummaryResponse
)
from app.services.curation_engine import CandidateCurationEngine
from app.core.database import get_supabase_client

router = APIRouter(prefix="/v1/curation", tags=["curation"])


def get_curation_engine():
    """Dependency to get curation engine."""
    supabase = get_supabase_client()
    return CandidateCurationEngine(supabase)


@router.post("/curate", response_model=CurationResponse)
async def curate_candidates(
    request: CurationRequest,
    engine: CandidateCurationEngine = Depends(get_curation_engine)
):
    """
    Curate shortlist of candidates for a role.

    This is the main endpoint that:
    1. Searches all network connections
    2. Ranks by fit to role
    3. Enriches top candidates on-demand
    4. Returns shortlist with rich context

    Request:
    ```json
    {
        "company_id": "uuid-...",
        "role_id": "uuid-...",
        "limit": 15
    }
    ```

    Response:
    ```json
    {
        "shortlist": [
            {
                "person_id": "uuid-...",
                "full_name": "Maya Patel",
                "match_score": 87,
                "context": {
                    "why_consider": [...],
                    "unknowns": [...],
                    "warm_path": "Direct LinkedIn connection"
                }
            }
        ],
        "total_searched": 305,
        "metadata": {
            "avg_match_score": 72,
            "enriched_count": 8
        }
    }
    ```
    """

    import time
    start_time = time.time()
    try:
        # Run curation
        shortlist = await engine.curate(
            company_id=request.company_id,
            role_id=request.role_id,
            limit=request.limit
        )

        processing_time = time.time() - start_time

        # Calculate metadata
        avg_score = sum(c.match_score for c in shortlist) / len(shortlist) if shortlist else 0
        enriched_count = sum(1 for c in shortlist if c.was_enriched)

        # Get total network size
        supabase = get_supabase_client()
        network_response = supabase.table('people')\
            .select('id', count='exact')\
            .eq('company_id', request.company_id)\
            .execute()

        total_searched = network_response.count or 0

        return CurationResponse(
            shortlist=shortlist,
            total_searched=total_searched,
            processing_time_seconds=round(processing_time, 2),
            metadata={
                'avg_match_score': round(avg_score, 1),
                'enriched_count': enriched_count,
                'avg_confidence': round(
                    sum(c.fit_confidence for c in shortlist) / len(shortlist) if shortlist else 0,
                    2
                ),
                'completeness': {
                    'high': sum(1 for c in shortlist if c.data_completeness >= 0.7),
                    'medium': sum(1 for c in shortlist if 0.3 <= c.data_completeness < 0.7),
                    'low': sum(1 for c in shortlist if c.data_completeness < 0.3)
                }
            }
        )


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Curation failed: {str(e)}")


@router.get("/candidate/{person_id}/context")
async def get_candidate_context(
    person_id: str,
    role_id: str,
    engine: CandidateCurationEngine = Depends(get_curation_engine)
):
    """
    Get detailed context for a specific candidate.

    Useful for "deep dive" when founder clicks on a candidate.
    """

    try:
        # Build candidate
        from app.services.candidate_builder import CandidateBuilder
        supabase = get_supabase_client()
        builder = CandidateBuilder(supabase)

        candidate = await builder.build(person_id)

        # Get role and company context
        role = await engine._get_role(role_id)
        company_dna = await engine._get_company_dna(role['company_id'])
        umo = await engine._get_umo(role['company_id'])

        # Build context
        context = await engine._build_context(candidate, role, company_dna, umo)

        # Calculate fit
        fit = engine._calculate_fit(candidate, role, company_dna, umo)

        return {
            'person_id': person_id,
            'full_name': candidate.full_name,
            'match_score': fit.score,
            'fit_confidence': fit.confidence,
            'context': context.dict(),
            'candidate_data': {
                'headline': candidate.headline,
                'location': candidate.location,
                'current_company': candidate.current_company,
                'current_title': candidate.current_title,
                'linkedin_url': candidate.linkedin_url,
                'github_url': candidate.github_url,
                'data_completeness': candidate.data_completeness
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@router.post("/candidate/{person_id}/feedback")
async def record_founder_feedback(
    person_id: str,
    role_id: str,
    decision: str,  # "interview", "pass", "need_more_info"
    notes: Optional[str] = None
):
    """
    Record founder's decision on a candidate.

    This helps improve future curation.
    """

    supabase = get_supabase_client()

    update_data = {
        "updated_at": "now()"
    }

    if decision == "interview":
        update_data["pipeline_status"] = "sourced"
    elif decision == "pass":
        update_data["pipeline_status"] = None # Remove from pipeline if passed

    # Update candidate status in people table
    try:
        supabase.table("people").update(update_data).eq("id", person_id).execute()
    except Exception as e:
        print(f"Failed to update candidate status: {e}")

    # TODO: Store detailed feedback for RL learning
    # result = supabase.table("feedback_actions").insert({ ... }).execute()

    return {
        'status': 'recorded',
        'person_id': person_id,
        'role_id': role_id,
        'decision': decision
    }


@router.post("/candidate/{person_id}/regenerate-summary", response_model=RegenerateSummaryResponse)
async def regenerate_ai_summary(
    person_id: str,
    role_id: str,
    engine: CandidateCurationEngine = Depends(get_curation_engine)
):
    """
    Regenerate AI summary for a candidate without re-enriching.

    Uses existing candidate data and Claude AI to generate a fresh
    narrative summary. Does NOT re-enrich via PDL or other sources.

    Example use case: Nikhil Hooda's summary shows rules-based template,
    but you want a more natural AI-generated narrative.
    """

    try:
        # Build candidate from existing data
        from app.services.candidate_builder import CandidateBuilder
        supabase = get_supabase_client()
        builder = CandidateBuilder(supabase)
        candidate = await builder.build(person_id)

        # Get role and company context
        role = await engine._get_role(role_id)
        company_dna = await engine._get_company_dna(role['company_id'])

        # Use Claude to generate AI summary
        from app.services.reasoning.claude_engine import ClaudeReasoningEngine
        claude_engine = ClaudeReasoningEngine()

        # Prepare candidate data for Claude
        candidate_data = {
            'id': person_id,
            'full_name': candidate.full_name,
            'current_title': candidate.current_title,
            'current_company': candidate.current_company,
            'location': candidate.location,
            'headline': candidate.headline,
            'skills': candidate.skills,
            'experience': [exp for exp in (candidate.experience or [])],
            'education': [edu for edu in (candidate.education or [])]
        }

        # Get AI analysis
        analysis = await claude_engine.analyze_candidate(
            candidate=candidate_data,
            role_title=role['title'],
            required_skills=role.get('required_skills', []),
            company_context={
                'name': company_dna.get('company_name', ''),
                'stage': company_dna.get('stage', ''),
                'values': company_dna.get('values', [])
            }
        )

        # Extract the AI-generated summary components
        ai_summary = AISummary(
            overall_assessment=analysis.overall_assessment,
            why_consider=analysis.why_consider,
            concerns=analysis.concerns,
            unknowns=analysis.unknowns,
            skill_reasoning=analysis.skill_reasoning,
            trajectory_reasoning=analysis.trajectory_reasoning,
            fit_reasoning=analysis.fit_reasoning,
            timing_reasoning=analysis.timing_reasoning
        )

        # Optionally store in database for future use
        # You can add a new 'ai_summary' JSONB column to the people table
        # and store the generated summary there
        try:
            supabase.table("people").update({
                "ai_summary": ai_summary.dict(),
                "updated_at": "now()"
            }).eq("id", person_id).execute()
        except Exception as e:
            print(f"Warning: Could not store AI summary: {e}")
            # Continue even if storage fails

        return RegenerateSummaryResponse(
            status='success',
            person_id=person_id,
            full_name=candidate.full_name,
            ai_summary=ai_summary,
            message='AI summary regenerated successfully'
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate summary: {str(e)}"
        )
