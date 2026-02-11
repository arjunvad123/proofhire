"""
Colleague Expander - Find former colleagues of network members.

The process:
1. Get employment history for network members
2. For each job, find other people who worked there at the same time
3. Calculate warmth score based on overlap duration
4. Return candidates with warm path through the network member

This requires either:
- PDL enrichment (preferred - has employment history with dates)
- LinkedIn data (if we have it from CSV import)
"""

import logging
from datetime import datetime, date
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService

logger = logging.getLogger(__name__)


class ColleagueExpander:
    """
    Expand the candidate pool by finding former colleagues.

    For each person in your network, find people they actually
    worked with (same company + overlapping dates).
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

    async def find_former_colleagues(
        self,
        network_member_ids: list[UUID] = None,
        role_filter: str = None,
        min_overlap_months: int = 6,
        limit: int = 100
    ) -> dict:
        """
        Find former colleagues of network members.

        Args:
            network_member_ids: Specific people to expand from (or all if None)
            role_filter: Filter colleagues by role (e.g., "ML Engineer")
            min_overlap_months: Minimum months of overlap required
            limit: Maximum colleagues to return

        Returns:
            Dict with discovered colleagues and warm paths
        """
        # Get network members to expand from
        if network_member_ids:
            network_members = []
            for pid in network_member_ids:
                person = await self.db.get_person(self.company_id, pid)
                if person:
                    network_members.append(self._to_dict(person) if hasattr(person, 'model_dump') else person)
        else:
            # Get all network members with employment history
            all_people_raw = await self.db.get_people(
                self.company_id,
                limit=10000,
                filters={"is_from_network": True}
            )
            network_members = [self._to_dict(p) for p in all_people_raw]

        # Filter to those with employment history
        members_with_history = [
            m for m in network_members
            if m.get("employment_history")
        ]

        if not members_with_history:
            logger.warning("No network members have employment history - need enrichment")
            return {
                "status": "needs_enrichment",
                "message": "Network members need employment history enrichment (PDL) before colleague expansion",
                "network_members_analyzed": len(network_members),
                "members_with_history": 0,
                "colleagues_found": 0,
                "colleagues": []
            }

        # Find colleagues for each member
        all_colleagues = []
        companies_analyzed = set()

        for member in members_with_history:
            employment = member.get("employment_history") or []

            for job in employment:
                company = job.get("company") or job.get("company_name")
                if not company:
                    continue

                companies_analyzed.add(company.lower())

                start_date = self._parse_date(job.get("start") or job.get("start_date"))
                end_date = self._parse_date(job.get("end") or job.get("end_date"))

                if not start_date:
                    continue

                if not end_date:
                    end_date = date.today()

                # This would query PDL for people at same company + overlapping dates
                # For now, we'll check against other network members
                colleagues = await self._find_internal_colleagues(
                    member=member,
                    company=company,
                    start_date=start_date,
                    end_date=end_date,
                    all_members=network_members,
                    role_filter=role_filter,
                    min_overlap_months=min_overlap_months
                )

                all_colleagues.extend(colleagues)

        # Deduplicate by person
        seen_ids = set()
        unique_colleagues = []
        for colleague in all_colleagues:
            cid = colleague.get("colleague_id")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                unique_colleagues.append(colleague)

        # Sort by warmth score
        unique_colleagues.sort(key=lambda x: x.get("warmth_score", 0), reverse=True)

        return {
            "status": "success",
            "network_members_analyzed": len(members_with_history),
            "companies_analyzed": len(companies_analyzed),
            "colleagues_found": len(unique_colleagues),
            "colleagues": unique_colleagues[:limit]
        }

    async def _find_internal_colleagues(
        self,
        member: dict,
        company: str,
        start_date: date,
        end_date: date,
        all_members: list[dict],
        role_filter: str = None,
        min_overlap_months: int = 6
    ) -> list[dict]:
        """Find colleagues from the same company among network members."""
        company_lower = company.lower()
        colleagues = []

        for other in all_members:
            # Skip self
            if other.get("id") == member.get("id"):
                continue

            other_employment = other.get("employment_history") or []

            for other_job in other_employment:
                other_company = (other_job.get("company") or other_job.get("company_name") or "").lower()

                # Check if same company
                if not self._companies_match(company_lower, other_company):
                    continue

                other_start = self._parse_date(other_job.get("start") or other_job.get("start_date"))
                other_end = self._parse_date(other_job.get("end") or other_job.get("end_date"))

                if not other_start:
                    continue
                if not other_end:
                    other_end = date.today()

                # Calculate overlap
                overlap_start = max(start_date, other_start)
                overlap_end = min(end_date, other_end)

                if overlap_start < overlap_end:
                    overlap_days = (overlap_end - overlap_start).days
                    overlap_months = overlap_days / 30

                    if overlap_months >= min_overlap_months:
                        # Apply role filter if specified
                        if role_filter:
                            other_title = (other.get("current_title") or "").lower()
                            if role_filter.lower() not in other_title:
                                continue

                        # Calculate warmth based on overlap
                        warmth = self._calculate_colleague_warmth(overlap_months, company)

                        colleagues.append({
                            "colleague_id": str(other.get("id")),
                            "colleague_name": other.get("full_name"),
                            "colleague_title": other.get("current_title"),
                            "colleague_company": other.get("current_company"),
                            "colleague_linkedin": other.get("linkedin_url"),
                            "via_person": {
                                "id": str(member.get("id")),
                                "name": member.get("full_name"),
                                "linkedin_url": member.get("linkedin_url")
                            },
                            "shared_company": company,
                            "overlap_months": round(overlap_months, 1),
                            "overlap_period": f"{overlap_start.isoformat()} to {overlap_end.isoformat()}",
                            "warmth_score": warmth,
                            "relationship": f"Worked together at {company} for {overlap_months:.0f} months",
                            "path_type": "former_colleague"
                        })
                        break  # Found overlap at this company, move to next person

        return colleagues

    def _calculate_colleague_warmth(self, overlap_months: float, company: str) -> float:
        """
        Calculate warmth score based on colleague relationship.

        Factors:
        - Duration of overlap (longer = warmer)
        - Company size (smaller = warmer, they definitely knew each other)
        """
        # Base warmth from duration
        if overlap_months >= 24:
            base_warmth = 0.9
        elif overlap_months >= 12:
            base_warmth = 0.85
        elif overlap_months >= 6:
            base_warmth = 0.75
        else:
            base_warmth = 0.6

        # Adjust for company size (would need company size data)
        # For now, assume startups have higher warmth
        startup_indicators = ["inc", "labs", "ai", "io", "ly"]
        if any(ind in company.lower() for ind in startup_indicators):
            base_warmth = min(1.0, base_warmth + 0.05)

        return round(base_warmth, 2)

    def _companies_match(self, company1: str, company2: str) -> bool:
        """Check if two company names refer to the same company."""
        # Exact match
        if company1 == company2:
            return True

        # Clean and compare
        c1 = company1.replace("inc.", "").replace("inc", "").replace("llc", "").replace(",", "").strip()
        c2 = company2.replace("inc.", "").replace("inc", "").replace("llc", "").replace(",", "").strip()

        if c1 == c2:
            return True

        # One contains the other
        if len(c1) > 3 and len(c2) > 3:
            if c1 in c2 or c2 in c1:
                return True

        return False

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

    async def get_expansion_summary(self) -> dict:
        """Get a summary of expansion potential."""
        # Get all network members
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=10000,
            filters={"is_from_network": True}
        )
        all_people = [self._to_dict(p) for p in all_people_raw]

        # Count those with employment history
        with_history = [p for p in all_people if p.get("employment_history")]

        # Count unique companies
        companies = set()
        for person in with_history:
            for job in person.get("employment_history", []):
                company = job.get("company") or job.get("company_name")
                if company:
                    companies.add(company.lower())

        return {
            "total_network_members": len(all_people),
            "members_with_employment_history": len(with_history),
            "unique_companies": len(companies),
            "top_companies": list(companies)[:20],
            "expansion_potential": len(with_history) > 0,
            "recommendation": self._get_recommendation(len(all_people), len(with_history))
        }

    def _get_recommendation(self, total: int, with_history: int) -> str:
        """Generate recommendation based on expansion potential."""
        if with_history == 0:
            return "Enrich network with employment history (PDL) to enable colleague expansion"
        elif with_history < total * 0.3:
            return f"Only {with_history}/{total} members have employment history. Consider PDL enrichment."
        else:
            return f"{with_history} network members available for colleague expansion"
