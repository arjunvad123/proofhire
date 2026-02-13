"""
Reward Model for Candidate Ranking

This model learns to predict which candidates will lead to positive outcomes
(interviews, hires) based on their features and the context of the search.

Training uses GRPO (Group Relative Policy Optimization):
- Groups candidates by search session
- Compares outcomes within each group
- Learns to prefer candidates that led to hires over those rejected

The model is used to adjust rankings:
    final_score = base_score * reward_model.score(candidate, context)

Reference: https://arxiv.org/html/2503.06034v1 (Rank-R1)
"""

import logging
import json
from typing import Optional
from pydantic import BaseModel
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class RewardPrediction(BaseModel):
    """Prediction from the reward model."""
    candidate_id: str
    reward_score: float  # 0-1, probability of positive outcome
    confidence: float    # 0-1, model confidence
    reasoning: str       # Why this score


class ModelWeights(BaseModel):
    """Learned weights for the reward model."""
    # Feature weights (learned from data)
    fit_weight: float = 0.40
    warmth_weight: float = 0.35
    timing_weight: float = 0.15
    network_bonus: float = 0.10

    # Interaction weights
    fit_warmth_interaction: float = 0.05
    high_urgency_bonus: float = 0.05

    # Learned adjustments
    company_preferences: dict = {}  # company_id -> feature adjustments
    role_type_preferences: dict = {}  # role_type -> feature adjustments

    # Meta
    version: str = "1.0.0"
    training_samples: int = 0
    last_updated: Optional[str] = None


class RewardModel:
    """
    Reward model that learns to predict hiring outcomes.

    The model learns from feedback:
    - Hired candidates get reward +10
    - Interviewed candidates get reward +5
    - Rejected candidates get reward -5

    Over time, the model learns which features predict success.

    Usage:
        from app.services.rl import reward_model

        # Score a candidate
        score = reward_model.score(candidate, context)

        # Train on new feedback
        reward_model.train_step(feedback_batch)
    """

    def __init__(self, weights_path: Optional[str] = None):
        self.weights_path = weights_path or "data/reward_model_weights.json"
        self.weights = self._load_weights()
        self.enabled = True

    def _load_weights(self) -> ModelWeights:
        """Load weights from file or use defaults."""
        try:
            path = Path(self.weights_path)
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                return ModelWeights(**data)
        except Exception as e:
            logger.warning(f"Could not load weights: {e}, using defaults")

        return ModelWeights()

    def _save_weights(self):
        """Save weights to file."""
        try:
            path = Path(self.weights_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(self.weights.model_dump(), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save weights: {e}")

    def score(
        self,
        candidate: dict,
        context: dict = {}
    ) -> RewardPrediction:
        """
        Score a candidate's likelihood of positive outcome.

        Args:
            candidate: Candidate dict with scores and features
            context: Search context (role_type, company preferences, etc.)

        Returns:
            RewardPrediction with score and reasoning
        """
        # Extract features
        fit_score = candidate.get("fit_score", 50) / 100
        warmth_score = candidate.get("warmth_score", 0) / 100
        timing_score = candidate.get("timing_score", 0) / 100
        is_network = candidate.get("is_from_network", False)
        timing_urgency = candidate.get("timing_urgency", "low")

        # Apply weights
        base_score = (
            fit_score * self.weights.fit_weight +
            warmth_score * self.weights.warmth_weight +
            timing_score * self.weights.timing_weight
        )

        # Apply bonuses
        if is_network:
            base_score += self.weights.network_bonus

        if timing_urgency == "high":
            base_score += self.weights.high_urgency_bonus

        # Interaction effect: high fit + high warmth is extra valuable
        if fit_score > 0.7 and warmth_score > 0.7:
            base_score += self.weights.fit_warmth_interaction

        # Apply company-specific preferences if available
        company_id = context.get("company_id")
        if company_id and company_id in self.weights.company_preferences:
            prefs = self.weights.company_preferences[company_id]
            # Adjust based on learned preferences
            base_score *= prefs.get("multiplier", 1.0)

        # Normalize to 0-1
        reward_score = min(max(base_score, 0), 1)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            fit_score, warmth_score, timing_score, is_network, reward_score
        )

        return RewardPrediction(
            candidate_id=str(candidate.get("id", "")),
            reward_score=round(reward_score, 3),
            confidence=0.7 if self.weights.training_samples > 100 else 0.4,
            reasoning=reasoning
        )

    def _generate_reasoning(
        self,
        fit: float,
        warmth: float,
        timing: float,
        is_network: bool,
        final_score: float
    ) -> str:
        """Generate human-readable reasoning."""
        factors = []

        if fit > 0.7:
            factors.append("strong skill match")
        elif fit > 0.4:
            factors.append("moderate skill match")

        if warmth > 0.7:
            factors.append("warm connection")
        elif warmth > 0.3:
            factors.append("some network overlap")

        if timing > 0.5:
            factors.append("good timing signals")

        if is_network:
            factors.append("direct network")

        if not factors:
            factors.append("matches basic criteria")

        return f"Score {final_score:.2f} based on: {', '.join(factors)}"

    def adjust_ranking(
        self,
        candidates: list[dict],
        context: dict = {}
    ) -> list[dict]:
        """
        Adjust candidate rankings using the reward model.

        Multiplies existing combined_score by reward model prediction.
        """
        for candidate in candidates:
            prediction = self.score(candidate, context)

            # Adjust combined score
            original_score = candidate.get("combined_score", 50)
            adjusted_score = original_score * (0.8 + prediction.reward_score * 0.4)

            candidate["combined_score"] = adjusted_score
            candidate["reward_adjustment"] = prediction.reward_score
            candidate["reward_reasoning"] = prediction.reasoning

        # Re-sort
        candidates.sort(key=lambda c: c.get("combined_score", 0), reverse=True)

        return candidates

    # =========================================================================
    # TRAINING (GRPO)
    # =========================================================================

    def train_step(
        self,
        feedback_batch: list[dict],
        learning_rate: float = 0.01
    ) -> dict:
        """
        Training step using GRPO-style optimization.

        Groups feedback by search session, then learns to prefer
        candidates that led to positive outcomes over negatives.

        Args:
            feedback_batch: List of feedback records with outcomes
            learning_rate: Learning rate for weight updates

        Returns:
            Training metrics
        """
        if not feedback_batch:
            return {"error": "No feedback provided"}

        # Group by search session
        sessions = {}
        for feedback in feedback_batch:
            session_id = feedback.get("search_session_id") or feedback.get("company_id")
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(feedback)

        # For each session, compute preference pairs
        total_pairs = 0
        weight_updates = {
            "fit": 0,
            "warmth": 0,
            "timing": 0,
            "network": 0
        }

        for session_id, session_feedback in sessions.items():
            # Split into positive and negative outcomes
            positives = [f for f in session_feedback if f.get("reward", 0) > 0]
            negatives = [f for f in session_feedback if f.get("reward", 0) < 0]

            # Create preference pairs
            for pos in positives:
                for neg in negatives:
                    total_pairs += 1

                    # Compute feature differences
                    fit_diff = (pos.get("context", {}).get("fit_score", 50) -
                                neg.get("context", {}).get("fit_score", 50)) / 100
                    warmth_diff = (pos.get("context", {}).get("warmth_score", 0) -
                                   neg.get("context", {}).get("warmth_score", 0)) / 100
                    timing_diff = (pos.get("context", {}).get("timing_score", 0) -
                                   neg.get("context", {}).get("timing_score", 0)) / 100

                    # Update weights to prefer the positive candidate's features
                    weight_updates["fit"] += fit_diff * learning_rate
                    weight_updates["warmth"] += warmth_diff * learning_rate
                    weight_updates["timing"] += timing_diff * learning_rate

        # Apply updates (with bounds)
        if total_pairs > 0:
            self.weights.fit_weight = max(0.2, min(0.6,
                self.weights.fit_weight + weight_updates["fit"] / total_pairs))
            self.weights.warmth_weight = max(0.2, min(0.5,
                self.weights.warmth_weight + weight_updates["warmth"] / total_pairs))
            self.weights.timing_weight = max(0.05, min(0.3,
                self.weights.timing_weight + weight_updates["timing"] / total_pairs))

            # Update meta
            self.weights.training_samples += len(feedback_batch)
            from datetime import datetime
            self.weights.last_updated = datetime.utcnow().isoformat()

            # Save
            self._save_weights()

        return {
            "pairs_processed": total_pairs,
            "sessions_processed": len(sessions),
            "feedback_count": len(feedback_batch),
            "new_weights": {
                "fit": round(self.weights.fit_weight, 3),
                "warmth": round(self.weights.warmth_weight, 3),
                "timing": round(self.weights.timing_weight, 3)
            },
            "total_training_samples": self.weights.training_samples
        }

    def learn_company_preferences(
        self,
        company_id: str,
        feedback: list[dict]
    ) -> dict:
        """
        Learn company-specific preferences from their feedback.

        Some companies might prefer:
        - Network candidates (high trust)
        - External candidates (diversity)
        - High urgency candidates (speed)
        """
        if not feedback:
            return {}

        # Analyze what led to hires for this company
        hires = [f for f in feedback if f.get("action") == "hired"]
        interviews = [f for f in feedback if f.get("action") == "interviewed"]

        if not hires and not interviews:
            return {}

        # Calculate average features of successful candidates
        successful = hires or interviews

        avg_fit = np.mean([f.get("context", {}).get("fit_score", 50) for f in successful])
        avg_warmth = np.mean([f.get("context", {}).get("warmth_score", 0) for f in successful])
        avg_timing = np.mean([f.get("context", {}).get("timing_score", 0) for f in successful])

        # Compare to baseline (50, 30, 20)
        fit_pref = avg_fit / 50  # > 1 means they prefer higher fit
        warmth_pref = avg_warmth / 30
        timing_pref = avg_timing / 20

        # Store preferences
        self.weights.company_preferences[company_id] = {
            "multiplier": 1.0,  # Base multiplier
            "fit_preference": fit_pref,
            "warmth_preference": warmth_pref,
            "timing_preference": timing_pref,
            "sample_size": len(successful)
        }

        self._save_weights()

        return self.weights.company_preferences[company_id]

    def get_model_info(self) -> dict:
        """Get information about the current model state."""
        return {
            "enabled": self.enabled,
            "version": self.weights.version,
            "training_samples": self.weights.training_samples,
            "last_updated": self.weights.last_updated,
            "weights": {
                "fit": self.weights.fit_weight,
                "warmth": self.weights.warmth_weight,
                "timing": self.weights.timing_weight,
                "network_bonus": self.weights.network_bonus
            },
            "company_preferences_count": len(self.weights.company_preferences)
        }


# =============================================================================
# SINGLETON
# =============================================================================

reward_model = RewardModel()
