"""
Prediction Engine - Unified Interface for Predictive Intelligence.

Combines all 6 prediction components into a single engine:
1. Query Autocomplete - Suggest search queries
2. Role Suggestion - Predict next roles to hire
3. Candidate Surfacing - Surface newly available candidates
4. Skill Prediction - Auto-suggest role requirements
5. Warm Path Alerts - Alert on network opportunities
6. Interview Prediction - Predict who will be interviewed

Usage:
    from app.services.prediction import prediction_engine

    # Get all predictions in one call
    insights = await prediction_engine.get_full_insights(
        company_id="...",
        user_id="...",
        current_query="ML"
    )

    # Or use individual predictors
    suggestions = await prediction_engine.autocomplete.suggest("ML")
"""

import logging
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from .query_autocomplete import QueryAutocomplete, QuerySuggestion
from .role_suggester import RoleSuggester, RoleSuggestion
from .candidate_surfacer import CandidateSurfacer, SurfacedCandidate
from .skill_predictor import SkillPredictor, RoleRequirements
from .warm_path_alerter import WarmPathAlerter, WarmPathAlert
from .interview_predictor import InterviewPredictor, InterviewPrediction

logger = logging.getLogger(__name__)


class PredictionInsights(BaseModel):
    """Complete prediction insights for a company."""
    company_id: str
    generated_at: datetime

    # Query suggestions (if partial query provided)
    query_suggestions: list[QuerySuggestion] = []

    # Role suggestions
    suggested_roles: list[RoleSuggestion] = []

    # Surfaced candidates (timing-based)
    surfaced_candidates: list[SurfacedCandidate] = []

    # Warm path alerts
    warm_path_alerts: list[WarmPathAlert] = []

    # Summary stats
    total_predictions: int = 0
    high_priority_count: int = 0


class DashboardInsights(BaseModel):
    """Insights optimized for dashboard display."""
    company_id: str

    # Immediate actions
    immediate_actions: list[dict] = []

    # Network opportunities
    network_highlights: list[dict] = []

    # Hiring recommendations
    hiring_recommendations: list[dict] = []

    # Summary
    summary: str = ""


class PredictionEngine:
    """
    Unified Prediction Engine.

    Orchestrates all 6 prediction components to provide
    anticipatory intelligence for founders.

    Features:
    - Query autocomplete as they type
    - Role suggestions based on company stage
    - Candidate surfacing based on timing signals
    - Skill suggestions for role requirements
    - Warm path alerts when network creates opportunities
    - Interview predictions based on historical patterns
    """

    def __init__(self):
        # Initialize all predictors
        self.autocomplete = QueryAutocomplete()
        self.role_suggester = RoleSuggester()
        self.candidate_surfacer = CandidateSurfacer()
        self.skill_predictor = SkillPredictor()
        self.warm_path_alerter = WarmPathAlerter()
        self.interview_predictor = InterviewPredictor()

        self._initialized = True

    async def get_full_insights(
        self,
        company_id: str,
        user_id: Optional[str] = None,
        current_query: Optional[str] = None,
        limit_per_category: int = 5
    ) -> PredictionInsights:
        """
        Get comprehensive prediction insights.

        This is the main entry point for the prediction layer.
        Runs all relevant predictors and combines results.

        Args:
            company_id: The company to get insights for
            user_id: Optional user for personalization
            current_query: Optional partial query for autocomplete
            limit_per_category: Max items per category

        Returns:
            PredictionInsights with all predictions
        """
        insights = PredictionInsights(
            company_id=company_id,
            generated_at=datetime.utcnow()
        )

        # 1. Query suggestions (if query provided)
        if current_query:
            try:
                insights.query_suggestions = await self.autocomplete.suggest(
                    partial_query=current_query,
                    company_id=company_id,
                    user_id=user_id,
                    limit=limit_per_category
                )
            except Exception as e:
                logger.warning(f"Query autocomplete failed: {e}")

        # 2. Role suggestions
        try:
            insights.suggested_roles = await self.role_suggester.suggest_next_roles(
                company_id=company_id,
                limit=limit_per_category
            )
        except Exception as e:
            logger.warning(f"Role suggestion failed: {e}")

        # 3. Surfaced candidates
        try:
            insights.surfaced_candidates = await self.candidate_surfacer.get_newly_available(
                company_id=company_id,
                limit=limit_per_category
            )
        except Exception as e:
            logger.warning(f"Candidate surfacing failed: {e}")

        # 4. Warm path alerts
        try:
            insights.warm_path_alerts = await self.warm_path_alerter.get_alerts(
                company_id=company_id,
                limit=limit_per_category
            )
        except Exception as e:
            logger.warning(f"Warm path alerts failed: {e}")

        # Calculate totals
        insights.total_predictions = (
            len(insights.query_suggestions) +
            len(insights.suggested_roles) +
            len(insights.surfaced_candidates) +
            len(insights.warm_path_alerts)
        )

        # Count high priority items
        high_priority = 0
        high_priority += len([r for r in insights.suggested_roles if r.priority == "immediate"])
        high_priority += len([c for c in insights.surfaced_candidates if c.urgency == "immediate"])
        high_priority += len([a for a in insights.warm_path_alerts if a.priority == "high"])
        insights.high_priority_count = high_priority

        return insights

    async def get_dashboard_insights(
        self,
        company_id: str
    ) -> DashboardInsights:
        """
        Get insights optimized for dashboard display.

        Returns actionable, prioritized insights.
        """
        # Get full insights
        full = await self.get_full_insights(
            company_id=company_id,
            limit_per_category=3
        )

        dashboard = DashboardInsights(company_id=company_id)

        # Build immediate actions from surfaced candidates
        for candidate in full.surfaced_candidates:
            if candidate.urgency == "immediate":
                dashboard.immediate_actions.append({
                    "type": "candidate",
                    "title": f"Reach out to {candidate.full_name}",
                    "subtitle": candidate.trigger_detail,
                    "action": candidate.recommended_action,
                    "candidate_id": candidate.id
                })

        # Add high-priority warm path alerts
        for alert in full.warm_path_alerts:
            if alert.priority == "high":
                dashboard.network_highlights.append({
                    "type": "network",
                    "title": alert.change_detail,
                    "subtitle": alert.opportunity,
                    "action": alert.suggested_action,
                    "connector_id": alert.connector_id
                })

        # Add role suggestions as hiring recommendations
        for role in full.suggested_roles:
            if role.priority in ["immediate", "soon"]:
                dashboard.hiring_recommendations.append({
                    "type": "role",
                    "title": f"Consider hiring: {role.role}",
                    "subtitle": role.reason,
                    "confidence": role.confidence,
                    "priority": role.priority
                })

        # Generate summary
        summary_parts = []
        if dashboard.immediate_actions:
            summary_parts.append(f"{len(dashboard.immediate_actions)} candidates to reach out to")
        if dashboard.network_highlights:
            summary_parts.append(f"{len(dashboard.network_highlights)} network opportunities")
        if dashboard.hiring_recommendations:
            summary_parts.append(f"{len(dashboard.hiring_recommendations)} roles to consider")

        dashboard.summary = "; ".join(summary_parts) if summary_parts else "No immediate actions needed"

        return dashboard

    async def get_search_predictions(
        self,
        company_id: str,
        user_id: str,
        partial_query: str
    ) -> dict:
        """
        Get predictions specifically for the search experience.

        Returns query suggestions plus related role info.
        """
        # Get autocomplete suggestions
        suggestions = await self.autocomplete.suggest(
            partial_query=partial_query,
            company_id=company_id,
            user_id=user_id,
            limit=8
        )

        # If we have a clear role title, get skill predictions
        skill_suggestions = []
        if len(partial_query) >= 3:
            # Try to get skills for the most likely role
            if suggestions:
                top_role = suggestions[0].role_title
                if top_role:
                    requirements = self.skill_predictor.predict_requirements(top_role)
                    skill_suggestions = requirements.required_skills[:5]

        return {
            "query_suggestions": [s.model_dump() for s in suggestions],
            "skill_suggestions": skill_suggestions,
            "partial_query": partial_query
        }

    async def predict_interview_outcomes(
        self,
        company_id: str,
        candidates: list[dict],
        role_title: Optional[str] = None
    ) -> list[InterviewPrediction]:
        """
        Predict which candidates will be interviewed.

        Uses historical patterns to rank by interview likelihood.
        """
        return await self.interview_predictor.predict_interviews(
            company_id=company_id,
            candidates=candidates,
            role_title=role_title
        )

    async def get_timing_digest(
        self,
        company_id: str
    ) -> dict:
        """
        Get a daily digest of timing-based opportunities.

        Combines candidate surfacing and warm path alerts.
        """
        # Get candidate digest
        candidate_digest = await self.candidate_surfacer.get_daily_digest(company_id)

        # Get warm path coverage
        coverage = await self.warm_path_alerter.get_target_company_coverage(company_id)
        missing = await self.warm_path_alerter.get_missing_coverage(company_id)

        return {
            "date": candidate_digest["date"],
            "candidates": {
                "total": candidate_digest["total_surfaced"],
                "immediate": candidate_digest["immediate_action"],
                "high_priority": candidate_digest["high_priority"]
            },
            "network": {
                "companies_covered": len(coverage),
                "companies_missing": len(missing),
                "top_coverage": list(coverage.keys())[:5],
                "priority_gaps": [m["company"] for m in missing[:3]]
            },
            "summary": candidate_digest["summary"]
        }

    async def get_hiring_plan(
        self,
        company_id: str
    ) -> dict:
        """
        Get a comprehensive hiring plan suggestion.

        Combines role suggestions with interview predictions.
        """
        return await self.role_suggester.get_hiring_plan(
            company_id=company_id,
            months_ahead=6
        )

    def suggest_role_requirements(
        self,
        role_title: str,
        company_context: Optional[dict] = None
    ) -> RoleRequirements:
        """
        Suggest requirements for a role.

        Used to auto-fill search forms.
        """
        return self.skill_predictor.predict_requirements(
            role_title=role_title,
            company_context=company_context
        )

    async def record_search(
        self,
        company_id: str,
        user_id: str,
        query: str,
        role_title: Optional[str] = None,
        skills: Optional[list[str]] = None
    ):
        """
        Record a search for learning.

        Updates autocomplete patterns.
        """
        await self.autocomplete.record_search(
            company_id=company_id,
            user_id=user_id,
            query=query,
            role_title=role_title,
            skills=skills
        )


# Singleton instance
prediction_engine = PredictionEngine()
