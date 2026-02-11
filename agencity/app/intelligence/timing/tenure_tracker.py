"""
Tenure Tracker - Track how long people have been at their current company.

The insight: People are most likely to leave:
1. Around the 2-year mark (initial commitment fulfilled)
2. Around the 4-year mark (vesting cliff)
3. Shortly after company changes (layoffs, reorgs, acquisitions)
"""

import logging
from datetime import datetime, date
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService

logger = logging.getLogger(__name__)


class TenureTracker:
    """
    Track and analyze tenure for network members.

    Identifies people approaching key career milestones
    where they're most likely to consider new opportunities.
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

    async def analyze_network_tenure(self) -> dict:
        """
        Analyze tenure patterns across the network.

        Returns breakdown by tenure bucket and people approaching milestones.
        """
        # Get all network connections
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=10000,
            filters={"is_from_network": True}
        )
        all_people = [self._to_dict(p) for p in all_people_raw]

        # Categorize by tenure
        tenure_buckets = {
            "0-1_years": [],
            "1-2_years": [],
            "2-3_years": [],
            "3-4_years": [],
            "4-5_years": [],
            "5+_years": [],
            "unknown": []
        }

        # People approaching milestones
        approaching_2_year = []
        approaching_4_year = []

        for person in all_people:
            # Try to determine tenure
            tenure_info = self._estimate_tenure(person)
            person["tenure_info"] = tenure_info

            if tenure_info["tenure_months"] is None:
                tenure_buckets["unknown"].append(person)
                continue

            months = tenure_info["tenure_months"]
            years = months / 12

            # Bucket
            if years < 1:
                tenure_buckets["0-1_years"].append(person)
            elif years < 2:
                tenure_buckets["1-2_years"].append(person)
            elif years < 3:
                tenure_buckets["2-3_years"].append(person)
            elif years < 4:
                tenure_buckets["3-4_years"].append(person)
            elif years < 5:
                tenure_buckets["4-5_years"].append(person)
            else:
                tenure_buckets["5+_years"].append(person)

            # Approaching milestones (within 3 months)
            if 21 <= months <= 24:  # 21-24 months
                approaching_2_year.append(person)
            if 45 <= months <= 48:  # 45-48 months (3.75-4 years)
                approaching_4_year.append(person)

        return {
            "total_analyzed": len(all_people),
            "tenure_distribution": {
                bucket: len(people) for bucket, people in tenure_buckets.items()
            },
            "milestones": {
                "approaching_2_year": {
                    "count": len(approaching_2_year),
                    "people": self._summarize_people(approaching_2_year[:10]),
                    "significance": "Initial commitment fulfilled, natural decision point"
                },
                "approaching_4_year": {
                    "count": len(approaching_4_year),
                    "people": self._summarize_people(approaching_4_year[:10]),
                    "significance": "Vesting cliff - equity fully vested"
                }
            }
        }

    def _estimate_tenure(self, person: dict) -> dict:
        """
        Estimate tenure from available data.

        Uses:
        1. Employment history if available
        2. Title changes
        3. LinkedIn connection date as proxy
        """
        # Check for explicit start date in employment history
        employment = person.get("employment_history") or []
        current_job = None

        for job in employment:
            if job.get("is_current") or job.get("current"):
                current_job = job
                break

        if current_job and current_job.get("start_date"):
            start_date = self._parse_date(current_job["start_date"])
            if start_date:
                tenure_months = self._months_since(start_date)
                return {
                    "tenure_months": tenure_months,
                    "start_date": start_date.isoformat(),
                    "source": "employment_history",
                    "confidence": 0.9
                }

        # Check for title that includes "since" or year
        title = person.get("current_title") or ""
        year_in_title = self._extract_year_from_title(title)
        if year_in_title:
            start_date = date(year_in_title, 1, 1)
            tenure_months = self._months_since(start_date)
            return {
                "tenure_months": tenure_months,
                "start_date": start_date.isoformat(),
                "source": "title_year",
                "confidence": 0.5
            }

        # No tenure data available
        return {
            "tenure_months": None,
            "start_date": None,
            "source": "unknown",
            "confidence": 0.0
        }

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

    def _extract_year_from_title(self, title: str) -> Optional[int]:
        """Extract a year from a title (e.g., 'Engineer since 2022')."""
        import re

        # Look for 4-digit year
        match = re.search(r'\b(20[12][0-9])\b', title)
        if match:
            year = int(match.group(1))
            current_year = datetime.now().year
            if 2010 <= year <= current_year:
                return year
        return None

    def _months_since(self, start_date: date) -> int:
        """Calculate months since a date."""
        today = date.today()
        months = (today.year - start_date.year) * 12 + (today.month - start_date.month)
        return max(0, months)

    def _summarize_people(self, people: list[dict]) -> list[dict]:
        """Create summaries of people for output."""
        return [
            {
                "name": p.get("full_name"),
                "title": p.get("current_title"),
                "company": p.get("current_company"),
                "linkedin_url": p.get("linkedin_url"),
                "tenure_months": p.get("tenure_info", {}).get("tenure_months")
            }
            for p in people
        ]

    async def get_people_at_milestone(
        self,
        milestone: str = "4_year",
        window_months: int = 3
    ) -> list[dict]:
        """
        Get people approaching a specific milestone.

        Args:
            milestone: "2_year" or "4_year"
            window_months: How close to milestone (e.g., 3 = within 3 months)

        Returns:
            List of people approaching the milestone
        """
        analysis = await self.analyze_network_tenure()

        if milestone == "2_year":
            return analysis["milestones"]["approaching_2_year"]["people"]
        elif milestone == "4_year":
            return analysis["milestones"]["approaching_4_year"]["people"]
        else:
            return []
