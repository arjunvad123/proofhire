"""
Feedback Collector

Records user actions on candidates to enable reward model training.

Action Types and Rewards:
- viewed: +0 (neutral, just tracking)
- saved/bookmarked: +1 (mild positive signal)
- contacted: +2 (strong positive signal)
- interviewed: +5 (very strong positive signal)
- hired: +10 (ultimate positive signal)
- ignored: -1 (mild negative signal)
- rejected: -5 (strong negative signal)

The feedback is stored in Supabase and used to:
1. Train the reward model (GRPO)
2. Personalize rankings for each user
3. Improve global ranking quality
"""

import logging
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel
from uuid import UUID

from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)


class FeedbackAction(str, Enum):
    """Types of actions users can take on candidates."""
    VIEWED = "viewed"
    SAVED = "saved"
    CONTACTED = "contacted"
    INTERVIEWED = "interviewed"
    HIRED = "hired"
    IGNORED = "ignored"
    REJECTED = "rejected"


# Reward values for each action
ACTION_REWARDS = {
    FeedbackAction.VIEWED: 0,
    FeedbackAction.SAVED: 1,
    FeedbackAction.CONTACTED: 2,
    FeedbackAction.INTERVIEWED: 5,
    FeedbackAction.HIRED: 10,
    FeedbackAction.IGNORED: -1,
    FeedbackAction.REJECTED: -5,
}


class FeedbackRecord(BaseModel):
    """A single feedback record."""
    id: Optional[str] = None
    user_id: str
    company_id: str
    candidate_id: str
    role_id: Optional[str] = None
    search_session_id: Optional[str] = None

    action: FeedbackAction
    reward: int

    # Context at time of action
    candidate_rank: Optional[int] = None
    fit_score: Optional[float] = None
    warmth_score: Optional[float] = None
    timing_score: Optional[float] = None
    combined_score: Optional[float] = None

    # Metadata
    created_at: Optional[datetime] = None
    notes: Optional[str] = None


class FeedbackStats(BaseModel):
    """Statistics about feedback for a company/user."""
    total_feedback: int
    actions_breakdown: dict[str, int]
    avg_reward: float
    conversion_rate: float  # % that led to contacted/interviewed/hired
    top_hired_sources: list[dict]  # Where hired candidates came from


class FeedbackCollector:
    """
    Collects and stores feedback on candidates.

    Usage:
        from app.services.feedback import feedback_collector

        # Record an action
        await feedback_collector.record_action(
            user_id="user-123",
            company_id="company-456",
            candidate_id="candidate-789",
            action=FeedbackAction.CONTACTED,
            context={
                "role_id": "role-abc",
                "fit_score": 85.0,
                "warmth_score": 70.0
            }
        )

        # Get training pairs
        pairs = await feedback_collector.get_training_pairs(company_id="...")
    """

    def __init__(self):
        self._supabase = None

    @property
    def supabase(self):
        """Lazy initialization of Supabase client."""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    async def record_action(
        self,
        user_id: str,
        company_id: str,
        candidate_id: str,
        action: FeedbackAction,
        role_id: Optional[str] = None,
        search_session_id: Optional[str] = None,
        candidate_rank: Optional[int] = None,
        fit_score: Optional[float] = None,
        warmth_score: Optional[float] = None,
        timing_score: Optional[float] = None,
        combined_score: Optional[float] = None,
        notes: Optional[str] = None
    ) -> FeedbackRecord:
        """
        Record a user action on a candidate.

        Args:
            user_id: The user taking the action
            company_id: The company doing the search
            candidate_id: The candidate being acted upon
            action: The type of action
            role_id: Optional role this search is for
            search_session_id: Optional session ID for grouping
            candidate_rank: Where candidate was ranked when action taken
            fit_score: Fit score at time of action
            warmth_score: Warmth score at time of action
            timing_score: Timing score at time of action
            combined_score: Combined score at time of action
            notes: Optional notes

        Returns:
            The created FeedbackRecord
        """
        reward = ACTION_REWARDS.get(action, 0)

        record = FeedbackRecord(
            user_id=user_id,
            company_id=company_id,
            candidate_id=candidate_id,
            role_id=role_id,
            search_session_id=search_session_id,
            action=action,
            reward=reward,
            candidate_rank=candidate_rank,
            fit_score=fit_score,
            warmth_score=warmth_score,
            timing_score=timing_score,
            combined_score=combined_score,
            created_at=datetime.utcnow(),
            notes=notes
        )

        # Store in Supabase
        try:
            data = record.model_dump(exclude={"id"})
            data["action"] = action.value
            data["created_at"] = data["created_at"].isoformat()

            result = self.supabase.table("candidate_feedback").insert(data).execute()

            if result.data:
                record.id = result.data[0].get("id")
                logger.info(f"Recorded feedback: {action.value} on {candidate_id}")
            else:
                logger.warning(f"Feedback insert returned no data")

        except Exception as e:
            # Log but don't fail - feedback is non-critical
            logger.error(f"Failed to record feedback: {e}")

        return record

    async def get_training_pairs(
        self,
        company_id: Optional[str] = None,
        limit: int = 1000,
        min_reward: int = -10,
        max_reward: int = 10
    ) -> list[dict]:
        """
        Get (candidate, context, outcome) triplets for reward model training.

        Returns pairs where we know the outcome (hired, rejected, etc.)
        These are used to train the reward model.
        """
        try:
            query = self.supabase.table("candidate_feedback").select("*")

            if company_id:
                query = query.eq("company_id", company_id)

            # Only get meaningful actions (not just views)
            query = query.neq("action", "viewed")

            query = query.order("created_at", desc=True).limit(limit)

            result = query.execute()

            pairs = []
            for record in result.data or []:
                pairs.append({
                    "candidate_id": record["candidate_id"],
                    "action": record["action"],
                    "reward": record["reward"],
                    "context": {
                        "role_id": record.get("role_id"),
                        "fit_score": record.get("fit_score"),
                        "warmth_score": record.get("warmth_score"),
                        "timing_score": record.get("timing_score"),
                        "combined_score": record.get("combined_score"),
                        "candidate_rank": record.get("candidate_rank"),
                    },
                    "timestamp": record.get("created_at")
                })

            return pairs

        except Exception as e:
            logger.error(f"Failed to get training pairs: {e}")
            return []

    async def get_feedback_stats(
        self,
        company_id: str,
        role_id: Optional[str] = None
    ) -> FeedbackStats:
        """Get feedback statistics for a company/role."""
        try:
            query = self.supabase.table("candidate_feedback")\
                .select("*")\
                .eq("company_id", company_id)

            if role_id:
                query = query.eq("role_id", role_id)

            result = query.execute()
            records = result.data or []

            # Calculate stats
            total = len(records)
            actions = {}
            rewards = []
            conversions = 0

            for r in records:
                action = r.get("action", "unknown")
                actions[action] = actions.get(action, 0) + 1
                rewards.append(r.get("reward", 0))

                if action in ["contacted", "interviewed", "hired"]:
                    conversions += 1

            avg_reward = sum(rewards) / len(rewards) if rewards else 0
            conversion_rate = conversions / total if total > 0 else 0

            return FeedbackStats(
                total_feedback=total,
                actions_breakdown=actions,
                avg_reward=round(avg_reward, 2),
                conversion_rate=round(conversion_rate, 3),
                top_hired_sources=[]  # TODO: Implement
            )

        except Exception as e:
            logger.error(f"Failed to get feedback stats: {e}")
            return FeedbackStats(
                total_feedback=0,
                actions_breakdown={},
                avg_reward=0,
                conversion_rate=0,
                top_hired_sources=[]
            )

    async def get_candidate_history(
        self,
        candidate_id: str,
        company_id: Optional[str] = None
    ) -> list[FeedbackRecord]:
        """Get all feedback history for a candidate."""
        try:
            query = self.supabase.table("candidate_feedback")\
                .select("*")\
                .eq("candidate_id", candidate_id)

            if company_id:
                query = query.eq("company_id", company_id)

            query = query.order("created_at", desc=True)

            result = query.execute()

            return [
                FeedbackRecord(
                    id=r.get("id"),
                    user_id=r.get("user_id"),
                    company_id=r.get("company_id"),
                    candidate_id=r.get("candidate_id"),
                    role_id=r.get("role_id"),
                    action=FeedbackAction(r.get("action")),
                    reward=r.get("reward", 0),
                    candidate_rank=r.get("candidate_rank"),
                    fit_score=r.get("fit_score"),
                    warmth_score=r.get("warmth_score"),
                    timing_score=r.get("timing_score"),
                    combined_score=r.get("combined_score"),
                    created_at=datetime.fromisoformat(r["created_at"]) if r.get("created_at") else None,
                    notes=r.get("notes")
                )
                for r in result.data or []
            ]

        except Exception as e:
            logger.error(f"Failed to get candidate history: {e}")
            return []

    async def record_batch(
        self,
        user_id: str,
        company_id: str,
        actions: list[tuple[str, FeedbackAction]]  # (candidate_id, action)
    ) -> int:
        """
        Record multiple actions at once (e.g., bulk ignore).

        Returns count of successfully recorded actions.
        """
        success = 0

        for candidate_id, action in actions:
            try:
                await self.record_action(
                    user_id=user_id,
                    company_id=company_id,
                    candidate_id=candidate_id,
                    action=action
                )
                success += 1
            except Exception:
                pass

        return success


# =============================================================================
# SINGLETON
# =============================================================================

feedback_collector = FeedbackCollector()


# =============================================================================
# DATABASE MIGRATION (for reference)
# =============================================================================

MIGRATION_SQL = """
-- Feedback table for storing user actions on candidates
CREATE TABLE IF NOT EXISTS candidate_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    company_id UUID NOT NULL REFERENCES companies(id),
    candidate_id TEXT NOT NULL,
    role_id UUID REFERENCES roles(id),
    search_session_id UUID,

    action TEXT NOT NULL CHECK (action IN ('viewed', 'saved', 'contacted', 'interviewed', 'hired', 'ignored', 'rejected')),
    reward INTEGER NOT NULL,

    -- Context at time of action
    candidate_rank INTEGER,
    fit_score NUMERIC(5,2),
    warmth_score NUMERIC(5,2),
    timing_score NUMERIC(5,2),
    combined_score NUMERIC(5,2),

    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- For efficient queries
    CONSTRAINT unique_user_candidate_action UNIQUE (user_id, candidate_id, action, role_id)
);

-- Indexes
CREATE INDEX idx_feedback_company ON candidate_feedback(company_id);
CREATE INDEX idx_feedback_candidate ON candidate_feedback(candidate_id);
CREATE INDEX idx_feedback_action ON candidate_feedback(action);
CREATE INDEX idx_feedback_created ON candidate_feedback(created_at DESC);

-- RLS
ALTER TABLE candidate_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own company feedback"
    ON candidate_feedback FOR SELECT
    USING (company_id IN (
        SELECT company_id FROM company_members WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can insert own feedback"
    ON candidate_feedback FOR INSERT
    WITH CHECK (user_id = auth.uid());
"""
