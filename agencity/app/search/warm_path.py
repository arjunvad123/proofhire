"""
Warm Path Calculator - Find the best introduction path to any candidate.

The key insight: people who worked at the SAME company at the SAME TIME
actually know each other. This lets us find "warm paths" to candidates
through shared employment history.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService

logger = logging.getLogger(__name__)


class WarmPathCalculator:
    """
    Calculate warm introduction paths to candidates.

    A "warm path" is a connection between the founder and a candidate
    through someone in the network who can make an introduction.

    Path types (by warmth score):
    1. Direct connection (1.0) - Already in network
    2. Same small startup (0.95) - Definitely know each other
    3. Same team at company (0.9) - Worked closely together
    4. Same company + overlapping dates (0.85) - Likely know each other
    5. Co-contributors on GitHub (0.8) - Collaborated on code
    6. Co-authors on papers (0.85) - Research collaborators
    7. Same school + overlapping years (0.7) - School connection
    8. Same industry event/community (0.5) - Might know each other
    9. No connection (0.0) - Cold outreach
    """

    def __init__(self, company_id: UUID):
        self.company_id = company_id
        self.db = CompanyDBService()
        self._network_cache = None

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

    async def _get_network(self) -> list[dict]:
        """Get and cache network connections."""
        if self._network_cache is None:
            raw = await self.db.get_people(
                self.company_id,
                limit=10000,
                filters={"is_from_network": True}
            )
            self._network_cache = [self._to_dict(p) for p in raw]
        return self._network_cache

    async def find_warm_path(self, candidate: dict) -> Optional[dict]:
        """
        Find the warmest introduction path to a candidate.

        Args:
            candidate: The target candidate dict

        Returns:
            Dict with path info or None if no warm path exists
        """
        network = await self._get_network()

        best_path = None
        best_warmth = 0.0

        candidate_name = (candidate.get("full_name") or "").lower()
        candidate_company = (candidate.get("current_company") or "").lower()
        candidate_employment = candidate.get("employment_history") or []
        candidate_education = candidate.get("education") or []
        candidate_linkedin = (candidate.get("linkedin_url") or "").lower()

        for connection in network:
            conn_name = (connection.get("full_name") or "").lower()
            conn_company = (connection.get("current_company") or "").lower()
            conn_employment = connection.get("employment_history") or []
            conn_education = connection.get("education") or []
            conn_linkedin = (connection.get("linkedin_url") or "").lower()

            # Check if candidate IS the connection (direct, tier 1)
            if self._is_same_person(candidate, connection):
                return {
                    "path_type": "direct",
                    "warmth_score": 1.0,
                    "via_person": None,
                    "relationship": "Direct connection - already in your network",
                    "action": "Message directly"
                }

            # Check for employment overlap
            overlap = self._find_employment_overlap(
                candidate_employment + [{"company": candidate_company, "current": True}],
                conn_employment + [{"company": conn_company, "current": True}]
            )

            if overlap:
                warmth = overlap["warmth"]
                if warmth > best_warmth:
                    best_warmth = warmth
                    best_path = {
                        "path_type": "shared_employer",
                        "warmth_score": warmth,
                        "via_person": {
                            "id": connection.get("id"),
                            "name": connection.get("full_name"),
                            "title": connection.get("current_title"),
                            "company": connection.get("current_company"),
                            "linkedin_url": connection.get("linkedin_url"),
                        },
                        "relationship": overlap["description"],
                        "action": f"Ask {connection.get('full_name', 'them').split()[0]} for intro"
                    }

            # Check for school overlap
            school_overlap = self._find_school_overlap(
                candidate_education,
                conn_education
            )

            if school_overlap and school_overlap["warmth"] > best_warmth:
                best_warmth = school_overlap["warmth"]
                best_path = {
                    "path_type": "shared_school",
                    "warmth_score": school_overlap["warmth"],
                    "via_person": {
                        "id": connection.get("id"),
                        "name": connection.get("full_name"),
                        "title": connection.get("current_title"),
                        "company": connection.get("current_company"),
                        "linkedin_url": connection.get("linkedin_url"),
                    },
                    "relationship": school_overlap["description"],
                    "action": f"Ask {connection.get('full_name', 'them').split()[0]} for intro (school connection)"
                }

        return best_path

    def _is_same_person(self, person1: dict, person2: dict) -> bool:
        """Check if two person dicts refer to the same person."""
        # Check LinkedIn URL match
        url1 = (person1.get("linkedin_url") or "").lower()
        url2 = (person2.get("linkedin_url") or "").lower()

        if url1 and url2:
            # Normalize LinkedIn URLs
            url1 = url1.replace("https://", "").replace("http://", "").replace("www.", "")
            url2 = url2.replace("https://", "").replace("http://", "").replace("www.", "")
            if url1 == url2:
                return True

        # Check name + company match
        name1 = (person1.get("full_name") or "").lower().strip()
        name2 = (person2.get("full_name") or "").lower().strip()
        company1 = (person1.get("current_company") or "").lower().strip()
        company2 = (person2.get("current_company") or "").lower().strip()

        if name1 and name2 and name1 == name2:
            if company1 and company2 and company1 == company2:
                return True

        return False

    def _find_employment_overlap(
        self,
        employment1: list[dict],
        employment2: list[dict]
    ) -> Optional[dict]:
        """
        Find employment overlap between two people.

        Returns warmth score and description if overlap found.
        """
        best_overlap = None
        best_warmth = 0.0

        for job1 in employment1:
            company1 = (job1.get("company") or job1.get("company_name") or "").lower()
            start1 = self._parse_date(job1.get("start") or job1.get("start_date"))
            end1 = self._parse_date(job1.get("end") or job1.get("end_date"))
            if job1.get("current"):
                end1 = datetime.now()

            if not company1:
                continue

            for job2 in employment2:
                company2 = (job2.get("company") or job2.get("company_name") or "").lower()
                start2 = self._parse_date(job2.get("start") or job2.get("start_date"))
                end2 = self._parse_date(job2.get("end") or job2.get("end_date"))
                if job2.get("current"):
                    end2 = datetime.now()

                if not company2:
                    continue

                # Check if same company
                if not self._companies_match(company1, company2):
                    continue

                # Check for date overlap
                if start1 and end1 and start2 and end2:
                    overlap_start = max(start1, start2)
                    overlap_end = min(end1, end2)

                    if overlap_start < overlap_end:
                        overlap_months = (overlap_end - overlap_start).days / 30

                        # Calculate warmth based on overlap duration
                        if overlap_months >= 12:
                            warmth = 0.85
                            desc = f"Both worked at {company1.title()} for {overlap_months:.0f}+ months overlap"
                        elif overlap_months >= 6:
                            warmth = 0.75
                            desc = f"Both worked at {company1.title()} (6+ month overlap)"
                        else:
                            warmth = 0.6
                            desc = f"Both worked at {company1.title()} (brief overlap)"

                        if warmth > best_warmth:
                            best_warmth = warmth
                            best_overlap = {
                                "warmth": warmth,
                                "description": desc,
                                "company": company1
                            }
                else:
                    # No date info, but same company
                    if 0.5 > best_warmth:
                        best_warmth = 0.5
                        best_overlap = {
                            "warmth": 0.5,
                            "description": f"Both worked at {company1.title()}",
                            "company": company1
                        }

        return best_overlap

    def _find_school_overlap(
        self,
        education1: list[dict],
        education2: list[dict]
    ) -> Optional[dict]:
        """Find school overlap between two people."""
        for edu1 in education1:
            school1 = (edu1.get("school") or edu1.get("school_name") or "").lower()
            year1 = edu1.get("graduation_year") or edu1.get("year")

            if not school1:
                continue

            for edu2 in education2:
                school2 = (edu2.get("school") or edu2.get("school_name") or "").lower()
                year2 = edu2.get("graduation_year") or edu2.get("year")

                if not school2:
                    continue

                # Check if same school
                if not self._schools_match(school1, school2):
                    continue

                # Check for year overlap
                if year1 and year2:
                    try:
                        y1 = int(year1)
                        y2 = int(year2)
                        year_diff = abs(y1 - y2)

                        if year_diff <= 2:
                            return {
                                "warmth": 0.75,
                                "description": f"Both attended {school1.title()} ({y1} & {y2})"
                            }
                        elif year_diff <= 4:
                            return {
                                "warmth": 0.6,
                                "description": f"Both attended {school1.title()}"
                            }
                    except ValueError:
                        pass

                # Same school, no year info
                return {
                    "warmth": 0.5,
                    "description": f"Both attended {school1.title()}"
                }

        return None

    def _companies_match(self, company1: str, company2: str) -> bool:
        """Check if two company names refer to the same company."""
        # Exact match
        if company1 == company2:
            return True

        # Common variations
        c1 = company1.replace("inc.", "").replace("inc", "").replace("llc", "").replace(",", "").strip()
        c2 = company2.replace("inc.", "").replace("inc", "").replace("llc", "").replace(",", "").strip()

        if c1 == c2:
            return True

        # One contains the other
        if len(c1) > 3 and len(c2) > 3:
            if c1 in c2 or c2 in c1:
                return True

        return False

    def _schools_match(self, school1: str, school2: str) -> bool:
        """Check if two school names refer to the same school."""
        # Exact match
        if school1 == school2:
            return True

        # Common variations
        s1 = school1.replace("university", "").replace("college", "").replace("of", "").strip()
        s2 = school2.replace("university", "").replace("college", "").replace("of", "").strip()

        if s1 == s2:
            return True

        # One contains the other
        if len(s1) > 3 and len(s2) > 3:
            if s1 in s2 or s2 in s1:
                return True

        return False

    def _parse_date(self, date_str) -> Optional[datetime]:
        """Parse a date string into datetime."""
        if not date_str:
            return None

        if isinstance(date_str, datetime):
            return date_str

        try:
            # Try YYYY-MM format
            if len(date_str) == 7:
                return datetime.strptime(date_str, "%Y-%m")
            # Try YYYY-MM-DD format
            elif len(date_str) == 10:
                return datetime.strptime(date_str, "%Y-%m-%d")
            # Try YYYY format
            elif len(date_str) == 4:
                return datetime.strptime(date_str, "%Y")
        except ValueError:
            pass

        return None

    async def find_paths_for_candidates(
        self,
        candidates: list[dict]
    ) -> list[dict]:
        """
        Find warm paths for multiple candidates.

        Adds warm_path info to each candidate dict.
        """
        results = []

        for candidate in candidates:
            path = await self.find_warm_path(candidate)

            if path:
                candidate["warm_path"] = path
                candidate["warmth_score"] = path["warmth_score"]
                candidate["tier"] = 2 if path["path_type"] != "direct" else 1
            else:
                candidate["warm_path"] = None
                candidate["warmth_score"] = 0.0
                candidate["tier"] = 4  # Cold

            results.append(candidate)

        return results

    async def filter_warm_candidates(
        self,
        candidates: list[dict],
        min_warmth: float = 0.5
    ) -> list[dict]:
        """Filter to only candidates with warm paths."""
        with_paths = await self.find_paths_for_candidates(candidates)
        return [c for c in with_paths if c.get("warmth_score", 0) >= min_warmth]
