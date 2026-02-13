"""
Candidate Surfacer - Proactively surface candidates who just became available.

Monitors:
- Layoff announcements affecting network contacts
- Tenure cliffs approaching (4-year vesting)
- Profile activity (updates, "open to work")
- Company events (acquisitions, leadership changes)

Usage:
    surfacer = CandidateSurfacer()
    candidates = await surfacer.get_newly_available(company_id="...")
    # Returns candidates with timing signals
"""

import logging
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.services.company_db import company_db
from app.search.readiness import ReadinessScorer
from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)


# =============================================================================
# RECENT LAYOFF COMPANIES (would be updated from news feed in production)
# =============================================================================

RECENT_LAYOFFS = {
    "meta": {"date": "2024-01", "percentage": 10, "departments": ["all"]},
    "google": {"date": "2024-01", "percentage": 6, "departments": ["engineering", "ads"]},
    "amazon": {"date": "2024-01", "percentage": 5, "departments": ["devices", "alexa"]},
    "microsoft": {"date": "2024-01", "percentage": 5, "departments": ["gaming", "linkedin"]},
    "salesforce": {"date": "2024-02", "percentage": 8, "departments": ["sales", "engineering"]},
    "stripe": {"date": "2023-11", "percentage": 14, "departments": ["all"]},
    "intel": {"date": "2024-08", "percentage": 15, "departments": ["manufacturing"]},
    "cisco": {"date": "2024-02", "percentage": 5, "departments": ["all"]},
    "snap": {"date": "2024-02", "percentage": 10, "departments": ["all"]},
    "spotify": {"date": "2024-01", "percentage": 6, "departments": ["all"]},
    "discord": {"date": "2024-01", "percentage": 17, "departments": ["all"]},
    "twitch": {"date": "2024-01", "percentage": 35, "departments": ["all"]},
    "unity": {"date": "2024-01", "percentage": 25, "departments": ["all"]},
    "riot": {"date": "2024-01", "percentage": 11, "departments": ["all"]},
}


class SurfacedCandidate(BaseModel):
    """A candidate surfaced due to timing signals."""
    id: str
    full_name: str
    current_title: Optional[str]
    current_company: Optional[str]
    linkedin_url: Optional[str]
    location: Optional[str]

    # Why they're surfaced
    trigger: str            # "layoff", "tenure_cliff", "profile_update", "open_to_work"
    trigger_detail: str     # Human-readable explanation
    urgency: str            # "immediate", "high", "medium"

    # Scores
    readiness_score: float  # 0-1
    fit_score: Optional[float] = None

    # Context
    signals: list[str]
    recommended_action: str
    surfaced_at: datetime


class CandidateSurfacer:
    """
    Proactively surface candidates who just became available.

    This is the "push" complement to search (which is "pull").
    Instead of waiting for founders to search, we alert them
    when good candidates become available.

    Triggers:
    1. Layoff at their company
    2. Approaching 4-year vesting cliff
    3. Profile recently updated
    4. "Open to Work" badge added
    5. Company acquired/merged
    """

    def __init__(self):
        self.readiness_scorer = ReadinessScorer()
        self._supabase = None

    @property
    def supabase(self):
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    async def get_newly_available(
        self,
        company_id: str,
        role_filter: Optional[str] = None,
        days_lookback: int = 30,
        limit: int = 20
    ) -> list[SurfacedCandidate]:
        """
        Get candidates who recently became available.

        Args:
            company_id: The company's network to scan
            role_filter: Optional role to filter for
            days_lookback: How far back to look
            limit: Max candidates to return

        Returns:
            List of SurfacedCandidate, sorted by urgency
        """
        surfaced = []

        # Get all network contacts
        people = await company_db.get_people(company_id, limit=5000)

        for person in people:
            p = person.model_dump() if hasattr(person, "model_dump") else person

            # Apply role filter if specified
            if role_filter:
                title = (p.get("current_title") or "").lower()
                if role_filter.lower() not in title:
                    continue

            # Check each trigger
            candidate = self._check_triggers(p)

            if candidate:
                surfaced.append(candidate)

        # Sort by urgency and readiness
        urgency_order = {"immediate": 0, "high": 1, "medium": 2}
        surfaced.sort(key=lambda x: (urgency_order.get(x.urgency, 3), -x.readiness_score))

        return surfaced[:limit]

    def _check_triggers(self, person: dict) -> Optional[SurfacedCandidate]:
        """Check all triggers for a person."""
        triggers = []
        signals = []
        urgency = "medium"

        company = (person.get("current_company") or "").lower()
        title = person.get("current_title") or ""

        # 1. Check layoff trigger
        layoff_info = self._check_layoff_trigger(company)
        if layoff_info:
            triggers.append(("layoff", layoff_info))
            signals.append(f"Company had {layoff_info['percentage']}% layoffs")
            urgency = "immediate"

        # 2. Check tenure cliff
        tenure_info = self._check_tenure_cliff(person)
        if tenure_info:
            triggers.append(("tenure_cliff", tenure_info))
            signals.append(tenure_info)
            if urgency != "immediate":
                urgency = "high"

        # 3. Check open to work
        if person.get("open_to_work"):
            triggers.append(("open_to_work", "Has Open to Work badge"))
            signals.append("Open to Work badge active")
            urgency = "immediate"

        # 4. Check profile activity
        activity_info = self._check_profile_activity(person)
        if activity_info:
            triggers.append(("profile_update", activity_info))
            signals.append(activity_info)
            if urgency == "medium":
                urgency = "high"

        # Only surface if there's a trigger
        if not triggers:
            return None

        # Get readiness score
        readiness = self.readiness_scorer.score(person)

        # Primary trigger
        primary_trigger = triggers[0]

        return SurfacedCandidate(
            id=str(person.get("id", "")),
            full_name=person.get("full_name") or "Unknown",
            current_title=title,
            current_company=person.get("current_company"),
            linkedin_url=person.get("linkedin_url"),
            location=person.get("location"),
            trigger=primary_trigger[0],
            trigger_detail=str(primary_trigger[1]),
            urgency=urgency,
            readiness_score=readiness["readiness_score"],
            signals=signals,
            recommended_action=self._get_recommended_action(primary_trigger[0], urgency),
            surfaced_at=datetime.utcnow()
        )

    def _check_layoff_trigger(self, company: str) -> Optional[dict]:
        """Check if company had recent layoffs."""
        for company_name, info in RECENT_LAYOFFS.items():
            if company_name in company:
                return info
        return None

    def _check_tenure_cliff(self, person: dict) -> Optional[str]:
        """Check if person is approaching tenure cliff."""
        # Try to get tenure from employment history
        employment = person.get("employment_history") or []

        for job in employment:
            if job.get("is_current") or job.get("current"):
                start = job.get("start_date") or job.get("start")
                if start:
                    try:
                        if isinstance(start, str):
                            if len(start) == 7:  # YYYY-MM
                                start_date = datetime.strptime(start, "%Y-%m")
                            elif len(start) == 10:  # YYYY-MM-DD
                                start_date = datetime.strptime(start, "%Y-%m-%d")
                            else:
                                continue
                        else:
                            continue

                        tenure_months = (datetime.now() - start_date).days / 30

                        if 42 <= tenure_months <= 48:
                            return f"Approaching 4-year cliff ({int(tenure_months)} months)"
                        elif 36 <= tenure_months < 42:
                            return f"Getting close to 4-year cliff ({int(tenure_months)} months)"

                    except (ValueError, TypeError):
                        pass

        return None

    def _check_profile_activity(self, person: dict) -> Optional[str]:
        """Check for recent profile activity."""
        updated = person.get("profile_updated_at") or person.get("updated_at")

        if updated:
            try:
                if isinstance(updated, str):
                    updated_date = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                else:
                    updated_date = updated

                days_ago = (datetime.now(updated_date.tzinfo) - updated_date).days

                if days_ago <= 7:
                    return "Profile updated this week"
                elif days_ago <= 14:
                    return "Profile updated in last 2 weeks"

            except (ValueError, TypeError):
                pass

        return None

    def _get_recommended_action(self, trigger: str, urgency: str) -> str:
        """Get recommended action based on trigger."""
        actions = {
            "layoff": "Reach out today - they may be actively looking",
            "tenure_cliff": "Good time to reconnect - they may be thinking about next steps",
            "open_to_work": "Reach out immediately - they're actively looking",
            "profile_update": "Good time to check in - they may be exploring options"
        }

        base_action = actions.get(trigger, "Consider reaching out")

        if urgency == "immediate":
            return f"URGENT: {base_action}"

        return base_action

    async def get_layoff_affected(
        self,
        company_id: str,
        limit: int = 50
    ) -> list[SurfacedCandidate]:
        """Get network contacts affected by recent layoffs."""
        return await self.get_newly_available(
            company_id=company_id,
            limit=limit
        )

    async def get_vesting_cliff_approaching(
        self,
        company_id: str,
        limit: int = 20
    ) -> list[SurfacedCandidate]:
        """Get network contacts approaching vesting cliffs."""
        all_surfaced = await self.get_newly_available(company_id, limit=100)
        return [s for s in all_surfaced if s.trigger == "tenure_cliff"][:limit]

    async def get_open_to_work(
        self,
        company_id: str,
        limit: int = 20
    ) -> list[SurfacedCandidate]:
        """Get network contacts with Open to Work badge."""
        all_surfaced = await self.get_newly_available(company_id, limit=100)
        return [s for s in all_surfaced if s.trigger == "open_to_work"][:limit]

    async def get_daily_digest(
        self,
        company_id: str
    ) -> dict:
        """
        Get a daily digest of newly available candidates.

        Returns:
            {
                "date": "2024-02-13",
                "total_surfaced": 12,
                "immediate_action": [...],
                "high_priority": [...],
                "summary": "..."
            }
        """
        surfaced = await self.get_newly_available(company_id, limit=50)

        immediate = [s for s in surfaced if s.urgency == "immediate"]
        high = [s for s in surfaced if s.urgency == "high"]
        medium = [s for s in surfaced if s.urgency == "medium"]

        summary_parts = []
        if immediate:
            summary_parts.append(f"{len(immediate)} need immediate action")
        if high:
            summary_parts.append(f"{len(high)} high priority")

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_surfaced": len(surfaced),
            "immediate_action": [s.model_dump() for s in immediate[:5]],
            "high_priority": [s.model_dump() for s in high[:5]],
            "medium_priority": [s.model_dump() for s in medium[:5]],
            "summary": "; ".join(summary_parts) if summary_parts else "No urgent candidates today"
        }
