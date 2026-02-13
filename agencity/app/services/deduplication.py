"""
Deduplication Engine - Merges candidates from Hermes + Network sources
"""

from typing import List, Dict, Optional
from app.models.unified_candidate import UnifiedCandidate
import re


class DeduplicationEngine:
    """
    Merges candidates found in both Hermes (candidates) and Network (people).

    Deduplication keys (in priority order):
    1. LinkedIn URL (most reliable)
    2. Email
    3. GitHub URL
    4. Name + University (fuzzy)
    """

    def deduplicate(
        self,
        hermes_candidates: List[UnifiedCandidate],
        network_candidates: List[UnifiedCandidate],
    ) -> List[UnifiedCandidate]:
        """
        Merge candidates from both sources.

        Returns:
            List of unique candidates with merged data
        """

        # Index by deduplication keys
        unified_map: Dict[str, UnifiedCandidate] = {}

        # Process Hermes candidates first (higher quality)
        for candidate in hermes_candidates:
            key = self._get_dedup_key(candidate)
            if key:
                unified_map[key] = candidate

        # Merge network candidates
        merged_count = 0
        for candidate in network_candidates:
            key = self._get_dedup_key(candidate)

            if key and key in unified_map:
                # Merge: candidate exists in both sources
                unified_map[key] = self._merge_candidates(
                    existing=unified_map[key],
                    new=candidate
                )
                merged_count += 1
            elif key:
                # New: only in network
                unified_map[key] = candidate

        print(f"Deduplication: {len(hermes_candidates)} Hermes + {len(network_candidates)} Network = {len(unified_map)} unique ({merged_count} merged)")

        return list(unified_map.values())

    def _get_dedup_key(self, candidate: UnifiedCandidate) -> Optional[str]:
        """
        Generate deduplication key for a candidate.

        Priority:
        1. LinkedIn URL (normalized)
        2. Email (lowercase)
        3. GitHub URL (normalized)
        4. Name + University (fuzzy)
        """

        # Priority 1: LinkedIn URL
        if candidate.linkedin_url:
            normalized = self._normalize_linkedin_url(candidate.linkedin_url)
            if normalized:
                return f"linkedin:{normalized}"

        # Priority 2: Email
        if candidate.email:
            return f"email:{candidate.email.lower().strip()}"

        # Priority 3: GitHub URL
        if candidate.github_url:
            normalized = self._normalize_github_url(candidate.github_url)
            if normalized:
                return f"github:{normalized}"

        # Priority 4: Name + University (less reliable)
        if candidate.full_name and candidate.university:
            name_normalized = self._normalize_name(candidate.full_name)
            uni_normalized = candidate.university.lower().strip()
            return f"name_uni:{name_normalized}:{uni_normalized}"

        # Fallback: Use person_id (no deduplication)
        return f"id:{candidate.person_id}"

    def _merge_candidates(
        self,
        existing: UnifiedCandidate,
        new: UnifiedCandidate
    ) -> UnifiedCandidate:
        """
        Merge two candidate records.

        Strategy:
        - Prefer Hermes data for: skills, education, GitHub
        - Prefer Network data for: current company, title, warmth
        - Union: sources, skills
        - Max: scores
        """

        # Track sources
        if "network" not in existing.sources:
            existing.sources.append("network")

        # Update source quality (multi-source bonus)
        existing.source_quality = min(1.0, existing.source_quality + 0.1)

        # Merge network-specific data
        if new.current_company and not existing.current_company:
            existing.current_company = new.current_company

        if new.current_title and not existing.current_title:
            existing.current_title = new.current_title

        if new.headline and not existing.headline:
            existing.headline = new.headline

        # Network intelligence
        existing.is_from_network = new.is_from_network or existing.is_from_network
        existing.trust_score = new.trust_score or existing.trust_score
        existing.warmth_score = max(existing.warmth_score, new.warmth_score)

        if new.warm_path_description:
            existing.warm_path_description = new.warm_path_description

        # Merge skills (union)
        existing.skills = list(set(existing.skills + new.skills))

        # Update data completeness
        existing.data_completeness = self._calculate_completeness(existing)

        return existing

    def _normalize_linkedin_url(self, url: str) -> Optional[str]:
        """Normalize LinkedIn URL to username."""
        if not url:
            return None

        # Extract username from LinkedIn URL
        # https://www.linkedin.com/in/username/ -> username
        match = re.search(r'linkedin\.com/in/([^/?]+)', url.lower())
        if match:
            return match.group(1)

        return None

    def _normalize_github_url(self, url: str) -> Optional[str]:
        """Normalize GitHub URL to username."""
        if not url:
            return None

        # Extract username from GitHub URL
        # https://github.com/username -> username
        match = re.search(r'github\.com/([^/?]+)', url.lower())
        if match:
            return match.group(1)

        return None

    def _normalize_name(self, name: str) -> str:
        """Normalize name for fuzzy matching."""
        # Remove special characters, lowercase, strip
        normalized = re.sub(r'[^a-z\s]', '', name.lower())
        return normalized.strip()

    def _calculate_completeness(self, candidate: UnifiedCandidate) -> float:
        """
        Calculate data completeness score (0-1).

        Checks:
        - Email (0.15)
        - LinkedIn (0.15)
        - Current company/title (0.20)
        - Skills (0.20)
        - Education (0.15)
        - GitHub (0.15)
        """

        score = 0.0

        if candidate.email:
            score += 0.15

        if candidate.linkedin_url:
            score += 0.15

        if candidate.current_company and candidate.current_title:
            score += 0.20

        if candidate.skills and len(candidate.skills) > 0:
            score += 0.20

        if candidate.university:
            score += 0.15

        if candidate.github_url or candidate.github_username:
            score += 0.15

        return min(1.0, score)
