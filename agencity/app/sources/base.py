"""
Base data source interface.

All data sources (GitHub, Devpost, Network, etc.) implement this interface.
"""

from abc import ABC, abstractmethod

from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData


class DataSource(ABC):
    """
    Abstract base class for candidate data sources.

    Each source:
    - Searches for candidates matching a blueprint
    - Enriches candidate data with additional info
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this source."""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Search priority (lower = higher priority).
        P0 = Our network
        P1 = GitHub
        P2 = Devpost
        etc.
        """
        pass

    @abstractmethod
    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 50,
    ) -> list[CandidateData]:
        """
        Search for candidates matching the blueprint.

        Args:
            blueprint: The role requirements
            limit: Maximum candidates to return

        Returns:
            List of candidate data (may be partial)
        """
        pass

    @abstractmethod
    async def enrich(
        self,
        candidate: CandidateData,
    ) -> CandidateData:
        """
        Enrich a candidate with additional data from this source.

        Args:
            candidate: Candidate to enrich

        Returns:
            Enriched candidate data
        """
        pass

    async def is_available(self) -> bool:
        """Check if this source is available (API keys configured, etc.)."""
        return True
