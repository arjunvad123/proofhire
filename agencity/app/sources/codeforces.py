"""
Codeforces Source - Competitive programming profiles.

Codeforces has 600K+ members with public ratings and problem-solving stats.
Great for finding strong algorithmic thinkers.

API Docs: https://codeforces.com/apiHelp
"""

import logging
from datetime import datetime

import httpx

from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData
from app.sources.base import DataSource

logger = logging.getLogger(__name__)


class CodeforcesSource(DataSource):
    """
    Search competitive programmers on Codeforces.

    Codeforces ratings:
    - Grandmaster (2600+): Top 0.1%
    - Master (2200-2399): Top 1%
    - Candidate Master (1900-2199): Top 5%
    - Expert (1600-1899): Top 15%
    - Specialist (1400-1599): Top 30%
    """

    BASE_URL = "https://codeforces.com/api"

    # Rating thresholds for filtering
    RATING_THRESHOLDS = {
        "grandmaster": 2600,
        "master": 2200,
        "candidate_master": 1900,
        "expert": 1600,
        "specialist": 1400,
    }

    @property
    def name(self) -> str:
        return "Codeforces"

    @property
    def priority(self) -> int:
        return 4

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 30,
    ) -> list[CandidateData]:
        """
        Search Codeforces for competitive programmers.

        Strategy:
        1. Get rated users list
        2. Filter by location preferences
        3. Sort by rating
        """
        # Check if role needs algorithmic skills
        if not self._is_relevant(blueprint):
            logger.info("Codeforces not relevant for this role, skipping")
            return []

        try:
            candidates = await self._search_rated_users(blueprint, limit)
            return candidates

        except Exception as e:
            logger.error(f"Codeforces search failed: {e}")
            return []

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """
        Enrich candidate with Codeforces stats.
        """
        if not hasattr(candidate, 'codeforces_handle') or not candidate.codeforces_handle:
            return candidate

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/user.info",
                    params={"handles": candidate.codeforces_handle},
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "OK" and data.get("result"):
                    user = data["result"][0]
                    # Add to skills based on rating
                    if user.get("rating"):
                        rating = user["rating"]
                        if rating >= 2200:
                            candidate.skills.append(f"Codeforces Master ({rating})")
                        elif rating >= 1900:
                            candidate.skills.append(f"Codeforces Candidate Master ({rating})")
                        elif rating >= 1600:
                            candidate.skills.append(f"Codeforces Expert ({rating})")

        except Exception as e:
            logger.warning(f"Codeforces enrichment failed: {e}")

        candidate.enriched_at = datetime.utcnow()
        return candidate

    async def is_available(self) -> bool:
        """Codeforces API is always available."""
        return True

    def _is_relevant(self, blueprint: RoleBlueprint) -> bool:
        """Check if competitive programming is relevant for this role."""
        keywords = [
            "algorithm", "data structure", "competitive", "problem solving",
            "backend", "systems", "infrastructure", "performance",
            "ml", "machine learning", "ai", "quantitative",
        ]

        text = f"{blueprint.role_title} {blueprint.specific_work} {' '.join(blueprint.must_haves)}".lower()
        return any(kw in text for kw in keywords)

    async def _search_rated_users(
        self,
        blueprint: RoleBlueprint,
        limit: int,
    ) -> list[CandidateData]:
        """
        Get rated users from Codeforces.

        Note: Codeforces API doesn't support search, so we get top users
        and filter by available criteria.
        """
        candidates = []

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Get rated users (returns all users sorted by rating desc)
            response = await client.get(
                f"{self.BASE_URL}/user.ratedList",
                params={"activeOnly": "true"},  # Only active users
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                return []

            users = data.get("result", [])

            # Filter and limit
            min_rating = 1600  # At least Expert level

            for user in users:
                if len(candidates) >= limit:
                    break

                rating = user.get("rating", 0)
                if rating < min_rating:
                    continue

                # Check location match if preferences exist
                country = user.get("country", "")
                city = user.get("city", "")
                org = user.get("organization", "")

                if blueprint.location_preferences:
                    location_match = any(
                        pref.lower() in f"{country} {city} {org}".lower()
                        for pref in blueprint.location_preferences
                    )
                    if not location_match:
                        continue

                # Build candidate
                handle = user.get("handle", "")
                name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                if not name:
                    name = handle

                rank = user.get("rank", "").replace(" ", "_")

                candidate = CandidateData(
                    id=f"cf_{handle}",
                    name=name,
                    location=f"{city}, {country}" if city else country,
                    skills=[
                        f"Codeforces {user.get('rank', 'Rated')} ({rating})",
                        "Algorithms",
                        "Data Structures",
                        "Competitive Programming",
                    ],
                    sources=["codeforces"],
                )

                # Store handle for enrichment
                candidate.codeforces_handle = handle

                candidates.append(candidate)

        logger.info(f"Codeforces found {len(candidates)} competitive programmers")
        return candidates


class LeetCodeSource(DataSource):
    """
    Search LeetCode profiles via third-party API.

    LeetCode has 10M+ users focused on interview preparation.
    """

    # Using CompeteAPI proxy
    BASE_URL = "https://competeapi.vercel.app"

    @property
    def name(self) -> str:
        return "LeetCode"

    @property
    def priority(self) -> int:
        return 5

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 20,
    ) -> list[CandidateData]:
        """
        LeetCode doesn't have a search API, so this is limited.
        We can only look up known usernames.
        """
        # LeetCode search is not available without usernames
        # This source is primarily for enrichment
        return []

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """
        Enrich candidate with LeetCode stats if username known.
        """
        leetcode_username = getattr(candidate, 'leetcode_username', None)
        if not leetcode_username:
            return candidate

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/user/leetcode/{leetcode_username}/"
                )
                if response.status_code == 200:
                    data = response.json()
                    # Add LeetCode stats to skills
                    solved = data.get("solved", 0)
                    if solved > 500:
                        candidate.skills.append(f"LeetCode: {solved}+ problems solved")
                    elif solved > 200:
                        candidate.skills.append(f"LeetCode: {solved} problems solved")

        except Exception as e:
            logger.warning(f"LeetCode enrichment failed: {e}")

        return candidate

    async def is_available(self) -> bool:
        return True
