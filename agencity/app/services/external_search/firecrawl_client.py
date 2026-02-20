"""
Firecrawl People Search Client

Uses Firecrawl's web search API to find people on LinkedIn, GitHub, etc.
Searches the web with site:linkedin.com/in queries and extracts profile data
from search results.

API docs: https://docs.firecrawl.dev
Auth: Bearer token
Pricing: Credits-based (~1 credit per search result)
"""

import asyncio
import logging
import re
import httpx
from typing import Optional
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)


class FirecrawlProfile(BaseModel):
    """Profile extracted from Firecrawl search results."""

    id: str
    full_name: str
    headline: Optional[str] = None
    location: Optional[str] = None

    # Current position (parsed from headline/title)
    current_title: Optional[str] = None
    current_company: Optional[str] = None

    # Experience
    experience: list[dict] = []

    # Education
    education: list[dict] = []

    # Skills (extracted from description)
    skills: list[str] = []

    # Links
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    twitter_url: Optional[str] = None
    personal_website: Optional[str] = None

    # Match info
    match_score: float = 0.0


class FirecrawlSearchResult(BaseModel):
    """Full search result from Firecrawl."""

    profiles: list[FirecrawlProfile]
    total_matches: int
    query_used: str


class FirecrawlClient:
    """
    Client that uses Firecrawl's web search to find people.

    Strategy:
    - Search "site:linkedin.com/in <role> <skills> <location>"
    - Parse LinkedIn titles/descriptions for profile info
    - Extract name, title, company, skills from search snippets
    - Use Clado enrichment for full profiles on the best matches

    This gives us access to essentially the entire LinkedIn directory
    through web search, without needing a LinkedIn API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'firecrawl_api_key', None)
        self.base_url = "https://api.firecrawl.dev/v1"
        self.enabled = bool(self.api_key)
        self.timeout_seconds = settings.external_api_timeout_seconds
        self.max_retries = max(settings.external_api_max_retries, 0)

    def _build_linkedin_query(self, query: str, location: Optional[str] = None) -> str:
        """Build a site:linkedin.com/in search query."""
        # Start with LinkedIn site restriction
        parts = ["site:linkedin.com/in"]
        parts.append(query)
        if location:
            parts.append(location)
        return " ".join(parts)

    def _parse_linkedin_result(self, data: dict) -> Optional[FirecrawlProfile]:
        """Parse a Firecrawl search result into a profile.

        LinkedIn search results typically have:
        - url: "https://www.linkedin.com/in/username"
        - title: "Full Name - Headline | Details - LinkedIn"
        - description: Summary snippet with skills/experience
        """
        url = data.get("url", "")
        title = data.get("title", "")
        description = data.get("description", "")

        # Must be a LinkedIn profile URL
        if "linkedin.com/in/" not in url:
            return None

        # Extract username from URL for ID
        username = ""
        match = re.search(r'linkedin\.com/in/([^/?#]+)', url)
        if match:
            username = match.group(1)

        # Parse the title: "Full Name - Headline | Company - LinkedIn"
        # Remove " - LinkedIn" suffix
        clean_title = re.sub(r'\s*[-|]\s*LinkedIn\s*$', '', title).strip()

        # Split on " - " to get name and headline
        name_parts = clean_title.split(" - ", 1)
        full_name = name_parts[0].strip() if name_parts else "Unknown"
        headline = name_parts[1].strip() if len(name_parts) > 1 else None

        # Skip if name looks like a company or generic page
        if not full_name or len(full_name) < 2 or full_name.lower() in ("linkedin", "people"):
            return None

        # Parse current title and company from headline
        current_title = None
        current_company = None
        if headline:
            # Common patterns: "Title at Company", "Title | Company", "Title - Company"
            for sep in [" at ", " @ "]:
                if sep in headline:
                    parts = headline.split(sep, 1)
                    current_title = parts[0].strip()
                    current_company = parts[1].strip()
                    break

            if not current_title:
                # Try pipe or dash separator: "Title | Company"
                for sep in [" | ", " - "]:
                    if sep in headline:
                        parts = headline.split(sep, 1)
                        current_title = parts[0].strip()
                        # Second part might be company or more title info
                        if len(parts[1].strip()) < 50:
                            current_company = parts[1].strip()
                        break

            if not current_title:
                current_title = headline

        # Extract skills from description
        skills = self._extract_skills(description + " " + (headline or ""))

        # Extract location from description
        location = self._extract_location(description)

        # Clean up the LinkedIn URL — normalize country subdomains to linkedin.com
        clean_url = url.split("?")[0].rstrip("/")
        if not clean_url.startswith("https://"):
            clean_url = f"https://{clean_url}"
        # Normalize uk.linkedin.com, ca.linkedin.com etc. to www.linkedin.com
        clean_url = re.sub(r'https?://[a-z]{2}\.linkedin\.com/', 'https://www.linkedin.com/', clean_url)
        # Remove /en, /fr language suffixes
        clean_url = re.sub(r'/[a-z]{2}$', '', clean_url)

        return FirecrawlProfile(
            id=f"fc-{username}" if username else f"fc-{hash(url) % 10**8}",
            full_name=full_name,
            headline=headline,
            location=location,
            current_title=current_title,
            current_company=current_company,
            skills=skills[:15],
            linkedin_url=clean_url,
            match_score=0.7,  # Base score; web search relevance is decent
        )

    def _extract_skills(self, text: str) -> list[str]:
        """Extract technology/skill keywords from text."""
        text_lower = text.lower()
        known_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "Java",
            "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin",
            "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
            "PostgreSQL", "MongoDB", "Redis", "GraphQL", "REST", "SQL",
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
            "PyTorch", "TensorFlow", "LLM", "AI",
            "React Native", "Flutter", "iOS", "Android",
            "Next.js", "Vue.js", "Angular", "Django", "FastAPI", "Flask",
            "Figma", "Product Design", "UX", "UI",
            "Data Science", "Data Engineering", "ETL",
            "DevOps", "CI/CD", "Linux", "Git",
        ]
        found = []
        for skill in known_skills:
            if skill.lower() in text_lower:
                found.append(skill)
        return found

    def _extract_location(self, text: str) -> Optional[str]:
        """Try to extract location from description text."""
        location_patterns = [
            r'(?:located in|based in|from)\s+([A-Z][a-zA-Z\s,]+(?:CA|NY|TX|WA|MA|IL|CO|GA|FL|OR|PA|VA|OH|NC|AZ|NJ|IN|TN|MO|MD|WI|MN|SC|AL|LA|KY|OK|CT|UT|IA|NV|AR|MS|KS|NM|NE|WV|ID|HI|NH|ME|MT|RI|DE|SD|ND|AK|VT|WY|DC))',
            r'(San Francisco|New York|Los Angeles|Seattle|Austin|Chicago|Boston|Denver|Atlanta|Portland|Miami|Dallas|Houston|San Diego|San Jose|Bay Area)',
            r'(Bangalore|Mumbai|Delhi|Hyderabad|Chennai|Pune|London|Berlin|Paris|Toronto|Vancouver|Singapore|Tokyo)',
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    async def search(
        self,
        query: str,
        limit: int = 50,
        location: Optional[str] = None
    ) -> FirecrawlSearchResult:
        """
        Search for people using Firecrawl web search.

        Searches LinkedIn profiles via site:linkedin.com/in queries.

        Args:
            query: Natural language search (e.g., "founding engineer react typescript")
            limit: Max results (default 50)
            location: Optional location filter

        Returns:
            FirecrawlSearchResult with matching profiles
        """
        if not self.enabled:
            return FirecrawlSearchResult(profiles=[], total_matches=0, query_used=query)

        search_query = self._build_linkedin_query(query, location)

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(
                        f"{self.base_url}/search",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "query": search_query,
                            "limit": min(limit, 20),  # Firecrawl search limit
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if not data.get("success"):
                            logger.error("Firecrawl search failed: %s", data.get("error", "unknown"))
                            return FirecrawlSearchResult(profiles=[], total_matches=0, query_used=search_query)

                        raw_results = data.get("data", [])
                        logger.info("Firecrawl search returned %s results for: %s", len(raw_results), search_query[:80])

                        profiles = []
                        for r in raw_results:
                            try:
                                profile = self._parse_linkedin_result(r)
                                if profile:
                                    profiles.append(profile)
                            except Exception as e:
                                logger.warning("Failed to parse Firecrawl result: %s", e)
                                continue

                        return FirecrawlSearchResult(
                            profiles=profiles,
                            total_matches=len(profiles),
                            query_used=search_query,
                        )

                    if response.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                        backoff = 0.5 * (2 ** attempt)
                        logger.warning("Firecrawl transient error %s, retrying in %.1fs", response.status_code, backoff)
                        await asyncio.sleep(backoff)
                        continue

                    logger.error("Firecrawl API error status=%s body=%s", response.status_code, response.text[:500])
                    return FirecrawlSearchResult(profiles=[], total_matches=0, query_used=search_query)

                except httpx.HTTPError as exc:
                    if attempt < self.max_retries:
                        backoff = 0.5 * (2 ** attempt)
                        logger.warning("Firecrawl request failed (%s), retrying in %.1fs", exc, backoff)
                        await asyncio.sleep(backoff)
                        continue
                    logger.exception("Firecrawl API exception after retries")
                    return FirecrawlSearchResult(profiles=[], total_matches=0, query_used=query)

    async def health_check(self) -> dict:
        """Return connectivity/auth status for Firecrawl provider."""
        if not self.enabled:
            return {"provider": "firecrawl", "ok": False, "reason": "missing_api_key"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"query": "site:linkedin.com/in software engineer", "limit": 1},
                )
                ok = response.status_code == 200 and response.json().get("success", False)
                return {"provider": "firecrawl", "ok": ok, "status_code": response.status_code}
        except httpx.HTTPError as exc:
            return {"provider": "firecrawl", "ok": False, "reason": str(exc)}


# Singleton instance
firecrawl_client = FirecrawlClient()
