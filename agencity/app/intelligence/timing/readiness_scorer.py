"""
Readiness Scorer - Predict how ready someone is to consider a new role.

Combines multiple signals into a single readiness score:
1. Tenure (approaching cliff = higher readiness)
2. Company signals (layoffs = higher readiness)
3. Title signals ("consultant" = higher readiness)
4. Activity signals (profile updates = higher readiness)

Score range: 0.0 (not ready) to 1.0 (very ready)
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService

logger = logging.getLogger(__name__)


# Companies known to have had recent layoffs
LAYOFF_COMPANIES = {
    "meta": {"date": "2024-01", "scale": "large"},
    "google": {"date": "2024-01", "scale": "large"},
    "amazon": {"date": "2024-01", "scale": "large"},
    "microsoft": {"date": "2024-01", "scale": "medium"},
    "salesforce": {"date": "2024-01", "scale": "medium"},
    "cisco": {"date": "2024-02", "scale": "medium"},
    "intel": {"date": "2024-08", "scale": "large"},
    "dell": {"date": "2024-02", "scale": "medium"},
    "twilio": {"date": "2024-02", "scale": "medium"},
    "snap": {"date": "2024-02", "scale": "medium"},
    "discord": {"date": "2024-01", "scale": "small"},
    "spotify": {"date": "2024-01", "scale": "medium"},
    "zoom": {"date": "2024-02", "scale": "small"},
    "doordash": {"date": "2024-01", "scale": "small"},
    "instacart": {"date": "2024-01", "scale": "small"},
    "robinhood": {"date": "2024-01", "scale": "medium"},
    "coinbase": {"date": "2024-01", "scale": "medium"},
    "stripe": {"date": "2023-11", "scale": "small"},
    "lyft": {"date": "2024-02", "scale": "medium"},
    "paypal": {"date": "2024-01", "scale": "medium"},
    "ebay": {"date": "2024-01", "scale": "medium"},
}

# Title patterns that indicate openness to opportunities
OPEN_TITLE_SIGNALS = [
    ("open to work", 1.0),
    ("open to opportunities", 1.0),
    ("seeking", 0.9),
    ("looking for", 0.9),
    ("available", 0.8),
    ("consultant", 0.7),
    ("advisor", 0.6),
    ("freelance", 0.7),
    ("contractor", 0.6),
    ("independent", 0.5),
    ("ex-", 0.8),
    ("former", 0.7),
    ("recently", 0.6),
    ("transitioned", 0.5),
    ("taking time", 0.4),
    ("on break", 0.4),
    ("sabbatical", 0.4),
]


class ReadinessScorer:
    """
    Score how ready a person is to consider new opportunities.

    Uses a weighted combination of signals:
    - Tenure signals (30% weight)
    - Company signals (30% weight)
    - Title signals (20% weight)
    - Activity signals (20% weight)
    """

    def __init__(self, company_id: UUID):
        self.company_id = company_id
        self.db = CompanyDBService()

    def _to_dict(self, obj) -> dict:
        """Convert a Pydantic model or object to a dict."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif hasattr(obj, "dict"):
            return obj.dict()
        elif isinstance(obj, dict):
            return obj
        else:
            return dict(obj)

    def calculate_readiness_score(self, person: dict) -> dict:
        """
        Calculate readiness score for a person.

        Returns:
            Dict with score, breakdown, and recommended action
        """
        signals = {
            "tenure": self._score_tenure(person),
            "company": self._score_company(person),
            "title": self._score_title(person),
            "activity": self._score_activity(person)
        }

        # Weighted combination
        weights = {
            "tenure": 0.30,
            "company": 0.30,
            "title": 0.20,
            "activity": 0.20
        }

        total_score = sum(
            signals[key]["score"] * weights[key]
            for key in signals
        )

        # Collect all active signals
        active_signals = []
        for category, signal_data in signals.items():
            if signal_data["score"] > 0:
                active_signals.extend(signal_data.get("reasons", []))

        # Determine urgency and recommendation
        urgency, recommendation = self._get_recommendation(total_score, active_signals)

        return {
            "readiness_score": round(total_score, 3),
            "urgency": urgency,
            "recommendation": recommendation,
            "signal_breakdown": {
                category: {
                    "score": round(data["score"], 3),
                    "weighted_contribution": round(data["score"] * weights[category], 3),
                    "reasons": data.get("reasons", [])
                }
                for category, data in signals.items()
            },
            "active_signals": active_signals
        }

    def _score_tenure(self, person: dict) -> dict:
        """Score based on tenure at current company."""
        score = 0.0
        reasons = []

        # Try to determine tenure
        tenure_months = self._get_tenure_months(person)

        if tenure_months is None:
            return {"score": 0.0, "reasons": ["Tenure unknown"]}

        # Score based on tenure duration
        if 42 <= tenure_months <= 48:  # 3.5-4 years (approaching cliff)
            score = 1.0
            reasons.append(f"Approaching 4-year vesting cliff ({tenure_months} months)")
        elif 36 <= tenure_months < 42:  # 3-3.5 years
            score = 0.7
            reasons.append(f"Getting close to vesting cliff ({tenure_months} months)")
        elif 24 <= tenure_months < 36:  # 2-3 years
            score = 0.4
            reasons.append(f"Mid-tenure, natural decision point ({tenure_months} months)")
        elif tenure_months > 48:  # Past cliff
            score = 0.6
            reasons.append(f"Past vesting cliff ({tenure_months} months) - no equity retention")
        else:
            score = 0.1
            reasons.append(f"Early tenure ({tenure_months} months)")

        return {"score": score, "reasons": reasons}

    def _score_company(self, person: dict) -> dict:
        """Score based on company signals (layoffs, etc.)."""
        score = 0.0
        reasons = []

        company = (person.get("current_company") or "").lower()

        if not company:
            return {"score": 0.0, "reasons": []}

        # Check for layoff companies
        for company_name, layoff_info in LAYOFF_COMPANIES.items():
            if company_name in company:
                scale = layoff_info["scale"]
                if scale == "large":
                    score = 1.0
                    reasons.append(f"Company ({company}) had large layoffs recently")
                elif scale == "medium":
                    score = 0.7
                    reasons.append(f"Company ({company}) had medium layoffs recently")
                else:
                    score = 0.4
                    reasons.append(f"Company ({company}) had some layoffs recently")
                break

        return {"score": score, "reasons": reasons}

    def _score_title(self, person: dict) -> dict:
        """Score based on title signals."""
        score = 0.0
        reasons = []

        title = (person.get("current_title") or "").lower()
        headline = (person.get("headline") or "").lower()

        combined = f"{title} {headline}"

        for signal, signal_score in OPEN_TITLE_SIGNALS:
            if signal in combined:
                if signal_score > score:
                    score = signal_score
                    reasons = [f"Title signal: '{signal}'"]

        return {"score": score, "reasons": reasons}

    def _score_activity(self, person: dict) -> dict:
        """Score based on activity signals."""
        score = 0.0
        reasons = []

        # Check for "Open to Work" badge
        if person.get("open_to_work"):
            score = 1.0
            reasons.append("Has 'Open to Work' badge")
            return {"score": score, "reasons": reasons}

        # Check for recent profile updates
        last_updated = person.get("profile_updated_at") or person.get("updated_at")
        if last_updated:
            try:
                if isinstance(last_updated, str):
                    updated_date = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                else:
                    updated_date = last_updated

                days_since_update = (datetime.now(updated_date.tzinfo) - updated_date).days

                if days_since_update <= 7:
                    score = 0.8
                    reasons.append("Profile updated in last week")
                elif days_since_update <= 30:
                    score = 0.5
                    reasons.append("Profile updated in last month")
            except (ValueError, TypeError):
                pass

        return {"score": score, "reasons": reasons}

    def _get_tenure_months(self, person: dict) -> Optional[int]:
        """Extract tenure in months from person data."""
        # Check for explicit tenure_months
        if person.get("tenure_months"):
            return person["tenure_months"]

        # Check employment history
        employment = person.get("employment_history") or []
        for job in employment:
            if job.get("is_current") or job.get("current"):
                start = job.get("start_date") or job.get("start")
                if start:
                    start_date = self._parse_date(start)
                    if start_date:
                        today = date.today()
                        months = (today.year - start_date.year) * 12 + (today.month - start_date.month)
                        return max(0, months)

        return None

    def _parse_date(self, date_val) -> Optional[date]:
        """Parse various date formats."""
        if date_val is None:
            return None

        if isinstance(date_val, date):
            return date_val

        if isinstance(date_val, datetime):
            return date_val.date()

        if isinstance(date_val, str):
            try:
                if len(date_val) == 7:  # YYYY-MM
                    return datetime.strptime(date_val, "%Y-%m").date()
                elif len(date_val) == 10:  # YYYY-MM-DD
                    return datetime.strptime(date_val, "%Y-%m-%d").date()
                elif len(date_val) == 4:  # YYYY
                    return datetime.strptime(date_val, "%Y").date()
            except ValueError:
                pass

        return None

    def _get_recommendation(self, score: float, signals: list[str]) -> tuple[str, str]:
        """Get urgency and recommendation based on score."""
        if score >= 0.8:
            return (
                "immediate",
                "High readiness - reach out immediately. Multiple strong signals."
            )
        elif score >= 0.6:
            return (
                "high",
                "Strong readiness signals - prioritize outreach this week."
            )
        elif score >= 0.4:
            return (
                "medium",
                "Moderate signals - good candidate for outreach."
            )
        elif score >= 0.2:
            return (
                "low",
                "Some signals present - consider for broader outreach."
            )
        else:
            return (
                "wait",
                "No strong signals - add to watch list for timing."
            )

    async def score_all_network(self) -> dict:
        """Score readiness for entire network."""
        # Get all network connections
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=999999,  # Get all (pagination handles this)
            filters={"is_from_network": True}
        )
        all_people = [self._to_dict(p) for p in all_people_raw]

        # Score each person
        scored = []
        for person in all_people:
            readiness = self.calculate_readiness_score(person)
            scored.append({
                **person,
                "readiness": readiness
            })

        # Sort by readiness score
        scored.sort(key=lambda x: x["readiness"]["readiness_score"], reverse=True)

        # Group by urgency
        by_urgency = {
            "immediate": [],
            "high": [],
            "medium": [],
            "low": [],
            "wait": []
        }

        for person in scored:
            urgency = person["readiness"]["urgency"]
            if len(by_urgency.get(urgency, [])) < 20:  # Limit each category
                by_urgency[urgency].append({
                    "id": str(person.get("id")),
                    "name": person.get("full_name"),
                    "title": person.get("current_title"),
                    "company": person.get("current_company"),
                    "linkedin_url": person.get("linkedin_url"),
                    "readiness_score": person["readiness"]["readiness_score"],
                    "signals": person["readiness"]["active_signals"]
                })

        return {
            "total_scored": len(scored),
            "by_urgency": {
                urgency: {
                    "count": len([p for p in scored if p["readiness"]["urgency"] == urgency]),
                    "top_candidates": people
                }
                for urgency, people in by_urgency.items()
            },
            "summary": {
                "immediate_action": len([p for p in scored if p["readiness"]["urgency"] == "immediate"]),
                "high_priority": len([p for p in scored if p["readiness"]["urgency"] == "high"]),
                "medium_priority": len([p for p in scored if p["readiness"]["urgency"] == "medium"]),
            }
        }

    async def get_timing_alerts(self) -> list[dict]:
        """Get timing-based alerts for the network."""
        scored = await self.score_all_network()

        alerts = []

        # Immediate action alerts
        immediate = scored["by_urgency"].get("immediate", {}).get("top_candidates", [])
        if immediate:
            alerts.append({
                "type": "immediate_action",
                "priority": "critical",
                "count": len(immediate),
                "message": f"{len(immediate)} people with very high readiness signals",
                "action": "Reach out today",
                "people": immediate[:5]
            })

        # High priority alerts
        high = scored["by_urgency"].get("high", {}).get("top_candidates", [])
        if high:
            alerts.append({
                "type": "high_priority",
                "priority": "high",
                "count": len(high),
                "message": f"{len(high)} people with strong readiness signals",
                "action": "Prioritize outreach this week",
                "people": high[:5]
            })

        return alerts
