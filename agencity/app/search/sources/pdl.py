"""
People Data Labs (PDL) integration.

PDL is the most powerful source for structured people search.
Supports queries by company, school, title, skills, location.
"""

import logging
from typing import Optional

import httpx

from app.search.models import DiscoveredCandidate, SearchPathway
from app.search.sources.base import SearchSource

logger = logging.getLogger(__name__)

PDL_API_URL = "https://api.peopledatalabs.com/v5/person/search"


class PDLSource(SearchSource):
    """People Data Labs search source."""

    name = "pdl"
    cost_per_query = 0.01  # ~$0.01 per search result
    rate_limit_per_minute = 100

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search(
        self,
        pathway: SearchPathway,
        max_results: int = 50
    ) -> list[DiscoveredCandidate]:
        """Execute PDL queries for this pathway."""
        if not self.is_configured:
            logger.warning("PDL not configured, skipping")
            return []

        candidates = []

        for query_dict in pathway.pdl_queries:
            try:
                query = query_dict.get("query", query_dict)
                description = query_dict.get("description", "PDL search")

                # Adjust size
                if isinstance(query, dict) and "size" in query:
                    query["size"] = min(query["size"], max_results)

                results = await self._execute_query(query)

                for result in results:
                    candidate = self._parse_pdl_result(result, pathway, description)
                    if candidate:
                        candidates.append(candidate)

            except Exception as e:
                logger.error(f"PDL query failed: {e}")
                continue

        logger.info(f"PDL returned {len(candidates)} candidates for pathway via {pathway.gateway_node.full_name}")
        return candidates

    async def _execute_query(self, query: dict) -> list[dict]:
        """Execute a PDL query."""
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(
                PDL_API_URL,
                headers=headers,
                json=query
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 402:
                logger.warning("PDL payment required - out of credits")
            elif e.response.status_code == 429:
                logger.warning("PDL rate limited")
            else:
                logger.error(f"PDL HTTP error: {e}")
            return []

        except Exception as e:
            logger.error(f"PDL request failed: {e}")
            return []

    def _parse_pdl_result(
        self,
        result: dict,
        pathway: SearchPathway,
        query_description: str
    ) -> Optional[DiscoveredCandidate]:
        """Parse a PDL result into a DiscoveredCandidate."""
        try:
            # Extract name
            full_name = result.get("full_name")
            if not full_name:
                first = result.get("first_name", "")
                last = result.get("last_name", "")
                full_name = f"{first} {last}".strip()

            if not full_name:
                return None

            # Extract current job
            job_title = result.get("job_title")
            job_company = result.get("job_company_name")

            # If not in top-level, check experience
            if not job_title and result.get("experience"):
                exp = result["experience"]
                if exp and len(exp) > 0:
                    current = exp[0]  # Most recent
                    job_title = current.get("title", {}).get("name")
                    job_company = current.get("company", {}).get("name")

            # LinkedIn URL
            linkedin_url = None
            if result.get("linkedin_url"):
                linkedin_url = result["linkedin_url"]
            elif result.get("profiles"):
                for profile in result["profiles"]:
                    if "linkedin" in profile.get("network", "").lower():
                        linkedin_url = profile.get("url")
                        break

            # GitHub URL
            github_url = None
            if result.get("github_url"):
                github_url = result["github_url"]
            elif result.get("profiles"):
                for profile in result["profiles"]:
                    if "github" in profile.get("network", "").lower():
                        github_url = profile.get("url")
                        break

            # Extract email (PDL may return boolean True if email exists but not included)
            email = None
            work_email = result.get("work_email")
            if isinstance(work_email, str):
                email = work_email
            elif result.get("personal_emails"):
                emails = result["personal_emails"]
                if isinstance(emails, list) and emails and isinstance(emails[0], str):
                    email = emails[0]

            # Extract location (may also be boolean)
            location = result.get("location_name")
            if not isinstance(location, str):
                location = None

            # Create candidate
            return self._create_candidate(
                raw_data={
                    "full_name": full_name,
                    "email": email,
                    "linkedin_url": linkedin_url,
                    "github_url": github_url,
                    "current_company": job_company,
                    "current_title": job_title,
                    "location": location,
                    "skills": result.get("skills", []) if isinstance(result.get("skills"), list) else [],
                    "experience": result.get("experience", []) if isinstance(result.get("experience"), list) else [],
                    "education": result.get("education", []) if isinstance(result.get("education"), list) else [],
                },
                pathway=pathway,
                query=query_description,
                confidence=0.85  # PDL data is generally reliable
            )

        except Exception as e:
            logger.error(f"Failed to parse PDL result: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if PDL is available."""
        if not self.is_configured:
            return False

        try:
            headers = {"X-Api-Key": self.api_key}
            response = await self.client.get(
                "https://api.peopledatalabs.com/v5/person/enrich",
                headers=headers,
                params={"email": "test@test.com"}  # Will fail but checks auth
            )
            # 404 means auth worked but no data - that's fine
            return response.status_code in [200, 404]
        except Exception:
            return False
