"""
Warm Path Finder

Finds connections between external candidates and the founder's network.
This is the key differentiator: Clado gives you WHO, we give you HOW TO REACH THEM.
"""

from typing import Optional
from pydantic import BaseModel
from app.services.network_index import NetworkIndex, NetworkContact, network_index_service
from app.services.external_search.clado_client import CladoProfile


class WarmPath(BaseModel):
    """A warm introduction path to a candidate."""

    path_type: str  # "company_overlap", "school_overlap", "skill_overlap", "direct"
    warmth_score: float  # 0-1, higher = warmer intro
    connector: NetworkContact  # The person who can make the intro
    relationship: str  # Human readable: "Both worked at Stripe"
    suggested_message: Optional[str] = None  # Intro request template


class CandidateWithWarmth(BaseModel):
    """External candidate enriched with warm path information."""

    # Original Clado data
    id: str
    full_name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    experience: list[dict] = []
    education: list[dict] = []
    skills: list[str] = []
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    match_score: float = 0.0  # Clado's fit score

    # Warm path additions
    warm_paths: list[WarmPath] = []  # All possible intro paths
    best_path: Optional[WarmPath] = None  # Highest warmth path
    warmth_score: float = 0.0  # Overall warmth (0 = cold, 1 = direct contact)
    is_in_network: bool = False  # True if already in founder's network

    # Combined score
    combined_score: float = 0.0  # fit + warmth weighted


class WarmPathFinder:
    """
    Finds warm introduction paths for external candidates.

    For each external candidate from Clado/PDL, we check:
    1. Are they already in the network? (warmth = 1.0)
    2. Did they work at the same company as a network contact? (warmth = 0.7)
    3. Did they go to the same school? (warmth = 0.5)
    4. Do they share rare skills? (warmth = 0.3)
    5. No overlap? (warmth = 0.0, cold outreach)
    """

    WARMTH_DIRECT = 1.0
    WARMTH_COMPANY_CURRENT = 0.8  # They work together NOW
    WARMTH_COMPANY_PAST = 0.65    # They worked together BEFORE
    WARMTH_SCHOOL = 0.5
    WARMTH_SKILL = 0.3
    WARMTH_COLD = 0.0

    async def find_warm_paths(
        self,
        candidate: CladoProfile,
        network_index: NetworkIndex
    ) -> CandidateWithWarmth:
        """
        Find all warm paths to a candidate.

        Args:
            candidate: Profile from Clado/PDL
            network_index: Indexed founder's network

        Returns:
            CandidateWithWarmth with paths and scores
        """
        warm_paths: list[WarmPath] = []

        # Check company overlaps (current and past)
        company_paths = self._find_company_overlaps(candidate, network_index)
        warm_paths.extend(company_paths)

        # Check school overlaps
        school_paths = self._find_school_overlaps(candidate, network_index)
        warm_paths.extend(school_paths)

        # Check skill overlaps (for rare skills)
        skill_paths = self._find_skill_overlaps(candidate, network_index)
        warm_paths.extend(skill_paths)

        # Sort by warmth
        warm_paths.sort(key=lambda p: p.warmth_score, reverse=True)

        # Determine best path and overall warmth
        best_path = warm_paths[0] if warm_paths else None
        warmth_score = best_path.warmth_score if best_path else self.WARMTH_COLD

        # Calculate combined score (fit 60%, warmth 40%)
        # match_score from Clado is 0-1, normalize to 0-100
        fit_normalized = candidate.match_score * 100 if candidate.match_score <= 1 else candidate.match_score
        combined_score = (fit_normalized * 0.6) + (warmth_score * 100 * 0.4)

        return CandidateWithWarmth(
            id=candidate.id,
            full_name=candidate.full_name,
            headline=candidate.headline,
            location=candidate.location,
            current_title=candidate.current_title,
            current_company=candidate.current_company,
            experience=candidate.experience,
            education=candidate.education,
            skills=candidate.skills,
            linkedin_url=candidate.linkedin_url,
            github_url=candidate.github_url,
            match_score=candidate.match_score * 100,  # Normalize to 0-100
            warm_paths=warm_paths,
            best_path=best_path,
            warmth_score=warmth_score,
            is_in_network=False,  # External candidates are not in network
            combined_score=combined_score
        )

    def _find_company_overlaps(
        self,
        candidate: CladoProfile,
        index: NetworkIndex
    ) -> list[WarmPath]:
        """Find network contacts who worked at same companies."""
        paths = []

        # Check current company
        if candidate.current_company:
            contacts = network_index_service.find_company_contacts(
                index, candidate.current_company
            )
            for contact in contacts[:3]:  # Limit to top 3
                # Determine if contact is currently at this company
                is_current = (
                    contact.current_company and
                    self._companies_match(contact.current_company, candidate.current_company)
                )

                warmth = self.WARMTH_COMPANY_CURRENT if is_current else self.WARMTH_COMPANY_PAST

                paths.append(WarmPath(
                    path_type="company_overlap",
                    warmth_score=warmth,
                    connector=contact,
                    relationship=f"{'Currently work together' if is_current else 'Both worked'} at {candidate.current_company}",
                    suggested_message=self._generate_company_intro_message(
                        contact, candidate, candidate.current_company, is_current
                    )
                ))

        # Check past companies
        for exp in candidate.experience:
            company = exp.get("company")
            if company and company != candidate.current_company:
                contacts = network_index_service.find_company_contacts(index, company)
                for contact in contacts[:2]:
                    paths.append(WarmPath(
                        path_type="company_overlap",
                        warmth_score=self.WARMTH_COMPANY_PAST,
                        connector=contact,
                        relationship=f"Both worked at {company}",
                        suggested_message=self._generate_company_intro_message(
                            contact, candidate, company, False
                        )
                    ))

        return paths

    def _find_school_overlaps(
        self,
        candidate: CladoProfile,
        index: NetworkIndex
    ) -> list[WarmPath]:
        """Find network contacts who went to same schools."""
        paths = []

        for edu in candidate.education:
            school = edu.get("school")
            if school:
                contacts = network_index_service.find_school_contacts(index, school)
                for contact in contacts[:2]:
                    paths.append(WarmPath(
                        path_type="school_overlap",
                        warmth_score=self.WARMTH_SCHOOL,
                        connector=contact,
                        relationship=f"Both attended {school}",
                        suggested_message=self._generate_school_intro_message(
                            contact, candidate, school
                        )
                    ))

        return paths

    def _find_skill_overlaps(
        self,
        candidate: CladoProfile,
        index: NetworkIndex
    ) -> list[WarmPath]:
        """Find contacts with rare skill overlaps."""
        paths = []

        for skill in candidate.skills[:5]:  # Check top 5 skills
            normalized = network_index_service._normalize(skill)
            contacts = index.skills.get(normalized, [])

            # Only count as warm path if skill is somewhat rare
            if 1 <= len(contacts) <= 10:
                for contact in contacts[:1]:
                    paths.append(WarmPath(
                        path_type="skill_overlap",
                        warmth_score=self.WARMTH_SKILL,
                        connector=contact,
                        relationship=f"Both work with {skill}",
                        suggested_message=f"Hey {contact.full_name.split()[0]}, I came across {candidate.full_name} who also works with {skill}. Given your expertise, I'd love your take on them."
                    ))

        return paths

    def _companies_match(self, company1: str, company2: str) -> bool:
        """Check if two company names refer to the same company."""
        if not company1 or not company2:
            return False
        n1 = network_index_service._normalize(company1)
        n2 = network_index_service._normalize(company2)
        return n1 == n2 or n1 in n2 or n2 in n1

    def _generate_company_intro_message(
        self,
        connector: NetworkContact,
        candidate: CladoProfile,
        company: str,
        is_current: bool
    ) -> str:
        """Generate a warm intro request message for company overlap."""
        connector_first = connector.full_name.split()[0]
        candidate_first = candidate.full_name.split()[0]

        if is_current:
            return f"""Hey {connector_first}! I'm looking to hire and came across {candidate.full_name} who works with you at {company}.

Would you be open to making an intro? I'd love to learn more about their work.

Thanks!"""
        else:
            return f"""Hey {connector_first}! I'm hiring and noticed you and {candidate_first} both worked at {company}.

Any chance you'd be open to making an intro? Would love to hear your take on them too.

Thanks!"""

    def _generate_school_intro_message(
        self,
        connector: NetworkContact,
        candidate: CladoProfile,
        school: str
    ) -> str:
        """Generate a warm intro request message for school overlap."""
        connector_first = connector.full_name.split()[0]

        return f"""Hey {connector_first}! I'm hiring and came across {candidate.full_name} who also went to {school}.

Any chance you might know them or could make an intro?

Thanks!"""

    async def enrich_candidates(
        self,
        candidates: list[CladoProfile],
        network_index: NetworkIndex
    ) -> list[CandidateWithWarmth]:
        """
        Enrich a list of candidates with warm path information.

        Args:
            candidates: List of Clado profiles
            network_index: Indexed founder's network

        Returns:
            List of candidates with warm paths, sorted by combined score
        """
        enriched = []

        for candidate in candidates:
            with_warmth = await self.find_warm_paths(candidate, network_index)
            enriched.append(with_warmth)

        # Sort by combined score (fit + warmth)
        enriched.sort(key=lambda c: c.combined_score, reverse=True)

        return enriched


# Singleton instance
warm_path_finder = WarmPathFinder()
