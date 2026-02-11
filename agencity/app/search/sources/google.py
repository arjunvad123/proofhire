"""
Google Custom Search Engine integration.

Good for discovery queries and finding LinkedIn profiles.
Cheaper than PDL but less structured results.
"""

import logging
import re
from typing import Optional

import httpx

from app.search.models import DiscoveredCandidate, SearchPathway
from app.search.sources.base import SearchSource

logger = logging.getLogger(__name__)

GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"


class GoogleSearchSource(SearchSource):
    """Google Custom Search Engine source."""

    name = "google"
    cost_per_query = 0.005  # $5 per 1000 queries
    rate_limit_per_minute = 100

    def __init__(
        self,
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None
    ):
        super().__init__(api_key)
        self.search_engine_id = search_engine_id
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def is_configured(self) -> bool:
        return self.api_key is not None and self.search_engine_id is not None

    async def search(
        self,
        pathway: SearchPathway,
        max_results: int = 50
    ) -> list[DiscoveredCandidate]:
        """Execute Google queries for this pathway."""
        if not self.is_configured:
            logger.warning("Google CSE not configured, skipping")
            return []

        candidates = []

        for query in pathway.google_queries:
            try:
                results = await self._execute_query(query, max_results=10)

                for result in results:
                    candidate = self._parse_google_result(result, pathway, query)
                    if candidate:
                        candidates.append(candidate)

            except Exception as e:
                logger.error(f"Google query failed: {e}")
                continue

        logger.info(f"Google returned {len(candidates)} candidates for pathway via {pathway.gateway_node.full_name}")
        return candidates

    async def _execute_query(self, query: str, max_results: int = 10) -> list[dict]:
        """Execute a Google Custom Search query."""
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(max_results, 10),  # Google max is 10 per request
        }

        try:
            response = await self.client.get(GOOGLE_CSE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Google CSE rate limited")
            else:
                logger.error(f"Google CSE HTTP error: {e}")
            return []

        except Exception as e:
            logger.error(f"Google CSE request failed: {e}")
            return []

    def _parse_google_result(
        self,
        result: dict,
        pathway: SearchPathway,
        query: str
    ) -> Optional[DiscoveredCandidate]:
        """Parse a Google result into a DiscoveredCandidate."""
        try:
            link = result.get("link", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            # Check if this is a LinkedIn profile
            linkedin_url = None
            if "linkedin.com/in/" in link:
                linkedin_url = link

            # Try to extract name from LinkedIn title
            # Format: "Name - Title - Company | LinkedIn"
            full_name = None
            current_title = None
            current_company = None

            if linkedin_url:
                # Parse LinkedIn title format
                parts = title.split(" - ")
                if len(parts) >= 1:
                    full_name = parts[0].strip()
                if len(parts) >= 2:
                    current_title = parts[1].strip()
                if len(parts) >= 3:
                    # Remove " | LinkedIn" suffix
                    company_part = parts[2].split("|")[0].strip()
                    current_company = company_part

            # GitHub profile
            github_url = None
            if "github.com/" in link:
                github_url = link
                # Extract username from URL
                match = re.search(r"github\.com/([^/]+)", link)
                if match:
                    full_name = match.group(1)

            # Twitter/X profile
            if "twitter.com/" in link or "x.com/" in link:
                match = re.search(r"(?:twitter|x)\.com/([^/]+)", link)
                if match:
                    full_name = match.group(1)

            # Skip if we couldn't extract a name
            if not full_name:
                return None

            # Clean up the name
            full_name = full_name.strip()
            if full_name.lower() in ["linkedin", "github", "twitter"]:
                return None

            return self._create_candidate(
                raw_data={
                    "full_name": full_name,
                    "linkedin_url": linkedin_url,
                    "github_url": github_url,
                    "current_company": current_company,
                    "current_title": current_title,
                    "source_url": link,
                    "snippet": snippet,
                },
                pathway=pathway,
                query=query,
                confidence=0.5  # Lower confidence - needs verification
            )

        except Exception as e:
            logger.error(f"Failed to parse Google result: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if Google CSE is available."""
        if not self.is_configured:
            return False

        try:
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": "test",
                "num": 1,
            }
            response = await self.client.get(GOOGLE_CSE_URL, params=params)
            return response.status_code == 200
        except Exception:
            return False
