"""
Vesting Predictor - Predict when people's equity vests.

Standard tech vesting: 4-year with 1-year cliff
- 25% vests at 1-year anniversary
- Then monthly for remaining 3 years
- 100% vested at 4 years

The 4-year mark is a natural decision point:
"I've maxed out my equity. Do I stay or go?"

Reach out 2-3 months BEFORE the cliff for best results.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService

logger = logging.getLogger(__name__)


# Common vesting schedules by company
COMPANY_VESTING_SCHEDULES = {
    # Big tech - standard 4-year
    "google": {"cliff_years": 1, "total_years": 4},
    "meta": {"cliff_years": 1, "total_years": 4},
    "apple": {"cliff_years": 1, "total_years": 4},
    "amazon": {"cliff_years": 1, "total_years": 4},  # Note: Amazon is weird, backloaded
    "microsoft": {"cliff_years": 1, "total_years": 4},
    "netflix": {"cliff_years": 0, "total_years": 4},  # Monthly from day 1

    # Startups - usually 4-year with cliff
    "default": {"cliff_years": 1, "total_years": 4}
}


class VestingPredictor:
    """
    Predict vesting cliffs and optimal outreach timing.

    Key insight: The 4-year vesting cliff is one of the most
    predictable career decision points. People who would never
    respond to a recruiter might be very receptive 2 months
    before their equity fully vests.
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

    def predict_vesting_cliff(
        self,
        start_date: date,
        company_name: str = None
    ) -> dict:
        """
        Predict vesting cliff date based on start date.

        Args:
            start_date: When the person started at the company
            company_name: Company name (for company-specific schedules)

        Returns:
            Dict with cliff dates and optimal outreach window
        """
        # Get company-specific schedule or default
        schedule = COMPANY_VESTING_SCHEDULES.get(
            (company_name or "").lower(),
            COMPANY_VESTING_SCHEDULES["default"]
        )

        # Calculate cliff dates
        one_year_cliff = start_date + timedelta(days=365 * schedule["cliff_years"]) if schedule["cliff_years"] > 0 else None
        four_year_cliff = start_date + timedelta(days=365 * schedule["total_years"])

        today = date.today()

        # Calculate days until each cliff
        days_to_one_year = (one_year_cliff - today).days if one_year_cliff else None
        days_to_four_year = (four_year_cliff - today).days

        # Determine current vesting status
        if today < start_date:
            status = "not_started"
            vested_percent = 0
        elif one_year_cliff and today < one_year_cliff:
            status = "pre_cliff"
            vested_percent = 0
        elif today < four_year_cliff:
            status = "vesting"
            # Calculate approximate vested percentage
            days_vested = (today - (one_year_cliff or start_date)).days
            total_days = (four_year_cliff - (one_year_cliff or start_date)).days
            vested_percent = 25 + (75 * days_vested / total_days) if total_days > 0 else 25
        else:
            status = "fully_vested"
            vested_percent = 100

        # Calculate optimal outreach window
        # Best time: 2-3 months before 4-year cliff
        optimal_outreach_start = four_year_cliff - timedelta(days=90)  # 3 months before
        optimal_outreach_end = four_year_cliff - timedelta(days=30)    # 1 month before

        in_optimal_window = optimal_outreach_start <= today <= optimal_outreach_end

        return {
            "start_date": start_date.isoformat(),
            "one_year_cliff": one_year_cliff.isoformat() if one_year_cliff else None,
            "four_year_cliff": four_year_cliff.isoformat(),
            "status": status,
            "vested_percent": round(vested_percent, 1),
            "days_to_one_year_cliff": days_to_one_year,
            "days_to_four_year_cliff": days_to_four_year,
            "optimal_outreach_window": {
                "start": optimal_outreach_start.isoformat(),
                "end": optimal_outreach_end.isoformat(),
                "in_window_now": in_optimal_window
            },
            "recommendation": self._get_outreach_recommendation(
                days_to_four_year, in_optimal_window, status
            )
        }

    def _get_outreach_recommendation(
        self,
        days_to_cliff: int,
        in_optimal_window: bool,
        status: str
    ) -> dict:
        """Generate outreach recommendation based on vesting status."""
        if status == "fully_vested":
            return {
                "action": "reach_out_now",
                "urgency": "high",
                "reason": "Equity fully vested - they have no financial incentive to stay",
                "message_angle": "They can make a move without leaving money on the table"
            }

        if in_optimal_window:
            return {
                "action": "reach_out_now",
                "urgency": "high",
                "reason": f"Optimal window - {days_to_cliff} days until vesting cliff",
                "message_angle": "Perfect timing to discuss what's next after their equity vests"
            }

        if 0 < days_to_cliff <= 120:  # Within 4 months
            return {
                "action": "reach_out_soon",
                "urgency": "medium",
                "reason": f"Approaching cliff - {days_to_cliff} days",
                "message_angle": "Plant the seed before they start actively looking"
            }

        if days_to_cliff > 120:
            return {
                "action": "wait",
                "urgency": "low",
                "reason": f"Too early - {days_to_cliff} days until cliff",
                "message_angle": "Add to watch list, reach out when closer to cliff"
            }

        return {
            "action": "standard_outreach",
            "urgency": "medium",
            "reason": "No specific timing advantage",
            "message_angle": "Standard approach based on fit and interest"
        }

    async def find_approaching_cliffs(
        self,
        days_ahead: int = 90
    ) -> list[dict]:
        """
        Find network members approaching vesting cliffs.

        Args:
            days_ahead: How many days ahead to look

        Returns:
            List of people approaching their 4-year cliff
        """
        # Get all network connections
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=10000,
            filters={"is_from_network": True}
        )
        all_people = [self._to_dict(p) for p in all_people_raw]

        approaching_cliff = []
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)

        for person in all_people:
            # Try to determine start date
            start_date = self._get_start_date(person)

            if not start_date:
                continue

            # Calculate 4-year cliff
            four_year_cliff = start_date + timedelta(days=365 * 4)

            # Check if within window
            if today <= four_year_cliff <= cutoff:
                days_until = (four_year_cliff - today).days
                vesting_info = self.predict_vesting_cliff(start_date, person.get("current_company"))

                approaching_cliff.append({
                    "person": {
                        "id": str(person.get("id")),
                        "name": person.get("full_name"),
                        "title": person.get("current_title"),
                        "company": person.get("current_company"),
                        "linkedin_url": person.get("linkedin_url")
                    },
                    "vesting": {
                        "start_date": start_date.isoformat(),
                        "cliff_date": four_year_cliff.isoformat(),
                        "days_until_cliff": days_until,
                        "vested_percent": vesting_info["vested_percent"]
                    },
                    "outreach": vesting_info["recommendation"]
                })

        # Sort by days until cliff (most urgent first)
        approaching_cliff.sort(key=lambda x: x["vesting"]["days_until_cliff"])

        logger.info(f"Found {len(approaching_cliff)} people approaching vesting cliff in next {days_ahead} days")

        return approaching_cliff

    def _get_start_date(self, person: dict) -> Optional[date]:
        """Try to determine when a person started their current job."""
        # Check employment history
        employment = person.get("employment_history") or []
        for job in employment:
            if job.get("is_current") or job.get("current"):
                start = job.get("start_date") or job.get("start")
                if start:
                    return self._parse_date(start)

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
