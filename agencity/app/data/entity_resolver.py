"""
Entity resolution for matching and merging people across data sources.

This module handles:
1. Matching people by email (highest confidence)
2. Matching people by LinkedIn URL
3. Fuzzy matching by name + company
4. Merging data from multiple sources
"""

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.models.company import Person, PersonCreate
from app.services.company_db import company_db

logger = logging.getLogger(__name__)


@dataclass
class ResolutionResult:
    """Result of entity resolution."""
    matched: bool
    person: Optional[Person]
    match_type: str  # "email", "linkedin_url", "fuzzy", "none"
    confidence: float  # 0-1


class EntityResolver:
    """
    Resolves people entities across data sources.

    Uses multiple matching strategies with different confidence levels:
    1. Email match: 99% confidence
    2. LinkedIn URL match: 95% confidence
    3. Fuzzy name + company: 70-85% confidence
    """

    def __init__(self, company_id: UUID):
        self.company_id = company_id

    async def resolve(
        self,
        email: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        full_name: Optional[str] = None,
        company: Optional[str] = None,
    ) -> ResolutionResult:
        """
        Try to match a person using available identifiers.

        Tries in order of confidence:
        1. Email (exact match)
        2. LinkedIn URL (exact match)
        3. Name + Company (fuzzy match) - TODO: implement

        Returns the first match found, or None if no match.
        """
        # 1. Email match (highest confidence)
        if email:
            normalized_email = email.lower().strip()
            person = await company_db.find_person_by_email(
                self.company_id, normalized_email
            )
            if person:
                logger.debug(f"Matched person by email: {email}")
                return ResolutionResult(
                    matched=True,
                    person=person,
                    match_type="email",
                    confidence=0.99,
                )

        # 2. LinkedIn URL match
        if linkedin_url:
            normalized_url = self._normalize_linkedin_url(linkedin_url)
            if normalized_url:
                person = await company_db.find_person_by_linkedin(
                    self.company_id, normalized_url
                )
                if person:
                    logger.debug(f"Matched person by LinkedIn: {linkedin_url}")
                    return ResolutionResult(
                        matched=True,
                        person=person,
                        match_type="linkedin_url",
                        confidence=0.95,
                    )

        # 3. Fuzzy name + company match - TODO: implement with better algorithm
        # For now, we skip fuzzy matching to avoid false positives

        # No match found
        return ResolutionResult(
            matched=False,
            person=None,
            match_type="none",
            confidence=0,
        )

    async def resolve_or_create(
        self,
        data: PersonCreate,
        is_from_network: bool = False,
        is_from_existing_db: bool = False,
    ) -> tuple[Person, bool]:
        """
        Resolve a person, or create if not found.

        Returns:
            tuple: (person, was_created)
        """
        # Try to resolve
        result = await self.resolve(
            email=data.email,
            linkedin_url=data.linkedin_url,
            full_name=data.full_name,
            company=data.current_company,
        )

        if result.matched and result.person:
            # Update existing person with new data
            updates = {}

            # Only update fields that are currently empty
            if not result.person.email and data.email:
                updates["email"] = data.email
            if not result.person.linkedin_url and data.linkedin_url:
                updates["linkedin_url"] = data.linkedin_url
            if not result.person.github_url and data.github_url:
                updates["github_url"] = data.github_url
            if not result.person.current_company and data.current_company:
                updates["current_company"] = data.current_company
            if not result.person.current_title and data.current_title:
                updates["current_title"] = data.current_title
            if not result.person.headline and data.headline:
                updates["headline"] = data.headline
            if not result.person.location and data.location:
                updates["location"] = data.location

            # Update source flags
            if is_from_network and not result.person.is_from_network:
                updates["is_from_network"] = True
            if is_from_existing_db and not result.person.is_from_existing_db:
                updates["is_from_existing_db"] = True

            if updates:
                await company_db.update_person(result.person.id, updates)
                # Refresh person data
                # For now, just update the local object
                for key, value in updates.items():
                    setattr(result.person, key, value)

            return result.person, False

        # Create new person
        person = await company_db.create_person(self.company_id, data)

        # Update source flags
        updates = {}
        if is_from_network:
            updates["is_from_network"] = True
        if is_from_existing_db:
            updates["is_from_existing_db"] = True

        if updates:
            await company_db.update_person(person.id, updates)
            for key, value in updates.items():
                setattr(person, key, value)

        return person, True

    def _normalize_linkedin_url(self, url: str) -> Optional[str]:
        """
        Normalize LinkedIn URL for consistent matching.

        Handles various formats:
        - https://www.linkedin.com/in/username
        - https://linkedin.com/in/username
        - www.linkedin.com/in/username
        - linkedin.com/in/username
        """
        if not url:
            return None

        url = url.strip().lower()

        # Remove protocol
        url = url.replace("https://", "").replace("http://", "")

        # Remove www.
        url = url.replace("www.", "")

        # Ensure it starts with linkedin.com
        if not url.startswith("linkedin.com"):
            return None

        # Remove trailing slash
        url = url.rstrip("/")

        # Add https:// for consistent storage
        return f"https://{url}"

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names.

        Uses simple token-based comparison.
        TODO: Implement Levenshtein or phonetic matching.
        """
        if not name1 or not name2:
            return 0

        tokens1 = set(name1.lower().split())
        tokens2 = set(name2.lower().split())

        if not tokens1 or not tokens2:
            return 0

        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        return len(intersection) / len(union)
