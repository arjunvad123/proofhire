"""
Supabase service for querying the candidate database.
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SupabaseService:
    """
    Async client for Supabase REST API.

    Queries the candidate database with filtering and pagination.
    """

    def __init__(self):
        self.base_url = settings.supabase_url
        self.api_key = settings.supabase_key
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        table: str,
        params: dict[str, Any] | None = None,
        select: str = "*",
    ) -> list[dict]:
        """Make a GET request to Supabase REST API."""
        url = f"{self.base_url}/rest/v1/{table}"

        query_params = params or {}
        query_params["select"] = select

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=query_params,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Supabase request failed: {e}")
                return []

    async def get_candidates(
        self,
        limit: int = 50,
        offset: int = 0,
        with_github: bool = False,
        skills_filter: list[str] | None = None,
        role_types: list[str] | None = None,
    ) -> list[dict]:
        """
        Get candidates from the database.

        Args:
            limit: Max candidates to return
            offset: Pagination offset
            with_github: Only return candidates with GitHub connected
            skills_filter: Filter by skills (any match)
            role_types: Filter by role types
        """
        params = {
            "limit": limit,
            "offset": offset,
            "order": "created_at.desc",
        }

        # Filter for candidates with GitHub
        if with_github:
            params["github_username"] = "not.is.null"

        select = "id,name,email,skills,university,location,github_username,role_type,years_of_experience,major,objectives,technical_projects,experience"

        candidates = await self._request("candidates", params, select)

        # Post-filter by skills if specified (Supabase text search is limited)
        if skills_filter and candidates:
            filtered = []
            for c in candidates:
                skills = (c.get("skills") or "").lower()
                if any(s.lower() in skills for s in skills_filter):
                    filtered.append(c)
            return filtered[:limit]

        return candidates

    async def get_candidate_by_id(self, candidate_id: str) -> dict | None:
        """Get a single candidate by ID."""
        params = {"id": f"eq.{candidate_id}"}
        select = "*"

        results = await self._request("candidates", params, select)
        return results[0] if results else None

    async def get_github_repos(
        self,
        candidate_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """Get GitHub repositories for a candidate."""
        params = {
            "candidate_id": f"eq.{candidate_id}",
            "order": "stargazers_count.desc",
            "limit": limit,
        }
        select = "id,name,full_name,description,language,stargazers_count,topics,html_url"

        return await self._request("github_repositories", params, select)

    async def search_candidates(
        self,
        query: str,
        limit: int = 50,
    ) -> list[dict]:
        """
        Search candidates by skills, university, or name.

        Uses ilike for case-insensitive partial matching.
        """
        # Build OR filter for multiple fields
        params = {
            "or": f"(skills.ilike.*{query}*,university.ilike.*{query}*,name.ilike.*{query}*,technical_projects.ilike.*{query}*)",
            "limit": limit,
            "order": "created_at.desc",
        }

        select = "id,name,email,skills,university,location,github_username,role_type,years_of_experience,major,objectives,technical_projects,experience"

        return await self._request("candidates", params, select)

    async def get_candidates_with_github_data(
        self,
        limit: int = 20,
    ) -> list[dict]:
        """
        Get candidates who have GitHub connected, with their top repos.

        Returns enriched candidate data with repository information.
        """
        # First get candidates with GitHub
        candidates = await self.get_candidates(
            limit=limit,
            with_github=True,
        )

        # Enrich with GitHub repos
        enriched = []
        for candidate in candidates:
            repos = await self.get_github_repos(candidate["id"], limit=5)
            candidate["github_repos"] = repos
            enriched.append(candidate)

        return enriched

    async def search_for_role(
        self,
        role_keywords: list[str],
        must_have_skills: list[str] | None = None,
        nice_to_have_skills: list[str] | None = None,
        location_preferences: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Search candidates matching a role blueprint.

        This is the main search method used by the NetworkSource.
        """
        all_candidates = []

        # High-value AI/ML keywords to search
        ai_keywords = ["langchain", "rag", "llm", "openai", "gpt", "pytorch", "tensorflow",
                       "machine learning", "ai", "nlp", "prompt"]

        # Combine role keywords with AI keywords
        search_keywords = list(set(role_keywords[:5] + ai_keywords[:5]))

        # Search by each keyword
        for keyword in search_keywords:
            results = await self.search_candidates(keyword, limit=30)
            all_candidates.extend(results)

        # Also get top candidates with GitHub (they're often the best)
        github_candidates = await self.get_candidates(limit=50, with_github=True)
        all_candidates.extend(github_candidates)

        # Deduplicate by ID
        seen_ids = set()
        unique_candidates = []
        for c in all_candidates:
            if c["id"] not in seen_ids:
                seen_ids.add(c["id"])
                unique_candidates.append(c)

        # Score and rank candidates
        scored = []
        for candidate in unique_candidates:
            score = 0
            skills = (candidate.get("skills") or "").lower()
            projects = (candidate.get("technical_projects") or "").lower()
            experience = (candidate.get("experience") or "").lower()
            combined = skills + " " + projects + " " + experience

            # Strong AI/ML signals (highest weight)
            ai_terms = ["langchain", "langgraph", "rag", "llm", "openai", "gpt", "anthropic",
                        "prompt engineering", "vector", "embedding", "pytorch", "tensorflow"]
            for term in ai_terms:
                if term in combined:
                    score += 20

            # PRODUCTION EXPERIENCE boost - actual work building these systems
            experience = (candidate.get("experience") or "").lower()
            projects = (candidate.get("technical_projects") or "").lower()

            # Check for actual production/work experience
            production_signals = ["intern", "engineer", "built", "deployed", "production",
                                  "shipped", "company", "startup"]
            has_production_exp = any(s in experience for s in production_signals)

            # Check for company names known for AI work
            ai_companies = ["nokia", "cohere", "anthropic", "openai", "google", "meta",
                            "microsoft", "amazon", "nvidia", "deepmind"]
            works_at_ai_company = any(c in experience for c in ai_companies)

            # Boost for production experience with AI skills
            if has_production_exp:
                for term in ai_terms[:5]:
                    if term in combined:
                        score += 20
                break_applied = True

            # Major boost for working at AI companies
            if works_at_ai_company:
                score += 50

            # Boost for hackathon wins (indicates shipping ability)
            if "first place" in projects.lower() or "winner" in projects.lower():
                score += 25

            # Boost for projects with real metrics (indicates impact)
            if "users" in projects or "deployed" in projects or "production" in projects:
                score += 15

            # Must-have skills boost
            if must_have_skills:
                for skill in must_have_skills:
                    if skill.lower() in combined:
                        score += 10

            # Nice-to-have skills boost
            if nice_to_have_skills:
                for skill in nice_to_have_skills:
                    if skill.lower() in combined:
                        score += 5

            # Location preference boost (high weight for matches)
            if location_preferences:
                location = (candidate.get("location") or "").lower()
                university = (candidate.get("university") or "").lower()
                for pref in location_preferences:
                    if pref.lower() in location or pref.lower() in university:
                        score += 25  # Strong boost for location match

            # Top university boost
            top_schools = ["waterloo", "stanford", "mit", "berkeley", "carnegie", "harvard", "columbia"]
            university = (candidate.get("university") or "").lower()
            for school in top_schools:
                if school in university:
                    score += 10

            # GitHub connected boost
            if candidate.get("github_username"):
                score += 10

            # Rich project descriptions indicate quality
            if len(projects) > 200:
                score += 5

            scored.append((score, candidate))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        return [c for _, c in scored[:limit]]

    async def get_top_candidates_for_demo(self, limit: int = 10) -> list[dict]:
        """
        Get the best candidates for demo purposes.

        Prioritizes candidates with:
        - GitHub connected
        - Strong skills
        - Good universities
        """
        # Get candidates with GitHub and interesting skills
        params = {
            "github_username": "not.is.null",
            "limit": limit * 2,  # Get extra to filter
            "order": "created_at.desc",
        }

        select = "id,name,email,skills,university,location,github_username,role_type,years_of_experience,major,technical_projects,experience"

        candidates = await self._request("candidates", params, select)

        # Score for demo quality
        scored = []
        for c in candidates:
            score = 0
            skills = (c.get("skills") or "").lower()
            projects = (c.get("technical_projects") or "").lower()
            university = (c.get("university") or "").lower()

            # AI/ML skills
            ai_terms = ["llm", "langchain", "rag", "pytorch", "tensorflow", "openai", "gpt", "machine learning", "ml"]
            for term in ai_terms:
                if term in skills or term in projects:
                    score += 5

            # Top universities
            top_schools = ["waterloo", "stanford", "mit", "berkeley", "carnegie", "harvard", "columbia"]
            for school in top_schools:
                if school in university:
                    score += 3

            # Rich project descriptions
            if len(projects) > 200:
                score += 2

            scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Get top candidates and enrich with repos
        top_candidates = [c for _, c in scored[:limit]]

        enriched = []
        for candidate in top_candidates:
            repos = await self.get_github_repos(candidate["id"], limit=5)
            candidate["github_repos"] = repos
            enriched.append(candidate)

        return enriched


# Global instance
supabase = SupabaseService()
