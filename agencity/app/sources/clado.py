"""
Clado Source - LinkedIn people search via Clado AI.

Clado provides access to 800M+ LinkedIn profiles with natural language search.
Uses AI agent filtering for high-quality results.

Docs: https://docs.clado.ai/api-reference/endpoint/search-people
"""

import logging
from datetime import datetime

import httpx

from app.config import settings
from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData, HackathonData
from app.sources.base import DataSource

logger = logging.getLogger(__name__)


class CladoSource(DataSource):
    """
    Search LinkedIn profiles via Clado AI.

    Features:
    - Natural language search across 800M+ profiles
    - AI agent filtering for relevance
    - Filter by companies, schools
    - Education and experience data
    """

    BASE_URL = "https://search.clado.ai"

    @property
    def name(self) -> str:
        return "LinkedIn (via Clado)"

    @property
    def priority(self) -> int:
        return 2  # After our network and GitHub

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, 'clado_api_key', '')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 30,
    ) -> list[CandidateData]:
        """
        Search Clado for candidates matching the blueprint.
        """
        if not self.api_key:
            logger.warning("Clado API key not configured, skipping search")
            return []

        # Build natural language query from blueprint
        query = self._build_query(blueprint)
        logger.info(f"Clado search query: {query}")

        try:
            candidates = await self._search_profiles(
                query=query,
                schools=blueprint.location_preferences,  # Schools are in location_preferences
                limit=limit,
            )
            return candidates

        except Exception as e:
            logger.error(f"Clado search failed: {e}")
            return []

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """
        Enrich candidate with additional Clado data.
        For now, just return as-is since search includes profile data.
        """
        candidate.enriched_at = datetime.utcnow()
        return candidate

    async def is_available(self) -> bool:
        """Check if Clado API is accessible."""
        return bool(self.api_key)

    def _build_query(self, blueprint: RoleBlueprint) -> str:
        """
        Build natural language query from blueprint.

        Clado works best with descriptive queries like:
        "software engineers with machine learning experience at startups"
        """
        parts = []

        # Role title
        parts.append(blueprint.role_title)

        # Add context from specific work
        if blueprint.specific_work:
            # Extract key skills/technologies
            work_lower = blueprint.specific_work.lower()
            if "llm" in work_lower or "prompt" in work_lower:
                parts.append("with LLM or AI experience")
            if "ml" in work_lower or "machine learning" in work_lower:
                parts.append("with machine learning background")
            if "backend" in work_lower:
                parts.append("backend development")
            if "frontend" in work_lower:
                parts.append("frontend development")

        # Add must-haves as skills
        if blueprint.must_haves:
            skills = " ".join(blueprint.must_haves[:3])
            parts.append(f"skilled in {skills}")

        # Add location context
        if blueprint.location_preferences:
            locations = ", ".join(blueprint.location_preferences[:2])
            parts.append(f"based in or studied at {locations}")

        return " ".join(parts)

    async def _search_profiles(
        self,
        query: str,
        schools: list[str] | None = None,
        companies: list[str] | None = None,
        limit: int = 30,
    ) -> list[CandidateData]:
        """
        Call Clado search API.
        """
        params = {
            "query": query,
            "limit": min(limit, 100),
            "advanced_filtering": True,  # Use AI filtering for quality
            "legacy": False,
        }

        if schools:
            params["schools"] = schools
        if companies:
            params["companies"] = companies

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/search",
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        candidates = []
        for result in data.get("results", []):
            candidate = self._parse_profile(result)
            if candidate:
                candidates.append(candidate)

        logger.info(f"Clado returned {len(candidates)} candidates")
        return candidates

    def _parse_profile(self, result: dict) -> CandidateData | None:
        """
        Parse Clado profile result into CandidateData.
        """
        profile = result.get("profile", {})
        if not profile:
            return None

        # Extract education
        education = result.get("education", [])
        school = None
        major = None
        graduation_year = None

        if education:
            latest = education[0]
            school = latest.get("school_name")
            major = latest.get("field_of_study")
            # Try to parse graduation year from end_date if available

        # Extract current role from experience
        experience = result.get("experience", [])
        current_role = None
        current_company = None

        if experience:
            current = experience[0]
            current_role = current.get("title")
            current_company = current.get("company_name")

        # Extract skills
        skills = profile.get("skills", [])

        return CandidateData(
            id=f"clado_{profile.get('id', '')}",
            name=profile.get("name", "Unknown"),
            email=profile.get("email"),  # May need enrichment
            school=school,
            major=major,
            graduation_year=graduation_year,
            location=profile.get("location"),
            linkedin_url=profile.get("linkedin_url"),
            current_role=current_role,
            current_company=current_company,
            skills=skills[:20] if skills else [],  # Limit skills
            sources=["clado"],
        )


class CladoEnricher:
    """
    Enrich candidate profiles with additional Clado data.

    Use this for:
    - Getting full profile details
    - Finding email addresses
    - Getting phone numbers
    """

    BASE_URL = "https://search.clado.ai"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, 'clado_api_key', '')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

    async def enrich_email(self, linkedin_url: str) -> str | None:
        """
        Get email for a LinkedIn profile.
        Costs 4 credits ($0.04) if found.
        """
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/api/enrich/email",
                    params={"linkedin_url": linkedin_url},
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("email")
        except Exception as e:
            logger.warning(f"Email enrichment failed: {e}")
            return None

    async def get_full_profile(self, linkedin_url: str) -> dict | None:
        """
        Get full profile data for a LinkedIn URL.
        Costs 2 credits ($0.02).
        """
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/api/profile",
                    params={"linkedin_url": linkedin_url},
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Profile fetch failed: {e}")
            return None
