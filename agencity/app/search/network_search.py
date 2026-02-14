"""
Network-First Search - Search within the founder's network FIRST.

This is the core insight: the network itself IS the candidate pool.
Before searching external APIs, find matches in the 3,637 connections.
"""

import logging
import re
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService

logger = logging.getLogger(__name__)


class NetworkSearch:
    """
    Search for candidates within the founder's existing network.

    This should be the FIRST search performed, before any external APIs.
    These candidates have the highest response rate because they already
    know the founder.
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

    def _to_dict_list(self, items: list) -> list[dict]:
        """Convert a list of Pydantic models to list of dicts."""
        return [self._to_dict(item) for item in items]

    async def search(
        self,
        role_title: str,
        required_skills: list[str] = None,
        locations: list[str] = None,
        limit: int = 50
    ) -> list[dict]:
        """
        Search the network for people matching the role.

        Args:
            role_title: The role to search for (e.g., "ML Engineer")
            required_skills: Skills to match
            locations: Preferred locations
            limit: Maximum results to return

        Returns:
            List of matching people from the network with match scores
        """
        # Get all network connections and convert to dicts
        # Use a high limit to get all connections (pagination would be better for very large networks)
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=999999,  # Get all connections (pagination handles this)
            filters={"is_from_network": True}
        )
        all_people = self._to_dict_list(all_people_raw)

        logger.info(f"Searching {len(all_people)} network connections for: {role_title}")

        # Build search patterns from role title
        role_patterns = self._build_role_patterns(role_title)
        skill_patterns = [s.lower() for s in (required_skills or [])]

        matches = []

        for person in all_people:
            title = (person.get("current_title") or "").lower()
            company = (person.get("current_company") or "").lower()
            location = (person.get("location") or "").lower()
            skills = [s.lower() for s in (person.get("skills") or [])]

            # Calculate match score
            score = 0.0
            match_reasons = []

            # Title matching (most important)
            title_score, title_matches = self._match_title(title, role_patterns)
            if title_score > 0:
                score += title_score * 0.5  # 50% weight on title
                match_reasons.extend(title_matches)

            # Skill matching
            skill_score, skill_matches = self._match_skills(title, skills, skill_patterns)
            if skill_score > 0:
                score += skill_score * 0.3  # 30% weight on skills
                match_reasons.extend(skill_matches)

            # Location matching
            if locations:
                loc_score = self._match_location(location, locations)
                score += loc_score * 0.2  # 20% weight on location
                if loc_score > 0:
                    match_reasons.append(f"Location match: {location}")

            # Must have at least title or skill match
            if score > 0.1:
                matches.append({
                    **person,
                    "match_score": round(score, 3),
                    "match_reasons": match_reasons,
                    "connection_type": "direct",  # They're in the network
                    "tier": 1
                })

        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        logger.info(f"Found {len(matches)} matches in network")

        return matches[:limit]

    def _build_role_patterns(self, role_title: str) -> dict:
        """Build search patterns from a role title."""
        role_lower = role_title.lower()

        patterns = {
            "exact": [],
            "primary": [],
            "secondary": [],
            "level": []
        }

        # Exact role patterns
        patterns["exact"].append(role_lower)

        # Primary role keywords (high signal)
        role_keywords = {
            "machine learning": ["machine learning", "ml ", " ml", "deep learning", "ai ", " ai"],
            "data scientist": ["data scientist", "data science"],
            "data engineer": ["data engineer", "data engineering"],
            "software engineer": ["software engineer", "software developer", "swe"],
            "backend": ["backend", "back-end", "back end"],
            "frontend": ["frontend", "front-end", "front end"],
            "fullstack": ["fullstack", "full-stack", "full stack"],
            "devops": ["devops", "dev ops", "sre", "site reliability"],
            "platform": ["platform engineer", "infrastructure"],
            "mobile": ["mobile engineer", "ios", "android"],
            "security": ["security engineer", "appsec", "infosec"],
        }

        for category, keywords in role_keywords.items():
            if any(kw in role_lower for kw in keywords):
                patterns["primary"].extend(keywords)

        # If nothing matched, use the role title words
        if not patterns["primary"]:
            words = role_lower.split()
            patterns["primary"] = [w for w in words if len(w) > 2]

        # Level patterns
        level_keywords = {
            "senior": ["senior", "sr.", "sr "],
            "staff": ["staff"],
            "principal": ["principal"],
            "lead": ["lead", "tech lead"],
            "manager": ["manager", "engineering manager"],
            "director": ["director"],
            "vp": ["vp ", "vice president"],
            "head": ["head of"],
        }

        for level, keywords in level_keywords.items():
            if any(kw in role_lower for kw in keywords):
                patterns["level"].extend(keywords)

        return patterns

    def _match_title(self, title: str, patterns: dict) -> tuple[float, list[str]]:
        """Match a person's title against role patterns."""
        score = 0.0
        reasons = []

        # Exact match (rare but perfect)
        for pattern in patterns["exact"]:
            if pattern in title:
                score += 1.0
                reasons.append(f"Exact title match: {pattern}")
                return score, reasons

        # Primary keyword match
        primary_matches = 0
        for pattern in patterns["primary"]:
            if pattern in title:
                primary_matches += 1
                reasons.append(f"Role match: {pattern}")

        if primary_matches > 0:
            score += min(0.8, primary_matches * 0.4)

        # Level match
        for pattern in patterns["level"]:
            if pattern in title:
                score += 0.1
                reasons.append(f"Level match: {pattern}")
                break

        return score, reasons

    def _match_skills(
        self,
        title: str,
        skills: list[str],
        required: list[str]
    ) -> tuple[float, list[str]]:
        """Match skills (from profile or inferred from title)."""
        if not required:
            return 0.0, []

        score = 0.0
        reasons = []

        # Check explicit skills
        for skill in required:
            if skill in skills:
                score += 0.5
                reasons.append(f"Skill: {skill}")
            # Also check if skill appears in title
            elif skill in title:
                score += 0.3
                reasons.append(f"Skill in title: {skill}")

        # Normalize
        score = min(1.0, score / len(required))

        return score, reasons

    def _match_location(self, location: str, preferred: list[str]) -> float:
        """Match location."""
        if not location or not preferred:
            return 0.0

        for pref in preferred:
            if pref.lower() in location:
                return 1.0

        return 0.0

    async def find_by_companies(
        self,
        companies: list[str],
        role_title: str = None
    ) -> list[dict]:
        """
        Find network connections at specific companies.

        Useful for finding former colleagues or people at target companies.
        """
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=999999,  # Get all (pagination handles this)
            filters={"is_from_network": True}
        )
        all_people = self._to_dict_list(all_people_raw)

        company_patterns = [c.lower() for c in companies]
        matches = []

        for person in all_people:
            current = (person.get("current_company") or "").lower()

            for pattern in company_patterns:
                if pattern in current:
                    # If role specified, also check title
                    if role_title:
                        title = (person.get("current_title") or "").lower()
                        role_patterns = self._build_role_patterns(role_title)
                        title_score, _ = self._match_title(title, role_patterns)
                        if title_score > 0:
                            matches.append({
                                **person,
                                "matched_company": pattern,
                                "tier": 1
                            })
                    else:
                        matches.append({
                            **person,
                            "matched_company": pattern,
                            "tier": 1
                        })
                    break

        return matches

    async def find_by_schools(
        self,
        schools: list[str],
        role_title: str = None
    ) -> list[dict]:
        """
        Find network connections from specific schools.

        School connections have tribal loyalty - Stanford grads help Stanford grads.
        """
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=999999,  # Get all (pagination handles this)
            filters={"is_from_network": True}
        )
        all_people = self._to_dict_list(all_people_raw)

        school_patterns = [s.lower() for s in schools]
        matches = []

        for person in all_people:
            education = person.get("education") or []

            for edu in education:
                school = (edu.get("school") or "").lower()

                for pattern in school_patterns:
                    if pattern in school:
                        if role_title:
                            title = (person.get("current_title") or "").lower()
                            role_patterns = self._build_role_patterns(role_title)
                            title_score, _ = self._match_title(title, role_patterns)
                            if title_score > 0:
                                matches.append({
                                    **person,
                                    "matched_school": school,
                                    "tier": 1
                                })
                        else:
                            matches.append({
                                **person,
                                "matched_school": school,
                                "tier": 1
                            })
                        break

        return matches

    async def get_network_stats(self) -> dict:
        """Get statistics about the network."""
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=999999,  # Get all (pagination handles this)
            filters={"is_from_network": True}
        )
        all_people = self._to_dict_list(all_people_raw)

        # Count by role category
        role_counts = {
            "engineers": 0,
            "managers": 0,
            "executives": 0,
            "recruiters": 0,
            "founders": 0,
            "investors": 0,
            "researchers": 0,
            "other": 0
        }

        companies = set()
        locations = {}

        for person in all_people:
            title = (person.get("current_title") or "").lower()
            company = person.get("current_company")
            location = person.get("location")

            # Categorize
            if any(kw in title for kw in ["engineer", "developer", "swe"]):
                role_counts["engineers"] += 1
            elif any(kw in title for kw in ["manager", "director", "head of"]):
                role_counts["managers"] += 1
            elif any(kw in title for kw in ["ceo", "cto", "cfo", "vp", "chief"]):
                role_counts["executives"] += 1
            elif any(kw in title for kw in ["recruit", "talent", "sourcer"]):
                role_counts["recruiters"] += 1
            elif any(kw in title for kw in ["founder", "co-founder"]):
                role_counts["founders"] += 1
            elif any(kw in title for kw in ["investor", "partner", "vc"]):
                role_counts["investors"] += 1
            elif any(kw in title for kw in ["research", "scientist", "phd"]):
                role_counts["researchers"] += 1
            else:
                role_counts["other"] += 1

            if company:
                companies.add(company)

            if location:
                locations[location] = locations.get(location, 0) + 1

        # Top locations
        top_locations = sorted(
            locations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            "total_connections": len(all_people),
            "role_breakdown": role_counts,
            "unique_companies": len(companies),
            "top_locations": dict(top_locations)
        }
