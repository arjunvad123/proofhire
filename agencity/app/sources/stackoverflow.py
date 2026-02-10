"""
Stack Overflow Source - Developer reputation and expertise.

Stack Overflow has profiles for millions of developers with
reputation scores, badges, and expertise tags.

API Docs: https://api.stackexchange.com/docs
"""

import logging
from datetime import datetime

import httpx

from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData
from app.sources.base import DataSource

logger = logging.getLogger(__name__)


class StackOverflowSource(DataSource):
    """
    Search developers on Stack Overflow.

    Reputation levels:
    - 100K+: Top contributors, recognized experts
    - 10K+: Trusted users, significant expertise
    - 1K+: Active contributors
    """

    BASE_URL = "https://api.stackexchange.com/2.3"

    @property
    def name(self) -> str:
        return "Stack Overflow"

    @property
    def priority(self) -> int:
        return 5

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 30,
    ) -> list[CandidateData]:
        """
        Search Stack Overflow for developers with relevant expertise.
        """
        # Build tag query from blueprint
        tags = self._extract_tags(blueprint)
        if not tags:
            logger.info("No relevant tags for Stack Overflow search")
            return []

        try:
            candidates = []

            async with httpx.AsyncClient(timeout=15.0) as client:
                for tag in tags[:3]:  # Limit to top 3 tags
                    users = await self._search_top_users_by_tag(client, tag, limit // 3)
                    candidates.extend(users)

            # Dedupe by user_id
            seen_ids = set()
            unique = []
            for c in candidates:
                if c.id not in seen_ids:
                    seen_ids.add(c.id)
                    unique.append(c)

            return unique[:limit]

        except Exception as e:
            logger.error(f"Stack Overflow search failed: {e}")
            return []

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """Stack Overflow candidates are enriched during search."""
        candidate.enriched_at = datetime.utcnow()
        return candidate

    async def is_available(self) -> bool:
        return True

    def _extract_tags(self, blueprint: RoleBlueprint) -> list[str]:
        """Extract Stack Overflow tags from blueprint."""
        # Map common terms to SO tags
        tag_mapping = {
            "python": "python",
            "javascript": "javascript",
            "typescript": "typescript",
            "react": "reactjs",
            "node": "node.js",
            "java": "java",
            "go": "go",
            "golang": "go",
            "rust": "rust",
            "c++": "c++",
            "ml": "machine-learning",
            "machine learning": "machine-learning",
            "ai": "artificial-intelligence",
            "llm": "large-language-model",
            "deep learning": "deep-learning",
            "nlp": "nlp",
            "backend": "backend",
            "frontend": "frontend",
            "aws": "amazon-web-services",
            "docker": "docker",
            "kubernetes": "kubernetes",
            "sql": "sql",
            "postgresql": "postgresql",
            "mongodb": "mongodb",
        }

        text = f"{blueprint.role_title} {blueprint.specific_work} {' '.join(blueprint.must_haves)}".lower()

        tags = []
        for term, tag in tag_mapping.items():
            if term in text and tag not in tags:
                tags.append(tag)

        return tags

    async def _search_top_users_by_tag(
        self,
        client: httpx.AsyncClient,
        tag: str,
        limit: int,
    ) -> list[CandidateData]:
        """
        Get top answerers for a specific tag.
        """
        candidates = []

        try:
            response = await client.get(
                f"{self.BASE_URL}/tags/{tag}/top-answerers/all_time",
                params={
                    "site": "stackoverflow",
                    "pagesize": min(limit, 30),
                    "filter": "!*Mg4Pjg8OTLnNnRo",  # Include user details
                },
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                user = item.get("user", {})
                if not user:
                    continue

                user_id = user.get("user_id")
                reputation = user.get("reputation", 0)

                # Only include users with meaningful reputation
                if reputation < 1000:
                    continue

                name = user.get("display_name", f"User {user_id}")
                location = user.get("location", "")

                # Build reputation description
                if reputation >= 100000:
                    rep_desc = f"Stack Overflow Top Contributor ({reputation:,} rep)"
                elif reputation >= 10000:
                    rep_desc = f"Stack Overflow Expert ({reputation:,} rep)"
                else:
                    rep_desc = f"Stack Overflow Active ({reputation:,} rep)"

                candidate = CandidateData(
                    id=f"so_{user_id}",
                    name=name,
                    location=location,
                    skills=[
                        rep_desc,
                        f"Expert in {tag}",
                    ],
                    sources=["stackoverflow"],
                )

                # Store SO link
                candidate.stackoverflow_url = user.get("link")

                candidates.append(candidate)

        except Exception as e:
            logger.warning(f"Stack Overflow tag search failed for {tag}: {e}")

        return candidates
