"""
Warm Path Finder

Finds connections between external candidates and the founder's network.
This is the key differentiator: Clado gives you WHO, we give you HOW TO REACH THEM.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.services.network_index import NetworkIndex, NetworkContact, network_index_service
from app.services.external_search.clado_client import CladoProfile


# =============================================================================
# TEMPORAL OVERLAP CHECKING
# =============================================================================

def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse YYYY or YYYY-MM format into datetime. Returns None if unparseable."""
    if not date_str:
        return None
    try:
        if len(date_str) == 4:  # "2023"
            return datetime(int(date_str), 1, 1)
        elif len(date_str) == 7:  # "2023-06"
            parts = date_str.split("-")
            return datetime(int(parts[0]), int(parts[1]), 1)
        elif len(date_str) >= 10:  # "2023-06-15" or longer
            parts = date_str.split("-")
            return datetime(int(parts[0]), int(parts[1]), int(parts[2][:2]))
    except (ValueError, IndexError):
        pass
    return None


def _check_temporal_overlap(
    exp1_start: Optional[str],
    exp1_end: Optional[str],
    exp2_start: Optional[str],
    exp2_end: Optional[str],
    min_overlap_months: int = 3
) -> tuple[bool, int]:
    """
    Check if two experience periods overlap by at least min_overlap_months.

    Args:
        exp1_start, exp1_end: Start/end dates for first experience
        exp2_start, exp2_end: Start/end dates for second experience
        min_overlap_months: Minimum overlap required (default 3 months)

    Returns:
        (has_overlap, overlap_months) - whether overlap exists and how many months
    """
    start1 = _parse_date(exp1_start)
    end1 = _parse_date(exp1_end) or datetime.now()  # No end = still there
    start2 = _parse_date(exp2_start)
    end2 = _parse_date(exp2_end) or datetime.now()

    # If we can't parse dates, assume no verifiable overlap
    if not start1 or not start2:
        return False, 0

    # Calculate overlap
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)

    if overlap_start >= overlap_end:
        return False, 0

    # Calculate overlap in months
    overlap_days = (overlap_end - overlap_start).days
    overlap_months = overlap_days // 30

    return overlap_months >= min_overlap_months, overlap_months


def _find_connector_experience_at_company(
    connector: NetworkContact,
    target_company: str,
) -> Optional[dict]:
    """
    Find connector's experience entry for a specific company.

    Returns the experience dict if found, None otherwise.
    """
    normalized_target = network_index_service._normalize(target_company)

    for exp in connector.experience:
        exp_company = exp.get("company", "")
        if not exp_company:
            continue

        normalized_exp = network_index_service._normalize(exp_company)

        # Check if same company (exact or fuzzy match)
        if normalized_exp == normalized_target or \
           normalized_exp in normalized_target or \
           normalized_target in normalized_exp:
            return exp

    return None


# =============================================================================
# CONNECTOR QUALITY SCORING
# =============================================================================

# Seniority level keywords → score
_SENIORITY_LEVELS = [
    (1.0, {"director", "vp", "vice president", "head", "principal", "cto", "ceo",
            "coo", "cfo", "founder", "co-founder", "cofounder", "partner", "evp",
            "svp", "chief"}),
    (0.9, {"senior", "staff", "lead", "sr", "manager"}),
    (0.7, set()),  # default / mid-level (no keyword match)
    (0.5, {"junior", "associate", "entry", "assistant", "jr"}),
    (0.3, {"intern", "student", "ambassador", "fellow", "apprentice", "trainee",
            "volunteer", "extern"}),
]

# Role function keyword groups
_ROLE_FUNCTIONS = {
    "engineering": {"engineer", "developer", "swe", "sde", "programmer", "software",
                    "backend", "frontend", "fullstack", "full-stack", "devops", "sre",
                    "infrastructure", "platform", "mobile", "ios", "android", "web"},
    "data": {"data", "analyst", "analytics", "scientist", "ml", "machine learning",
             "ai", "deep learning", "nlp", "computer vision"},
    "product": {"product", "pm", "program manager", "product manager", "tpm"},
    "design": {"design", "designer", "ux", "ui", "creative", "graphic"},
    "marketing": {"marketing", "growth", "brand", "content", "seo", "sem"},
    "sales": {"sales", "account", "bd", "business development", "revenue"},
    "ops": {"operations", "ops", "supply chain", "logistics", "procurement"},
    "hr": {"hr", "human resources", "people", "talent", "recruiter", "recruiting"},
    "finance": {"finance", "accounting", "controller", "treasury", "fp&a"},
}

# Adjacent function pairs (bidirectional)
_ADJACENT_FUNCTIONS = {
    frozenset({"engineering", "data"}),
    frozenset({"engineering", "product"}),
    frozenset({"product", "design"}),
    frozenset({"marketing", "sales"}),
    frozenset({"data", "product"}),
    frozenset({"ops", "finance"}),
}


def _score_seniority(title: str) -> float:
    """Score connector seniority from title keywords. Returns 0.0-1.0."""
    if not title:
        return 0.7  # Unknown = mid-level assumption
    title_lower = title.lower()
    # Check from highest to lowest — first match wins
    for score, keywords in _SENIORITY_LEVELS:
        if keywords and any(kw in title_lower for kw in keywords):
            return score
    return 0.7  # Mid-level default


def _score_company_size(contact_count: int) -> float:
    """Score based on how many network contacts are at the target company. Returns 0.0-1.0."""
    if contact_count <= 2:
        return 1.0
    elif contact_count <= 5:
        return 0.8
    elif contact_count <= 15:
        return 0.6
    elif contact_count <= 50:
        return 0.4
    else:
        return 0.25


def _get_role_function(title: str) -> Optional[str]:
    """Extract the role function from a title string."""
    if not title:
        return None
    title_lower = title.lower()
    for function_name, keywords in _ROLE_FUNCTIONS.items():
        if any(kw in title_lower for kw in keywords):
            return function_name
    return None


def _score_role_relevance(connector_title: str, candidate_title: str) -> float:
    """Score how relevant the connector's role is to the candidate's. Returns 0.0-1.0."""
    func_a = _get_role_function(connector_title)
    func_b = _get_role_function(candidate_title)

    if func_a is None or func_b is None:
        return 0.5  # Can't determine — neutral

    if func_a == func_b:
        return 1.0

    if frozenset({func_a, func_b}) in _ADJACENT_FUNCTIONS:
        return 0.7

    return 0.4


def _score_company_match(company_a: str, company_b: str) -> float:
    """Score how well two company names actually match. Returns 0.0-1.0."""
    if not company_a or not company_b:
        return 0.0

    norm_a = network_index_service._normalize(company_a)
    norm_b = network_index_service._normalize(company_b)

    if norm_a == norm_b:
        return 1.0

    # Substring match — check length ratio to catch StudyFetch vs Fetch
    if norm_a in norm_b or norm_b in norm_a:
        shorter = min(len(norm_a), len(norm_b))
        longer = max(len(norm_a), len(norm_b))
        ratio = shorter / longer if longer > 0 else 0
        if ratio >= 0.7:
            return 0.7  # Close lengths — likely same company (e.g. "Microsoft" vs "Microsoft Corp")
        else:
            return 0.2  # Very different lengths — likely false positive (StudyFetch vs Fetch)

    return 0.0  # No match at all


def score_connector(
    connector: NetworkContact,
    candidate_title: str,
    company_contact_count: int,
    candidate_company: str,
) -> tuple[float, list[str]]:
    """
    Score a connector's quality for making an intro.

    Returns:
        (quality_score, human_readable_signals)
        quality_score is 0.0-1.0
    """
    seniority = _score_seniority(connector.current_title)
    company_size = _score_company_size(company_contact_count)
    role_rel = _score_role_relevance(connector.current_title, candidate_title)
    match_qual = _score_company_match(connector.current_company, candidate_company)

    quality = (
        seniority * 0.25 +
        company_size * 0.30 +
        role_rel * 0.20 +
        match_qual * 0.25
    )

    # Build human-readable signals
    signals = []

    # Seniority signal
    seniority_label = "Unknown level"
    if seniority >= 1.0:
        seniority_label = "Senior leader"
    elif seniority >= 0.9:
        seniority_label = "Senior"
    elif seniority >= 0.7:
        seniority_label = "Mid-level"
    elif seniority >= 0.5:
        seniority_label = "Junior"
    else:
        seniority_label = "Intern/student"
    connector_role = connector.current_title or "unknown role"
    signals.append(f"{seniority_label} ({connector_role})")

    # Network density signal — how many of YOUR contacts are at this company
    if company_contact_count > 15:
        signals.append(f"{company_contact_count} contacts in network (diluted)")
    elif company_contact_count > 5:
        signals.append(f"{company_contact_count} contacts in network")
    else:
        signals.append(f"{company_contact_count} contact{'s' if company_contact_count != 1 else ''} in network (strong signal)")

    # Role relevance signal
    if role_rel >= 1.0:
        signals.append("Same function")
    elif role_rel >= 0.7:
        signals.append("Adjacent function")
    elif role_rel <= 0.4:
        signals.append("Different function")

    # Company match signal
    if match_qual < 1.0 and match_qual > 0.0:
        if match_qual <= 0.2:
            signals.append(f"Weak company match ({connector.current_company} vs {candidate_company})")
        else:
            signals.append("Partial company match")

    return quality, signals


class ScoredConnector(BaseModel):
    """A connector with quality scoring and temporal overlap info."""

    connector: NetworkContact
    quality_score: float  # 0-1, quality of this connector
    quality_signals: list[str] = []  # Human-readable quality signals
    has_temporal_overlap: bool = False  # Did they actually overlap in time?
    overlap_months: int = 0  # How many months they overlapped
    suggested_message: Optional[str] = None  # Personalized intro message


class WarmPath(BaseModel):
    """A warm introduction path to a candidate."""

    path_type: str  # "company_overlap", "school_overlap", "skill_overlap", "direct"
    warmth_score: float  # 0-1, higher = warmer intro
    connector: NetworkContact  # Best connector (for backwards compatibility)
    relationship: str  # Human readable: "Both worked at Stripe"
    suggested_message: Optional[str] = None  # Intro request template
    connector_quality: float = 0.0  # 0-1, quality of the connector for this intro
    quality_signals: list[str] = []  # Human-readable quality signals

    # Multiple connectors support
    all_connectors: list[ScoredConnector] = []  # All viable connectors, ranked by quality
    total_connectors: int = 0  # Total count of connectors for this path


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
        """Find network contacts who worked at same companies, with temporal overlap checking."""
        paths = []

        def _score_all_connectors(
            contacts: list[NetworkContact],
            candidate_company: str,
            candidate_start: Optional[str],
            candidate_end: Optional[str],
            is_current_company: bool,
        ) -> Optional[WarmPath]:
            """Score all contacts, check temporal overlap, return WarmPath with multiple connectors."""
            if not contacts:
                return None

            # Get company contact count for size scoring
            normalized_company = network_index_service._normalize(candidate_company)
            company_index = index.companies.get(normalized_company)
            contact_count = company_index.count if company_index else len(contacts)

            scored_connectors: list[ScoredConnector] = []

            for contact in contacts:
                # Base quality scoring
                quality, signals = score_connector(
                    connector=contact,
                    candidate_title=candidate.current_title or "",
                    company_contact_count=contact_count,
                    candidate_company=candidate_company,
                )

                # Check company match quality to filter false positives
                match_qual = _score_company_match(contact.current_company, candidate_company)
                if match_qual < 0.35 and is_current_company:
                    continue

                # Check temporal overlap
                connector_exp = _find_connector_experience_at_company(contact, candidate_company)
                has_overlap = False
                overlap_months = 0

                if connector_exp:
                    has_overlap, overlap_months = _check_temporal_overlap(
                        connector_exp.get("start_date"),
                        connector_exp.get("end_date"),
                        candidate_start,
                        candidate_end,
                        min_overlap_months=3
                    )

                # Boost quality for verified temporal overlap
                if has_overlap:
                    # Boost based on overlap duration (max +0.2 for 2+ years)
                    overlap_boost = min(overlap_months / 24, 1.0) * 0.2
                    quality = min(quality + overlap_boost, 1.0)
                    signals.append(f"Verified overlap: {overlap_months} months")
                elif connector_exp and not has_overlap:
                    # Penalize if we have dates but no overlap
                    quality *= 0.6
                    signals.append("No temporal overlap (different time periods)")

                # Determine if currently working together
                is_current = (
                    contact.current_company and
                    self._companies_match(contact.current_company, candidate_company) and
                    is_current_company
                )

                # Generate personalized message
                message = self._generate_company_intro_message(
                    contact, candidate, candidate_company, is_current, has_overlap, overlap_months
                )

                scored_connectors.append(ScoredConnector(
                    connector=contact,
                    quality_score=round(quality, 3),
                    quality_signals=signals,
                    has_temporal_overlap=has_overlap,
                    overlap_months=overlap_months,
                    suggested_message=message,
                ))

            if not scored_connectors:
                return None

            # Sort by quality (temporal overlap gives boost, so it factors in)
            scored_connectors.sort(key=lambda c: c.quality_score, reverse=True)

            # Best connector for backwards compatibility
            best = scored_connectors[0]

            # Calculate warmth based on best connector
            is_current = (
                best.connector.current_company and
                self._companies_match(best.connector.current_company, candidate_company) and
                is_current_company
            )

            # Higher warmth for verified temporal overlap
            if best.has_temporal_overlap:
                base_warmth = self.WARMTH_COMPANY_CURRENT if is_current else self.WARMTH_COMPANY_PAST
            else:
                # Lower warmth if no verified overlap
                base_warmth = (self.WARMTH_COMPANY_CURRENT if is_current else self.WARMTH_COMPANY_PAST) * 0.7

            adjusted_warmth = base_warmth * best.quality_score

            # Build relationship string
            if is_current and best.has_temporal_overlap:
                relationship = f"Currently work together at {candidate_company}"
            elif best.has_temporal_overlap:
                relationship = f"Overlapped at {candidate_company} for {best.overlap_months} months"
            else:
                relationship = f"Both worked at {candidate_company}"

            return WarmPath(
                path_type="company_overlap",
                warmth_score=adjusted_warmth,
                connector=best.connector,
                relationship=relationship,
                suggested_message=best.suggested_message,
                connector_quality=best.quality_score,
                quality_signals=best.quality_signals,
                all_connectors=scored_connectors[:5],  # Top 5 connectors
                total_connectors=len(scored_connectors),
            )

        # Check current company
        if candidate.current_company:
            contacts = network_index_service.find_company_contacts(
                index, candidate.current_company
            )
            # For current company, candidate is still there (no end date)
            path = _score_all_connectors(
                contacts,
                candidate.current_company,
                candidate_start=None,  # We need to find this from experience
                candidate_end=None,
                is_current_company=True,
            )

            # Try to find candidate's start date at current company
            for exp in candidate.experience:
                if exp.get("company") == candidate.current_company and not exp.get("end_date"):
                    path = _score_all_connectors(
                        contacts,
                        candidate.current_company,
                        candidate_start=exp.get("start_date"),
                        candidate_end=None,
                        is_current_company=True,
                    )
                    break

            if path:
                paths.append(path)

        # Check past companies
        for exp in candidate.experience:
            company = exp.get("company")
            if company and company != candidate.current_company:
                contacts = network_index_service.find_company_contacts(index, company)
                path = _score_all_connectors(
                    contacts,
                    company,
                    candidate_start=exp.get("start_date"),
                    candidate_end=exp.get("end_date"),
                    is_current_company=False,
                )
                if path:
                    paths.append(path)

        return paths

    def _find_school_overlaps(
        self,
        candidate: CladoProfile,
        index: NetworkIndex
    ) -> list[WarmPath]:
        """Find network contacts who went to same schools, scored by seniority."""
        paths = []

        for edu in candidate.education:
            school = edu.get("school")
            if school:
                contacts = network_index_service.find_school_contacts(index, school)
                if not contacts:
                    continue

                # Score all connectors
                scored_connectors: list[ScoredConnector] = []

                for contact in contacts:
                    seniority = _score_seniority(contact.current_title)
                    quality = seniority  # For school overlaps, quality = seniority
                    signals = []

                    if seniority >= 0.9:
                        signals.append(f"Senior connector ({contact.current_title or 'unknown'})")
                    elif seniority <= 0.3:
                        signals.append(f"Junior connector ({contact.current_title or 'unknown'})")
                    else:
                        signals.append(f"{contact.current_title or 'Unknown role'}")

                    message = self._generate_school_intro_message(contact, candidate, school)

                    scored_connectors.append(ScoredConnector(
                        connector=contact,
                        quality_score=round(quality, 3),
                        quality_signals=signals,
                        has_temporal_overlap=False,  # Not checking school overlap timing
                        overlap_months=0,
                        suggested_message=message,
                    ))

                # Sort by quality
                scored_connectors.sort(key=lambda c: c.quality_score, reverse=True)

                best = scored_connectors[0]
                adjusted_warmth = self.WARMTH_SCHOOL * best.quality_score

                paths.append(WarmPath(
                    path_type="school_overlap",
                    warmth_score=adjusted_warmth,
                    connector=best.connector,
                    relationship=f"Both attended {school}",
                    suggested_message=best.suggested_message,
                    connector_quality=best.quality_score,
                    quality_signals=best.quality_signals,
                    all_connectors=scored_connectors[:5],  # Top 5 connectors
                    total_connectors=len(scored_connectors),
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
        is_current: bool,
        has_temporal_overlap: bool = False,
        overlap_months: int = 0,
    ) -> str:
        """Generate a warm intro request message for company overlap."""
        connector_first = connector.full_name.split()[0]
        candidate_first = candidate.full_name.split()[0]

        if is_current:
            return f"""Hey {connector_first}! I'm looking to hire and came across {candidate.full_name} who works with you at {company}.

Would you be open to making an intro? I'd love to learn more about their work.

Thanks!"""
        elif has_temporal_overlap and overlap_months >= 6:
            # Strong overlap - they likely know each other
            years = overlap_months // 12
            months = overlap_months % 12
            duration = f"{years} year{'s' if years != 1 else ''}" if years > 0 else ""
            if months > 0 and years > 0:
                duration += f" and {months} month{'s' if months != 1 else ''}"
            elif months > 0:
                duration = f"{months} month{'s' if months != 1 else ''}"
            return f"""Hey {connector_first}! I'm hiring and noticed you and {candidate_first} overlapped at {company} for about {duration}.

Any chance you know them and could make an intro? Would love your take on them too.

Thanks!"""
        elif has_temporal_overlap:
            # Some overlap
            return f"""Hey {connector_first}! I'm hiring and noticed you and {candidate_first} overlapped at {company}.

Any chance you crossed paths and could make an intro?

Thanks!"""
        else:
            # No verified overlap
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
