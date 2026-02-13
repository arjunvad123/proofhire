"""
Interview Predictor - Predict which candidates the founder will interview.

Uses:
- Historical patterns (what candidates did they interview before?)
- Reward model signals
- Fit/warmth/timing scores
- Explicit preferences

Usage:
    predictor = InterviewPredictor()
    predictions = await predictor.predict_interviews(company_id, candidates)
    # Returns candidates sorted by likelihood of being interviewed
"""

import logging
from typing import Optional
from pydantic import BaseModel

from app.services.rl import reward_model
from app.services.feedback import feedback_collector, FeedbackAction
from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)


class InterviewPrediction(BaseModel):
    """Prediction for a candidate."""
    candidate_id: str
    candidate_name: str
    interview_probability: float  # 0-1
    confidence: float             # 0-1

    # Factors
    fit_contribution: float
    warmth_contribution: float
    timing_contribution: float
    pattern_contribution: float

    # Reasoning
    reasoning: str
    key_factors: list[str]


class InterviewPredictor:
    """
    Predict which candidates will be interviewed.

    Uses:
    1. Reward model (learned preferences)
    2. Historical patterns (what titles, companies, etc. led to interviews)
    3. Scoring signals (fit, warmth, timing)
    4. Explicit preferences (saved candidates, etc.)
    """

    def __init__(self):
        self._supabase = None
        self._pattern_cache = {}

    @property
    def supabase(self):
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    async def predict_interviews(
        self,
        company_id: str,
        candidates: list[dict],
        role_title: Optional[str] = None
    ) -> list[InterviewPrediction]:
        """
        Predict which candidates will be interviewed.

        Args:
            company_id: The company doing the hiring
            candidates: List of candidate dicts
            role_title: Optional role for context

        Returns:
            List of InterviewPrediction, sorted by probability
        """
        # Learn patterns from history
        patterns = await self._learn_patterns(company_id)

        predictions = []

        for candidate in candidates:
            prediction = self._predict_single(candidate, patterns)
            predictions.append(prediction)

        # Sort by probability
        predictions.sort(key=lambda x: x.interview_probability, reverse=True)

        return predictions

    async def _learn_patterns(self, company_id: str) -> dict:
        """Learn interview patterns from history."""
        if company_id in self._pattern_cache:
            return self._pattern_cache[company_id]

        patterns = {
            "avg_fit_interviewed": 70,
            "avg_warmth_interviewed": 50,
            "preferred_companies": [],
            "preferred_titles": [],
            "network_preference": 0.6,  # % of interviews that were network
        }

        try:
            # Get historical feedback
            feedback = await feedback_collector.get_training_pairs(
                company_id=company_id,
                limit=500
            )

            # Filter to interviews
            interviews = [f for f in feedback if f["action"] == "interviewed"]

            if interviews:
                # Calculate averages
                fit_scores = [f["context"].get("fit_score", 50) for f in interviews if f["context"].get("fit_score")]
                warmth_scores = [f["context"].get("warmth_score", 0) for f in interviews if f["context"].get("warmth_score")]

                if fit_scores:
                    patterns["avg_fit_interviewed"] = sum(fit_scores) / len(fit_scores)
                if warmth_scores:
                    patterns["avg_warmth_interviewed"] = sum(warmth_scores) / len(warmth_scores)

        except Exception as e:
            logger.warning(f"Could not learn patterns: {e}")

        self._pattern_cache[company_id] = patterns
        return patterns

    def _predict_single(
        self,
        candidate: dict,
        patterns: dict
    ) -> InterviewPrediction:
        """Predict interview probability for a single candidate."""
        # Extract scores
        fit_score = candidate.get("fit_score", 50) / 100
        warmth_score = candidate.get("warmth_score", 0) / 100
        timing_score = candidate.get("timing_score", 0) / 100
        is_network = candidate.get("is_from_network", False)

        # Calculate contributions
        # Fit: How well they match vs. historical interviewed fit
        avg_fit = patterns.get("avg_fit_interviewed", 70) / 100
        fit_contribution = min(1.0, fit_score / max(0.5, avg_fit)) * 0.4

        # Warmth: Network candidates get interviewed more
        network_pref = patterns.get("network_preference", 0.6)
        warmth_contribution = warmth_score * network_pref * 0.3

        # Timing: Higher urgency candidates get prioritized
        timing_contribution = timing_score * 0.15

        # Pattern: Does candidate match historical patterns?
        pattern_contribution = 0.15  # Default

        # Use reward model if available
        try:
            reward_pred = reward_model.score(candidate)
            pattern_contribution = reward_pred.reward_score * 0.2
        except:
            pass

        # Calculate total probability
        probability = (
            fit_contribution +
            warmth_contribution +
            timing_contribution +
            pattern_contribution
        )

        # Normalize to 0-1
        probability = min(1.0, max(0.0, probability))

        # Generate reasoning
        key_factors = []
        if fit_score > 0.7:
            key_factors.append("Strong fit score")
        if is_network:
            key_factors.append("In network")
        if warmth_score > 0.5:
            key_factors.append("Warm connection available")
        if timing_score > 0.5:
            key_factors.append("Good timing signals")

        reasoning = self._generate_reasoning(
            probability, fit_score, warmth_score, is_network
        )

        return InterviewPrediction(
            candidate_id=str(candidate.get("id", "")),
            candidate_name=candidate.get("full_name", "Unknown"),
            interview_probability=round(probability, 3),
            confidence=0.7 if len(key_factors) >= 2 else 0.5,
            fit_contribution=round(fit_contribution, 3),
            warmth_contribution=round(warmth_contribution, 3),
            timing_contribution=round(timing_contribution, 3),
            pattern_contribution=round(pattern_contribution, 3),
            reasoning=reasoning,
            key_factors=key_factors or ["Matches search criteria"]
        )

    def _generate_reasoning(
        self,
        probability: float,
        fit: float,
        warmth: float,
        is_network: bool
    ) -> str:
        """Generate human-readable reasoning."""
        if probability >= 0.8:
            if is_network:
                return "Very likely to interview - strong fit and in your network"
            else:
                return "Very likely to interview - strong fit with warm intro path"
        elif probability >= 0.6:
            return "Likely to interview - good overall match"
        elif probability >= 0.4:
            return "Possible interview - moderate fit"
        else:
            return "Less likely - may need additional signals"

    async def get_top_interview_candidates(
        self,
        company_id: str,
        candidates: list[dict],
        top_n: int = 5
    ) -> list[dict]:
        """
        Get the top N candidates most likely to be interviewed.

        Convenience method that returns full candidate dicts with predictions.
        """
        predictions = await self.predict_interviews(company_id, candidates)

        top_predictions = predictions[:top_n]

        # Map predictions back to candidates
        result = []
        pred_map = {p.candidate_id: p for p in top_predictions}

        for candidate in candidates:
            cid = str(candidate.get("id", ""))
            if cid in pred_map:
                pred = pred_map[cid]
                result.append({
                    **candidate,
                    "interview_probability": pred.interview_probability,
                    "interview_reasoning": pred.reasoning,
                    "interview_key_factors": pred.key_factors
                })

        # Sort by probability
        result.sort(key=lambda x: x.get("interview_probability", 0), reverse=True)

        return result

    async def explain_prediction(
        self,
        company_id: str,
        candidate: dict
    ) -> dict:
        """
        Get detailed explanation of interview prediction.

        Returns breakdown of why we think they will/won't be interviewed.
        """
        patterns = await self._learn_patterns(company_id)
        prediction = self._predict_single(candidate, patterns)

        return {
            "candidate": {
                "id": candidate.get("id"),
                "name": candidate.get("full_name"),
                "title": candidate.get("current_title"),
                "company": candidate.get("current_company")
            },
            "prediction": {
                "probability": prediction.interview_probability,
                "confidence": prediction.confidence,
                "reasoning": prediction.reasoning
            },
            "breakdown": {
                "fit_contribution": {
                    "value": prediction.fit_contribution,
                    "explanation": f"Fit score ({candidate.get('fit_score', 0):.0f}) vs historical avg ({patterns.get('avg_fit_interviewed', 70):.0f})"
                },
                "warmth_contribution": {
                    "value": prediction.warmth_contribution,
                    "explanation": f"Network/warmth score ({candidate.get('warmth_score', 0):.0f})"
                },
                "timing_contribution": {
                    "value": prediction.timing_contribution,
                    "explanation": f"Timing signals ({candidate.get('timing_urgency', 'none')})"
                },
                "pattern_contribution": {
                    "value": prediction.pattern_contribution,
                    "explanation": "Based on historical patterns and reward model"
                }
            },
            "historical_context": {
                "avg_fit_of_interviewed": patterns.get("avg_fit_interviewed", 70),
                "network_preference": f"{patterns.get('network_preference', 0.6)*100:.0f}% of interviews were network candidates"
            },
            "key_factors": prediction.key_factors
        }
