"""
People Data Labs API Client

PDL provides access to 1.5B+ professional profiles with structured data.
Uses SQL-like queries for searching.

Pricing: ~$0.10 per enrichment/search result
"""

import asyncio
import logging
import httpx
from typing import Optional
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)


class PDLProfile(BaseModel):
    """Profile returned from PDL search."""

    id: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    location_country: Optional[str] = None

    # Current position
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    industry: Optional[str] = None

    # Experience (simplified)
    experience: list[dict] = []

    # Education (simplified)
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


class PDLSearchResult(BaseModel):
    """Full search result from PDL."""

    profiles: list[PDLProfile]
    total_matches: int
    query_used: str


class PDLClient:
    """
    Client for People Data Labs API.

    PDL uses SQL-like queries:
    - SELECT * FROM person WHERE job_title LIKE '%engineer%'
    - SELECT * FROM person WHERE skills @> ARRAY['python', 'react']
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'pdl_api_key', None)
        self.base_url = "https://api.peopledatalabs.com/v5"
        self.enabled = bool(self.api_key)
        self.timeout_seconds = settings.external_api_timeout_seconds
        self.max_retries = max(settings.external_api_max_retries, 0)

    async def search(
        self,
        query: str,
        limit: int = 50,
        location: Optional[str] = None
    ) -> PDLSearchResult:
        """
        Search for people using natural language query.

        Converts natural language to PDL SQL format.

        Args:
            query: Natural language search (e.g., "UGC creators with D2C experience")
            limit: Max results (default 50, max 100)
            location: Optional country filter

        Returns:
            PDLSearchResult with matching profiles
        """
        if not self.enabled:
            return PDLSearchResult(profiles=[], total_matches=0, query_used=query)

        # Convert natural language to PDL SQL
        sql = self._build_sql_query(query, location, limit)

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.get(
                        f"{self.base_url}/person/search",
                        headers={
                            "X-Api-Key": self.api_key,
                            "Content-Type": "application/json"
                        },
                        params={
                            "sql": sql,
                            "size": min(limit, 100)
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        profiles = [self._parse_profile(p) for p in data.get("data", [])]
                        return PDLSearchResult(
                            profiles=profiles,
                            total_matches=data.get("total", len(profiles)),
                            query_used=sql
                        )

                    if response.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                        backoff = 0.5 * (2 ** attempt)
                        logger.warning("PDL transient error %s, retrying in %.1fs", response.status_code, backoff)
                        await asyncio.sleep(backoff)
                        continue

                    error_payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error = error_payload.get("error", {})
                    logger.error("PDL API error status=%s message=%s", response.status_code, error.get("message", "unknown"))
                    return PDLSearchResult(profiles=[], total_matches=0, query_used=sql)

                except httpx.HTTPError as exc:
                    if attempt < self.max_retries:
                        backoff = 0.5 * (2 ** attempt)
                        logger.warning("PDL request failed (%s), retrying in %.1fs", exc, backoff)
                        await asyncio.sleep(backoff)
                        continue
                    logger.exception("PDL API exception after retries")
                    return PDLSearchResult(profiles=[], total_matches=0, query_used=query)

    def _build_sql_query(
        self,
        natural_query: str,
        location: Optional[str],
        limit: int
    ) -> str:
        """
        Convert natural language query to PDL SQL.

        Examples:
        - "UGC creators" -> job_title LIKE '%ugc%' OR job_title LIKE '%content creator%'
        - "React developers" -> job_title LIKE '%react%' OR skills @> ARRAY['react']
        """
        query_lower = natural_query.lower()
        conditions = []

        # Extract key terms
        if "ugc" in query_lower or "content creator" in query_lower:
            conditions.append(
                "(job_title LIKE '%content creator%' OR job_title LIKE '%ugc%' OR job_title LIKE '%influencer%')"
            )
        elif "engineer" in query_lower or "developer" in query_lower:
            conditions.append(
                "(job_title LIKE '%engineer%' OR job_title LIKE '%developer%')"
            )
        elif "designer" in query_lower:
            conditions.append("job_title LIKE '%designer%'")
        elif "founder" in query_lower or "ceo" in query_lower:
            conditions.append(
                "(job_title LIKE '%founder%' OR job_title LIKE '%ceo%')"
            )
        else:
            # Generic title search
            words = [w for w in natural_query.split() if len(w) > 3]
            if words:
                title_conds = [f"job_title LIKE '%{w.lower()}%'" for w in words[:3]]
                conditions.append(f"({' OR '.join(title_conds)})")

        # Add location filter
        if location:
            conditions.append(f"location_country='{location.lower()}'")
        else:
            # Default to US
            conditions.append("location_country='united states'")

        # Build final SQL
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return f"SELECT * FROM person WHERE {where_clause}"

    def _parse_profile(self, data: dict) -> PDLProfile:
        """Parse PDL API response into PDLProfile."""

        # Build experience list
        experience = []
        if data.get("experience"):
            for exp in data.get("experience", [])[:5]:
                experience.append({
                    "company": exp.get("company", {}).get("name"),
                    "title": exp.get("title", {}).get("name"),
                    "start_date": exp.get("start_date"),
                    "end_date": exp.get("end_date"),
                    "is_primary": exp.get("is_primary", False)
                })

        # Build education list
        education = []
        if data.get("education"):
            for edu in data.get("education", [])[:3]:
                education.append({
                    "school": edu.get("school", {}).get("name"),
                    "degree": edu.get("degrees", [""])[0] if edu.get("degrees") else None,
                    "field": edu.get("majors", [""])[0] if edu.get("majors") else None,
                    "start_date": edu.get("start_date"),
                    "end_date": edu.get("end_date")
                })

        # Build location string (filter out booleans - PDL returns True/False for some fields)
        location_parts = []
        locality = data.get("location_locality")
        region = data.get("location_region")
        country = data.get("location_country")

        if locality and isinstance(locality, str):
            location_parts.append(locality)
        if region and isinstance(region, str):
            location_parts.append(region)
        if country and isinstance(country, str):
            location_parts.append(country)
        location = ", ".join(location_parts) if location_parts else None

        return PDLProfile(
            id=data.get("id", ""),
            full_name=data.get("full_name", "Unknown"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            headline=data.get("job_title"),
            location=location,
            location_country=data.get("location_country"),
            current_title=data.get("job_title"),
            current_company=data.get("job_company_name"),
            industry=data.get("industry"),
            experience=experience,
            education=education,
            skills=data.get("skills", [])[:20],
            linkedin_url=f"https://{data['linkedin_url']}" if data.get("linkedin_url") else None,
            github_url=f"https://{data['github_url']}" if data.get("github_url") else None,
            twitter_url=f"https://{data['twitter_url']}" if data.get("twitter_url") else None,
            facebook_url=f"https://{data['facebook_url']}" if data.get("facebook_url") else None,
            personal_website=data.get("personal_emails", [None])[0] if data.get("personal_emails") else None,
            match_score=0.8  # PDL doesn't return scores, assume high relevance
        )

    async def enrich_profile(self, linkedin_url: str) -> Optional[PDLProfile]:
        """
        Get full profile data for a specific LinkedIn URL.

        Args:
            linkedin_url: LinkedIn profile URL

        Returns:
            PDLProfile with full data or None
        """
        if not self.enabled:
            return None

        # Clean LinkedIn URL
        clean_url = linkedin_url.replace("https://", "").replace("http://", "").replace("www.", "")

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/person/enrich",
                    headers={
                        "X-Api-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    params={"profile": clean_url},
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_profile(data.get("data", {}))
                logger.error("PDL enrich error status=%s body=%s", response.status_code, response.text[:500])
                return None

            except httpx.HTTPError:
                logger.exception("PDL enrich request failed")
                return None

    async def health_check(self) -> dict:
        """Return connectivity/auth status for PDL provider."""
        if not self.enabled:
            return {"provider": "pdl", "ok": False, "reason": "missing_api_key"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    f"{self.base_url}/person/enrich",
                    headers={"X-Api-Key": self.api_key},
                    params={"email": "healthcheck@example.com"},
                )
                ok = response.status_code in (200, 404)
                return {"provider": "pdl", "ok": ok, "status_code": response.status_code}
        except httpx.HTTPError as exc:
            return {"provider": "pdl", "ok": False, "reason": str(exc)}


# Singleton instance
pdl_client = PDLClient()
