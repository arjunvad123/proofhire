"""
Master Orchestrator

The single entry point that combines ALL systems:
- V1-V5 Search Engines
- Intelligence Pillars (Activation, Timing, Expansion, Company)
- Kimi K2.5 Reasoning
- RL-based Ranking

This is the unified interface for the entire search/intelligence system.

Usage:
    from app.services.master_orchestrator import master_orchestrator

    result = await master_orchestrator.search(
        company_id="...",
        role_title="ML Engineer",
        required_skills=["Python", "PyTorch"],
        mode="full"  # or "quick" or "network_only"
    )
"""

import asyncio
import logging
import time
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

# Core search engines
from app.services.unified_search import unified_search, Candidate, SearchResult
from app.services.network_index import network_index_service

# Intelligence pillars (use the simple one from search for compatibility)
from app.search.readiness import ReadinessScorer
# These require company_id and are used asynchronously when needed:
# from app.intelligence.timing.readiness_scorer import ReadinessScorer as TimingReadinessScorer
# from app.intelligence.activation.reverse_reference import ReverseReferenceGenerator
# from app.intelligence.expansion.colleague_expander import ColleagueExpander
# from app.intelligence.company.event_monitor import CompanyEventMonitor

# Reasoning layer
from app.services.reasoning import kimi_engine

# RL layer
from app.services.rl import reward_model

# Feedback
from app.services.feedback import feedback_collector, FeedbackAction

# Prediction Layer
from app.services.prediction import prediction_engine

# Config
from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# RESULT MODELS
# =============================================================================

class IntelligenceSignals(BaseModel):
    """Signals from the intelligence layer."""
    # Timing
    high_urgency_candidates: int
    vesting_cliff_approaching: int
    layoff_exposure: int

    # Activation
    pending_recommendations: int
    network_asks_sent: int

    # Expansion
    former_colleagues_found: int

    # Company events
    active_alerts: int


class MasterSearchResult(BaseModel):
    """Complete result from master orchestrator."""
    # Core search results
    search_result: SearchResult

    # Intelligence signals
    intelligence: IntelligenceSignals

    # Reasoning
    reasoning_enabled: bool
    candidates_analyzed: int
    query_reasoning: Optional[dict] = None

    # RL
    rl_enabled: bool
    rl_adjusted: bool

    # Meta
    total_duration_seconds: float
    mode: str
    features_used: list[str]
    warnings: list[str] = []
    degraded: bool = False
    decision_confidence: str = "high"  # high | medium | low
    recommended_actions: list[str] = []


# =============================================================================
# MASTER ORCHESTRATOR
# =============================================================================

class MasterOrchestrator:
    """
    Unified orchestrator for all search and intelligence systems.

    Modes:
    - "full": All features (reasoning, intelligence, RL)
    - "quick": Fast search (no deep research, no reasoning)
    - "network_only": Only search the network
    - "intelligence": Intelligence signals only (no search)

    Architecture:
    ┌─────────────────────────────────────────────────┐
    │             Master Orchestrator                  │
    ├─────────────────────────────────────────────────┤
    │  ┌─────────────┐  ┌─────────────────────────┐  │
    │  │  Reasoning  │  │    Intelligence Layer   │  │
    │  │   (Kimi)    │  │  (4 Pillars)            │  │
    │  └─────────────┘  └─────────────────────────┘  │
    │          │                    │                 │
    │          ▼                    ▼                 │
    │  ┌─────────────────────────────────────────┐   │
    │  │           Unified Search (V5)           │   │
    │  │  (Network + External + Warm Paths)      │   │
    │  └─────────────────────────────────────────┘   │
    │          │                                      │
    │          ▼                                      │
    │  ┌─────────────────────────────────────────┐   │
    │  │           RL Ranking Layer              │   │
    │  │  (Reward Model Adjustment)              │   │
    │  └─────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────┘
    """

    def __init__(self):
        # Initialize intelligence components
        self.readiness_scorer = ReadinessScorer()

    async def get_health_status(self) -> dict:
        """Return orchestrator dependency health for ops checks."""
        provider_health = {
            "supabase_configured": bool(settings.supabase_url and settings.supabase_key),
            "anthropic_configured": bool(settings.anthropic_api_key),
            "perplexity_configured": bool(settings.perplexity_api_key),
            "clado_configured": bool(settings.clado_api_key),
            "pdl_configured": bool(settings.pdl_api_key),
        }
        return {
            "status": "ok" if provider_health["supabase_configured"] else "degraded",
            "reasoning_enabled": kimi_engine.enabled,
            "rl_enabled": reward_model.enabled,
            "providers": provider_health,
        }

    async def search(
        self,
        company_id: str,
        role_title: str,
        required_skills: list[str] = [],
        preferred_skills: list[str] = [],
        location: Optional[str] = None,
        years_experience: Optional[int] = None,
        mode: str = "full",  # "full", "quick", "network_only"
        include_external: Optional[bool] = None,
        include_timing: Optional[bool] = None,
        deep_research: Optional[bool] = None,
        limit: int = 20,
        user_id: Optional[str] = None,  # For feedback tracking
        role_id: Optional[str] = None
    ) -> MasterSearchResult:
        """
        Execute a master search with all systems integrated.

        Args:
            company_id: The hiring company
            role_title: Position to fill
            required_skills: Must-have skills
            preferred_skills: Nice-to-have skills
            location: Preferred location
            years_experience: Minimum years
            mode: Search mode ("full", "quick", "network_only")
            limit: Max candidates to return
            user_id: For tracking feedback
            role_id: For tracking feedback

        Returns:
            MasterSearchResult with candidates and intelligence
        """
        start_time = time.time()
        features_used = []

        print(f"\n{'='*60}")
        print(f"MASTER ORCHESTRATOR: {role_title}")
        print(f"Mode: {mode}")
        print(f"{'='*60}")
        warnings: list[str] = []
        degraded = False

        # Step 1: Query Reasoning (if enabled)
        query_reasoning = None
        if mode == "full" and kimi_engine.enabled:
            print("\n1. Query Reasoning (Kimi K2.5)...")
            features_used.append("kimi_reasoning")

            # Build network index first for context
            network_index = await network_index_service.build_index(company_id)
            network_stats = network_index_service.get_network_stats(network_index)

            reasoning = await kimi_engine.reason_about_queries(
                role_title=role_title,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                location=location,
                network_companies=network_stats.get("top_companies", []),
                network_schools=network_stats.get("top_schools", [])
            )

            query_reasoning = reasoning.model_dump()
            print(f"   Primary query: {reasoning.primary_query}")
        else:
            print("\n1. Query Reasoning: Skipped")

        # Step 2: Execute Unified Search
        print("\n2. Unified Search (V5)...")
        features_used.append("unified_search")

        search_result = await unified_search.search(
            company_id=company_id,
            role_title=role_title,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            location=location,
            years_experience=years_experience,
            include_external=(mode != "network_only") if include_external is None else include_external,
            include_timing=(mode in ["full", "quick"]) if include_timing is None else include_timing,
            deep_research=(mode == "full") if deep_research is None else deep_research,
            limit=limit * 2  # Get extra for RL filtering
        )

        print(f"   Found {search_result.total_found} candidates")
        if include_external is not False and not search_result.external_yield_ok:
            degraded = True
            warnings.extend(search_result.external_diagnostics)
            warnings.append(
                "External providers produced no candidates; rankings are currently network-dominant."
            )

        # Step 3: Gather Intelligence Signals
        print("\n3. Intelligence Signals...")
        features_used.append("intelligence")

        intelligence = await self._gather_intelligence(
            company_id=company_id,
            candidates=[c.model_dump() for c in search_result.candidates]
        )

        print(f"   High urgency: {intelligence.high_urgency_candidates}")
        print(f"   Vesting cliffs: {intelligence.vesting_cliff_approaching}")

        # Step 4: Candidate Analysis with Kimi (for top candidates in full mode)
        candidates_analyzed = 0
        if mode == "full" and kimi_engine.enabled:
            print("\n4. Candidate Analysis (Kimi Agent Swarm)...")
            features_used.append("kimi_analysis")

            # Analyze top 10 candidates
            top_candidates = search_result.candidates[:10]

            for i, candidate in enumerate(top_candidates):
                analysis = await kimi_engine.analyze_candidate(
                    candidate=candidate.model_dump(),
                    role_title=role_title,
                    required_skills=required_skills
                )

                # Update candidate with analysis
                candidate.why_consider = analysis.why_consider
                candidate.unknowns = analysis.unknowns
                candidate.confidence = analysis.confidence

                candidates_analyzed += 1

            print(f"   Analyzed {candidates_analyzed} candidates")
        else:
            print("\n4. Candidate Analysis: Skipped")

        # Step 5: RL Ranking Adjustment
        rl_adjusted = False
        if reward_model.enabled and mode in ["full", "quick"]:
            print("\n5. RL Ranking Adjustment...")
            features_used.append("rl_ranking")

            candidates_dicts = [c.model_dump() for c in search_result.candidates]

            adjusted = reward_model.adjust_ranking(
                candidates=candidates_dicts,
                context={
                    "company_id": company_id,
                    "role_title": role_title,
                    "role_id": role_id
                }
            )

            # Convert back to Candidate objects
            search_result.candidates = [
                Candidate(**c) for c in adjusted[:limit]
            ]

            rl_adjusted = True
            print(f"   Rankings adjusted by reward model")
        else:
            print("\n5. RL Ranking: Skipped")
            # Still limit results
            search_result.candidates = search_result.candidates[:limit]

        # Step 6: Record view feedback (if user_id provided)
        if user_id:
            print("\n6. Recording Feedback...")
            features_used.append("feedback")

            for candidate in search_result.candidates[:5]:
                await feedback_collector.record_action(
                    user_id=user_id,
                    company_id=company_id,
                    candidate_id=candidate.id,
                    action=FeedbackAction.VIEWED,
                    role_id=role_id,
                    fit_score=candidate.fit_score,
                    warmth_score=candidate.warmth_score,
                    timing_score=candidate.timing_score,
                    combined_score=candidate.combined_score
                )

        duration = time.time() - start_time

        print(f"\n{'='*60}")
        print(f"DONE in {duration:.1f}s")
        print(f"Features: {', '.join(features_used)}")
        print(f"{'='*60}\n")

        if warnings:
            logger.warning("Master orchestrator warnings: %s", warnings)

        decision_confidence = "high"
        if degraded and len(search_result.candidates) < max(5, limit // 2):
            decision_confidence = "low"
        elif degraded:
            decision_confidence = "medium"

        recommended_actions: list[str] = []
        if degraded:
            recommended_actions.extend(
                [
                    "Prioritize Tier 1 network candidates for immediate outreach while external yield recovers.",
                    "Broaden role query terms (titles + adjacent skills) and re-run search in quick mode.",
                    "Re-run external search after provider budget/credits reset or limits are increased.",
                ]
            )
            if search_result.tier_2_count == 0:
                recommended_actions.append(
                    "Trigger warm-path generation from top network companies/schools to create Tier 2 options."
                )
        else:
            recommended_actions.append(
                "Proceed with top ranked candidates and log feedback actions to improve ranking quality."
            )

        return MasterSearchResult(
            search_result=search_result,
            intelligence=intelligence,
            reasoning_enabled=kimi_engine.enabled,
            candidates_analyzed=candidates_analyzed,
            query_reasoning=query_reasoning,
            rl_enabled=reward_model.enabled,
            rl_adjusted=rl_adjusted,
            total_duration_seconds=round(duration, 2),
            mode=mode,
            features_used=features_used,
            warnings=warnings,
            degraded=degraded,
            decision_confidence=decision_confidence,
            recommended_actions=recommended_actions,
        )

    async def _gather_intelligence(
        self,
        company_id: str,
        candidates: list[dict]
    ) -> IntelligenceSignals:
        """Gather intelligence signals from all pillars."""
        # Timing intelligence
        high_urgency = 0
        vesting_cliff = 0
        layoff_exposure = 0

        for candidate in candidates:
            if candidate.get("timing_urgency") == "high":
                high_urgency += 1

            signals = candidate.get("timing_signals", [])
            if "vesting_cliff" in signals or "long_tenure" in signals:
                vesting_cliff += 1
            if "layoff_exposure" in signals:
                layoff_exposure += 1

        return IntelligenceSignals(
            high_urgency_candidates=high_urgency,
            vesting_cliff_approaching=vesting_cliff,
            layoff_exposure=layoff_exposure,
            pending_recommendations=0,  # TODO: Implement
            network_asks_sent=0,  # TODO: Implement
            former_colleagues_found=0,  # TODO: Implement
            active_alerts=0  # TODO: Implement
        )

    async def quick_search(
        self,
        company_id: str,
        role_title: str,
        required_skills: list[str] = [],
        limit: int = 20
    ) -> MasterSearchResult:
        """Convenience method for quick search."""
        return await self.search(
            company_id=company_id,
            role_title=role_title,
            required_skills=required_skills,
            mode="quick",
            limit=limit
        )

    async def network_only_search(
        self,
        company_id: str,
        role_title: str,
        required_skills: list[str] = [],
        limit: int = 20
    ) -> MasterSearchResult:
        """Convenience method for network-only search."""
        return await self.search(
            company_id=company_id,
            role_title=role_title,
            required_skills=required_skills,
            mode="network_only",
            limit=limit
        )

    # =========================================================================
    # INTELLIGENCE-ONLY METHODS
    # =========================================================================

    async def get_timing_alerts(
        self,
        company_id: str,
        limit: int = 20
    ) -> list[dict]:
        """Get timing-based alerts for candidates in the network."""
        from app.services.company_db import company_db

        people = await company_db.get_people(company_id, limit=5000)

        # Score everyone for readiness
        alerts = []
        for person in people:
            p = person.model_dump() if hasattr(person, "model_dump") else person
            readiness = self.readiness_scorer.score(p)

            if readiness["readiness_score"] >= 0.3:
                alerts.append({
                    **p,
                    **readiness,
                    "alert_type": "timing"
                })

        # Sort by readiness
        alerts.sort(key=lambda x: x["readiness_score"], reverse=True)

        return alerts[:limit]

    async def get_intelligence_summary(
        self,
        company_id: str
    ) -> dict:
        """Get summary of all intelligence signals for a company."""
        # Get network stats
        network_index = await network_index_service.build_index(company_id)
        network_stats = network_index_service.get_network_stats(network_index)

        # Get timing alerts
        timing_alerts = await self.get_timing_alerts(company_id, limit=100)

        # Get RL model info
        rl_info = reward_model.get_model_info()

        return {
            "network": {
                "total_contacts": network_stats["total_contacts"],
                "unique_companies": network_stats["unique_companies"],
                "unique_schools": network_stats["unique_schools"]
            },
            "timing": {
                "high_readiness_count": len([a for a in timing_alerts if a["readiness_score"] >= 0.5]),
                "moderate_readiness_count": len([a for a in timing_alerts if 0.3 <= a["readiness_score"] < 0.5]),
                "top_signals": timing_alerts[:5]
            },
            "rl_model": rl_info,
            "reasoning_available": kimi_engine.enabled
        }

    # =========================================================================
    # FEEDBACK METHODS
    # =========================================================================

    async def record_candidate_action(
        self,
        user_id: str,
        company_id: str,
        candidate_id: str,
        action: str,
        role_id: Optional[str] = None,
        context: dict = {}
    ) -> dict:
        """Record a user action on a candidate."""
        try:
            action_enum = FeedbackAction(action)
        except ValueError:
            return {"error": f"Invalid action: {action}"}

        record = await feedback_collector.record_action(
            user_id=user_id,
            company_id=company_id,
            candidate_id=candidate_id,
            action=action_enum,
            role_id=role_id,
            fit_score=context.get("fit_score"),
            warmth_score=context.get("warmth_score"),
            timing_score=context.get("timing_score"),
            combined_score=context.get("combined_score")
        )

        return record.model_dump()

    async def train_from_feedback(
        self,
        company_id: Optional[str] = None,
        limit: int = 1000
    ) -> dict:
        """Trigger training from recent feedback."""
        # Get training pairs
        pairs = await feedback_collector.get_training_pairs(
            company_id=company_id,
            limit=limit
        )

        if not pairs:
            return {"message": "No feedback available for training"}

        # Train
        result = reward_model.train_step(pairs)

        # Learn company preferences if company_id provided
        if company_id:
            prefs = reward_model.learn_company_preferences(company_id, pairs)
            result["company_preferences"] = prefs

        return result

    # =========================================================================
    # PREDICTION METHODS
    # =========================================================================

    async def get_predictions(
        self,
        company_id: str,
        user_id: Optional[str] = None,
        current_query: Optional[str] = None
    ) -> dict:
        """
        Get full predictive insights for a company.

        Includes:
        - Query autocomplete suggestions
        - Role suggestions based on company stage
        - Surfaced candidates with timing signals
        - Warm path alerts from network changes
        """
        insights = await prediction_engine.get_full_insights(
            company_id=company_id,
            user_id=user_id,
            current_query=current_query
        )
        return insights.model_dump()

    async def get_dashboard_predictions(
        self,
        company_id: str
    ) -> dict:
        """Get predictions optimized for dashboard display."""
        insights = await prediction_engine.get_dashboard_insights(company_id)
        return insights.model_dump()

    async def autocomplete_query(
        self,
        company_id: str,
        user_id: str,
        partial_query: str
    ) -> dict:
        """Get search query autocomplete suggestions."""
        return await prediction_engine.get_search_predictions(
            company_id=company_id,
            user_id=user_id,
            partial_query=partial_query
        )

    async def predict_interviews(
        self,
        company_id: str,
        candidates: list[dict],
        role_title: Optional[str] = None
    ) -> list[dict]:
        """Predict which candidates will be interviewed."""
        predictions = await prediction_engine.predict_interview_outcomes(
            company_id=company_id,
            candidates=candidates,
            role_title=role_title
        )
        return [p.model_dump() for p in predictions]

    async def get_timing_digest(
        self,
        company_id: str
    ) -> dict:
        """Get daily digest of timing-based opportunities."""
        return await prediction_engine.get_timing_digest(company_id)

    async def get_hiring_plan(
        self,
        company_id: str
    ) -> dict:
        """Get suggested hiring plan based on company stage and patterns."""
        return await prediction_engine.get_hiring_plan(company_id)

    def suggest_role_requirements(
        self,
        role_title: str,
        company_context: Optional[dict] = None
    ) -> dict:
        """Suggest requirements for a role (skills, years, etc.)."""
        requirements = prediction_engine.suggest_role_requirements(
            role_title=role_title,
            company_context=company_context
        )
        return requirements.model_dump()

    async def record_search_for_learning(
        self,
        company_id: str,
        user_id: str,
        query: str,
        role_title: Optional[str] = None,
        skills: Optional[list[str]] = None
    ):
        """Record a search to improve autocomplete predictions."""
        await prediction_engine.record_search(
            company_id=company_id,
            user_id=user_id,
            query=query,
            role_title=role_title,
            skills=skills
        )


# =============================================================================
# SINGLETON
# =============================================================================

master_orchestrator = MasterOrchestrator()


# =============================================================================
# DEMO
# =============================================================================

async def demo():
    """Demo the master orchestrator."""
    result = await master_orchestrator.search(
        company_id="100b5ac1-1912-4970-a378-04d0169fd597",
        role_title="ML Engineer",
        required_skills=["Python", "PyTorch", "Machine Learning"],
        mode="quick",  # Use quick for demo
        limit=10
    )

    print("\n" + "="*60)
    print("DEMO RESULTS")
    print("="*60)
    print(f"Mode: {result.mode}")
    print(f"Duration: {result.total_duration_seconds}s")
    print(f"Features: {', '.join(result.features_used)}")
    print(f"Total found: {result.search_result.total_found}")
    print(f"RL adjusted: {result.rl_adjusted}")

    print("\nTOP CANDIDATES:")
    for i, candidate in enumerate(result.search_result.candidates[:5], 1):
        print(f"  {i}. {candidate.full_name}")
        print(f"     Title: {candidate.current_title}")
        print(f"     Score: {candidate.combined_score:.1f} (fit: {candidate.fit_score:.0f}, warmth: {candidate.warmth_score:.0f})")
        print(f"     Tier: {candidate.tier}")

    return result


if __name__ == "__main__":
    asyncio.run(demo())
