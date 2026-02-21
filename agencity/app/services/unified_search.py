"""
Unified Search Engine

Consolidates V1-V5 + Intelligence into ONE system.
This is the ONLY search interface needed.

Usage:
    engine = UnifiedSearchEngine()
    results = await engine.search(
        company_id="...",
        role_title="Software Engineer",
        required_skills=["Python", "React"],
        include_external=True,  # Search beyond network
        include_timing=True,    # Add timing signals
        deep_research=True,     # Research top candidates
        limit=15
    )
"""

import asyncio
import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)
from app.services.company_db import company_db
from app.services.network_index import network_index_service, NetworkIndex
from app.services.warm_path_finder import (
    warm_path_finder, WarmPath, score_connector, _score_company_match,
    _score_seniority,
)
from app.services.external_search.clado_client import clado_client, CladoProfile
from app.services.external_search.apollo_client import apollo_client, ApolloProfile
from app.services.external_search.firecrawl_client import firecrawl_client, FirecrawlProfile
from app.services.external_search.query_generator import query_generator
from app.config import settings


# =============================================================================
# UNIFIED DATA MODELS
# =============================================================================

class Candidate(BaseModel):
    """Single unified candidate model - replaces all previous models."""

    # Identity
    id: str
    full_name: str
    email: Optional[str] = None

    # Current position
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None

    # Links
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    twitter_url: Optional[str] = None

    # Experience & Skills
    skills: list[str] = []
    experience: list[dict] = []
    education: list[dict] = []

    # === SCORES (all 0-100) ===
    fit_score: float = 0.0          # How well they match the role
    warmth_score: float = 0.0       # How warm the connection is (0=cold, 100=direct)
    timing_score: float = 0.0       # How ready they are to move
    combined_score: float = 0.0     # Final ranking score

    # === SOURCE & PATH ===
    source: str = "network"         # "network", "external", "referral"
    tier: int = 1                   # 1=network, 2=warm external, 3=cold
    is_from_network: bool = True

    # Warm path info
    warm_path: Optional[WarmPath] = None
    intro_message: Optional[str] = None

    # === TIMING SIGNALS ===
    timing_signals: list[str] = []  # ["layoff", "long_tenure", "profile_updated"]
    timing_urgency: str = "low"     # "high", "medium", "low"

    # === DEEP RESEARCH ===
    deep_research: Optional[dict] = None  # Perplexity findings
    research_highlights: list[str] = []   # Key points to show

    # === CONTEXT ===
    why_consider: list[str] = []    # Bullet points of why they're good
    unknowns: list[str] = []        # What we don't know
    confidence: float = 0.5         # How confident we are (0-1)


class SearchResult(BaseModel):
    """Unified search result."""

    # Query info
    role_title: str
    query_used: str
    search_duration_seconds: float

    # Network stats
    network_size: int
    network_companies: int
    network_schools: int

    # Results
    candidates: list[Candidate]     # All candidates, sorted by combined_score
    total_found: int

    # Breakdown by tier
    tier_1_count: int  # Direct network
    tier_2_count: int  # Warm external
    tier_3_count: int  # Cold external

    # Timing summary
    high_urgency_count: int
    timing_enabled: bool

    # Research summary
    deep_researched_count: int
    research_enabled: bool

    # External provider diagnostics
    external_provider_stats: dict = {}
    external_provider_health: dict = {}
    external_diagnostics: list[str] = []
    external_yield_ok: bool = True


# =============================================================================
# UNIFIED SEARCH ENGINE
# =============================================================================

class UnifiedSearchEngine:
    """
    ONE search engine to rule them all.

    Combines:
    - Network search (V2)
    - External search with warm paths (V5)
    - Timing intelligence (V3)
    - Progressive enrichment (V4)
    - Deep research (V4)

    All in one clean interface.
    """

    # Scoring weights
    WEIGHT_FIT = 0.50       # 50% - skills/experience match
    WEIGHT_WARMTH = 0.30    # 30% - connection strength
    WEIGHT_TIMING = 0.20    # 20% - readiness to move

    # Timing signal scores
    TIMING_LAYOFF = 40
    TIMING_LONG_TENURE = 20
    TIMING_PROFILE_UPDATE = 15
    TIMING_JOB_SEARCHING = 25

    async def search(
        self,
        company_id: str,
        role_title: str,
        required_skills: list[str] = [],
        preferred_skills: list[str] = [],
        location: Optional[str] = None,
        years_experience: Optional[int] = None,
        include_external: bool = True,
        include_timing: bool = True,
        deep_research: bool = True,
        limit: int = 20
    ) -> SearchResult:
        """
        Execute unified search across all sources.

        Args:
            company_id: The hiring company
            role_title: Position to fill
            required_skills: Must-have skills
            preferred_skills: Nice-to-have skills
            location: Preferred location
            years_experience: Minimum years
            include_external: Search Clado/PDL beyond network
            include_timing: Calculate timing/urgency signals
            deep_research: Run Perplexity on top candidates
            limit: Max candidates to return

        Returns:
            SearchResult with unified candidate list
        """
        import time
        start_time = time.time()

        print(f"\n🔍 UNIFIED SEARCH: {role_title}")
        print(f"   Skills: {', '.join(required_skills)}")
        print(f"   External: {include_external}, Timing: {include_timing}, Research: {deep_research}")

        # Step 1: Build network index
        print("\n📊 Step 1: Building network index...")
        network_index = await network_index_service.build_index(company_id)
        network_stats = network_index_service.get_network_stats(network_index)
        print(f"   {network_stats['total_contacts']} contacts, {network_stats['unique_companies']} companies")

        # Step 2: Search network (Tier 1)
        print("\n🌐 Step 2: Searching network...")
        network_candidates = await self._search_network(
            company_id, role_title, required_skills, network_index
        )
        print(f"   Found {len(network_candidates)} in network")

        # Step 3: Search external (Tier 2-3) if enabled
        external_candidates = []
        external_meta = {
            "provider_stats": {},
            "provider_health": {},
            "diagnostics": [],
            "yield_ok": True,
        }
        if include_external:
            print("\n🔎 Step 3: Searching external sources...")
            external_candidates, external_meta = await self._search_external(
                role_title, required_skills, preferred_skills,
                location, network_stats, network_index, limit
            )
            print(f"   Found {len(external_candidates)} external")

        # Step 3.5: Enrich top external candidates with Clado
        if include_external and external_candidates:
            print("\n🔬 Step 3.5: Enriching top external candidates via Clado...")
            external_candidates = await self._enrich_external_candidates(
                external_candidates, role_title, required_skills, max_enrich=10
            )

        # Step 4: Add timing signals if enabled
        all_candidates = network_candidates + external_candidates
        if include_timing:
            print("\n⏱️ Step 4: Calculating timing signals...")
            all_candidates = await self._add_timing_signals(all_candidates)
            high_urgency = len([c for c in all_candidates if c.timing_urgency == "high"])
            print(f"   {high_urgency} high urgency candidates")

        # Step 5: Calculate final scores and rank
        print("\n📈 Step 5: Ranking candidates...")
        all_candidates = self._calculate_final_scores(all_candidates)
        all_candidates.sort(key=lambda c: c.combined_score, reverse=True)

        # Step 6: Deep research top candidates if enabled
        researched_count = 0
        research_enabled = deep_research and (
            (settings.anthropic_web_search_enabled and settings.anthropic_api_key)
            or settings.perplexity_api_key
        )
        if research_enabled:
            print("\n🔬 Step 6: Deep researching top candidates...")
            all_candidates = await self._deep_research_top(
                all_candidates, role_title, required_skills, top_n=3
            )
            researched_count = min(3, len(all_candidates))
            print(f"   Researched {researched_count} candidates")

        # Step 7: Build context for top candidates
        print("\n📝 Step 7: Building context...")
        all_candidates = self._build_context(all_candidates[:limit], role_title, required_skills)

        # Finalize
        duration = time.time() - start_time
        final_candidates = all_candidates[:limit]

        tier_1 = len([c for c in final_candidates if c.tier == 1])
        tier_2 = len([c for c in final_candidates if c.tier == 2])
        tier_3 = len([c for c in final_candidates if c.tier == 3])

        print(f"\n✅ DONE in {duration:.1f}s")
        print(f"   Tier 1 (network): {tier_1}, Tier 2 (warm): {tier_2}, Tier 3 (cold): {tier_3}")

        return SearchResult(
            role_title=role_title,
            query_used=f"{role_title} with {', '.join(required_skills[:3])}",
            search_duration_seconds=round(duration, 2),
            network_size=network_stats['total_contacts'],
            network_companies=network_stats['unique_companies'],
            network_schools=network_stats['unique_schools'],
            candidates=final_candidates,
            total_found=len(all_candidates),
            tier_1_count=tier_1,
            tier_2_count=tier_2,
            tier_3_count=tier_3,
            high_urgency_count=len([c for c in final_candidates if c.timing_urgency == "high"]),
            timing_enabled=include_timing,
            deep_researched_count=researched_count,
            research_enabled=deep_research,
            external_provider_stats=external_meta.get("provider_stats", {}),
            external_provider_health=external_meta.get("provider_health", {}),
            external_diagnostics=external_meta.get("diagnostics", []),
            external_yield_ok=external_meta.get("yield_ok", True),
        )

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    async def _search_network(
        self,
        company_id: str,
        role_title: str,
        required_skills: list[str],
        network_index: NetworkIndex
    ) -> list[Candidate]:
        """Search the founder's direct network."""
        people = await company_db.get_people(company_id, limit=5000)
        candidates = []

        for person in people:
            # Handle Pydantic models
            if hasattr(person, 'model_dump'):
                p = person.model_dump()
            else:
                p = person if isinstance(person, dict) else {}

            # Calculate fit score
            fit_score = self._calculate_fit(p, role_title, required_skills)

            # Only include relevant candidates
            if fit_score < 15:
                continue

            candidates.append(Candidate(
                id=str(p.get("id", "")),
                full_name=p.get("full_name") or "Unknown",
                email=p.get("email"),
                current_title=p.get("current_title"),
                current_company=p.get("current_company"),
                headline=p.get("headline"),
                location=p.get("location"),
                linkedin_url=p.get("linkedin_url"),
                github_url=p.get("github_url"),
                fit_score=fit_score,
                warmth_score=100.0,  # Direct network = max warmth
                timing_score=0.0,    # Will be calculated later
                source="network",
                tier=1,
                is_from_network=True
            ))

        return candidates

    async def _search_external(
        self,
        role_title: str,
        required_skills: list[str],
        preferred_skills: list[str],
        location: Optional[str],
        network_stats: dict,
        network_index: NetworkIndex,
        limit: int
    ) -> tuple[list[Candidate], dict]:
        """Search ALL external APIs in parallel and find warm paths."""

        # Generate smart queries
        queries = await query_generator.generate_queries(
            role_title=role_title,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            location=location,
            network_companies=network_stats.get('top_companies', []),
            network_schools=network_stats.get('top_schools', [])
        )

        search_query = queries.primary_query.query

        # Build Firecrawl tasks: primary query + expansion queries for more candidates
        firecrawl_tasks = [
            firecrawl_client.search(search_query, limit=20, location=location)
        ]
        for eq in queries.expansion_queries[:2]:
            firecrawl_tasks.append(
                firecrawl_client.search(eq.query, limit=15, location=location)
            )

        # Run ENABLED providers in parallel (skip unconfigured ones gracefully)
        from app.services.external_search.firecrawl_client import FirecrawlSearchResult
        from app.services.external_search.apollo_client import ApolloSearchResult as ApolloSR
        from app.services.external_search.clado_client import CladoSearchResult as CladoSR

        search_tasks = []
        task_labels = []

        # Clado
        if clado_client.enabled:
            search_tasks.append(clado_client.search(search_query, limit=limit))
            task_labels.append("clado")
        # Apollo
        if apollo_client.enabled:
            search_tasks.append(apollo_client.search(search_query, limit=limit, location=location))
            task_labels.append("apollo")
        # Firecrawl (multiple queries)
        if firecrawl_client.enabled:
            for ft in firecrawl_tasks:
                search_tasks.append(ft)
                task_labels.append("firecrawl")

        # Log which providers are active
        active_names = sorted(set(task_labels)) or ["none"]
        skipped_names = [
            name for name, client in [("clado", clado_client), ("apollo", apollo_client), ("firecrawl", firecrawl_client)]
            if not client.enabled
        ]
        if skipped_names:
            print(f"   Providers active: {', '.join(active_names)} | skipped (no API key): {', '.join(skipped_names)}")
        else:
            print(f"   Providers active: {', '.join(active_names)}")

        all_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Map results back to providers
        clado_results = CladoSR(profiles=[], total_matches=0, query_interpreted="", search_id="")
        apollo_results = ApolloSR(profiles=[], total_matches=0, query_used=search_query)
        firecrawl_profiles = []

        for label, result in zip(task_labels, all_results):
            if isinstance(result, Exception):
                logger.warning("Provider %s raised exception: %s", label, result)
                continue
            if label == "clado":
                clado_results = result
            elif label == "apollo":
                apollo_results = result
            elif label == "firecrawl":
                firecrawl_profiles.extend(result.profiles)

        firecrawl_results = FirecrawlSearchResult(
            profiles=firecrawl_profiles,
            total_matches=len(firecrawl_profiles),
            query_used=search_query,
        )

        # Health checks only for enabled providers
        health_tasks = {}
        if clado_client.enabled:
            health_tasks["clado"] = clado_client.health_check()
        if apollo_client.enabled:
            health_tasks["apollo"] = apollo_client.health_check()
        if firecrawl_client.enabled:
            health_tasks["firecrawl"] = firecrawl_client.health_check()

        health_results = {}
        if health_tasks:
            results_list = await asyncio.gather(*health_tasks.values(), return_exceptions=True)
            for name, res in zip(health_tasks.keys(), results_list):
                if isinstance(res, Exception):
                    health_results[name] = {"provider": name, "ok": False, "reason": str(res)}
                else:
                    health_results[name] = res

        # Fill in skipped providers as explicitly skipped (not unhealthy)
        clado_health = health_results.get("clado", {"provider": "clado", "ok": False, "reason": "not_configured"})
        apollo_health = health_results.get("apollo", {"provider": "apollo", "ok": False, "reason": "not_configured"})
        firecrawl_health = health_results.get("firecrawl", {"provider": "firecrawl", "ok": False, "reason": "not_configured"})

        candidates = []
        seen_linkedin_urls = set()
        diagnostics = []

        # Quality threshold — below this, don't create a warm path
        QUALITY_THRESHOLD = 0.35

        def _build_warm_paths(
            current_company: Optional[str],
            current_title: Optional[str],
            education: list[dict],
            full_name: str,
        ) -> list[WarmPath]:
            warm_paths = []
            if current_company:
                contacts = network_index_service.find_company_contacts(network_index, current_company)
                if contacts:
                    # Get company contact count
                    normalized = network_index_service._normalize(current_company)
                    company_idx = network_index.companies.get(normalized)
                    contact_count = company_idx.count if company_idx else len(contacts)

                    # Score all connectors and pick the best
                    best_contact = None
                    best_quality = -1.0
                    best_signals = []

                    for contact in contacts:
                        # Check company match quality first
                        match_qual = _score_company_match(contact.current_company, current_company)
                        if match_qual < QUALITY_THRESHOLD:
                            continue  # Skip false positive matches (e.g. StudyFetch vs Fetch)

                        quality, signals = score_connector(
                            connector=contact,
                            candidate_title=current_title or "",
                            company_contact_count=contact_count,
                            candidate_company=current_company,
                        )

                        if quality > best_quality:
                            best_quality = quality
                            best_contact = contact
                            best_signals = signals

                    if best_contact and best_quality >= QUALITY_THRESHOLD:
                        base_warmth = 0.75
                        adjusted_warmth = base_warmth * best_quality

                        warm_paths.append(WarmPath(
                            path_type="company_overlap",
                            warmth_score=adjusted_warmth,
                            connector=best_contact,
                            relationship=f"Both at {current_company}",
                            suggested_message=f"Hey {best_contact.full_name.split()[0]}! I came across {full_name} who works with you. Would you be open to making an intro?",
                            connector_quality=round(best_quality, 2),
                            quality_signals=best_signals,
                        ))

            for edu in education:
                school = edu.get("school")
                if school:
                    contacts = network_index_service.find_school_contacts(network_index, school)
                    if contacts:
                        # Pick the best connector by seniority
                        best_contact = max(contacts, key=lambda c: _score_seniority(c.current_title))
                        quality = _score_seniority(best_contact.current_title)
                        signals = []
                        if quality >= 0.9:
                            signals.append(f"Senior connector ({best_contact.current_title or 'unknown'})")
                        elif quality <= 0.3:
                            signals.append(f"Junior connector ({best_contact.current_title or 'unknown'})")

                        adjusted_warmth = 0.50 * quality

                        warm_paths.append(WarmPath(
                            path_type="school_overlap",
                            warmth_score=adjusted_warmth,
                            connector=best_contact,
                            relationship=f"Both attended {school}",
                            connector_quality=round(quality, 2),
                            quality_signals=signals,
                        ))
            return warm_paths

        def _add_candidate(profile, source_provider: str):
            """Add a profile from any provider to the candidate list, deduplicating by LinkedIn URL."""
            if profile.linkedin_url and profile.linkedin_url.lower() in seen_linkedin_urls:
                return
            if profile.linkedin_url:
                seen_linkedin_urls.add(profile.linkedin_url.lower())

            warm_paths = _build_warm_paths(
                profile.current_company,
                profile.current_title,
                getattr(profile, 'education', []),
                profile.full_name,
            )

            best_path = warm_paths[0] if warm_paths else None
            warmth_score = best_path.warmth_score * 100 if best_path else 0
            tier = 2 if warmth_score > 0 else 3

            candidates.append(Candidate(
                id=profile.id,
                full_name=profile.full_name,
                current_title=profile.current_title,
                current_company=profile.current_company,
                headline=profile.headline,
                location=profile.location,
                linkedin_url=profile.linkedin_url,
                github_url=getattr(profile, 'github_url', None),
                twitter_url=getattr(profile, 'twitter_url', None),
                skills=getattr(profile, 'skills', []),
                experience=getattr(profile, 'experience', []),
                education=getattr(profile, 'education', []),
                fit_score=(profile.match_score * 100 if profile.match_score and profile.match_score <= 1 else profile.match_score) or 50.0,
                warmth_score=warmth_score,
                source="external",
                tier=tier,
                is_from_network=False,
                warm_path=best_path,
                intro_message=best_path.suggested_message if best_path else None
            ))

        # --- CACHE: collect all LinkedIn URLs from results for batch lookup ---
        all_profiles_with_source = []
        for profile in clado_results.profiles:
            all_profiles_with_source.append((profile, "clado"))
        for profile in firecrawl_results.profiles:
            all_profiles_with_source.append((profile, "firecrawl"))
        for profile in apollo_results.profiles:
            all_profiles_with_source.append((profile, "apollo"))

        cache_lookup_urls = [
            p.linkedin_url.lower()
            for p, _ in all_profiles_with_source
            if p.linkedin_url
        ]

        cached_records = {}
        if cache_lookup_urls:
            try:
                cached_records = await company_db.get_cached_external_candidates(
                    cache_lookup_urls, max_age_days=7
                )
                if cached_records:
                    print(f"   Cache: {len(cached_records)} hits, {len(cache_lookup_urls) - len(cached_records)} misses")
            except Exception as e:
                logger.warning("Cache lookup failed (non-fatal): %s", e)

        # Process all providers — use cache when available, store new results
        cache_store_tasks = []
        for profile, source_provider in all_profiles_with_source:
            linkedin_key = profile.linkedin_url.lower() if profile.linkedin_url else None
            cached = cached_records.get(linkedin_key) if linkedin_key else None

            if cached:
                # Use cached enrichment data if available (richer than search result)
                if cached.get("enrichment_source"):
                    profile.skills = cached.get("skills") or getattr(profile, 'skills', [])
                    profile.experience = cached.get("experience") or getattr(profile, 'experience', [])
                    profile.education = cached.get("education") or getattr(profile, 'education', [])
                    if cached.get("headline"):
                        profile.headline = cached["headline"]
                    if cached.get("location"):
                        profile.location = cached["location"]

            _add_candidate(profile, source_provider)

            # Store new/updated results in cache (fire-and-forget)
            if linkedin_key and not cached:
                cache_store_tasks.append(
                    company_db.upsert_external_candidate({
                        "linkedin_url": profile.linkedin_url,
                        "full_name": profile.full_name,
                        "current_title": profile.current_title,
                        "current_company": profile.current_company,
                        "headline": profile.headline,
                        "location": profile.location,
                        "skills": getattr(profile, 'skills', []),
                        "experience": getattr(profile, 'experience', []),
                        "education": getattr(profile, 'education', []),
                        "github_url": getattr(profile, 'github_url', None),
                        "twitter_url": getattr(profile, 'twitter_url', None),
                        "discovery_source": source_provider,
                    })
                )

        # Store new candidates in cache (non-blocking)
        if cache_store_tasks:
            results = await asyncio.gather(*cache_store_tasks, return_exceptions=True)
            stored = sum(1 for r in results if not isinstance(r, Exception))
            print(f"   Cache: stored {stored} new candidates")

        provider_stats = {
            "clado_total_matches": clado_results.total_matches,
            "clado_profiles_returned": len(clado_results.profiles),
            "firecrawl_total_matches": firecrawl_results.total_matches,
            "firecrawl_profiles_returned": len(firecrawl_results.profiles),
            "apollo_total_matches": apollo_results.total_matches,
            "apollo_profiles_returned": len(apollo_results.profiles),
            "deduped_external_candidates": len(candidates),
        }
        provider_health = {
            "clado": clado_health,
            "firecrawl": firecrawl_health,
            "apollo": apollo_health,
        }

        # Diagnostics — only warn about providers that ARE configured but failing
        active_providers = sum(1 for h in [clado_health, firecrawl_health, apollo_health] if h.get("ok"))
        configured_providers = sum(1 for c in [clado_client, apollo_client, firecrawl_client] if c.enabled)

        if len(candidates) == 0 and configured_providers > 0:
            diagnostics.append(
                f"External search returned zero candidates across {active_providers}/{configured_providers} "
                "active providers. Check provider credits, query quality, or provider limits."
            )
        for name, health, client in [
            ("Clado", clado_health, clado_client),
            ("Firecrawl", firecrawl_health, firecrawl_client),
            ("Apollo", apollo_health, apollo_client),
        ]:
            if client.enabled and not health.get("ok"):
                diagnostics.append(f"{name} provider configured but unhealthy: {health.get('reason', 'unknown')}")

        meta = {
            "provider_stats": provider_stats,
            "provider_health": provider_health,
            "diagnostics": diagnostics,
            "active_providers": active_providers,
            "yield_ok": len(candidates) > 0,
        }
        return candidates, meta

    async def _enrich_external_candidates(
        self,
        candidates: list[Candidate],
        role_title: str,
        required_skills: list[str],
        max_enrich: int = 10
    ) -> list[Candidate]:
        """
        Enrich top external candidates using Clado's waterfall enrichment.

        Firecrawl only gives us name/title/company from search snippets.
        Clado enrichment fills in skills, experience, education — giving
        the scoring engine much better data to work with.

        Cost: ~$0.01-$0.03 per candidate (1-3 Clado credits)
        """
        if not clado_client.enabled:
            print("   Clado not configured, skipping enrichment")
            return candidates

        # Pick candidates with LinkedIn URLs, sorted by current fit_score
        enrichable = [
            (i, c) for i, c in enumerate(candidates)
            if c.linkedin_url and c.source == "external"
        ]
        # Prioritize by fit_score so we enrich the most promising first
        enrichable.sort(key=lambda x: x[1].fit_score, reverse=True)
        enrichable = enrichable[:max_enrich]

        if not enrichable:
            print("   No candidates with LinkedIn URLs to enrich")
            return candidates

        print(f"   Enriching {len(enrichable)} candidates via Clado waterfall...")

        # Run enrichment in parallel (batched to avoid rate limits)
        async def _enrich_one(idx: int, candidate: Candidate) -> tuple[int, Optional[CladoProfile]]:
            try:
                profile = await clado_client.get_profile_with_fallback(candidate.linkedin_url)
                return (idx, profile)
            except Exception as e:
                logger.warning("Clado enrichment failed for %s: %s", candidate.full_name, e)
                return (idx, None)

        # Run all enrichments in parallel
        results = await asyncio.gather(*[
            _enrich_one(idx, c) for idx, c in enrichable
        ])

        enriched_count = 0
        cache_update_tasks = []
        for idx, profile in results:
            if profile is None:
                continue

            c = candidates[idx]
            enriched_count += 1

            # Update with enriched data (only override if we got better data)
            if profile.skills:
                c.skills = profile.skills
            if profile.experience:
                c.experience = profile.experience
            if profile.education:
                c.education = profile.education
            if profile.headline and not c.headline:
                c.headline = profile.headline
            if profile.location and not c.location:
                c.location = profile.location
            if profile.current_title:
                c.current_title = profile.current_title
            if profile.current_company:
                c.current_company = profile.current_company

            # Recalculate fit score with enriched data
            person_dict = {
                "headline": c.headline or "",
                "current_title": c.current_title or "",
                "skills": c.skills,
            }
            # Enhanced fit calculation using skills
            new_fit = self._calculate_fit(person_dict, role_title, required_skills)
            # Also check skills list directly
            skill_bonus = 0
            for skill in required_skills:
                if any(skill.lower() in s.lower() for s in c.skills):
                    skill_bonus += 10
            new_fit = min(new_fit + skill_bonus, 100)

            if new_fit > c.fit_score:
                c.fit_score = new_fit

            c.confidence = 0.8  # Higher confidence after enrichment

            # Update cache with enriched data
            if c.linkedin_url:
                cache_update_tasks.append(
                    company_db.update_external_candidate_enrichment(
                        linkedin_url=c.linkedin_url,
                        enrichment_source="clado_profile",
                        enrichment_data=profile.model_dump() if hasattr(profile, 'model_dump') else {},
                        updated_fields={
                            "skills": c.skills,
                            "experience": c.experience,
                            "education": c.education,
                            "current_title": c.current_title,
                            "current_company": c.current_company,
                            "headline": c.headline,
                            "location": c.location,
                        },
                    )
                )

        # Update cache with enrichment (non-blocking)
        if cache_update_tasks:
            await asyncio.gather(*cache_update_tasks, return_exceptions=True)

        print(f"   Enriched {enriched_count}/{len(enrichable)} candidates successfully")
        return candidates

    async def _add_timing_signals(self, candidates: list[Candidate]) -> list[Candidate]:
        """Add timing/urgency signals to candidates."""

        # Known layoff companies (would be fetched from a real source)
        layoff_companies = {"stripe", "meta", "amazon", "google", "microsoft", "salesforce"}

        for candidate in candidates:
            signals = []
            timing_score = 0

            company = (candidate.current_company or "").lower()

            # Check layoff exposure
            if any(lc in company for lc in layoff_companies):
                signals.append("layoff_exposure")
                timing_score += self.TIMING_LAYOFF

            # Check tenure (from experience if available)
            # For now, add random signals for demo
            if candidate.fit_score > 70:
                signals.append("strong_fit")
                timing_score += 10

            candidate.timing_signals = signals
            candidate.timing_score = min(timing_score, 100)

            # Set urgency level
            if timing_score >= 40:
                candidate.timing_urgency = "high"
            elif timing_score >= 20:
                candidate.timing_urgency = "medium"
            else:
                candidate.timing_urgency = "low"

        return candidates

    def _calculate_fit(self, person: dict, role_title: str, required_skills: list[str]) -> float:
        """Calculate how well a person fits the role."""
        score = 0.0

        headline = (person.get("headline") or "").lower()
        title = (person.get("current_title") or "").lower()
        combined = f"{headline} {title}"

        # Title match
        role_words = role_title.lower().split()
        for word in role_words:
            if len(word) > 3 and word in combined:
                score += 20

        # Skills match
        for skill in required_skills:
            if skill.lower() in combined:
                score += 15

        return min(score, 100)

    def _calculate_final_scores(self, candidates: list[Candidate]) -> list[Candidate]:
        """Calculate combined scores for all candidates."""

        for c in candidates:
            c.combined_score = (
                c.fit_score * self.WEIGHT_FIT +
                c.warmth_score * self.WEIGHT_WARMTH +
                c.timing_score * self.WEIGHT_TIMING
            )

        return candidates

    async def _deep_research_top(
        self,
        candidates: list[Candidate],
        role_title: str,
        required_skills: list[str],
        top_n: int = 3
    ) -> list[Candidate]:
        """
        Run deep research on top N candidates.

        Uses Claude Research Agent Team (preferred) or Perplexity (fallback).
        Checks cache first — skips research for candidates researched in last 30 days.
        """
        # Try Claude Research Agent Team first
        if settings.anthropic_web_search_enabled and settings.anthropic_api_key:
            return await self._deep_research_claude(candidates, role_title, required_skills, top_n)

        # Fallback to Perplexity
        return await self._deep_research_perplexity(candidates, role_title, required_skills, top_n)

    async def _deep_research_claude(
        self,
        candidates: list[Candidate],
        role_title: str,
        required_skills: list[str],
        top_n: int = 3
    ) -> list[Candidate]:
        """Deep research using Claude Research Agent Team with caching."""
        from app.services.research.research_agent_team import ResearchOrchestrator

        try:
            orchestrator = ResearchOrchestrator(max_concurrent=3)

            # Check cache for already-researched candidates (30-day window)
            to_research = []
            cached_indices = {}
            for i, candidate in enumerate(candidates[:top_n]):
                if candidate.linkedin_url:
                    try:
                        cached = await company_db.get_cached_candidate_by_url(
                            candidate.linkedin_url, max_age_days=30
                        )
                        if cached and cached.get("research_data"):
                            # Use cached research
                            cached_indices[i] = cached
                            print(f"   Cache hit (research): {candidate.full_name}")
                            continue
                    except Exception:
                        pass
                to_research.append((i, candidate))

            # Research uncached candidates
            if to_research:
                print(f"   Researching {len(to_research)} candidates via Claude Agent Team...")
                candidate_dicts = [
                    {
                        "full_name": c.full_name,
                        "current_title": c.current_title,
                        "current_company": c.current_company,
                        "linkedin_url": c.linkedin_url,
                        "location": c.location,
                    }
                    for _, c in to_research
                ]

                results = await orchestrator.research_candidates(
                    candidate_dicts, role_title, required_skills, top_n=len(candidate_dicts)
                )

                for (idx, candidate), result in zip(to_research, results):
                    result_dict = result.model_dump()
                    candidate.deep_research = result_dict

                    # Extract highlights from findings
                    for finding in result.findings:
                        if finding.verified and finding.confidence >= 0.7:
                            candidate.research_highlights.append(
                                f"🔬 {finding.category.title()}: {finding.title}"
                            )

                    if result.identity_confidence >= 0.7:
                        candidate.confidence = max(candidate.confidence, result.identity_confidence)

                    # Store in cache
                    if candidate.linkedin_url:
                        try:
                            await company_db.update_external_candidate_research(
                                linkedin_url=candidate.linkedin_url,
                                research_data=result_dict,
                                research_confidence=result.identity_confidence,
                            )
                        except Exception as e:
                            logger.warning("Failed to cache research for %s: %s", candidate.full_name, e)

            # Apply cached research
            for idx, cached in cached_indices.items():
                candidate = candidates[idx]
                candidate.deep_research = cached["research_data"]
                candidate.confidence = max(candidate.confidence, cached.get("research_confidence", 0.5))

                # Re-extract highlights from cached findings
                for finding in cached["research_data"].get("findings", []):
                    if finding.get("verified") and finding.get("confidence", 0) >= 0.7:
                        candidate.research_highlights.append(
                            f"🔬 {finding.get('category', 'unknown').title()}: {finding.get('title', '')}"
                        )

        except Exception as e:
            print(f"   Claude research error: {e}")
            logger.exception("Claude research agent team failed")

        return candidates

    async def _deep_research_perplexity(
        self,
        candidates: list[Candidate],
        role_title: str,
        required_skills: list[str],
        top_n: int = 3
    ) -> list[Candidate]:
        """Fallback deep research using Perplexity."""
        try:
            from app.services.research.perplexity_researcher import DeepResearchEngine

            engine = DeepResearchEngine(settings.perplexity_api_key)

            for i, candidate in enumerate(candidates[:top_n]):
                print(f"   Researching {i+1}/{top_n}: {candidate.full_name} (Perplexity)...")

                class SimpleCandidate:
                    def __init__(self, c):
                        self.full_name = c.full_name
                        self.current_title = c.current_title
                        self.current_company = c.current_company
                        self.linkedin_url = c.linkedin_url
                        self.location = c.location

                insights = await engine.researcher.research_candidate(
                    SimpleCandidate(candidate),
                    role_title,
                    required_skills
                )

                candidate.deep_research = insights

                raw = insights.get("raw_research", "")
                if "github" in raw.lower():
                    candidate.research_highlights.append("🔬 GitHub profile found")
                if any(skill.lower() in raw.lower() for skill in required_skills[:3]):
                    candidate.research_highlights.append("🔬 Relevant skills confirmed")

        except Exception as e:
            print(f"   Perplexity research error: {e}")

        return candidates

    def _build_context(
        self,
        candidates: list[Candidate],
        role_title: str,
        required_skills: list[str]
    ) -> list[Candidate]:
        """Build why_consider and unknowns for each candidate."""

        for c in candidates:
            why = []
            unknowns = []

            # Why consider
            if c.is_from_network:
                why.append("✓ Direct connection in your network")

            if c.warm_path:
                connector = c.warm_path.connector
                connector_info = connector.full_name
                if connector.current_title and connector.current_company:
                    connector_info += f" ({connector.current_title} @ {connector.current_company})"
                elif connector.current_company:
                    connector_info += f" @ {connector.current_company}"
                quality_pct = f" | Quality: {c.warm_path.connector_quality:.2f}" if c.warm_path.connector_quality else ""
                why.append(f"🤝 Warm intro via {connector_info}: {c.warm_path.relationship}{quality_pct}")
                if c.warm_path.quality_signals:
                    why.append(f"   Signals: {', '.join(c.warm_path.quality_signals)}")
                if connector.linkedin_url:
                    why.append(f"🔗 Connector LinkedIn: {connector.linkedin_url}")

            if c.fit_score >= 80:
                why.append(f"💪 Strong fit ({c.fit_score:.0f}% match)")
            elif c.fit_score >= 50:
                why.append(f"✓ Good fit ({c.fit_score:.0f}% match)")

            if c.timing_urgency == "high":
                why.append("⚡ High urgency - may be ready to move")

            if c.research_highlights:
                why.extend(c.research_highlights)

            # Unknowns
            if not c.skills:
                unknowns.append("Skills not verified")
            if not c.experience:
                unknowns.append("Work history not available")
            if c.confidence < 0.5:
                unknowns.append("Limited data - needs verification")

            c.why_consider = why or ["Matches search criteria"]
            c.unknowns = unknowns or ["None identified"]

        return candidates


# =============================================================================
# SINGLETON
# =============================================================================

unified_search = UnifiedSearchEngine()
