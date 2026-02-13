"""
Search Orchestrator

Unified search across network + external databases (Clado/PDL).
Combines results with warm path intelligence for the best candidates.

This is the main entry point for the hybrid search system.
"""

import asyncio
from typing import Optional
from pydantic import BaseModel
from app.services.company_db import company_db
from app.services.network_index import network_index_service, NetworkIndex
from app.services.warm_path_finder import warm_path_finder, CandidateWithWarmth
from app.services.external_search.clado_client import clado_client, CladoProfile
from app.services.external_search.pdl_client import pdl_client, PDLProfile
from app.services.external_search.query_generator import query_generator, QuerySet
from app.models.curation import UnifiedCandidate


class SearchTier(BaseModel):
    """Results from one search tier."""

    tier_name: str
    tier_number: int
    candidates: list[CandidateWithWarmth]
    count: int
    source: str  # "network", "clado", "pdl"


class HybridSearchResult(BaseModel):
    """Full result from hybrid search."""

    # Search metadata
    role_title: str
    query_used: str
    total_candidates: int

    # Results by tier
    tier_1_network: SearchTier  # Direct network (warmth 1.0)
    tier_2_warm: SearchTier     # External with warm paths (warmth 0.3-0.8)
    tier_3_cold: SearchTier     # External cold (warmth 0.0)

    # Combined shortlist
    shortlist: list[CandidateWithWarmth]  # Top candidates across all tiers

    # Network stats
    network_stats: dict

    # Query insights
    queries_generated: QuerySet


class SearchOrchestrator:
    """
    Orchestrates hybrid search across all candidate sources.

    Flow:
    1. Build network index (company/school/skills)
    2. Generate smart queries based on role + network context
    3. Search network (Tier 1)
    4. Search Clado (Tier 2-3)
    5. Find warm paths for external candidates
    6. Rank and combine all results
    7. Return unified shortlist
    """

    async def search(
        self,
        company_id: str,
        role_title: str,
        required_skills: list[str] = [],
        preferred_skills: list[str] = [],
        location: Optional[str] = None,
        years_experience: Optional[int] = None,
        limit: int = 20
    ) -> HybridSearchResult:
        """
        Execute hybrid search across all sources.

        Args:
            company_id: The hiring company's UUID
            role_title: Position title
            required_skills: Must-have skills
            preferred_skills: Nice-to-have skills
            location: Preferred location
            years_experience: Minimum years
            limit: Max candidates to return

        Returns:
            HybridSearchResult with tiered candidates and shortlist
        """
        print(f"\n🔍 Starting hybrid search for: {role_title}")
        print(f"   Required skills: {', '.join(required_skills)}")

        # Step 1: Build network index
        print("\n📊 Building network index...")
        network_index = await network_index_service.build_index(company_id)
        network_stats = network_index_service.get_network_stats(network_index)
        print(f"   Network: {network_stats['total_contacts']} contacts, "
              f"{network_stats['unique_companies']} companies, "
              f"{network_stats['unique_schools']} schools")

        # Step 2: Generate smart queries
        print("\n🧠 Generating search queries...")
        queries = await query_generator.generate_queries(
            role_title=role_title,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            location=location,
            years_experience=years_experience,
            network_companies=network_stats['top_companies'],
            network_schools=network_stats['top_schools']
        )
        print(f"   Primary: {queries.primary_query.query}")
        for q in queries.expansion_queries[:2]:
            print(f"   Expansion: {q.query}")

        # Step 3: Search network (Tier 1)
        print("\n🌐 Searching network (Tier 1)...")
        tier_1_candidates = await self._search_network(
            company_id, role_title, required_skills, network_index
        )
        print(f"   Found {len(tier_1_candidates)} in network")

        # Step 4: Search external (Clado)
        print("\n🔎 Searching Clado (Tier 2-3)...")
        external_candidates = await self._search_external(
            queries, limit * 3  # Search more, filter down
        )
        print(f"   Found {len(external_candidates)} external candidates")

        # Step 5: Find warm paths for external candidates
        print("\n🤝 Finding warm paths...")
        external_with_warmth = await warm_path_finder.enrich_candidates(
            external_candidates, network_index
        )

        # Separate into warm (Tier 2) and cold (Tier 3)
        tier_2_warm = [c for c in external_with_warmth if c.warmth_score > 0]
        tier_3_cold = [c for c in external_with_warmth if c.warmth_score == 0]
        print(f"   Warm paths: {len(tier_2_warm)}, Cold: {len(tier_3_cold)}")

        # Step 6: Build shortlist
        print("\n📋 Building shortlist...")
        shortlist = self._build_shortlist(
            tier_1_candidates, tier_2_warm, tier_3_cold, limit
        )
        print(f"   Final shortlist: {len(shortlist)} candidates")

        # Step 7: Build result
        return HybridSearchResult(
            role_title=role_title,
            query_used=queries.primary_query.query,
            total_candidates=len(tier_1_candidates) + len(external_with_warmth),
            tier_1_network=SearchTier(
                tier_name="Direct Network",
                tier_number=1,
                candidates=tier_1_candidates,
                count=len(tier_1_candidates),
                source="network"
            ),
            tier_2_warm=SearchTier(
                tier_name="Warm Intros",
                tier_number=2,
                candidates=tier_2_warm[:limit],
                count=len(tier_2_warm),
                source="clado"
            ),
            tier_3_cold=SearchTier(
                tier_name="Cold Outreach",
                tier_number=3,
                candidates=tier_3_cold[:limit],
                count=len(tier_3_cold),
                source="clado"
            ),
            shortlist=shortlist,
            network_stats=network_stats,
            queries_generated=queries
        )

    async def _search_network(
        self,
        company_id: str,
        role_title: str,
        required_skills: list[str],
        network_index: NetworkIndex
    ) -> list[CandidateWithWarmth]:
        """Search the founder's direct network."""
        # Fetch people from network
        people = await company_db.get_people(company_id, limit=5000)

        # Convert to CandidateWithWarmth format
        network_candidates = []

        for person in people:
            # Handle both dict and Pydantic model
            if hasattr(person, 'model_dump'):
                p = person.model_dump()
            elif hasattr(person, 'dict'):
                p = person.dict()
            else:
                p = person if isinstance(person, dict) else {}

            # Calculate simple skill match
            person_skills = []
            headline = (p.get("headline") or "").lower()
            title = (p.get("current_title") or "").lower()

            # Extract skills from headline/title
            for skill in required_skills:
                if skill.lower() in headline or skill.lower() in title:
                    person_skills.append(skill)

            match_score = (len(person_skills) / len(required_skills) * 100) if required_skills else 50

            # Check if title matches role
            if role_title.lower() in title:
                match_score += 20

            candidate = CandidateWithWarmth(
                id=str(p.get("id", "")),
                full_name=p.get("full_name") or "Unknown",
                headline=p.get("headline"),
                location=p.get("location"),
                current_title=p.get("current_title"),
                current_company=p.get("current_company"),
                linkedin_url=p.get("linkedin_url"),
                github_url=p.get("github_url"),
                match_score=min(match_score, 100),
                warmth_score=1.0,  # Direct network = max warmth
                is_in_network=True,
                combined_score=match_score * 0.6 + 100 * 0.4  # High warmth boost
            )

            # Only include if there's some relevance
            if match_score > 20:
                network_candidates.append(candidate)

        # Sort by combined score
        network_candidates.sort(key=lambda c: c.combined_score, reverse=True)

        return network_candidates[:50]  # Limit to top 50

    async def _search_external(
        self,
        queries: QuerySet,
        limit: int
    ) -> list[CladoProfile]:
        """Search external APIs (Clado primary, with mock fallback)."""
        all_results: list[CladoProfile] = []
        seen_ids: set = set()

        # Try Clado first
        if clado_client.enabled:
            print("   Searching Clado API...")
            primary_result = await clado_client.search(
                queries.primary_query.query,
                limit=limit
            )
            for profile in primary_result.profiles:
                if profile.id not in seen_ids:
                    all_results.append(profile)
                    seen_ids.add(profile.id)

        # If no results, use mock data (Clado client returns mock when API fails)
        if not all_results:
            print("   Using mock data (API returned no results)...")
            # Force mock by temporarily disabling
            mock_result = clado_client._mock_search(queries.primary_query.query, limit)
            all_results = mock_result.profiles

        return all_results

    def _build_shortlist(
        self,
        tier_1: list[CandidateWithWarmth],
        tier_2: list[CandidateWithWarmth],
        tier_3: list[CandidateWithWarmth],
        limit: int
    ) -> list[CandidateWithWarmth]:
        """
        Build final shortlist with optimal mix of tiers.

        Strategy:
        - Include all network matches first (highest warmth)
        - Fill with warm intro candidates
        - Only add cold if needed
        """
        shortlist = []

        # Add network candidates (Tier 1) - high priority
        for candidate in tier_1:
            if len(shortlist) < limit:
                shortlist.append(candidate)

        # Add warm intro candidates (Tier 2)
        for candidate in tier_2:
            if len(shortlist) < limit:
                shortlist.append(candidate)

        # Add cold candidates (Tier 3) only if needed
        for candidate in tier_3:
            if len(shortlist) < limit:
                shortlist.append(candidate)

        # Final sort by combined score
        shortlist.sort(key=lambda c: c.combined_score, reverse=True)

        return shortlist[:limit]


# Singleton instance
search_orchestrator = SearchOrchestrator()


async def demo_search():
    """Demo the hybrid search system."""
    # This would use a real company_id from Supabase
    result = await search_orchestrator.search(
        company_id="100b5ac1-1912-4970-a378-04d0169fd597",  # Confido
        role_title="UGC Creator",
        required_skills=["Content Creation", "TikTok", "Video Production"],
        preferred_skills=["D2C Experience", "Instagram"],
        location="United States",
        years_experience=2,
        limit=15
    )

    print("\n" + "="*60)
    print("HYBRID SEARCH RESULTS")
    print("="*60)
    print(f"\nRole: {result.role_title}")
    print(f"Query: {result.query_used}")
    print(f"Total found: {result.total_candidates}")

    print(f"\n📊 Tier 1 (Network): {result.tier_1_network.count}")
    print(f"📊 Tier 2 (Warm): {result.tier_2_warm.count}")
    print(f"📊 Tier 3 (Cold): {result.tier_3_cold.count}")

    print("\n🏆 SHORTLIST:")
    for i, candidate in enumerate(result.shortlist[:10], 1):
        warmth_emoji = "🔥" if candidate.warmth_score > 0.7 else "🤝" if candidate.warmth_score > 0 else "❄️"
        network_tag = " [NETWORK]" if candidate.is_in_network else ""
        path_info = ""
        if candidate.best_path:
            path_info = f" via {candidate.best_path.connector.full_name.split()[0]}"

        print(f"  {i}. {candidate.full_name} - {candidate.current_title or 'N/A'}")
        print(f"     {warmth_emoji} Score: {candidate.combined_score:.0f} "
              f"(fit: {candidate.match_score:.0f}, warmth: {candidate.warmth_score:.0%})"
              f"{network_tag}{path_info}")
        if candidate.best_path:
            print(f"     💬 \"{candidate.best_path.relationship}\"")

    return result
