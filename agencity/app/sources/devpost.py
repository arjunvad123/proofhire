"""
Devpost Source - Hackathon projects and participants.

Devpost is the largest hackathon platform with millions of projects.
Great for finding builders who ship fast.
"""

import logging
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData, HackathonData
from app.sources.base import DataSource

logger = logging.getLogger(__name__)


class DevpostSource(DataSource):
    """
    Search hackathon projects on Devpost.

    Since Devpost doesn't have a public API, we search their website
    and extract project/participant data.
    """

    BASE_URL = "https://devpost.com"

    @property
    def name(self) -> str:
        return "Devpost Hackathons"

    @property
    def priority(self) -> int:
        return 3  # After network, GitHub, LinkedIn

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 20,
    ) -> list[CandidateData]:
        """
        Search Devpost for relevant hackathon projects.
        """
        # Build search query
        query = self._build_query(blueprint)
        logger.info(f"Devpost search query: {query}")

        try:
            projects = await self._search_projects(query, limit)
            candidates = await self._extract_participants(projects)
            return candidates[:limit]

        except Exception as e:
            logger.error(f"Devpost search failed: {e}")
            return []

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """Devpost candidates are enriched during search."""
        candidate.enriched_at = datetime.utcnow()
        return candidate

    async def is_available(self) -> bool:
        """Devpost is always available (public website)."""
        return True

    def _build_query(self, blueprint: RoleBlueprint) -> str:
        """Build search query from blueprint."""
        terms = []

        # Add role-related keywords
        role_lower = blueprint.role_title.lower()
        if "prompt" in role_lower or "llm" in role_lower:
            terms.extend(["AI", "LLM", "GPT", "chatbot"])
        if "ml" in role_lower or "machine learning" in role_lower:
            terms.extend(["machine learning", "ML", "neural network"])
        if "backend" in role_lower:
            terms.extend(["API", "backend", "server"])
        if "frontend" in role_lower:
            terms.extend(["frontend", "React", "web app"])

        # Add must-haves
        terms.extend(blueprint.must_haves[:2])

        return " ".join(terms[:5])

    async def _search_projects(
        self,
        query: str,
        limit: int,
    ) -> list[dict]:
        """
        Search Devpost software page for projects.
        """
        projects = []

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Search the software gallery
            url = f"{self.BASE_URL}/software/search"
            params = {"query": query}

            try:
                response = await client.get(url, params=params)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Find project cards
                project_cards = soup.select(".gallery-item")[:limit]

                for card in project_cards:
                    link = card.select_one("a.link-to-software")
                    title_el = card.select_one("h5")
                    tagline_el = card.select_one(".tagline")

                    if link and title_el:
                        projects.append({
                            "url": self.BASE_URL + link.get("href", ""),
                            "title": title_el.get_text(strip=True),
                            "tagline": tagline_el.get_text(strip=True) if tagline_el else "",
                        })

            except Exception as e:
                logger.warning(f"Devpost search error: {e}")

        return projects

    async def _extract_participants(
        self,
        projects: list[dict],
    ) -> list[CandidateData]:
        """
        Extract participant info from project pages.
        """
        candidates = []
        seen_names = set()

        async with httpx.AsyncClient(timeout=15.0) as client:
            for project in projects[:10]:  # Limit to avoid too many requests
                try:
                    response = await client.get(project["url"])
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, "html.parser")

                    # Find team members
                    members = soup.select(".software-team-member")

                    # Get hackathon name
                    hackathon_el = soup.select_one(".software-list-content a")
                    hackathon_name = hackathon_el.get_text(strip=True) if hackathon_el else "Unknown Hackathon"

                    # Check if won prize
                    prize_el = soup.select_one(".winner")
                    won_prize = prize_el is not None
                    prize_name = prize_el.get_text(strip=True) if prize_el else None

                    # Get technologies used
                    tech_tags = soup.select(".cp-tag")
                    technologies = [tag.get_text(strip=True) for tag in tech_tags]

                    for member in members:
                        name_el = member.select_one("h5, .user-name")
                        if not name_el:
                            continue

                        name = name_el.get_text(strip=True)
                        if name in seen_names:
                            continue
                        seen_names.add(name)

                        # Get GitHub/LinkedIn links if available
                        github_link = member.select_one('a[href*="github.com"]')
                        linkedin_link = member.select_one('a[href*="linkedin.com"]')

                        github_username = None
                        if github_link:
                            github_url = github_link.get("href", "")
                            match = re.search(r"github\.com/([^/]+)", github_url)
                            if match:
                                github_username = match.group(1)

                        # Create hackathon data
                        hackathon = HackathonData(
                            name=hackathon_name,
                            project_name=project["title"],
                            project_description=project["tagline"],
                            won_prize=won_prize,
                            prize=prize_name,
                            technologies=technologies,
                            devpost_url=project["url"],
                        )

                        candidate = CandidateData(
                            id=f"devpost_{name.lower().replace(' ', '_')}",
                            name=name,
                            github_username=github_username,
                            linkedin_url=linkedin_link.get("href") if linkedin_link else None,
                            hackathons=[hackathon],
                            sources=["devpost"],
                        )

                        candidates.append(candidate)

                except Exception as e:
                    logger.warning(f"Failed to parse project {project['url']}: {e}")

        logger.info(f"Devpost found {len(candidates)} participants")
        return candidates
