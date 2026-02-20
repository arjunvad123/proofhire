"""
Clado API Client

Clado.ai provides natural language people search across 800M+ profiles.
Uses parallel LLM inference to evaluate candidates against queries.

ENDPOINTS (as of 2025):
- /api/enrich/linkedin - Get cached profile (1 credit, ~$0.01)
- /api/enrich/scrape   - Real-time scrape (2 credits, ~$0.02)
- /api/search          - Natural language search

WATERFALL STRATEGY:
1. Try get_profile() first ($0.01) - usually has cached data
2. If not found or stale, use scrape_profile() ($0.02) - real-time
3. Fall back to PDL ($0.10) if Clado fails

NOTE: The /api/enrich/contacts endpoint only returns contact info (email/phone),
NOT full profile data. Use /api/enrich/linkedin or /api/enrich/scrape for profiles.
"""

import asyncio
import logging
import httpx
from typing import Optional
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)


class CladoExperience(BaseModel):
    """Work experience entry from Clado."""
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None  # "YYYY-MM" or "YYYY"
    end_date: Optional[str] = None    # "YYYY-MM", "YYYY", or None for current
    duration: Optional[str] = None    # Human readable: "2 years 3 months"
    description: Optional[str] = None
    location: Optional[str] = None


class CladoEducation(BaseModel):
    """Education entry from Clado."""
    school: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class CladoProfile(BaseModel):
    """Profile returned from Clado API."""

    id: str
    full_name: str
    headline: Optional[str] = None
    location: Optional[str] = None

    # Current position
    current_title: Optional[str] = None
    current_company: Optional[str] = None

    # Experience - structured with dates
    experience: list[dict] = []  # [{company, title, start_date, end_date, duration, description}]

    # Education - structured
    education: list[dict] = []  # [{school, degree, field, start_year, end_year}]

    # Skills and signals
    skills: list[str] = []

    # Links
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    twitter_url: Optional[str] = None
    personal_website: Optional[str] = None

    # Contact info (from /api/enrich only - may be None)
    email: Optional[str] = None
    phone: Optional[str] = None

    # Clado-specific scoring (from search results)
    match_score: Optional[float] = None  # How well they match the query (None if not from search)
    match_explanation: Optional[str] = None  # Why Clado thinks they match

    # Data freshness
    last_updated: Optional[str] = None  # When profile was last scraped
    data_source: str = "clado"  # "clado_profile", "clado_scrape", "clado_search"


class CladoSearchResult(BaseModel):
    """Full search result from Clado."""

    profiles: list[CladoProfile]
    total_matches: int
    query_interpreted: str  # How Clado understood the query
    search_id: str  # For pagination/follow-up


class CladoClient:
    """
    Client for Clado.ai people search API.

    Clado uses natural language queries like:
    - "Software engineers who worked at Stripe"
    - "UGC creators with D2C brand experience"
    - "ML engineers who went to Stanford and worked at Google"

    The API runs parallel LLM inference to evaluate millions of profiles
    against the query and returns ranked matches.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'clado_api_key', None)
        self.base_url = "https://search.clado.ai/api"  # Clado API base URL
        self.enabled = bool(self.api_key)
        self.timeout_seconds = settings.external_api_timeout_seconds
        self.max_retries = max(settings.external_api_max_retries, 0)

    async def search(
        self,
        query: str,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> CladoSearchResult:
        """
        Search for people using natural language query.

        Args:
            query: Natural language search (e.g., "React developers in SF")
            limit: Max results to return (default 100)
            filters: Optional filters like location, company, school

        Returns:
            CladoSearchResult with matching profiles
        """
        if not self.enabled:
            if settings.allow_mock_external_search:
                logger.warning("Clado API key missing, returning mock search results")
                return self._mock_search(query, limit)
            logger.warning("Clado API key missing, returning no results")
            return CladoSearchResult(
                profiles=[],
                total_matches=0,
                query_interpreted=query,
                search_id=""
            )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    # Clado uses GET with query parameters
                    response = await client.get(
                        f"{self.base_url}/search",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        params={
                            "query": query,
                            "limit": limit,
                            "advanced_filtering": "true",
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        logger.info("Clado search raw response keys: %s, total: %s", list(data.keys()), data.get("total", data.get("total_matches", 0)))
                        # Clado returns "results" (not "profiles") and "total" (not "total_matches")
                        raw_results = data.get("results", data.get("profiles", []))
                        profiles = []
                        for r in raw_results:
                            try:
                                profiles.append(self._parse_profile_response({"data": r} if "profile" in r else r, "clado_search"))
                            except Exception as e:
                                logger.warning("Failed to parse Clado search result: %s", e)
                                try:
                                    profiles.append(CladoProfile(**r))
                                except Exception:
                                    continue
                        return CladoSearchResult(
                            profiles=profiles,
                            total_matches=data.get("total", data.get("total_matches", len(profiles))),
                            query_interpreted=data.get("query", data.get("query_interpreted", query)),
                            search_id=data.get("search_id", ""),
                        )

                    if response.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                        backoff = 0.5 * (2 ** attempt)
                        logger.warning("Clado transient error %s, retrying in %.1fs", response.status_code, backoff)
                        await asyncio.sleep(backoff)
                        continue

                    logger.error("Clado API error status=%s body=%s", response.status_code, response.text[:500])
                    return CladoSearchResult(
                        profiles=[],
                        total_matches=0,
                        query_interpreted=query,
                        search_id="",
                    )

                except httpx.HTTPError as exc:
                    if attempt < self.max_retries:
                        backoff = 0.5 * (2 ** attempt)
                        logger.warning("Clado request failed (%s), retrying in %.1fs", exc, backoff)
                        await asyncio.sleep(backoff)
                        continue

                    logger.exception("Clado API exception after retries")
                    return CladoSearchResult(
                        profiles=[],
                        total_matches=0,
                        query_interpreted=query,
                        search_id="",
                    )

    async def get_profile(self, linkedin_url: str) -> Optional[CladoProfile]:
        """
        Get cached profile data for a LinkedIn URL.

        Cost: 1 credit (~$0.01)
        Endpoint: GET /api/enrich/linkedin?linkedin_url=...

        This returns cached data from Clado's database. Fast and cheap,
        but may be stale for profiles not recently scraped.

        Args:
            linkedin_url: LinkedIn profile URL

        Returns:
            CladoProfile with cached data, or None if not found
        """
        if not self.enabled:
            return None

        # Normalize URL
        clean_url = self._normalize_linkedin_url(linkedin_url)

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/enrich/linkedin",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"linkedin_url": clean_url},
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_profile_response(data, "clado_profile")
                elif response.status_code == 404:
                    logger.info("Clado profile not found for %s", clean_url)
                    return None
                else:
                    logger.error("Clado get_profile error status=%s body=%s", response.status_code, response.text[:500])
                    return None

            except httpx.HTTPError:
                logger.exception("Clado get_profile request failed")
                return None

    async def scrape_profile(self, linkedin_url: str) -> Optional[CladoProfile]:
        """
        Real-time scrape of a LinkedIn profile.

        Cost: 2 credits (~$0.02)
        Endpoint: GET /api/enrich/scrape?linkedin_url=...

        This performs a fresh scrape of the LinkedIn profile. Use when:
        - get_profile() returns None (not in cache)
        - get_profile() data looks stale
        - You need guaranteed fresh data

        Args:
            linkedin_url: LinkedIn profile URL

        Returns:
            CladoProfile with fresh data, or None if scrape fails
        """
        if not self.enabled:
            return None

        # Normalize URL
        clean_url = self._normalize_linkedin_url(linkedin_url)

        async with httpx.AsyncClient(timeout=self.timeout_seconds * 2) as client:  # Longer timeout for scrape
            try:
                response = await client.get(
                    f"{self.base_url}/enrich/scrape",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"linkedin_url": clean_url},
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_profile_response(data, "clado_scrape")
                elif response.status_code == 404:
                    logger.warning("Clado scrape could not find profile %s", clean_url)
                    return None
                else:
                    logger.error("Clado scrape_profile error status=%s body=%s", response.status_code, response.text[:500])
                    return None

            except httpx.HTTPError:
                logger.exception("Clado scrape_profile request failed")
                return None

    async def enrich_profile(self, linkedin_url: str) -> Optional[CladoProfile]:
        """
        DEPRECATED: Use get_profile() or scrape_profile() instead.

        This method uses the /api/enrich endpoint which only returns
        contact info (email/phone), NOT full profile data.

        For backwards compatibility, this now calls get_profile() first,
        then scrape_profile() if not found.
        """
        logger.warning(
            "enrich_profile() is deprecated. Use get_profile() or scrape_profile(). "
            "Falling back to get_profile() -> scrape_profile() waterfall."
        )
        profile = await self.get_profile(linkedin_url)
        if profile is None:
            profile = await self.scrape_profile(linkedin_url)
        return profile

    async def get_profile_with_fallback(self, linkedin_url: str) -> Optional[CladoProfile]:
        """
        Get profile using waterfall strategy: cache first, then scrape.

        Cost: 1-3 credits (~$0.01-$0.03) depending on cache hit

        This is the recommended method for enrichment:
        1. Try get_profile() (cached, $0.01)
        2. If not found, try scrape_profile() (real-time, $0.02)

        Args:
            linkedin_url: LinkedIn profile URL

        Returns:
            CladoProfile or None if all attempts fail
        """
        # Try cache first
        profile = await self.get_profile(linkedin_url)
        if profile is not None:
            logger.info("Clado cache hit for %s", linkedin_url)
            return profile

        # Fall back to real-time scrape
        logger.info("Clado cache miss, scraping %s", linkedin_url)
        return await self.scrape_profile(linkedin_url)

    def _normalize_linkedin_url(self, url: str) -> str:
        """Normalize LinkedIn URL to standard format."""
        import re
        url = url.strip()
        # Remove protocol
        url = url.replace("https://", "").replace("http://", "")
        # Remove www
        url = url.replace("www.", "")
        # Handle country-specific LinkedIn domains (uk.linkedin.com, ca.linkedin.com, etc.)
        url = re.sub(r'^[a-z]{2}\.linkedin\.com', 'linkedin.com', url)
        # Ensure it starts with linkedin.com
        if not url.startswith("linkedin.com"):
            url = f"linkedin.com/in/{url}"
        # Remove trailing /en or /fr language suffixes
        url = re.sub(r'/[a-z]{2}$', '', url)
        # Remove trailing slash
        url = url.rstrip("/")
        return f"https://{url}"

    def _parse_profile_response(self, data: dict, source: str) -> CladoProfile:
        """Parse Clado API response into CladoProfile.

        Clado returns data nested as: {data: {data: {profile fields}}}
        The inner data object has fields like:
        - firstName, lastName (not full_name)
        - fullPositions (not experience)
        - educations (not education)
        - skills as [{name: ...}]
        - geo.full for location
        """
        # Handle nested response structure: data.data.{fields}
        if "data" in data:
            inner = data.get("data") or {}
            if isinstance(inner, dict) and "data" in inner:
                profile_data = inner.get("data") or {}
            else:
                profile_data = inner if isinstance(inner, dict) else {}
        else:
            profile_data = data

        # Extract experience from fullPositions or position
        experience = []
        positions = profile_data.get("fullPositions") or profile_data.get("position") or profile_data.get("experience", []) or []
        for exp in positions:
            # Handle date objects like {year: 2025, month: 0, day: 0}
            start = exp.get("start", {}) or {}
            end = exp.get("end", {}) or {}

            start_date = None
            if start.get("year") and start.get("year") > 0:
                start_date = f"{start['year']}"
                if start.get("month") and start.get("month") > 0:
                    start_date = f"{start['year']}-{start['month']:02d}"

            end_date = None
            if end.get("year") and end.get("year") > 0:
                end_date = f"{end['year']}"
                if end.get("month") and end.get("month") > 0:
                    end_date = f"{end['year']}-{end['month']:02d}"

            experience.append({
                "company": exp.get("companyName") or exp.get("company") or exp.get("company_name"),
                "title": exp.get("title") or exp.get("position"),
                "start_date": start_date or exp.get("start_date"),
                "end_date": end_date or exp.get("end_date"),
                "duration": exp.get("duration"),
                "description": exp.get("description"),
                "location": exp.get("location"),
                "employment_type": exp.get("employmentType"),
            })

        # Extract education from educations
        education = []
        educations = profile_data.get("educations") or profile_data.get("education", []) or []
        for edu in educations:
            start = edu.get("start", {}) or {}
            end = edu.get("end", {}) or {}

            education.append({
                "school": edu.get("schoolName") or edu.get("school") or edu.get("school_name"),
                "degree": edu.get("degree") or edu.get("degree_name"),
                "field": edu.get("fieldOfStudy") or edu.get("field") or edu.get("field_of_study"),
                "start_year": start.get("year") if start.get("year") and start.get("year") > 0 else edu.get("start_year"),
                "end_year": end.get("year") if end.get("year") and end.get("year") > 0 else edu.get("end_year"),
                "grade": edu.get("grade"),
                "description": edu.get("description"),
            })

        # Extract skills - Clado returns [{name: "Python", ...}]
        raw_skills = profile_data.get("skills", []) or []
        if raw_skills and isinstance(raw_skills[0], dict):
            skills = [s.get("name") for s in raw_skills if s.get("name")]
        else:
            skills = raw_skills

        # Extract current position from experience if not provided
        current_title = profile_data.get("current_title") or profile_data.get("occupation")
        current_company = profile_data.get("current_company")

        if not current_title and experience:
            # Find current role (no end_date or end_date is empty)
            for exp in experience:
                if not exp.get("end_date"):
                    current_title = current_title or exp.get("title")
                    current_company = current_company or exp.get("company")
                    break

        # Extract location from geo object
        geo = profile_data.get("geo", {}) or {}
        location = profile_data.get("location") or geo.get("full") or geo.get("city")

        # Build full name
        full_name = profile_data.get("full_name")
        if not full_name:
            first = profile_data.get("firstName", "") or ""
            last = profile_data.get("lastName", "") or ""
            full_name = f"{first} {last}".strip()

        # Build profile
        return CladoProfile(
            id=str(profile_data.get("id") or profile_data.get("urn") or profile_data.get("username") or "unknown"),
            full_name=full_name,
            headline=profile_data.get("headline") or profile_data.get("summary"),
            location=location,
            current_title=current_title,
            current_company=current_company,
            experience=experience,
            education=education,
            skills=skills,
            linkedin_url=profile_data.get("linkedin_url") or profile_data.get("profile_url") or (f"https://linkedin.com/in/{profile_data.get('username')}" if profile_data.get("username") else None),
            github_url=profile_data.get("github_url"),
            twitter_url=profile_data.get("twitter_url"),
            personal_website=profile_data.get("personal_website"),
            email=profile_data.get("email"),
            phone=profile_data.get("phone"),
            last_updated=profile_data.get("last_updated"),
            data_source=source,
        )

    async def health_check(self) -> dict:
        """Return connectivity/auth status for Clado provider."""
        if not self.enabled:
            return {"provider": "clado", "ok": False, "reason": "missing_api_key"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"query": "software engineer", "limit": 1},
                )
                ok = response.status_code == 200
                return {"provider": "clado", "ok": ok, "status_code": response.status_code}
        except httpx.HTTPError as exc:
            return {"provider": "clado", "ok": False, "reason": str(exc)}

    def _mock_search(self, query: str, limit: int) -> CladoSearchResult:
        """
        Return mock data when API key not configured.
        Useful for development and testing.
        """
        # Parse query for mock response
        mock_profiles = []

        if "ugc" in query.lower() or "creator" in query.lower():
            mock_profiles = [
                CladoProfile(
                    id="clado-1",
                    full_name="Maya Rodriguez",
                    headline="UGC Creator | D2C Brand Partnerships",
                    location="Los Angeles, CA",
                    current_title="Freelance UGC Creator",
                    current_company="Self-Employed",
                    experience=[
                        {"company": "Glossier", "title": "Brand Ambassador", "duration": "2 years"},
                        {"company": "Self-Employed", "title": "UGC Creator", "duration": "3 years"}
                    ],
                    education=[
                        {"school": "UCLA", "degree": "BA", "field": "Communications", "year": "2020"}
                    ],
                    skills=["Content Creation", "TikTok", "Instagram", "Video Editing", "D2C Marketing"],
                    linkedin_url="https://linkedin.com/in/mayarodriguez",
                    match_score=0.92,
                    match_explanation="Strong D2C experience with Glossier, active UGC portfolio"
                ),
                CladoProfile(
                    id="clado-2",
                    full_name="Alex Kim",
                    headline="Content Creator & Social Media Strategist",
                    location="San Francisco, CA",
                    current_title="Senior Content Creator",
                    current_company="Allbirds",
                    experience=[
                        {"company": "Allbirds", "title": "Senior Content Creator", "duration": "1 year"},
                        {"company": "Warby Parker", "title": "Content Creator", "duration": "2 years"}
                    ],
                    education=[
                        {"school": "UC Berkeley", "degree": "BA", "field": "Media Studies", "year": "2019"}
                    ],
                    skills=["UGC", "Brand Storytelling", "Video Production", "Social Media"],
                    linkedin_url="https://linkedin.com/in/alexkim-content",
                    match_score=0.88,
                    match_explanation="D2C experience at Allbirds and Warby Parker"
                ),
                CladoProfile(
                    id="clado-3",
                    full_name="Jordan Lee",
                    headline="TikTok Creator | 500K+ Followers",
                    location="New York, NY",
                    current_title="Influencer & UGC Creator",
                    current_company="Independent",
                    experience=[
                        {"company": "Independent", "title": "TikTok Creator", "duration": "4 years"},
                        {"company": "Multiple D2C Brands", "title": "UGC Partner", "duration": "2 years"}
                    ],
                    skills=["TikTok", "UGC", "Viral Content", "Brand Partnerships"],
                    linkedin_url="https://linkedin.com/in/jordanlee-creator",
                    twitter_url="https://twitter.com/jordanleecreates",
                    match_score=0.85,
                    match_explanation="Large TikTok following, multiple D2C brand partnerships"
                )
            ]
        elif "engineer" in query.lower() or "developer" in query.lower():
            mock_profiles = [
                CladoProfile(
                    id="clado-4",
                    full_name="Sarah Chen",
                    headline="Senior Software Engineer | Ex-Stripe",
                    location="San Francisco, CA",
                    current_title="Staff Engineer",
                    current_company="Figma",
                    experience=[
                        {"company": "Figma", "title": "Staff Engineer", "duration": "2 years"},
                        {"company": "Stripe", "title": "Senior Engineer", "duration": "3 years"},
                        {"company": "Google", "title": "Software Engineer", "duration": "2 years"}
                    ],
                    education=[
                        {"school": "Stanford", "degree": "MS", "field": "Computer Science", "year": "2017"}
                    ],
                    skills=["Python", "TypeScript", "React", "Distributed Systems", "API Design"],
                    linkedin_url="https://linkedin.com/in/sarahchen-eng",
                    github_url="https://github.com/sarahchen",
                    match_score=0.95,
                    match_explanation="Strong pedigree: Figma, Stripe, Google. Stanford CS."
                ),
                CladoProfile(
                    id="clado-5",
                    full_name="David Park",
                    headline="Full Stack Developer | React + Node",
                    location="Seattle, WA",
                    current_title="Senior Developer",
                    current_company="Airbnb",
                    experience=[
                        {"company": "Airbnb", "title": "Senior Developer", "duration": "3 years"},
                        {"company": "Microsoft", "title": "Software Engineer", "duration": "2 years"}
                    ],
                    education=[
                        {"school": "University of Washington", "degree": "BS", "field": "Computer Science", "year": "2018"}
                    ],
                    skills=["React", "Node.js", "TypeScript", "GraphQL", "AWS"],
                    linkedin_url="https://linkedin.com/in/davidpark-dev",
                    github_url="https://github.com/davidpark",
                    match_score=0.89,
                    match_explanation="Airbnb and Microsoft experience, strong full-stack skills"
                )
            ]
        else:
            # Generic response
            mock_profiles = [
                CladoProfile(
                    id="clado-generic-1",
                    full_name="Sample Candidate",
                    headline="Professional matching your query",
                    location="United States",
                    match_score=0.75,
                    match_explanation=f"Matched query: {query}"
                )
            ]

        return CladoSearchResult(
            profiles=mock_profiles[:limit],
            total_matches=len(mock_profiles),
            query_interpreted=query,
            search_id="mock-search-001"
        )


# Singleton instance
clado_client = CladoClient()
