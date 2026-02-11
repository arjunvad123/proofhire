"""
GitHub API integration.

Excellent for finding engineers through:
- Repository contributors
- Organization members
- User search by company/location
"""

import logging
from typing import Optional

import httpx

from app.search.models import DiscoveredCandidate, SearchPathway
from app.search.sources.base import SearchSource

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"


class GitHubSource(SearchSource):
    """GitHub API search source."""

    name = "github"
    cost_per_query = 0.0  # Free (with rate limits)
    rate_limit_per_minute = 30  # Unauthenticated: 10, authenticated: 30

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search(
        self,
        pathway: SearchPathway,
        max_results: int = 50
    ) -> list[DiscoveredCandidate]:
        """Execute GitHub queries for this pathway."""
        candidates = []

        for query_dict in pathway.github_queries:
            try:
                query_type = query_dict.get("type", "user_search")
                description = query_dict.get("description", "GitHub search")

                if query_type == "user_search":
                    results = await self._search_users(query_dict.get("query", ""))
                elif query_type == "org_members":
                    results = await self._get_org_members(query_dict.get("org", ""))
                elif query_type == "repo_search":
                    results = await self._search_repo_contributors(query_dict)
                else:
                    continue

                for result in results[:max_results]:
                    candidate = self._parse_github_user(result, pathway, description)
                    if candidate:
                        candidates.append(candidate)

            except Exception as e:
                logger.error(f"GitHub query failed: {e}")
                continue

        logger.info(f"GitHub returned {len(candidates)} candidates for pathway via {pathway.gateway_node.full_name}")
        return candidates

    def _get_headers(self) -> dict:
        """Get request headers, with auth if available."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Agencity-Search"
        }
        if self.api_key:
            headers["Authorization"] = f"token {self.api_key}"
        return headers

    async def _search_users(self, query: str, filter_company: str = None) -> list[dict]:
        """Search GitHub users.

        Note: GitHub User Search API doesn't support company: qualifier.
        Valid qualifiers: type, in, repos, location, language, created, followers.
        If we need to filter by company, we fetch user details and filter locally.
        """
        # Remove invalid company: qualifier if present and extract for local filtering
        if "company:" in query.lower():
            import re
            match = re.search(r"company:(\S+)", query, re.IGNORECASE)
            if match:
                filter_company = match.group(1).replace('"', '').replace("'", "")
                query = re.sub(r"company:\S+", "", query, flags=re.IGNORECASE).strip()

        # If query is empty after removing company, use a broader search
        if not query.strip():
            query = "repos:>10 followers:>5"  # Active users

        try:
            response = await self.client.get(
                f"{GITHUB_API_URL}/search/users",
                headers=self._get_headers(),
                params={"q": query, "per_page": 50}
            )
            response.raise_for_status()
            data = response.json()

            # Get full user details for each result
            users = []
            for item in data.get("items", [])[:30]:  # Limit to avoid rate limits
                user = await self._get_user_details(item.get("login"))
                if user:
                    # If we need to filter by company, check the company field
                    if filter_company:
                        user_company = (user.get("company") or "").lower()
                        if filter_company.lower() in user_company:
                            users.append(user)
                    else:
                        users.append(user)

                if len(users) >= 20:  # Enough users
                    break

            return users

        except Exception as e:
            logger.error(f"GitHub user search failed: {e}")
            return []

    async def _get_org_members(self, org: str) -> list[dict]:
        """Get members of a GitHub organization."""
        if not org:
            return []

        # Clean org name - GitHub orgs can only have alphanumeric and hyphens
        import re
        org = re.sub(r'[^a-zA-Z0-9-]', '', org.lower())
        if not org or len(org) < 2:
            return []

        try:
            response = await self.client.get(
                f"{GITHUB_API_URL}/orgs/{org}/members",
                headers=self._get_headers(),
                params={"per_page": 50}
            )

            if response.status_code in [404, 422]:
                # Org doesn't exist, is private, or invalid name
                return []

            response.raise_for_status()
            members = response.json()

            # Get full details for each member
            users = []
            for member in members[:20]:  # Limit
                user = await self._get_user_details(member.get("login"))
                if user:
                    users.append(user)

            return users

        except Exception as e:
            logger.error(f"GitHub org members failed: {e}")
            return []

    async def _search_repo_contributors(self, query_dict: dict) -> list[dict]:
        """Search for repos and get their contributors."""
        query = query_dict.get("query", "")
        get_contributors = query_dict.get("get_contributors", True)
        languages = query_dict.get("languages", [])

        # Clean org: prefix if present (GitHub orgs can only have alphanumeric and hyphens)
        import re
        if "org:" in query:
            # Extract and clean the org name
            match = re.search(r'org:([^\s]+)', query)
            if match:
                org_name = match.group(1)
                clean_org = re.sub(r'[^a-zA-Z0-9-]', '', org_name.lower())
                if clean_org and len(clean_org) >= 2:
                    query = query.replace(f"org:{org_name}", f"org:{clean_org}")
                else:
                    # Skip invalid org search, use general query
                    query = re.sub(r'org:[^\s]+\s*', '', query).strip()

        # Add language filter to query if specified
        if languages:
            lang_filter = " ".join([f"language:{lang}" for lang in languages[:2]])
            query = f"{query} {lang_filter}"

        if not query.strip():
            return []

        try:
            # First, search for repos
            response = await self.client.get(
                f"{GITHUB_API_URL}/search/repositories",
                headers=self._get_headers(),
                params={"q": query, "per_page": 10, "sort": "stars"}
            )

            # Handle invalid queries gracefully
            if response.status_code == 422:
                logger.debug(f"GitHub query invalid (422): {query}")
                return []
            response.raise_for_status()
            repos = response.json().get("items", [])

            if not get_contributors:
                return []

            # Get contributors from top repos
            users = []
            for repo in repos[:3]:  # Top 3 repos
                owner = repo.get("owner", {}).get("login")
                name = repo.get("name")

                contrib_response = await self.client.get(
                    f"{GITHUB_API_URL}/repos/{owner}/{name}/contributors",
                    headers=self._get_headers(),
                    params={"per_page": 20}
                )

                if contrib_response.status_code == 200:
                    for contrib in contrib_response.json()[:10]:
                        user = await self._get_user_details(contrib.get("login"))
                        if user:
                            user["_repo_contributed"] = f"{owner}/{name}"
                            users.append(user)

            return users

        except Exception as e:
            logger.error(f"GitHub repo contributor search failed: {e}")
            return []

    async def _get_user_details(self, username: str) -> Optional[dict]:
        """Get full user details."""
        if not username:
            return None

        try:
            response = await self.client.get(
                f"{GITHUB_API_URL}/users/{username}",
                headers=self._get_headers()
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to get user {username}: {e}")
            return None

    def _parse_github_user(
        self,
        user: dict,
        pathway: SearchPathway,
        query_description: str
    ) -> Optional[DiscoveredCandidate]:
        """Parse a GitHub user into a DiscoveredCandidate."""
        try:
            login = user.get("login", "")
            name = user.get("name") or login

            if not name:
                return None

            # Build GitHub URL
            github_url = user.get("html_url") or f"https://github.com/{login}"

            # Company (GitHub often has this)
            company = user.get("company", "")
            if company and company.startswith("@"):
                company = company[1:]  # Remove @ prefix

            # Try to find LinkedIn from bio
            bio = user.get("bio", "") or ""
            linkedin_url = None
            if "linkedin.com" in bio.lower():
                import re
                match = re.search(r"linkedin\.com/in/[\w-]+", bio.lower())
                if match:
                    linkedin_url = f"https://www.{match.group(0)}"

            # Email (if public)
            email = user.get("email")

            return self._create_candidate(
                raw_data={
                    "full_name": name,
                    "email": email,
                    "linkedin_url": linkedin_url,
                    "github_url": github_url,
                    "current_company": company,
                    "location": user.get("location"),
                    "bio": bio,
                    "github_followers": user.get("followers", 0),
                    "github_repos": user.get("public_repos", 0),
                    "github_username": login,
                },
                pathway=pathway,
                query=query_description,
                confidence=0.7  # GitHub profiles are real people
            )

        except Exception as e:
            logger.error(f"Failed to parse GitHub user: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if GitHub API is available."""
        try:
            response = await self.client.get(
                f"{GITHUB_API_URL}/rate_limit",
                headers=self._get_headers()
            )
            return response.status_code == 200
        except Exception:
            return False
