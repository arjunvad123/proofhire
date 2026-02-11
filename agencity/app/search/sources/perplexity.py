"""
Perplexity AI integration.

Uses AI-powered search for complex research queries.
Great for questions like "Who are notable engineers from X company?"
"""

import logging
import re
from typing import Optional

import httpx

from app.search.models import DiscoveredCandidate, SearchPathway
from app.search.sources.base import SearchSource

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


class PerplexitySource(SearchSource):
    """Perplexity AI search source."""

    name = "perplexity"
    cost_per_query = 0.005  # Approximate cost per query
    rate_limit_per_minute = 20

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.client = httpx.AsyncClient(timeout=60.0)

    async def search(
        self,
        pathway: SearchPathway,
        max_results: int = 50
    ) -> list[DiscoveredCandidate]:
        """Execute Perplexity queries for this pathway."""
        if not self.is_configured:
            logger.warning("Perplexity not configured, skipping")
            return []

        candidates = []

        for query in pathway.perplexity_queries:
            try:
                response_text = await self._execute_query(query)
                if response_text:
                    extracted = self._extract_candidates(
                        response_text, pathway, query
                    )
                    candidates.extend(extracted)

            except Exception as e:
                logger.error(f"Perplexity query failed: {e}")
                continue

        logger.info(f"Perplexity returned {len(candidates)} candidates for pathway via {pathway.gateway_node.full_name}")
        return candidates[:max_results]

    async def _execute_query(self, query: str) -> Optional[str]:
        """Execute a Perplexity query."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Enhance the query to get structured output
        enhanced_query = f"""
{query}

Please provide specific names of real people with their:
- Full name
- Current company
- Current title/role
- LinkedIn URL if known

Format each person on a new line like:
Name: [full name] | Company: [company] | Title: [title] | LinkedIn: [url or "unknown"]
"""

        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional recruiter research assistant. Provide accurate, specific information about real people. Only mention people you are confident exist with accurate details."
                },
                {
                    "role": "user",
                    "content": enhanced_query
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.2,  # Low temperature for factual responses
        }

        try:
            response = await self.client.post(
                PERPLEXITY_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Extract the response text
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")

            return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Perplexity rate limited")
            else:
                logger.error(f"Perplexity HTTP error: {e}")
            return None

        except Exception as e:
            logger.error(f"Perplexity request failed: {e}")
            return None

    def _extract_candidates(
        self,
        response_text: str,
        pathway: SearchPathway,
        query: str
    ) -> list[DiscoveredCandidate]:
        """Extract candidate information from Perplexity response."""
        candidates = []

        # Pattern 1: Structured format we requested
        # Name: John Doe | Company: Google | Title: Engineer | LinkedIn: url
        pattern1 = r"Name:\s*([^|]+)\|\s*Company:\s*([^|]+)\|\s*Title:\s*([^|]+)\|\s*LinkedIn:\s*([^\n]+)"

        for match in re.finditer(pattern1, response_text, re.IGNORECASE):
            name = match.group(1).strip()
            company = match.group(2).strip()
            title = match.group(3).strip()
            linkedin = match.group(4).strip()

            if linkedin.lower() in ["unknown", "n/a", "not available"]:
                linkedin = None
            elif linkedin and not linkedin.startswith("http"):
                linkedin = None

            if name and len(name) > 2:
                candidate = self._create_candidate(
                    raw_data={
                        "full_name": name,
                        "linkedin_url": linkedin,
                        "current_company": company if company.lower() != "unknown" else None,
                        "current_title": title if title.lower() != "unknown" else None,
                        "source": "perplexity",
                    },
                    pathway=pathway,
                    query=query,
                    confidence=0.6  # Perplexity needs verification
                )
                candidates.append(candidate)

        # Pattern 2: Bullet points with names
        # - John Doe (Engineer at Google)
        # - Jane Smith, CTO of Startup
        pattern2 = r"[-•]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s*[,\(]([^)\n]+)[\)]?)?"

        for match in re.finditer(pattern2, response_text):
            name = match.group(1).strip()
            context = match.group(2).strip() if match.group(2) else ""

            # Skip if already found via pattern 1
            if any(c.full_name.lower() == name.lower() for c in candidates):
                continue

            # Try to parse company/title from context
            company = None
            title = None

            if context:
                # "Engineer at Google" pattern
                at_match = re.search(r"(.+?)\s+at\s+(.+)", context, re.IGNORECASE)
                if at_match:
                    title = at_match.group(1).strip()
                    company = at_match.group(2).strip()
                # "CTO of Startup" pattern
                of_match = re.search(r"(.+?)\s+of\s+(.+)", context, re.IGNORECASE)
                if of_match:
                    title = of_match.group(1).strip()
                    company = of_match.group(2).strip()

            if name and len(name) > 2 and len(name.split()) >= 2:
                candidate = self._create_candidate(
                    raw_data={
                        "full_name": name,
                        "current_company": company,
                        "current_title": title,
                        "source": "perplexity",
                    },
                    pathway=pathway,
                    query=query,
                    confidence=0.5
                )
                candidates.append(candidate)

        # Pattern 3: Just names in bold or with LinkedIn URLs
        linkedin_pattern = r"linkedin\.com/in/([\w-]+)"
        for match in re.finditer(linkedin_pattern, response_text):
            username = match.group(1)
            linkedin_url = f"https://www.linkedin.com/in/{username}"

            # Check if we already have this LinkedIn
            if any(c.linkedin_url == linkedin_url for c in candidates):
                continue

            # Try to find name near the URL
            candidate = self._create_candidate(
                raw_data={
                    "full_name": username.replace("-", " ").title(),
                    "linkedin_url": linkedin_url,
                    "source": "perplexity",
                },
                pathway=pathway,
                query=query,
                confidence=0.4
            )
            candidates.append(candidate)

        return candidates

    async def health_check(self) -> bool:
        """Check if Perplexity is available."""
        if not self.is_configured:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "sonar",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
            response = await self.client.post(
                PERPLEXITY_API_URL,
                headers=headers,
                json=payload
            )
            return response.status_code == 200
        except Exception:
            return False
