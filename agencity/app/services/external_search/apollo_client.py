"""
Apollo.io API Client

Apollo provides access to 275M+ contacts with structured search filters.
Search is FREE (no credits consumed). Credits only used for enrichment (emails/phones).

API docs: https://apolloio.github.io/apollo-api-docs/
Auth: x-api-key header
"""

import asyncio
import logging
import httpx
from typing import Optional
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)


class ApolloProfile(BaseModel):
    """Profile returned from Apollo search."""

    id: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None

    # Current position
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    seniority: Optional[str] = None

    # Experience
    experience: list[dict] = []

    # Education
    education: list[dict] = []

    # Skills
    skills: list[str] = []

    # Links
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    personal_website: Optional[str] = None

    # Match info
    match_score: float = 0.0


class ApolloSearchResult(BaseModel):
    """Full search result from Apollo."""

    profiles: list[ApolloProfile]
    total_matches: int
    query_used: str


class ApolloClient:
    """
    Client for Apollo.io people search API.

    Apollo uses structured filters (not natural language):
    - person_titles: ["software engineer", "developer"]
    - person_locations: ["San Francisco, CA"]
    - q_keywords: "python react"

    Search is FREE. Enrichment (emails/phones) costs credits.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'apollo_api_key', None)
        self.base_url = "https://api.apollo.io/api/v1"
        self.enabled = bool(self.api_key)
        self.timeout_seconds = settings.external_api_timeout_seconds
        self.max_retries = max(settings.external_api_max_retries, 0)

    def _build_search_params(
        self,
        query: str,
        limit: int,
        location: Optional[str] = None
    ) -> dict:
        """Convert natural language query into Apollo structured filters."""
        query_lower = query.lower()
        params: dict = {
            "page": 1,
            "per_page": min(limit, 100),
        }

        # Extract title keywords for person_titles filter
        title_keywords = []
        title_terms = [
            "engineer", "developer", "designer", "founder", "ceo", "cto",
            "product manager", "data scientist", "ml engineer", "devops",
            "creator", "ugc", "content creator", "influencer", "marketer",
            "analyst", "consultant", "director", "vp", "head of",
        ]
        for term in title_terms:
            if term in query_lower:
                title_keywords.append(term)

        if title_keywords:
            params["person_titles"] = title_keywords
        else:
            # Use the full query as keyword search
            params["q_keywords"] = query

        # Extract location
        if location:
            params["person_locations"] = [location]
        else:
            # Try to extract location from query
            location_indicators = {
                "san francisco": "San Francisco, California, United States",
                "sf": "San Francisco, California, United States",
                "new york": "New York, New York, United States",
                "nyc": "New York, New York, United States",
                "los angeles": "Los Angeles, California, United States",
                "la": "Los Angeles, California, United States",
                "seattle": "Seattle, Washington, United States",
                "austin": "Austin, Texas, United States",
                "chicago": "Chicago, Illinois, United States",
                "boston": "Boston, Massachusetts, United States",
                "india": "India",
                "bangalore": "Bangalore, Karnataka, India",
                "london": "London, England, United Kingdom",
            }
            for indicator, loc in location_indicators.items():
                if indicator in query_lower:
                    params["person_locations"] = [loc]
                    break

        # Extract skill/technology keywords
        tech_terms = []
        tech_keywords = [
            "python", "react", "javascript", "typescript", "node", "java",
            "go", "rust", "aws", "gcp", "azure", "docker", "kubernetes",
            "ml", "machine learning", "ai", "deep learning", "pytorch",
            "tensorflow", "sql", "graphql", "redis", "postgres",
        ]
        for tech in tech_keywords:
            if tech in query_lower:
                tech_terms.append(tech)

        if tech_terms and "q_keywords" not in params:
            params["q_keywords"] = " ".join(tech_terms)

        return params

    def _parse_contact(self, data: dict) -> ApolloProfile:
        """Parse an Apollo contact into ApolloProfile."""
        # Build experience from employment_history if available
        experience = []
        for hist in (data.get("employment_history") or [])[:10]:
            experience.append({
                "company": hist.get("organization_name", ""),
                "title": hist.get("title", ""),
                "start_date": hist.get("start_date", ""),
                "end_date": hist.get("end_date", ""),
                "description": hist.get("description", ""),
            })

        # Build education
        education = []
        for edu in (data.get("education") or [])[:5]:
            education.append({
                "school": edu.get("school_name") or edu.get("raw_name", ""),
                "degree": edu.get("degree", ""),
                "field": edu.get("field_of_study", ""),
                "year": edu.get("end_date", ""),
            })

        # Build location
        city = data.get("city", "")
        state = data.get("state", "")
        country = data.get("country", "")
        parts = [p for p in [city, state, country] if p]
        location = ", ".join(parts) if parts else None

        # Organization info
        org = data.get("organization", {}) or {}

        return ApolloProfile(
            id=data.get("id", ""),
            full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or "Unknown",
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            headline=data.get("headline") or data.get("title"),
            location=location,
            current_title=data.get("title"),
            current_company=data.get("organization_name") or org.get("name"),
            seniority=data.get("seniority"),
            experience=experience,
            education=education,
            skills=data.get("skills", []) or [],
            linkedin_url=data.get("linkedin_url"),
            github_url=data.get("github_url"),
            twitter_url=data.get("twitter_url"),
            facebook_url=data.get("facebook_url"),
            personal_website=data.get("website_url"),
            match_score=0.75,  # Apollo doesn't return scores; assume decent relevance
        )

    async def search(
        self,
        query: str,
        limit: int = 50,
        location: Optional[str] = None
    ) -> ApolloSearchResult:
        """
        Search for people using natural language query (converted to structured filters).

        Args:
            query: Natural language search (converted to Apollo filters)
            limit: Max results (default 50, max 100)
            location: Optional location filter

        Returns:
            ApolloSearchResult with matching profiles
        """
        if not self.enabled:
            return ApolloSearchResult(profiles=[], total_matches=0, query_used=query)

        params = self._build_search_params(query, limit, location)

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(
                        f"{self.base_url}/mixed_people/search",
                        headers={
                            "x-api-key": self.api_key,
                            "Content-Type": "application/json",
                        },
                        json=params,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        raw_contacts = data.get("people", data.get("contacts", []))
                        logger.info(
                            "Apollo search returned %s results for params: %s",
                            len(raw_contacts),
                            {k: v for k, v in params.items() if k != "api_key"},
                        )

                        profiles = []
                        for c in raw_contacts:
                            try:
                                profiles.append(self._parse_contact(c))
                            except Exception as e:
                                logger.warning("Failed to parse Apollo contact: %s", e)
                                continue

                        return ApolloSearchResult(
                            profiles=profiles,
                            total_matches=data.get("pagination", {}).get("total_entries", len(profiles)),
                            query_used=str(params),
                        )

                    if response.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                        backoff = 0.5 * (2 ** attempt)
                        logger.warning("Apollo transient error %s, retrying in %.1fs", response.status_code, backoff)
                        await asyncio.sleep(backoff)
                        continue

                    logger.error("Apollo API error status=%s body=%s", response.status_code, response.text[:500])
                    return ApolloSearchResult(profiles=[], total_matches=0, query_used=str(params))

                except httpx.HTTPError as exc:
                    if attempt < self.max_retries:
                        backoff = 0.5 * (2 ** attempt)
                        logger.warning("Apollo request failed (%s), retrying in %.1fs", exc, backoff)
                        await asyncio.sleep(backoff)
                        continue
                    logger.exception("Apollo API exception after retries")
                    return ApolloSearchResult(profiles=[], total_matches=0, query_used=query)

    async def enrich_profile(self, linkedin_url: str) -> Optional[ApolloProfile]:
        """
        Enrich a person by LinkedIn URL (costs credits).

        Args:
            linkedin_url: LinkedIn profile URL

        Returns:
            ApolloProfile with enriched data or None
        """
        if not self.enabled:
            return None

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/people/match",
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={"linkedin_url": linkedin_url},
                )

                if response.status_code == 200:
                    data = response.json()
                    person = data.get("person", data)
                    if person:
                        return self._parse_contact(person)
                logger.error("Apollo enrich error status=%s body=%s", response.status_code, response.text[:500])
                return None

            except httpx.HTTPError:
                logger.exception("Apollo enrich request failed")
                return None

    async def health_check(self) -> dict:
        """Return connectivity/auth status for Apollo provider."""
        if not self.enabled:
            return {"provider": "apollo", "ok": False, "reason": "missing_api_key"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/mixed_people/search",
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={"page": 1, "per_page": 1, "person_titles": ["engineer"]},
                )
                ok = response.status_code == 200
                info = {"provider": "apollo", "ok": ok, "status_code": response.status_code}
                if ok:
                    data = response.json()
                    info["total_results"] = data.get("pagination", {}).get("total_entries", 0)
                return info
        except httpx.HTTPError as exc:
            return {"provider": "apollo", "ok": False, "reason": str(exc)}


# Singleton instance
apollo_client = ApolloClient()
