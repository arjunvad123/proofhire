"""
GitHub Source - Find developers via GitHub API.

P1 priority - great for finding active builders.
Uses GraphQL API for efficiency.
"""

import logging
from datetime import datetime

import httpx

from app.config import settings
from app.models.blueprint import RoleBlueprint
from app.models.candidate import (
    ActivityStats,
    CandidateData,
    RepoData,
)
from app.sources.base import DataSource

logger = logging.getLogger(__name__)


class GitHubSource(DataSource):
    """
    Search and enrich candidates via GitHub API.

    Search strategies:
    1. Search repos matching skills → get contributors
    2. Search users by location/bio
    3. Find people who starred relevant repos
    """

    GRAPHQL_URL = "https://api.github.com/graphql"
    REST_URL = "https://api.github.com"

    @property
    def name(self) -> str:
        return "GitHub"

    @property
    def priority(self) -> int:
        return 1

    def __init__(self, token: str | None = None):
        self.token = token or settings.github_token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 50,
    ) -> list[CandidateData]:
        """
        Search GitHub for developers matching the blueprint.
        """
        if not self.token:
            logger.warning("GitHub token not configured, skipping search")
            return []

        candidates = []

        # Build search query from blueprint
        query = self._build_search_query(blueprint)
        logger.info(f"GitHub search query: {query}")

        try:
            # Search for users
            users = await self._search_users(query, limit)

            for user in users:
                candidate = CandidateData(
                    id=f"gh_{user['login']}",
                    name=user.get("name") or user["login"],
                    github_username=user["login"],
                    github_url=user["html_url"],
                    location=user.get("location"),
                    sources=["github"],
                )
                candidates.append(candidate)

        except Exception as e:
            logger.error(f"GitHub search failed: {e}")

        return candidates[:limit]

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """
        Enrich candidate with detailed GitHub data.

        Fetches:
        - Repository list with analysis
        - Contribution activity
        - Profile details
        """
        if not candidate.github_username or not self.token:
            return candidate

        try:
            # Fetch repos and activity using GraphQL
            data = await self._fetch_user_data(candidate.github_username)

            if data:
                # Parse repos
                repos = []
                for repo in data.get("repositories", {}).get("nodes", []):
                    repo_data = RepoData(
                        name=repo["name"],
                        description=repo.get("description"),
                        language=repo.get("primaryLanguage", {}).get("name"),
                        stars=repo.get("stargazerCount", 0),
                        forks=repo.get("forkCount", 0),
                        is_fork=repo.get("isFork", False),
                    )
                    # Check for LLM/ML indicators
                    desc = (repo.get("description") or "").lower()
                    name = repo["name"].lower()
                    if any(kw in desc or kw in name for kw in ["llm", "gpt", "claude", "openai", "langchain"]):
                        repo_data.has_llm_usage = True
                    if any(kw in desc or kw in name for kw in ["ml", "machine learning", "neural", "tensorflow", "pytorch"]):
                        repo_data.has_ml_code = True

                    repos.append(repo_data)

                candidate.github_repos = repos

                # Parse activity
                contrib = data.get("contributionsCollection", {})
                candidate.github_activity = ActivityStats(
                    commits_last_90_days=contrib.get("totalCommitContributions", 0),
                    prs_last_90_days=contrib.get("totalPullRequestContributions", 0),
                    issues_last_90_days=contrib.get("totalIssueContributions", 0),
                    total_contributions_last_year=contrib.get("contributionCalendar", {}).get("totalContributions", 0),
                )

            candidate.enriched_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"GitHub enrichment failed for {candidate.github_username}: {e}")

        return candidate

    async def is_available(self) -> bool:
        """Check if GitHub API is accessible."""
        return bool(self.token)

    def _build_search_query(self, blueprint: RoleBlueprint) -> str:
        """Build GitHub user search query from blueprint."""
        parts = []

        # Add role-related keywords
        role_keywords = blueprint.role_title.lower().split()
        for kw in role_keywords:
            if kw not in ["a", "an", "the", "for", "at"]:
                parts.append(kw)

        # Add must-haves as keywords
        for must_have in blueprint.must_haves[:3]:  # Limit to top 3
            parts.append(must_have.lower())

        # Add location filter
        for loc in blueprint.location_preferences[:1]:  # Only first location
            parts.append(f"location:{loc}")

        return " ".join(parts)

    async def _search_users(self, query: str, limit: int) -> list[dict]:
        """Search GitHub users via REST API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.REST_URL}/search/users",
                params={"q": query, "per_page": min(limit, 100)},
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])

    async def _fetch_user_data(self, username: str) -> dict | None:
        """Fetch detailed user data via GraphQL."""
        query = """
        query($username: String!) {
            user(login: $username) {
                name
                bio
                location
                company
                contributionsCollection {
                    totalCommitContributions
                    totalPullRequestContributions
                    totalIssueContributions
                    contributionCalendar {
                        totalContributions
                    }
                }
                repositories(first: 10, orderBy: {field: STARGAZERS_COUNT, direction: DESC}, ownerAffiliations: OWNER) {
                    nodes {
                        name
                        description
                        primaryLanguage { name }
                        stargazerCount
                        forkCount
                        isFork
                    }
                }
            }
        }
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": {"username": username}},
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("user")
