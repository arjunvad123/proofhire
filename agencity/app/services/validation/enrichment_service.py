"""
Enrichment Service

Validates and enriches candidates extracted from LinkedIn using external data sources.
Uses a tiered waterfall approach to balance cost and data quality:

WATERFALL STRATEGY:
1. LinkedIn Extraction (source of truth): linkedin_url, full_name, current_company, current_title
2. Clado Get Profile ($0.01): Cached profile - fast and cheap
3. Clado Scrape ($0.02): Real-time scrape if cache miss
4. PDL Enrichment ($0.10): Final fallback when Clado fails

COST BREAKDOWN:
- Best case (Clado cache hit): $0.01
- Typical case (Clado scrape): $0.02
- Worst case (Clado fails, PDL fallback): $0.12

The service validates that enriched data matches the LinkedIn-extracted identity
before returning results.
"""

import logging
from typing import Optional
from enum import Enum
from pydantic import BaseModel
from difflib import SequenceMatcher

from app.services.external_search.clado_client import clado_client, CladoProfile
from app.services.external_search.pdl_client import pdl_client, PDLProfile

logger = logging.getLogger(__name__)


class EnrichmentSource(str, Enum):
    """Source of enrichment data."""
    LINKEDIN = "linkedin"       # Original extraction
    CLADO_PROFILE = "clado_profile"  # $0.01 - cached profile
    CLADO_SCRAPE = "clado_scrape"    # $0.02 - real-time scrape
    CLADO = "clado"             # Generic clado (backwards compat)
    PDL = "pdl"                 # $0.10 per enrichment
    NONE = "none"               # No enrichment available


class ValidationStatus(str, Enum):
    """Status of identity validation."""
    VERIFIED = "verified"      # Enriched data matches LinkedIn extraction
    PARTIAL = "partial"        # Some fields match, some don't
    MISMATCH = "mismatch"      # Enriched data doesn't match (possible wrong person)
    UNVERIFIED = "unverified"  # No enrichment to compare against


class LinkedInCandidate(BaseModel):
    """Candidate data extracted from LinkedIn connections."""
    linkedin_url: str
    full_name: str
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    headline: Optional[str] = None


class EnrichedCandidate(BaseModel):
    """Fully enriched and validated candidate."""

    # Identity (from LinkedIn extraction)
    linkedin_url: str
    full_name: str

    # Current position (validated)
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    headline: Optional[str] = None

    # Enriched data
    experience: list[dict] = []
    education: list[dict] = []
    skills: list[str] = []

    # Additional links
    github_url: Optional[str] = None
    twitter_url: Optional[str] = None
    personal_website: Optional[str] = None

    # Location
    location: Optional[str] = None

    # Validation metadata
    enrichment_source: EnrichmentSource = EnrichmentSource.NONE
    validation_status: ValidationStatus = ValidationStatus.UNVERIFIED
    validation_details: dict = {}
    confidence: float = 0.0  # 0-1 based on data completeness + validation

    # Cost tracking
    enrichment_cost_usd: float = 0.0


class EnrichmentResult(BaseModel):
    """Result of enrichment attempt."""
    success: bool
    candidate: Optional[EnrichedCandidate] = None
    error: Optional[str] = None
    source_used: EnrichmentSource = EnrichmentSource.NONE
    cost_usd: float = 0.0


class EnrichmentService:
    """
    Service for enriching and validating LinkedIn-extracted candidates.

    WATERFALL STRATEGY:
    1. Clado Get Profile ($0.01) - cached data, fast
    2. Clado Scrape ($0.02) - real-time if cache miss
    3. PDL Enrichment ($0.10) - fallback if Clado fails

    Cost structure:
    - Clado cache hit: $0.01
    - Clado scrape: $0.02
    - Clado miss + PDL fallback: $0.10 (or $0.12 if Clado charged before fail)
    """

    CLADO_PROFILE_COST_USD = 0.01  # /api/profile endpoint
    CLADO_SCRAPE_COST_USD = 0.02   # /api/scrape endpoint
    CLADO_COST_USD = 0.01          # Backwards compat (deprecated)
    PDL_COST_USD = 0.10

    # Thresholds for string similarity matching
    NAME_MATCH_THRESHOLD = 0.85
    COMPANY_MATCH_THRESHOLD = 0.70
    TITLE_MATCH_THRESHOLD = 0.60

    def __init__(self):
        self.clado = clado_client
        self.pdl = pdl_client

    async def enrich(
        self,
        candidate: LinkedInCandidate,
        prefer_pdl: bool = False,
        skip_clado: bool = False,
    ) -> EnrichmentResult:
        """
        Enrich a LinkedIn-extracted candidate with external data.

        Args:
            candidate: LinkedIn-extracted candidate data
            prefer_pdl: If True, use PDL first (higher cost, higher quality)
            skip_clado: If True, skip Clado entirely (use when Clado is unreliable)

        Returns:
            EnrichmentResult with enriched candidate or error
        """
        total_cost = 0.0

        # Strategy: Try cheaper source first unless prefer_pdl is set
        if prefer_pdl:
            # PDL first, Clado as fallback
            result = await self._enrich_with_pdl(candidate)
            total_cost += self.PDL_COST_USD

            if not result.success and not skip_clado:
                clado_result = await self._enrich_with_clado(candidate)
                total_cost += self.CLADO_COST_USD
                if clado_result.success:
                    result = clado_result
        else:
            # Clado first, PDL as fallback
            if not skip_clado:
                result = await self._enrich_with_clado(candidate)
                total_cost += self.CLADO_COST_USD

                if result.success:
                    result.cost_usd = total_cost
                    return result
            else:
                result = EnrichmentResult(success=False, error="Clado skipped")

            # Fall back to PDL if Clado failed
            if not result.success:
                pdl_result = await self._enrich_with_pdl(candidate)
                total_cost += self.PDL_COST_USD
                result = pdl_result

        result.cost_usd = total_cost
        return result

    async def enrich_with_pdl_enhanced(
        self,
        candidate: LinkedInCandidate,
    ) -> EnrichmentResult:
        """
        Enrich using PDL with multiple identifiers for better matching.

        Uses linkedin_url + company + name for higher match confidence.
        This is the recommended approach when you need high-quality data.

        Cost: $0.10 per enrichment
        """
        if not self.pdl.enabled:
            return EnrichmentResult(
                success=False,
                error="PDL API not configured",
                source_used=EnrichmentSource.NONE,
            )

        try:
            # Build params for enhanced matching
            # PDL supports combining multiple identifiers
            params = {
                "profile": self._clean_linkedin_url(candidate.linkedin_url),
            }

            # Add name if available (improves match confidence)
            if candidate.full_name:
                params["name"] = candidate.full_name

            # Add company if available (improves match confidence)
            if candidate.current_company:
                params["company"] = candidate.current_company

            # Make the enrichment request with enhanced params
            import httpx
            async with httpx.AsyncClient(timeout=self.pdl.timeout_seconds) as client:
                response = await client.get(
                    f"{self.pdl.base_url}/person/enrich",
                    headers={
                        "X-Api-Key": self.pdl.api_key,
                        "Content-Type": "application/json"
                    },
                    params=params,
                )

                if response.status_code == 200:
                    data = response.json()
                    pdl_profile = self.pdl._parse_profile(data.get("data", {}))

                    # Validate and convert to EnrichedCandidate
                    enriched = self._convert_pdl_to_enriched(pdl_profile, candidate)
                    enriched.enrichment_cost_usd = self.PDL_COST_USD

                    # Validate identity
                    enriched = self._validate_identity(enriched, candidate)

                    return EnrichmentResult(
                        success=True,
                        candidate=enriched,
                        source_used=EnrichmentSource.PDL,
                        cost_usd=self.PDL_COST_USD,
                    )

                elif response.status_code == 404:
                    logger.info("PDL: No match found for %s", candidate.linkedin_url)
                    return EnrichmentResult(
                        success=False,
                        error="No matching profile found in PDL",
                        source_used=EnrichmentSource.PDL,
                        cost_usd=0.0,  # PDL doesn't charge for 404s
                    )
                else:
                    logger.error("PDL enhanced enrich error: %s", response.text[:500])
                    return EnrichmentResult(
                        success=False,
                        error=f"PDL API error: {response.status_code}",
                        source_used=EnrichmentSource.PDL,
                        cost_usd=0.0,
                    )

        except Exception as e:
            logger.exception("PDL enhanced enrichment failed")
            return EnrichmentResult(
                success=False,
                error=str(e),
                source_used=EnrichmentSource.PDL,
            )

    async def _enrich_with_clado(
        self,
        candidate: LinkedInCandidate,
    ) -> EnrichmentResult:
        """
        Enrich using Clado API with waterfall strategy.

        1. Try get_profile() first ($0.01) - cached data
        2. If not found, try scrape_profile() ($0.02) - real-time

        Total cost: $0.01-$0.03 depending on cache hit
        """
        if not self.clado.enabled:
            return EnrichmentResult(
                success=False,
                error="Clado API not configured",
                source_used=EnrichmentSource.NONE,
            )

        total_cost = 0.0

        try:
            # Step 1: Try cached profile first ($0.01)
            logger.info("Clado: Trying cached profile for %s", candidate.linkedin_url)
            profile = await self.clado.get_profile(candidate.linkedin_url)
            total_cost += self.CLADO_PROFILE_COST_USD
            source = EnrichmentSource.CLADO_PROFILE

            # Step 2: If not in cache, scrape real-time ($0.02)
            if profile is None:
                logger.info("Clado: Cache miss, scraping %s", candidate.linkedin_url)
                profile = await self.clado.scrape_profile(candidate.linkedin_url)
                total_cost += self.CLADO_SCRAPE_COST_USD
                source = EnrichmentSource.CLADO_SCRAPE

            if profile is None:
                return EnrichmentResult(
                    success=False,
                    error="Clado enrichment returned no data (cache miss + scrape failed)",
                    source_used=EnrichmentSource.CLADO,
                    cost_usd=total_cost,
                )

            enriched = self._convert_clado_to_enriched(profile, candidate)
            enriched.enrichment_cost_usd = total_cost

            # Validate identity
            enriched = self._validate_identity(enriched, candidate)
            enriched.enrichment_source = source

            return EnrichmentResult(
                success=True,
                candidate=enriched,
                source_used=source,
                cost_usd=total_cost,
            )

        except Exception as e:
            logger.exception("Clado enrichment failed")
            return EnrichmentResult(
                success=False,
                error=str(e),
                source_used=EnrichmentSource.CLADO,
                cost_usd=total_cost,
            )

    async def _enrich_with_pdl(
        self,
        candidate: LinkedInCandidate,
    ) -> EnrichmentResult:
        """Enrich using PDL API (basic linkedin_url only)."""
        if not self.pdl.enabled:
            return EnrichmentResult(
                success=False,
                error="PDL API not configured",
                source_used=EnrichmentSource.NONE,
            )

        try:
            profile = await self.pdl.enrich_profile(candidate.linkedin_url)

            if profile is None:
                return EnrichmentResult(
                    success=False,
                    error="PDL enrichment returned no data",
                    source_used=EnrichmentSource.PDL,
                    cost_usd=0.0,  # PDL doesn't charge for 404s
                )

            enriched = self._convert_pdl_to_enriched(profile, candidate)
            enriched.enrichment_cost_usd = self.PDL_COST_USD

            # Validate identity
            enriched = self._validate_identity(enriched, candidate)

            return EnrichmentResult(
                success=True,
                candidate=enriched,
                source_used=EnrichmentSource.PDL,
                cost_usd=self.PDL_COST_USD,
            )

        except Exception as e:
            logger.exception("PDL enrichment failed")
            return EnrichmentResult(
                success=False,
                error=str(e),
                source_used=EnrichmentSource.PDL,
            )

    def _convert_clado_to_enriched(
        self,
        profile: CladoProfile,
        original: LinkedInCandidate,
    ) -> EnrichedCandidate:
        """Convert Clado profile to EnrichedCandidate."""
        return EnrichedCandidate(
            # Use original LinkedIn data as source of truth for identity
            linkedin_url=original.linkedin_url,
            full_name=profile.full_name or original.full_name,

            # Use enriched data for current position
            current_company=profile.current_company or original.current_company,
            current_title=profile.current_title or original.current_title,
            headline=profile.headline or original.headline,

            # Enriched data
            experience=profile.experience,
            education=profile.education,
            skills=profile.skills,

            # Links
            github_url=profile.github_url,
            twitter_url=profile.twitter_url,
            personal_website=profile.personal_website,

            # Location
            location=profile.location,

            # Metadata
            enrichment_source=EnrichmentSource.CLADO,
        )

    def _convert_pdl_to_enriched(
        self,
        profile: PDLProfile,
        original: LinkedInCandidate,
    ) -> EnrichedCandidate:
        """Convert PDL profile to EnrichedCandidate."""
        return EnrichedCandidate(
            # Use original LinkedIn data as source of truth for identity
            linkedin_url=original.linkedin_url,
            full_name=profile.full_name or original.full_name,

            # Use enriched data for current position
            current_company=profile.current_company or original.current_company,
            current_title=profile.current_title or original.current_title,
            headline=profile.headline or original.headline,

            # Enriched data
            experience=profile.experience,
            education=profile.education,
            skills=profile.skills,

            # Links
            github_url=profile.github_url,
            twitter_url=profile.twitter_url,
            personal_website=profile.personal_website,

            # Location
            location=profile.location,

            # Metadata
            enrichment_source=EnrichmentSource.PDL,
        )

    def _validate_identity(
        self,
        enriched: EnrichedCandidate,
        original: LinkedInCandidate,
    ) -> EnrichedCandidate:
        """
        Validate that enriched data matches the LinkedIn extraction.

        Compares name, company, and title to ensure we got the right person.
        """
        validation_details = {}
        match_count = 0
        total_checks = 0

        # Check name match
        if original.full_name and enriched.full_name:
            name_similarity = self._string_similarity(
                original.full_name, enriched.full_name
            )
            validation_details["name_similarity"] = round(name_similarity, 2)
            validation_details["name_match"] = name_similarity >= self.NAME_MATCH_THRESHOLD
            total_checks += 1
            if validation_details["name_match"]:
                match_count += 1

        # Check company match
        if original.current_company and enriched.current_company:
            company_similarity = self._string_similarity(
                original.current_company, enriched.current_company
            )
            validation_details["company_similarity"] = round(company_similarity, 2)
            validation_details["company_match"] = company_similarity >= self.COMPANY_MATCH_THRESHOLD
            total_checks += 1
            if validation_details["company_match"]:
                match_count += 1

        # Check title match
        if original.current_title and enriched.current_title:
            title_similarity = self._string_similarity(
                original.current_title, enriched.current_title
            )
            validation_details["title_similarity"] = round(title_similarity, 2)
            validation_details["title_match"] = title_similarity >= self.TITLE_MATCH_THRESHOLD
            total_checks += 1
            if validation_details["title_match"]:
                match_count += 1

        # Determine validation status
        if total_checks == 0:
            status = ValidationStatus.UNVERIFIED
        elif match_count == total_checks:
            status = ValidationStatus.VERIFIED
        elif match_count > 0:
            status = ValidationStatus.PARTIAL
        else:
            status = ValidationStatus.MISMATCH

        # Calculate confidence score
        confidence = self._calculate_confidence(enriched, status, match_count, total_checks)

        enriched.validation_status = status
        enriched.validation_details = validation_details
        enriched.confidence = confidence

        return enriched

    def _calculate_confidence(
        self,
        enriched: EnrichedCandidate,
        status: ValidationStatus,
        match_count: int,
        total_checks: int,
    ) -> float:
        """
        Calculate confidence score based on data completeness and validation.

        Returns 0.0-1.0
        """
        confidence = 0.0

        # Base confidence from LinkedIn URL (required)
        if enriched.linkedin_url:
            confidence += 0.20

        # Validation status bonus
        if status == ValidationStatus.VERIFIED:
            confidence += 0.25
        elif status == ValidationStatus.PARTIAL:
            confidence += 0.10
        elif status == ValidationStatus.MISMATCH:
            confidence -= 0.20  # Penalty for mismatch

        # Data completeness bonuses
        if len(enriched.experience) >= 2:
            confidence += 0.15
        elif len(enriched.experience) >= 1:
            confidence += 0.08

        if len(enriched.education) >= 1:
            confidence += 0.10

        if len(enriched.skills) >= 5:
            confidence += 0.10
        elif len(enriched.skills) >= 1:
            confidence += 0.05

        if enriched.github_url:
            confidence += 0.10

        # Enrichment source bonus
        if enriched.enrichment_source == EnrichmentSource.PDL:
            confidence += 0.10  # PDL is more reliable
        elif enriched.enrichment_source == EnrichmentSource.CLADO:
            confidence += 0.05

        return min(max(confidence, 0.0), 1.0)

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio between two strings."""
        if not s1 or not s2:
            return 0.0
        return SequenceMatcher(None, s1.lower().strip(), s2.lower().strip()).ratio()

    def _clean_linkedin_url(self, url: str) -> str:
        """Clean LinkedIn URL for API usage."""
        url = url.replace("https://", "").replace("http://", "").replace("www.", "")
        # Remove trailing slashes
        url = url.rstrip("/")
        return url

    async def enrich_batch(
        self,
        candidates: list[LinkedInCandidate],
        max_concurrent: int = 5,
        prefer_pdl: bool = False,
    ) -> list[EnrichmentResult]:
        """
        Enrich multiple candidates with concurrency control.

        Args:
            candidates: List of LinkedIn-extracted candidates
            max_concurrent: Max concurrent enrichment requests
            prefer_pdl: If True, use PDL first for all candidates

        Returns:
            List of EnrichmentResults in same order as input
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_with_limit(candidate: LinkedInCandidate) -> EnrichmentResult:
            async with semaphore:
                return await self.enrich(candidate, prefer_pdl=prefer_pdl)

        tasks = [enrich_with_limit(c) for c in candidates]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(EnrichmentResult(
                    success=False,
                    error=str(result),
                ))
            else:
                final_results.append(result)

        return final_results

    def get_provider_status(self) -> dict:
        """Get status of enrichment providers."""
        return {
            "clado": {
                "enabled": self.clado.enabled,
                "endpoints": {
                    "get_profile": {"cost_usd": self.CLADO_PROFILE_COST_USD, "description": "Cached profile data"},
                    "scrape_profile": {"cost_usd": self.CLADO_SCRAPE_COST_USD, "description": "Real-time scrape"},
                },
                "cost_range": f"${self.CLADO_PROFILE_COST_USD:.2f}-${self.CLADO_PROFILE_COST_USD + self.CLADO_SCRAPE_COST_USD:.2f}",
            },
            "pdl": {
                "enabled": self.pdl.enabled,
                "cost_per_enrichment": self.PDL_COST_USD,
            },
            "waterfall_strategy": {
                "order": ["clado_profile", "clado_scrape", "pdl"],
                "best_case_cost": self.CLADO_PROFILE_COST_USD,
                "worst_case_cost": self.CLADO_PROFILE_COST_USD + self.CLADO_SCRAPE_COST_USD + self.PDL_COST_USD,
            }
        }


# Singleton instance
enrichment_service = EnrichmentService()
