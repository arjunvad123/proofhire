"""
Unified Search Orchestrator - Searches Hermes + Network sources in parallel
"""

from typing import List, Optional
import asyncio
from datetime import datetime

from app.models.unified_candidate import UnifiedCandidate, SimpleScore
from app.models.blueprint import RoleBlueprint
from app.services.deduplication import DeduplicationEngine
from app.core.database import get_supabase_client


class UnifiedSearchOrchestrator:
    """
    Orchestrates search across Hermes (candidates) and Network (people) sources.

    Flow:
    1. Parallel search both tables
    2. Convert to UnifiedCandidate
    3. Deduplicate
    4. Simple scoring
    5. Tier results (warm vs cold)
    """

    def __init__(self):
        self.dedup = DeduplicationEngine()
        self.supabase = get_supabase_client()

    async def search(
        self,
        company_id: str,
        role: RoleBlueprint,
        limit: int = 100
    ) -> dict:
        """
        Main search flow.

        Returns:
            {
                "tier_1_warm": [...],      # Warm candidates (network or opted-in)
                "tier_2_cold": [...],      # Cold candidates
                "stats": {...},
                "duration_seconds": 47.3
            }
        """

        start_time = datetime.utcnow()

        # Step 1: Parallel search both sources
        hermes_task = self._search_hermes(role, limit)
        network_task = self._search_network(company_id, role, limit)

        hermes_candidates, network_candidates = await asyncio.gather(
            hermes_task, network_task
        )

        print(f"Search results: {len(hermes_candidates)} Hermes, {len(network_candidates)} Network")

        # Step 2: Deduplicate
        unified = self.dedup.deduplicate(hermes_candidates, network_candidates)

        # Step 3: Simple scoring
        scored = []
        for candidate in unified:
            score = self._calculate_simple_score(candidate, role)
            scored.append({
                "candidate": candidate,
                "score": score
            })

        # Sort by total score
        scored.sort(key=lambda x: x["score"].total_score, reverse=True)

        # Step 4: Tier results
        tiered = self._tier_results(scored)

        duration = (datetime.utcnow() - start_time).total_seconds()

        return {
            "tier_1_warm": tiered["tier_1"],
            "tier_2_cold": tiered["tier_2"],
            "stats": {
                "hermes_searched": len(hermes_candidates),
                "network_searched": len(network_candidates),
                "duplicates_merged": len(hermes_candidates) + len(network_candidates) - len(unified),
                "total_unique": len(unified),
            },
            "duration_seconds": duration
        }

    async def _search_hermes(
        self,
        role: RoleBlueprint,
        limit: int
    ) -> List[UnifiedCandidate]:
        """
        Search the candidates table (Hermes - 1,378 opted-in).
        """

        query = self.supabase.table("candidates").select("*")

        # Skill matching (simple OR match)
        if role.must_haves:
            # Match any of the required skills in the skills field
            skill_conditions = []
            for skill in role.must_haves[:3]:  # Top 3 skills
                skill_conditions.append(f"skills.ilike.%{skill}%")

            if skill_conditions:
                query = query.or_(",".join(skill_conditions))

        # Location matching
        if role.location_preferences:
            location_conditions = []
            for loc in role.location_preferences:
                location_conditions.append(f"location.ilike.%{loc}%")

            if location_conditions:
                query = query.or_(",".join(location_conditions))

        results = query.limit(limit).execute()

        # Convert to UnifiedCandidate
        candidates = []
        for row in results.data:
            candidate = self._hermes_row_to_candidate(row)
            candidates.append(candidate)

        return candidates

    async def _search_network(
        self,
        company_id: str,
        role: RoleBlueprint,
        limit: int
    ) -> List[UnifiedCandidate]:
        """
        Search the people table (Network - 7,274 LinkedIn connections).
        """

        query = self.supabase.table("people").select("""
            *,
            person_enrichments(*)
        """).eq("company_id", company_id)

        # Title matching
        if role.role_title:
            query = query.ilike("current_title", f"%{role.role_title}%")

        # Location matching
        if role.location_preferences:
            location_conditions = []
            for loc in role.location_preferences:
                location_conditions.append(f"location.ilike.%{loc}%")

            if location_conditions:
                query = query.or_(",".join(location_conditions))

        results = query.limit(limit).execute()

        # Convert to UnifiedCandidate
        candidates = []
        for row in results.data:
            candidate = self._network_row_to_candidate(row)
            candidates.append(candidate)

        return candidates

    def _hermes_row_to_candidate(self, row: dict) -> UnifiedCandidate:
        """Convert candidates table row to UnifiedCandidate."""

        # Parse skills (comma-separated or structured)
        skills = []
        if row.get("skills"):
            if isinstance(row["skills"], str):
                skills = [s.strip() for s in row["skills"].split(",")]
            elif isinstance(row["skills"], list):
                skills = row["skills"]

        # Parse major
        major = row.get("major") or []
        if isinstance(major, str):
            major = [major]

        # Parse role_type
        role_type = row.get("role_type") or []

        return UnifiedCandidate(
            person_id=row["id"],
            email=row.get("email"),
            linkedin_url=None,  # Hermes doesn't have LinkedIn
            github_url=row.get("github_profile_url"),
            full_name=row.get("name", ""),
            location=row.get("location"),
            headline=None,
            current_company=None,
            current_title=None,
            skills=skills,
            education_level=row.get("education_level"),
            university=row.get("university"),
            major=major,
            years_of_experience=row.get("years_of_experience"),
            github_username=row.get("github_username"),
            github_profile_url=row.get("github_profile_url"),
            sources=["hermes"],
            primary_source="hermes",
            source_quality=0.95,  # Hermes is high quality
            is_from_network=False,
            trust_score=None,
            warmth_score=0.0,
            warm_path_description=None,
            opted_in=True,  # Hermes candidates opted in
            role_type=role_type,
            data_completeness=0.0,  # Will be calculated
            has_enrichment=False,
            enrichment_source=None,
            created_at=row.get("created_at"),
            last_enriched=None,
        )

    def _network_row_to_candidate(self, row: dict) -> UnifiedCandidate:
        """Convert people table row to UnifiedCandidate."""

        # Get enrichment data if available
        enrichments = row.get("person_enrichments", [])
        enrichment = enrichments[0] if enrichments else {}

        # Parse skills from enrichment
        skills = []
        if enrichment.get("skills"):
            if isinstance(enrichment["skills"], list):
                skills = enrichment["skills"]
            elif isinstance(enrichment["skills"], dict):
                # Extract skill names from structured data
                skills = enrichment["skills"].get("list", [])

        # Calculate warmth score
        warmth = 0.8 if row.get("is_from_network") else 0.3

        return UnifiedCandidate(
            person_id=row["id"],
            email=row.get("email"),
            linkedin_url=row.get("linkedin_url"),
            github_url=row.get("github_url"),
            full_name=row.get("full_name", ""),
            location=row.get("location"),
            headline=row.get("headline"),
            current_company=row.get("current_company"),
            current_title=row.get("current_title"),
            skills=skills,
            education_level=None,
            university=None,
            major=[],
            years_of_experience=None,
            github_username=None,
            github_profile_url=row.get("github_url"),
            sources=["network"],
            primary_source="network",
            source_quality=0.70,  # Network is medium quality
            is_from_network=row.get("is_from_network", False),
            trust_score=row.get("trust_score"),
            warmth_score=warmth,
            warm_path_description="Direct LinkedIn connection" if row.get("is_from_network") else None,
            opted_in=False,
            role_type=[],
            data_completeness=0.0,  # Will be calculated
            has_enrichment=bool(enrichments),
            enrichment_source=enrichment.get("enrichment_source"),
            created_at=row.get("created_at"),
            last_enriched=row.get("last_enriched"),
        )

    def _calculate_simple_score(
        self,
        candidate: UnifiedCandidate,
        role: RoleBlueprint
    ) -> SimpleScore:
        """
        Calculate simple score (no complex reasoning).

        Components:
        - 40% Skills match
        - 30% Source quality
        - 30% Warmth
        """

        # Skills match (0-100)
        skills_match = self._score_skills_match(candidate.skills, role.must_haves)

        # Source quality (0-100)
        source_quality = candidate.source_quality * 100

        # Warmth (0-100)
        warmth = candidate.warmth_score * 100
        if candidate.opted_in:
            warmth = max(warmth, 50)  # Opted-in is at least 50

        # Total score
        total = (
            0.40 * skills_match +
            0.30 * source_quality +
            0.30 * warmth
        )

        # Suggested next step
        if candidate.is_from_network or candidate.opted_in:
            next_step = "Reach out directly" if candidate.is_from_network else "Email (opted-in)"
        elif candidate.warm_path_description:
            next_step = f"Get intro via {candidate.warm_path_description}"
        else:
            next_step = "Cold outreach"

        return SimpleScore(
            candidate_id=candidate.person_id,
            candidate_name=candidate.full_name,
            total_score=total,
            skills_match=skills_match,
            source_quality=source_quality,
            warmth=warmth,
            is_warm=candidate.is_from_network or candidate.opted_in,
            is_opted_in=candidate.opted_in,
            has_github=bool(candidate.github_url or candidate.github_username),
            suggested_next_step=next_step,
        )

    def _score_skills_match(
        self,
        candidate_skills: List[str],
        required_skills: List[str]
    ) -> float:
        """
        Score skills match (0-100).

        Simple overlap calculation.
        """

        if not required_skills:
            return 50.0  # Neutral if no requirements

        if not candidate_skills:
            return 0.0

        # Normalize skills (lowercase)
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        required_skills_lower = [s.lower() for s in required_skills]

        # Count matches
        matches = 0
        for req_skill in required_skills_lower:
            for cand_skill in candidate_skills_lower:
                if req_skill in cand_skill or cand_skill in req_skill:
                    matches += 1
                    break

        # Calculate percentage
        match_pct = matches / len(required_skills)

        return match_pct * 100

    def _tier_results(
        self,
        scored: List[dict]
    ) -> dict:
        """
        Tier results into warm vs cold.

        Tier 1 (Warm): is_from_network=True OR opted_in=True
        Tier 2 (Cold): Others
        """

        tier_1 = []
        tier_2 = []

        for item in scored:
            candidate = item["candidate"]
            score = item["score"]

            if candidate.is_from_network or candidate.opted_in:
                tier_1.append(item)
            else:
                tier_2.append(item)

        return {
            "tier_1": tier_1,
            "tier_2": tier_2,
        }
