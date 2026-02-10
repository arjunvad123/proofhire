"""
ProductHunt Source - Makers and builders.

ProductHunt has profiles of people who build and ship products.
Great for finding entrepreneurial talent who can execute.

API Docs: https://api.producthunt.com/v2/docs
"""

import logging
from datetime import datetime

import httpx

from app.config import settings
from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData
from app.sources.base import DataSource

logger = logging.getLogger(__name__)


class ProductHuntSource(DataSource):
    """
    Search makers on ProductHunt.

    Good for finding:
    - People who ship products
    - Entrepreneurial engineers
    - Full-stack builders
    """

    BASE_URL = "https://api.producthunt.com/v2/api/graphql"

    @property
    def name(self) -> str:
        return "ProductHunt"

    @property
    def priority(self) -> int:
        return 7

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, 'producthunt_api_key', '')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 20,
    ) -> list[CandidateData]:
        """
        Search ProductHunt for makers.

        Strategy: Find products matching the domain, then get their makers.
        """
        if not self.api_key:
            logger.info("ProductHunt API key not configured, skipping")
            return []

        # Check if role needs builder mentality
        if not self._is_relevant(blueprint):
            return []

        try:
            candidates = await self._search_makers(blueprint, limit)
            return candidates

        except Exception as e:
            logger.error(f"ProductHunt search failed: {e}")
            return []

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """ProductHunt candidates include maker info from search."""
        candidate.enriched_at = datetime.utcnow()
        return candidate

    async def is_available(self) -> bool:
        return bool(self.api_key)

    def _is_relevant(self, blueprint: RoleBlueprint) -> bool:
        """Check if ProductHunt is relevant for this role."""
        # Good for startup/product roles
        keywords = [
            "startup", "product", "full stack", "fullstack",
            "founder", "builder", "ship", "launch",
            "mvp", "saas", "app",
        ]

        text = f"{blueprint.company_context} {blueprint.specific_work}".lower()
        return any(kw in text for kw in keywords)

    async def _search_makers(
        self,
        blueprint: RoleBlueprint,
        limit: int,
    ) -> list[CandidateData]:
        """
        Search for products and extract makers.
        """
        candidates = []

        # Build topic query
        topic = self._get_topic(blueprint)

        query = """
        query($topic: String!, $first: Int!) {
            posts(topic: $topic, first: $first, order: VOTES) {
                edges {
                    node {
                        name
                        tagline
                        votesCount
                        makers {
                            id
                            name
                            headline
                            twitterUsername
                            websiteUrl
                        }
                    }
                }
            }
        }
        """

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    self.BASE_URL,
                    json={
                        "query": query,
                        "variables": {"topic": topic, "first": 20},
                    },
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()

                seen_makers = set()

                for edge in data.get("data", {}).get("posts", {}).get("edges", []):
                    post = edge.get("node", {})
                    product_name = post.get("name", "")
                    votes = post.get("votesCount", 0)

                    for maker in post.get("makers", []):
                        maker_id = maker.get("id")
                        if maker_id in seen_makers:
                            continue
                        seen_makers.add(maker_id)

                        name = maker.get("name", "Unknown")
                        headline = maker.get("headline", "")

                        # Build skills from context
                        skills = ["Product Builder", "Shipped Products"]
                        if votes > 100:
                            skills.append(f"Made {product_name} ({votes} votes)")

                        candidate = CandidateData(
                            id=f"ph_{maker_id}",
                            name=name,
                            current_role=headline,
                            skills=skills,
                            sources=["producthunt"],
                        )

                        # Add Twitter if available
                        if maker.get("twitterUsername"):
                            candidate.twitter_handle = maker["twitterUsername"]

                        candidates.append(candidate)

                        if len(candidates) >= limit:
                            break

                    if len(candidates) >= limit:
                        break

            except Exception as e:
                logger.warning(f"ProductHunt search failed: {e}")

        logger.info(f"ProductHunt found {len(candidates)} makers")
        return candidates

    def _get_topic(self, blueprint: RoleBlueprint) -> str:
        """Map blueprint to ProductHunt topic."""
        text = f"{blueprint.role_title} {blueprint.specific_work}".lower()

        if "ai" in text or "ml" in text or "llm" in text:
            return "artificial-intelligence"
        if "developer" in text or "api" in text:
            return "developer-tools"
        if "saas" in text:
            return "saas"
        if "mobile" in text or "ios" in text or "android" in text:
            return "iphone"
        if "design" in text:
            return "design-tools"

        return "tech"  # Default
