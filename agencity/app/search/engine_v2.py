"""
Search Engine V2 - Network-First Search

This is the improved search engine that actually leverages the network.

Key differences from V1:
1. Searches the network FIRST (Tier 1)
2. Finds 2nd-degree connections via employment overlap (Tier 2)
3. Identifies recruiters to contact (Tier 3)
4. External APIs only as last resort (Tier 4)

The output is tiered by "warmth" - how likely the candidate is to respond.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.search.network_search import NetworkSearch
from app.search.readiness import ReadinessScorer
from app.search.recruiters import RecruiterFinder
from app.search.warm_path import WarmPathCalculator

# Import V1 components for Tier 4 (external search)
from app.search.engine import SearchEngine as V1SearchEngine
from app.search.models import SearchTarget

logger = logging.getLogger(__name__)


class TieredCandidate(BaseModel):
    """A candidate with tier and warmth information."""
    id: Optional[str] = None
    full_name: str
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None

    # Tier info
    tier: int  # 1=network, 2=one-intro, 3=recruiter, 4=cold
    tier_label: str

    # Scores
    match_score: float = 0.0
    readiness_score: float = 0.0
    warmth_score: float = 0.0
    combined_score: float = 0.0

    # Signals
    match_reasons: list[str] = []
    readiness_signals: list[str] = []

    # Path info (for Tier 2)
    warm_path: Optional[dict] = None

    # Action to take
    action: str


class SearchResultsV2(BaseModel):
    """Tiered search results."""
    # Candidates by tier
    tier_1_network: list[TieredCandidate] = []
    tier_2_one_intro: list[TieredCandidate] = []
    tier_3_recruiters: list[dict] = []
    tier_4_cold: list[TieredCandidate] = []

    # Metadata
    search_target: dict
    search_duration_seconds: float
    network_size: int
    total_candidates: int

    # Counts
    tier_1_count: int = 0
    tier_2_count: int = 0
    tier_3_count: int = 0
    tier_4_count: int = 0

    # Recommendations
    primary_recommendation: str
    recruiter_recommendation: Optional[str] = None


class SearchEngineV2:
    """
    Network-first search engine.

    Search priority:
    1. Tier 1: People in the network who match the role
    2. Tier 2: People reachable via shared employment/school
    3. Tier 3: Recruiters to contact for referrals
    4. Tier 4: External search results (cold)
    """

    def __init__(self, company_id: UUID):
        self.company_id = company_id

        # Initialize components
        self.network_search = NetworkSearch(company_id)
        self.readiness_scorer = ReadinessScorer()
        self.recruiter_finder = RecruiterFinder(company_id)
        self.warm_path_calculator = WarmPathCalculator(company_id)

        # V1 engine for external search (Tier 4)
        self.v1_engine = V1SearchEngine(company_id)

    async def search(
        self,
        role_title: str,
        required_skills: list[str] = None,
        preferred_backgrounds: list[str] = None,
        locations: list[str] = None,
        max_results: int = 50,
        include_cold: bool = True
    ) -> SearchResultsV2:
        """
        Execute a network-first search.

        Args:
            role_title: Role to search for
            required_skills: Required skills
            preferred_backgrounds: Preferred company/school backgrounds
            locations: Preferred locations
            max_results: Max total results
            include_cold: Whether to include Tier 4 (external) results

        Returns:
            SearchResultsV2 with tiered candidates
        """
        started_at = datetime.utcnow()
        logger.info(f"V2 Search starting for: {role_title}")

        required_skills = required_skills or []
        preferred_backgrounds = preferred_backgrounds or []
        locations = locations or []

        # Run searches in parallel
        tier1_task = self._search_tier1(role_title, required_skills, locations)
        tier3_task = self._search_tier3(role_title)

        tier1_results, tier3_results = await asyncio.gather(
            tier1_task,
            tier3_task
        )

        # Tier 2: Find warm paths for external candidates
        # (We'll populate this from V1 results if include_cold is True)
        tier2_results = []
        tier4_results = []

        if include_cold:
            # Run V1 engine for external results
            target = SearchTarget(
                role_title=role_title,
                required_skills=required_skills,
                preferred_backgrounds=preferred_backgrounds,
                locations=locations,
                max_results=max_results
            )

            try:
                v1_results = await self.v1_engine.search(
                    target=target,
                    max_pathways=5,
                    max_results_per_source=20
                )

                # For each V1 result, check if there's a warm path
                for candidate in v1_results.candidates:
                    candidate_dict = {
                        "full_name": candidate.full_name,
                        "current_title": candidate.current_title,
                        "current_company": candidate.current_company,
                        "linkedin_url": candidate.linkedin_url,
                        "email": candidate.email,
                        "location": candidate.location,
                        "employment_history": getattr(candidate, "experience", []),
                        "education": getattr(candidate, "education", []),
                    }

                    # Check for warm path
                    warm_path = await self.warm_path_calculator.find_warm_path(candidate_dict)

                    if warm_path and warm_path["warmth_score"] >= 0.5:
                        # Tier 2: One intro away
                        tier2_results.append(
                            self._create_tiered_candidate(
                                candidate_dict,
                                tier=2,
                                warm_path=warm_path
                            )
                        )
                    else:
                        # Tier 4: Cold
                        tier4_results.append(
                            self._create_tiered_candidate(
                                candidate_dict,
                                tier=4,
                                warm_path=warm_path
                            )
                        )

            except Exception as e:
                logger.error(f"V1 search failed: {e}")

        # Get network stats
        network_stats = await self.network_search.get_network_stats()

        # Calculate duration
        duration = (datetime.utcnow() - started_at).total_seconds()

        # Generate recommendations
        primary_rec = self._generate_recommendation(
            tier1_results, tier2_results, tier3_results, tier4_results
        )
        recruiter_rec = self._generate_recruiter_recommendation(tier3_results)

        # Build results
        results = SearchResultsV2(
            tier_1_network=tier1_results[:20],
            tier_2_one_intro=tier2_results[:20],
            tier_3_recruiters=tier3_results[:10],
            tier_4_cold=tier4_results[:20] if include_cold else [],

            search_target={
                "role_title": role_title,
                "required_skills": required_skills,
                "preferred_backgrounds": preferred_backgrounds,
                "locations": locations
            },
            search_duration_seconds=round(duration, 2),
            network_size=network_stats["total_connections"],
            total_candidates=len(tier1_results) + len(tier2_results) + len(tier4_results),

            tier_1_count=len(tier1_results),
            tier_2_count=len(tier2_results),
            tier_3_count=len(tier3_results),
            tier_4_count=len(tier4_results),

            primary_recommendation=primary_rec,
            recruiter_recommendation=recruiter_rec
        )

        logger.info(
            f"V2 Search complete in {duration:.1f}s. "
            f"Tier1={len(tier1_results)}, Tier2={len(tier2_results)}, "
            f"Tier3={len(tier3_results)}, Tier4={len(tier4_results)}"
        )

        return results

    async def _search_tier1(
        self,
        role_title: str,
        required_skills: list[str],
        locations: list[str]
    ) -> list[TieredCandidate]:
        """Search for candidates in the network (Tier 1)."""
        # Search network
        matches = await self.network_search.search(
            role_title=role_title,
            required_skills=required_skills,
            locations=locations,
            limit=100
        )

        # Score readiness
        scored = self.readiness_scorer.batch_score(matches)

        # Convert to TieredCandidate
        results = []
        for person in scored:
            results.append(
                self._create_tiered_candidate(person, tier=1)
            )

        # Sort by combined score
        results.sort(key=lambda x: x.combined_score, reverse=True)

        return results

    async def _search_tier3(self, role_title: str) -> list[dict]:
        """Find recruiters in the network (Tier 3)."""
        # Determine specialty based on role
        specialty = None
        role_lower = role_title.lower()

        if any(kw in role_lower for kw in ["engineer", "developer", "ml", "ai", "data"]):
            specialty = "tech"
        elif any(kw in role_lower for kw in ["sales", "account", "revenue"]):
            specialty = "sales"
        elif any(kw in role_lower for kw in ["product", "pm"]):
            specialty = "product"
        elif any(kw in role_lower for kw in ["design", "ux", "ui"]):
            specialty = "design"

        recruiters = await self.recruiter_finder.find_recruiters(specialty=specialty)

        # Add outreach message for each
        from app.search.recruiters import RecruiterOutreach

        for r in recruiters:
            r["suggested_message"] = RecruiterOutreach.generate_message(
                r,
                role_title=role_title
            )

        return recruiters

    def _create_tiered_candidate(
        self,
        person: dict,
        tier: int,
        warm_path: dict = None
    ) -> TieredCandidate:
        """Create a TieredCandidate from a person dict."""
        tier_labels = {
            1: "In Your Network",
            2: "One Intro Away",
            3: "Via Recruiter",
            4: "Cold Outreach"
        }

        actions = {
            1: "Message directly",
            2: f"Ask {warm_path['via_person']['name'].split()[0] if warm_path and warm_path.get('via_person') else 'connection'} for intro",
            3: "Ask for referral",
            4: "Cold outreach (lower priority)"
        }

        match_score = person.get("match_score", 0.5)
        readiness_score = person.get("readiness_score", 0.0)
        warmth_score = 1.0 if tier == 1 else (
            warm_path["warmth_score"] if warm_path else 0.0
        )

        # Combined score weights: match (40%), readiness (30%), warmth (30%)
        combined_score = (
            match_score * 0.4 +
            readiness_score * 0.3 +
            warmth_score * 0.3
        )

        return TieredCandidate(
            id=str(person.get("id", "")),
            full_name=person.get("full_name", "Unknown"),
            current_title=person.get("current_title"),
            current_company=person.get("current_company"),
            linkedin_url=person.get("linkedin_url"),
            email=person.get("email"),
            location=person.get("location"),

            tier=tier,
            tier_label=tier_labels.get(tier, "Unknown"),

            match_score=round(match_score, 3),
            readiness_score=round(readiness_score, 3),
            warmth_score=round(warmth_score, 3),
            combined_score=round(combined_score, 3),

            match_reasons=person.get("match_reasons", []),
            readiness_signals=person.get("readiness_signals", []),

            warm_path=warm_path,
            action=actions.get(tier, "Contact")
        )

    def _generate_recommendation(
        self,
        tier1: list,
        tier2: list,
        tier3: list,
        tier4: list
    ) -> str:
        """Generate primary recommendation based on results."""
        if tier1:
            return (
                f"Start with Tier 1: You have {len(tier1)} people in your network "
                f"who match this role. They're most likely to respond. Message them directly."
            )
        elif tier3:
            return (
                f"No direct matches in your network, but you know {len(tier3)} recruiters. "
                f"Reach out to them first - they know who's actively looking."
            )
        elif tier2:
            return (
                f"Found {len(tier2)} candidates reachable via warm intros. "
                f"Ask your connections for introductions."
            )
        elif tier4:
            return (
                f"No warm paths found. {len(tier4)} cold candidates available, "
                f"but response rates will be lower."
            )
        else:
            return "No candidates found. Try broadening your search criteria."

    def _generate_recruiter_recommendation(self, recruiters: list) -> Optional[str]:
        """Generate recruiter-specific recommendation."""
        if not recruiters:
            return None

        tech_recruiters = [r for r in recruiters if r.get("specialty") == "tech"]

        if tech_recruiters:
            names = [r.get("full_name", "").split()[0] for r in tech_recruiters[:3]]
            return (
                f"You know {len(tech_recruiters)} tech recruiters: {', '.join(names)}. "
                f"A quick message to them could yield 5-10 qualified, actively-looking candidates."
            )
        else:
            return (
                f"You know {len(recruiters)} recruiters. They might know candidates "
                f"or can refer you to tech-focused recruiters."
            )

    async def get_network_summary(self) -> dict:
        """Get a summary of the network for the UI."""
        stats = await self.network_search.get_network_stats()
        recruiter_summary = await self.recruiter_finder.get_recruiter_summary()

        return {
            "network_stats": stats,
            "recruiter_summary": recruiter_summary,
            "recommendations": [
                "Your network is your #1 hiring asset",
                f"You have {stats['total_connections']} connections to leverage",
                f"You know {recruiter_summary['total_recruiters']} recruiters who can help",
            ]
        }
