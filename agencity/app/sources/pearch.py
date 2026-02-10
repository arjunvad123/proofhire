"""
Pearch AI Source - Alternative LinkedIn people search.

Pearch is another YC-backed people search API, alternative to Clado.
Claims to be more accurate than LinkedIn Recruiter.

Docs: https://pearch.ai
"""

import logging
from datetime import datetime

import httpx

from app.config import settings
from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData
from app.sources.base import DataSource

logger = logging.getLogger(__name__)


class PearchSource(DataSource):
    """
    Search people via Pearch AI.

    Features:
    - Natural language search
    - Fast search (3-40 sec) or Pro search (30-300 sec)
    - Verified emails and phone numbers
    - Credit-based pricing
    """

    BASE_URL = "https://api.pearch.ai/v1"

    @property
    def name(self) -> str:
        return "Pearch (LinkedIn)"

    @property
    def priority(self) -> int:
        return 3  # Same priority as Clado, use as alternative

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, 'pearch_api_key', '')
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
        Search Pearch for candidates matching the blueprint.
        """
        if not self.api_key:
            logger.info("Pearch API key not configured, skipping")
            return []

        # Build natural language query
        query = self._build_query(blueprint)
        logger.info(f"Pearch search query: {query}")

        try:
            candidates = await self._search_profiles(query, limit)
            return candidates

        except Exception as e:
            logger.error(f"Pearch search failed: {e}")
            return []

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """Enrich candidate with email via Pearch."""
        if not self.api_key or not candidate.linkedin_url:
            return candidate

        try:
            email = await self._get_email(candidate.linkedin_url)
            if email:
                candidate.email = email
        except Exception as e:
            logger.warning(f"Pearch email enrichment failed: {e}")

        candidate.enriched_at = datetime.utcnow()
        return candidate

    async def is_available(self) -> bool:
        return bool(self.api_key)

    def _build_query(self, blueprint: RoleBlueprint) -> str:
        """Build natural language query for Pearch."""
        parts = [blueprint.role_title]

        # Add skills
        if blueprint.must_haves:
            parts.append(f"with experience in {', '.join(blueprint.must_haves[:3])}")

        # Add company context
        if "startup" in blueprint.company_context.lower():
            parts.append("at startups")

        # Add location
        if blueprint.location_preferences:
            parts.append(f"based in {' or '.join(blueprint.location_preferences[:2])}")

        return " ".join(parts)

    async def _search_profiles(
        self,
        query: str,
        limit: int,
    ) -> list[CandidateData]:
        """Call Pearch search API."""
        candidates = []

        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for search
            response = await client.post(
                f"{self.BASE_URL}/search",
                json={
                    "query": query,
                    "limit": min(limit, 100),
                    "search_type": "fast",  # Use fast search
                    "include_contact": False,  # Don't spend credits on emails yet
                },
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

            for profile in data.get("results", []):
                candidate = self._parse_profile(profile)
                if candidate:
                    candidates.append(candidate)

        logger.info(f"Pearch returned {len(candidates)} candidates")
        return candidates

    def _parse_profile(self, profile: dict) -> CandidateData | None:
        """Parse Pearch profile into CandidateData."""
        if not profile:
            return None

        # Extract education
        education = profile.get("education", [])
        school = None
        major = None

        if education:
            latest = education[0]
            school = latest.get("school")
            major = latest.get("field_of_study")

        # Extract current role
        experience = profile.get("experience", [])
        current_role = None
        current_company = None

        if experience:
            current = experience[0]
            current_role = current.get("title")
            current_company = current.get("company")

        return CandidateData(
            id=f"pearch_{profile.get('id', '')}",
            name=profile.get("name", "Unknown"),
            email=profile.get("email"),
            school=school,
            major=major,
            location=profile.get("location"),
            linkedin_url=profile.get("linkedin_url"),
            current_role=current_role,
            current_company=current_company,
            skills=profile.get("skills", [])[:20],
            sources=["pearch"],
        )

    async def _get_email(self, linkedin_url: str) -> str | None:
        """Get email for a LinkedIn profile (costs credits)."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/enrich/email",
                json={"linkedin_url": linkedin_url},
                headers=self.headers,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("email")
        return None
