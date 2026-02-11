"""
Candidate Ranker - Scores and ranks discovered candidates.

Combines multiple signals:
- Source quality (PDL > Google > Perplexity)
- Pathway strength (how good was the network connection)
- Multi-source bonus (found via multiple APIs = higher signal)
- Network proximity (in network > 2nd degree > cold)
- Role match (skills/title alignment)
"""

import logging
from typing import Optional
from uuid import UUID

from app.search.models import (
    DiscoveredCandidate,
    SearchTarget,
)
from app.services.company_db import company_db

logger = logging.getLogger(__name__)


class CandidateRanker:
    """Ranks discovered candidates by quality and relevance."""

    # Source quality scores
    SOURCE_QUALITY = {
        "pdl": 0.9,           # Structured, verified data
        "github": 0.8,        # Real profiles
        "google": 0.5,        # Needs verification
        "perplexity": 0.4,    # AI-generated, needs verification
    }

    def __init__(self, company_id: UUID):
        self.company_id = company_id
        self._network_cache: Optional[dict] = None

    async def rank_candidates(
        self,
        candidates: list[DiscoveredCandidate],
        target: SearchTarget
    ) -> list[DiscoveredCandidate]:
        """
        Score and rank all candidates.
        Returns sorted list with scores populated.
        """
        logger.info(f"Ranking {len(candidates)} candidates")

        # Load network for proximity checking
        await self._load_network_cache()

        # Score each candidate
        for candidate in candidates:
            self._score_candidate(candidate, target)

        # Sort by final score
        candidates.sort(key=lambda c: c.final_score, reverse=True)

        logger.info(f"Ranking complete. Top score: {candidates[0].final_score if candidates else 0:.2f}")
        return candidates

    async def _load_network_cache(self):
        """Load network data for proximity checking."""
        if self._network_cache is not None:
            return

        # Get all people in network
        people = await company_db.get_people(
            self.company_id,
            limit=10000,
            filters={"is_from_network": True}
        )

        self._network_cache = {
            "by_email": {},
            "by_linkedin": {},
            "by_name": {},
            "companies": set(),
            "schools": set(),
        }

        for person in people:
            if person.email:
                self._network_cache["by_email"][person.email.lower()] = person.id
            if person.linkedin_url:
                self._network_cache["by_linkedin"][person.linkedin_url.lower()] = person.id
            if person.full_name:
                self._network_cache["by_name"][person.full_name.lower()] = person.id
            if person.current_company:
                self._network_cache["companies"].add(person.current_company.lower())

    def _score_candidate(
        self,
        candidate: DiscoveredCandidate,
        target: SearchTarget
    ):
        """Calculate all score components for a candidate."""

        # 1. Source quality score
        candidate.source_quality_score = self._calculate_source_quality(candidate)

        # 2. Multi-source bonus
        candidate.multi_source_bonus = self._calculate_multi_source_bonus(candidate)

        # 3. Network proximity score
        candidate.network_proximity_score = self._calculate_network_proximity(candidate)

        # 4. Pathway strength score (average across sources)
        candidate.pathway_strength_score = self._calculate_pathway_strength(candidate)

        # 5. Role match score
        candidate.role_match_score = self._calculate_role_match(candidate, target)

        # Final score: weighted combination
        candidate.final_score = (
            candidate.source_quality_score * 0.15 +
            candidate.multi_source_bonus * 0.15 +
            candidate.network_proximity_score * 0.30 +
            candidate.pathway_strength_score * 0.15 +
            candidate.role_match_score * 0.25
        )

    def _calculate_source_quality(self, candidate: DiscoveredCandidate) -> float:
        """Calculate quality based on which sources found this candidate."""
        if not candidate.sources:
            return 0.3

        # Use the highest quality source
        best_quality = 0.0
        for source in candidate.sources:
            quality = self.SOURCE_QUALITY.get(source.api, 0.3)
            # Factor in confidence from the API
            quality *= source.confidence
            best_quality = max(best_quality, quality)

        return best_quality

    def _calculate_multi_source_bonus(self, candidate: DiscoveredCandidate) -> float:
        """Bonus for being found via multiple independent sources."""
        unique_apis = set(s.api for s in candidate.sources)
        unique_pathways = set(
            s.pathway_person_id for s in candidate.sources
            if s.pathway_person_id
        )

        # Bonus based on number of sources
        api_bonus = min(0.5, len(unique_apis) * 0.15)
        pathway_bonus = min(0.5, len(unique_pathways) * 0.1)

        return api_bonus + pathway_bonus

    def _calculate_network_proximity(self, candidate: DiscoveredCandidate) -> float:
        """Calculate how close this candidate is to your network."""
        if not self._network_cache:
            return 0.3

        # Check if directly in network
        in_network = False
        network_id = None

        if candidate.email:
            network_id = self._network_cache["by_email"].get(candidate.email.lower())
        if not network_id and candidate.linkedin_url:
            network_id = self._network_cache["by_linkedin"].get(candidate.linkedin_url.lower())
        if not network_id and candidate.full_name:
            network_id = self._network_cache["by_name"].get(candidate.full_name.lower())

        if network_id:
            candidate.in_network = True
            candidate.network_person_id = network_id
            candidate.pathway_hops = 1
            return 1.0  # Maximum score for direct connections

        # Check for 2nd degree signals
        second_degree_signals = 0

        # Same company as someone in network
        if candidate.current_company:
            if candidate.current_company.lower() in self._network_cache["companies"]:
                second_degree_signals += 1

        # Has a pathway through network (was found via network node)
        if candidate.sources:
            pathways_with_node = [s for s in candidate.sources if s.pathway_person_id]
            if pathways_with_node:
                second_degree_signals += 1
                candidate.pathway_hops = 2

        if second_degree_signals > 0:
            return 0.6 + (second_degree_signals * 0.1)

        # Cold candidate
        candidate.pathway_hops = 99
        return 0.3

    def _calculate_pathway_strength(self, candidate: DiscoveredCandidate) -> float:
        """Calculate average pathway strength across all sources."""
        if not candidate.sources:
            return 0.3

        strengths = []
        for source in candidate.sources:
            # Source confidence is a proxy for pathway strength
            strengths.append(source.confidence)

        return sum(strengths) / len(strengths) if strengths else 0.3

    def _calculate_role_match(
        self,
        candidate: DiscoveredCandidate,
        target: SearchTarget
    ) -> float:
        """Calculate how well candidate matches the target role."""
        score = 0.0

        # Title match
        if candidate.current_title and target.role_title:
            title_lower = candidate.current_title.lower()
            target_lower = target.role_title.lower()

            # Extract key terms
            target_terms = set(target_lower.replace("-", " ").split())
            title_terms = set(title_lower.replace("-", " ").split())

            # Common role keywords
            role_keywords = {
                "engineer", "developer", "scientist", "manager",
                "lead", "senior", "staff", "principal", "director"
            }

            matching_terms = target_terms & title_terms
            matching_role_keywords = matching_terms & role_keywords

            if matching_role_keywords:
                score += 0.3
            if len(matching_terms) >= 2:
                score += 0.2

        # Skill match (from raw data if available)
        raw_skills = candidate.raw_data.get("skills", [])
        if raw_skills and target.required_skills:
            raw_skills_lower = [s.lower() for s in raw_skills]
            required_lower = [s.lower() for s in target.required_skills]

            matches = sum(1 for s in required_lower if s in raw_skills_lower)
            score += min(0.3, matches * 0.1)

        # Company match (preferred backgrounds)
        if candidate.current_company and target.preferred_backgrounds:
            company_lower = candidate.current_company.lower()
            for bg in target.preferred_backgrounds:
                if bg.lower() in company_lower:
                    score += 0.2
                    break

        return min(1.0, score)

    def deduplicate_candidates(
        self,
        candidates: list[DiscoveredCandidate]
    ) -> list[DiscoveredCandidate]:
        """
        Deduplicate candidates found via multiple sources.
        Merges their source information.
        """
        seen = {}  # Key -> candidate

        for candidate in candidates:
            # Create dedup key
            key = self._get_dedup_key(candidate)

            if key in seen:
                # Merge sources
                existing = seen[key]
                existing.sources.extend(candidate.sources)

                # Merge raw data
                for k, v in candidate.raw_data.items():
                    if k not in existing.raw_data or not existing.raw_data[k]:
                        existing.raw_data[k] = v

                # Update best values
                if candidate.linkedin_url and not existing.linkedin_url:
                    existing.linkedin_url = candidate.linkedin_url
                if candidate.github_url and not existing.github_url:
                    existing.github_url = candidate.github_url
                if candidate.email and not existing.email:
                    existing.email = candidate.email
            else:
                seen[key] = candidate

        return list(seen.values())

    def _get_dedup_key(self, candidate: DiscoveredCandidate) -> str:
        """Generate a deduplication key for a candidate."""
        # Prefer LinkedIn URL as primary key
        if candidate.linkedin_url:
            return f"linkedin:{candidate.linkedin_url.lower()}"

        # Then email
        if candidate.email:
            return f"email:{candidate.email.lower()}"

        # Then GitHub
        if candidate.github_url:
            return f"github:{candidate.github_url.lower()}"

        # Fall back to name (less reliable)
        return f"name:{candidate.full_name.lower()}"
