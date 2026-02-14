"""
Warm Path Finder - Find the warmest introduction path to any candidate.

Consolidates all warm path calculation:
1. Direct connection (they're in the network)
2. Former colleague (same company + overlapping dates)
3. School connection (same school + overlapping years)
4. Recommendation (network member recommended them)
5. Recruiter connection (can make intro through recruiter relationship)

Returns the BEST path, not just any path.
"""

import logging
from datetime import datetime, date
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService

logger = logging.getLogger(__name__)


class WarmPathFinder:
    """
    Find the warmest introduction path to a candidate.

    Given a candidate (by LinkedIn URL or profile data),
    find the best way to reach them through the network.
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
                limit=999999,  # Get all (pagination handles this)
                filters={"is_from_network": True}
            )
            self._network_cache = [self._to_dict(p) for p in raw]
        return self._network_cache

    async def find_all_paths(self, candidate: dict) -> dict:
        """
        Find all possible warm paths to a candidate.

        Args:
            candidate: Dict with candidate info (name, linkedin_url, employment_history, education)

        Returns:
            Dict with all paths found, sorted by warmth
        """
        network = await self._get_network()

        paths = []

        # Check if candidate is already in network (direct connection)
        direct = self._find_direct_connection(candidate, network)
        if direct:
            paths.append(direct)

        # Find colleague paths (employment overlap)
        colleague_paths = self._find_colleague_paths(candidate, network)
        paths.extend(colleague_paths)

        # Find school paths (education overlap)
        school_paths = self._find_school_paths(candidate, network)
        paths.extend(school_paths)

        # Find recommendation paths
        rec_paths = await self._find_recommendation_paths(candidate)
        paths.extend(rec_paths)

        # Sort by warmth score
        paths.sort(key=lambda x: x.get("warmth_score", 0), reverse=True)

        # Get best path
        best_path = paths[0] if paths else None

        return {
            "candidate": {
                "name": candidate.get("full_name") or candidate.get("name"),
                "title": candidate.get("current_title") or candidate.get("title"),
                "company": candidate.get("current_company") or candidate.get("company"),
                "linkedin_url": candidate.get("linkedin_url")
            },
            "has_warm_path": len(paths) > 0,
            "warmest_path": best_path,
            "all_paths": paths,
            "path_summary": self._summarize_paths(paths)
        }

    def _find_direct_connection(self, candidate: dict, network: list[dict]) -> Optional[dict]:
        """Check if candidate is directly in the network."""
        candidate_linkedin = (candidate.get("linkedin_url") or "").lower()
        candidate_name = (candidate.get("full_name") or candidate.get("name") or "").lower()
        candidate_company = (candidate.get("current_company") or candidate.get("company") or "").lower()

        for person in network:
            # Check LinkedIn match
            person_linkedin = (person.get("linkedin_url") or "").lower()
            if candidate_linkedin and person_linkedin:
                # Normalize URLs
                c_url = candidate_linkedin.replace("https://", "").replace("http://", "").replace("www.", "")
                p_url = person_linkedin.replace("https://", "").replace("http://", "").replace("www.", "")
                if c_url == p_url:
                    return {
                        "path_type": "direct",
                        "warmth_score": 1.0,
                        "via_person": None,
                        "relationship": "Direct connection - already in your network",
                        "action": "Message directly"
                    }

            # Check name + company match
            person_name = (person.get("full_name") or "").lower()
            person_company = (person.get("current_company") or "").lower()

            if candidate_name and person_name and candidate_name == person_name:
                if candidate_company and person_company and candidate_company == person_company:
                    return {
                        "path_type": "direct",
                        "warmth_score": 1.0,
                        "via_person": None,
                        "relationship": "Direct connection - already in your network",
                        "action": "Message directly"
                    }

        return None

    def _find_colleague_paths(self, candidate: dict, network: list[dict]) -> list[dict]:
        """Find paths through former colleague relationships."""
        paths = []

        candidate_employment = candidate.get("employment_history") or []
        candidate_company = candidate.get("current_company") or candidate.get("company")

        # Add current company to employment
        if candidate_company:
            candidate_employment = candidate_employment + [{"company": candidate_company, "current": True}]

        for person in network:
            person_employment = person.get("employment_history") or []
            person_company = person.get("current_company")

            if person_company:
                person_employment = person_employment + [{"company": person_company, "current": True}]

            overlap = self._find_employment_overlap(candidate_employment, person_employment)

            if overlap:
                paths.append({
                    "path_type": "former_colleague",
                    "warmth_score": overlap["warmth"],
                    "via_person": {
                        "id": str(person.get("id")),
                        "name": person.get("full_name"),
                        "title": person.get("current_title"),
                        "company": person.get("current_company"),
                        "linkedin_url": person.get("linkedin_url")
                    },
                    "relationship": overlap["description"],
                    "overlap_details": overlap,
                    "action": f"Ask {(person.get('full_name') or 'them').split()[0]} for intro"
                })

        return paths

    def _find_school_paths(self, candidate: dict, network: list[dict]) -> list[dict]:
        """Find paths through school connections."""
        paths = []

        candidate_education = candidate.get("education") or []

        for person in network:
            person_education = person.get("education") or []

            overlap = self._find_school_overlap(candidate_education, person_education)

            if overlap:
                paths.append({
                    "path_type": "school_connection",
                    "warmth_score": overlap["warmth"],
                    "via_person": {
                        "id": str(person.get("id")),
                        "name": person.get("full_name"),
                        "title": person.get("current_title"),
                        "company": person.get("current_company"),
                        "linkedin_url": person.get("linkedin_url")
                    },
                    "relationship": overlap["description"],
                    "action": f"Ask {(person.get('full_name') or 'them').split()[0]} for intro (school connection)"
                })

        return paths

    async def _find_recommendation_paths(self, candidate: dict) -> list[dict]:
        """Find if anyone has recommended this candidate."""
        paths = []

        candidate_name = (candidate.get("full_name") or candidate.get("name") or "").lower()
        candidate_linkedin = (candidate.get("linkedin_url") or "").lower()

        # Get recommendations
        recommendations = await self.db.get_recommendations(self.company_id)

        for rec in recommendations:
            rec_name = (rec.get("recommended_name") or "").lower()
            rec_linkedin = (rec.get("recommended_linkedin") or "").lower()

            # Check for match
            name_match = candidate_name and rec_name and (candidate_name in rec_name or rec_name in candidate_name)
            linkedin_match = candidate_linkedin and rec_linkedin and candidate_linkedin == rec_linkedin

            if name_match or linkedin_match:
                # Get recommender info
                recommender_id = rec.get("recommender_id")
                recommender = await self.db.get_person(self.company_id, UUID(recommender_id)) if recommender_id else None

                paths.append({
                    "path_type": "recommendation",
                    "warmth_score": 0.95,
                    "via_person": {
                        "id": str(recommender_id) if recommender_id else None,
                        "name": recommender.get("full_name") if recommender else "Network member",
                        "title": recommender.get("current_title") if recommender else None,
                        "company": recommender.get("current_company") if recommender else None,
                        "linkedin_url": recommender.get("linkedin_url") if recommender else None
                    },
                    "relationship": f"Recommended by network: \"{rec.get('recommended_context', 'Would be a great fit')}\"",
                    "action": "Request introduction through recommender"
                })

        return paths

    def _find_employment_overlap(self, emp1: list[dict], emp2: list[dict]) -> Optional[dict]:
        """Find employment overlap between two people."""
        best_overlap = None
        best_warmth = 0.0

        for job1 in emp1:
            company1 = (job1.get("company") or job1.get("company_name") or "").lower()
            start1 = self._parse_date(job1.get("start") or job1.get("start_date"))
            end1 = self._parse_date(job1.get("end") or job1.get("end_date"))
            if job1.get("current"):
                end1 = date.today()

            if not company1:
                continue

            for job2 in emp2:
                company2 = (job2.get("company") or job2.get("company_name") or "").lower()
                start2 = self._parse_date(job2.get("start") or job2.get("start_date"))
                end2 = self._parse_date(job2.get("end") or job2.get("end_date"))
                if job2.get("current"):
                    end2 = date.today()

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
                                "company": company1,
                                "overlap_months": round(overlap_months, 1)
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

    def _find_school_overlap(self, edu1: list[dict], edu2: list[dict]) -> Optional[dict]:
        """Find school overlap between two people."""
        for e1 in edu1:
            school1 = (e1.get("school") or e1.get("school_name") or "").lower()
            year1 = e1.get("graduation_year") or e1.get("year")

            if not school1:
                continue

            for e2 in edu2:
                school2 = (e2.get("school") or e2.get("school_name") or "").lower()
                year2 = e2.get("graduation_year") or e2.get("year")

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
        if company1 == company2:
            return True

        c1 = company1.replace("inc.", "").replace("inc", "").replace("llc", "").replace(",", "").strip()
        c2 = company2.replace("inc.", "").replace("inc", "").replace("llc", "").replace(",", "").strip()

        if c1 == c2:
            return True

        if len(c1) > 3 and len(c2) > 3:
            if c1 in c2 or c2 in c1:
                return True

        return False

    def _schools_match(self, school1: str, school2: str) -> bool:
        """Check if two school names refer to the same school."""
        if school1 == school2:
            return True

        s1 = school1.replace("university", "").replace("college", "").replace("of", "").strip()
        s2 = school2.replace("university", "").replace("college", "").replace("of", "").strip()

        if s1 == s2:
            return True

        if len(s1) > 3 and len(s2) > 3:
            if s1 in s2 or s2 in s1:
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
                if len(date_val) == 7:
                    return datetime.strptime(date_val, "%Y-%m").date()
                elif len(date_val) == 10:
                    return datetime.strptime(date_val, "%Y-%m-%d").date()
                elif len(date_val) == 4:
                    return datetime.strptime(date_val, "%Y").date()
            except ValueError:
                pass

        return None

    def _summarize_paths(self, paths: list[dict]) -> dict:
        """Summarize the paths found."""
        by_type = {}
        for path in paths:
            path_type = path.get("path_type", "unknown")
            by_type[path_type] = by_type.get(path_type, 0) + 1

        return {
            "total_paths": len(paths),
            "by_type": by_type,
            "best_warmth": paths[0]["warmth_score"] if paths else 0,
            "recommended_approach": self._get_approach_recommendation(paths)
        }

    def _get_approach_recommendation(self, paths: list[dict]) -> str:
        """Get recommendation for how to approach the candidate."""
        if not paths:
            return "No warm path - consider cold outreach or finding a connection"

        best = paths[0]
        path_type = best.get("path_type")
        warmth = best.get("warmth_score", 0)

        if path_type == "direct":
            return "Message directly - they're already in your network"
        elif path_type == "recommendation":
            return "Ask the recommender to make an introduction"
        elif warmth >= 0.8:
            return f"Strong warm path - request intro through {best.get('via_person', {}).get('name', 'connection')}"
        elif warmth >= 0.6:
            return f"Good warm path - worth requesting intro"
        else:
            return "Weak warm path - consider finding a stronger connection"
