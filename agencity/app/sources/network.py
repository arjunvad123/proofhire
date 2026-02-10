"""
Network Source - Our own candidate database.

This is P0 priority - our opted-in network of 6,000+ candidates.
Fastest and highest quality source.
"""

import logging
from datetime import datetime

from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData
from app.sources.base import DataSource

logger = logging.getLogger(__name__)


class NetworkSource(DataSource):
    """
    Search our internal candidate network.

    This is the highest priority source because:
    - Candidates have opted in
    - Data is verified
    - Fast to query (direct DB)
    """

    @property
    def name(self) -> str:
        return "Our Network"

    @property
    def priority(self) -> int:
        return 0  # Highest priority

    def __init__(self, db_session=None):
        self.db = db_session

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 50,
    ) -> list[CandidateData]:
        """
        Search our network using filters and full-text search.

        Search strategy:
        1. Filter by location if preferences exist
        2. Full-text search on skills and experience
        3. Rank by relevance
        """
        # TODO: Implement actual database query
        # For now, return mock data for testing

        logger.info(f"Searching network for: {blueprint.role_title}")

        # Mock candidates for MVP testing
        mock_candidates = [
            CandidateData(
                id="net_001",
                name="Maya Patel",
                email="maya@example.com",
                school="UC San Diego",
                major="Computer Science",
                graduation_year=2026,
                location="San Diego, CA",
                clubs=["Triton AI", "ACM"],
                github_username="mayapatel",
                sources=["network"],
            ),
            CandidateData(
                id="net_002",
                name="Alex Chen",
                email="alex@example.com",
                school="Stanford",
                major="Computer Science",
                graduation_year=2025,
                location="Palo Alto, CA",
                clubs=["Stanford AI Club"],
                github_username="alexchen",
                sources=["network"],
            ),
            CandidateData(
                id="net_003",
                name="Jordan Lee",
                email="jordan@example.com",
                school="UC Berkeley",
                major="EECS",
                graduation_year=2026,
                location="Berkeley, CA",
                clubs=["ML@Berkeley"],
                github_username="jordanlee",
                sources=["network"],
            ),
        ]

        # Filter by location preferences if specified
        if blueprint.location_preferences:
            filtered = []
            for candidate in mock_candidates:
                for pref in blueprint.location_preferences:
                    pref_lower = pref.lower()
                    if (
                        (candidate.school and pref_lower in candidate.school.lower())
                        or (candidate.location and pref_lower in candidate.location.lower())
                    ):
                        filtered.append(candidate)
                        break
            if filtered:
                mock_candidates = filtered

        return mock_candidates[:limit]

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """
        Network candidates are already enriched in our DB.
        This is mostly a pass-through.
        """
        # Mark as enriched
        candidate.enriched_at = datetime.utcnow()
        return candidate

    async def is_available(self) -> bool:
        """Network source is always available."""
        return True
