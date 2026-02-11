"""
Base class for search sources.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.search.models import CandidateSource, DiscoveredCandidate, SearchPathway


class SearchSource(ABC):
    """Base class for all search sources (PDL, Google, GitHub, etc.)"""

    name: str = "base"
    cost_per_query: float = 0.0
    rate_limit_per_minute: int = 60

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._query_count = 0

    @property
    def is_configured(self) -> bool:
        """Check if this source is properly configured."""
        return self.api_key is not None

    @abstractmethod
    async def search(
        self,
        pathway: SearchPathway,
        max_results: int = 50
    ) -> list[DiscoveredCandidate]:
        """
        Execute search queries for this pathway.
        Returns discovered candidates.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the source is available and working."""
        pass

    def _create_candidate(
        self,
        raw_data: dict,
        pathway: SearchPathway,
        query: str,
        confidence: float = 0.5
    ) -> DiscoveredCandidate:
        """Helper to create a candidate from raw API data."""
        return DiscoveredCandidate(
            full_name=raw_data.get("full_name", raw_data.get("name", "Unknown")),
            email=raw_data.get("email"),
            linkedin_url=raw_data.get("linkedin_url"),
            github_url=raw_data.get("github_url"),
            current_company=raw_data.get("current_company", raw_data.get("company")),
            current_title=raw_data.get("current_title", raw_data.get("title")),
            location=raw_data.get("location"),
            sources=[
                CandidateSource(
                    api=self.name,
                    query=query,
                    pathway_person_id=pathway.gateway_node.person_id,
                    access_pattern=pathway.access_pattern,
                    confidence=confidence,
                )
            ],
            raw_data=raw_data,
        )
