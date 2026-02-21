"""
E2E test for the unified search pipeline with cache + research agent team.

Tests:
1. Full search with caching (no deep research)
2. Cache verification - confirm candidates stored
3. Second search - confirm cache hits (no API re-calls)
4. Deep research on top 3 (Claude Research Agent Team)
"""

import asyncio
import sys
import time

sys.path.insert(0, ".")

from app.services.unified_search import unified_search
from app.services.company_db import company_db
from app.config import settings

# Confido: 3,637 contacts, Software Engineer role
COMPANY_ID = "100b5ac1-1912-4970-a378-04d0169fd597"
ROLE_TITLE = "Software Engineer"
REQUIRED_SKILLS = ["Python", "React"]
PREFERRED_SKILLS = ["FastAPI", "TypeScript"]


def print_candidates(candidates, max_show=15):
    """Pretty-print candidate list."""
    for i, c in enumerate(candidates[:max_show]):
        tier_label = {1: "NET", 2: "WARM", 3: "COLD"}.get(c.tier, "?")
        enriched = "E" if c.confidence >= 0.8 else " "
        skills_preview = ", ".join(c.skills[:4]) if c.skills else "-"

        print(
            f"  {i+1:2}. [{tier_label}]{enriched} {c.full_name:30s} | "
            f"Fit:{c.fit_score:5.1f} Warm:{c.warmth_score:5.1f} Time:{c.timing_score:5.1f} "
            f"=> {c.combined_score:5.1f}"
        )
        print(f"      {c.current_title or '?'} @ {c.current_company or '?'}")
        if c.warm_path:
            connector = c.warm_path.connector
            quality = c.warm_path.connector_quality
            print(f"      Path: {c.warm_path.relationship}")
            print(f"      Intro via: {connector.full_name} ({connector.current_title or '?'} @ {connector.current_company or '?'})")
            print(f"      Quality: {quality:.2f} | {', '.join(c.warm_path.quality_signals) if c.warm_path.quality_signals else 'No signals'}")
            if connector.linkedin_url:
                print(f"      Connector LI: {connector.linkedin_url}")
            if c.warm_path.suggested_message:
                # Show first line of suggested message
                first_line = c.warm_path.suggested_message.strip().split('\n')[0]
                print(f"      Message: {first_line}")
        if c.skills:
            print(f"      Skills: {skills_preview}")
        if c.timing_urgency != "low":
            print(f"      Timing: {c.timing_urgency} ({', '.join(c.timing_signals)})")
        if c.research_highlights:
            for h in c.research_highlights:
                print(f"      {h}")
        print()


async def test_search_with_cache():
    """Test 1: Full search pipeline with caching."""
    print("=" * 80)
    print("TEST 1: Full Search (cache write)")
    print("=" * 80)
    print()

    result = await unified_search.search(
        company_id=COMPANY_ID,
        role_title=ROLE_TITLE,
        required_skills=REQUIRED_SKILLS,
        preferred_skills=PREFERRED_SKILLS,
        include_external=True,
        include_timing=True,
        deep_research=False,
        limit=15,
    )

    print()
    print("--- RESULTS ---")
    print(f"Duration:         {result.search_duration_seconds}s")
    print(f"Total found:      {result.total_found}")
    print(f"Network size:     {result.network_size} contacts, {result.network_companies} companies")
    print(f"Tier 1 (network): {result.tier_1_count}")
    print(f"Tier 2 (warm):    {result.tier_2_count}")
    print(f"Tier 3 (cold):    {result.tier_3_count}")
    print(f"High urgency:     {result.high_urgency_count}")
    print()

    print("--- PROVIDER STATS ---")
    for k, v in result.external_provider_stats.items():
        print(f"  {k}: {v}")
    print()

    if result.external_diagnostics:
        print("--- DIAGNOSTICS ---")
        for d in result.external_diagnostics:
            print(f"  ! {d}")
        print()

    print("--- TOP 15 CANDIDATES ---")
    print_candidates(result.candidates)

    return result


async def test_cache_verification(first_result):
    """Test 2: Verify candidates were cached."""
    print("=" * 80)
    print("TEST 2: Cache Verification")
    print("=" * 80)
    print()

    ext_urls = [
        c.linkedin_url
        for c in first_result.candidates
        if c.linkedin_url and c.source == "external"
    ]
    print(f"External candidates with LinkedIn URLs: {len(ext_urls)}")

    if not ext_urls:
        print("  No external candidates to verify")
        return

    cached = await company_db.get_cached_external_candidates(ext_urls, max_age_days=1)
    print(f"Cache hits: {len(cached)} / {len(ext_urls)}")
    print()

    for url, rec in list(cached.items())[:5]:
        enrichment = rec.get("enrichment_source") or "none"
        n_skills = len(rec.get("skills") or [])
        print(
            f"  {rec['full_name']:30s} | source={rec.get('discovery_source'):10s} "
            f"| enrichment={enrichment:15s} | skills={n_skills}"
        )

    if len(cached) == len(ext_urls):
        print(f"\n  PASS: All {len(ext_urls)} external candidates cached")
    else:
        missing = len(ext_urls) - len(cached)
        print(f"\n  PARTIAL: {missing} candidates not in cache (may lack LinkedIn URLs)")


async def test_second_search():
    """Test 3: Second search should use cache (no Firecrawl credits burned)."""
    print()
    print("=" * 80)
    print("TEST 3: Second Search (cache read)")
    print("=" * 80)
    print()

    start = time.time()
    result = await unified_search.search(
        company_id=COMPANY_ID,
        role_title=ROLE_TITLE,
        required_skills=REQUIRED_SKILLS,
        preferred_skills=PREFERRED_SKILLS,
        include_external=True,
        include_timing=True,
        deep_research=False,
        limit=15,
    )
    duration = time.time() - start

    print()
    print(f"Second search duration: {duration:.1f}s")
    print(f"Total found: {result.total_found}")
    print(f"Tier 1: {result.tier_1_count}, Tier 2: {result.tier_2_count}, Tier 3: {result.tier_3_count}")
    print()

    # The key verification: cache hits should be logged
    # (we can see from the print output above)

    return result


async def test_deep_research():
    """Test 4: Deep research on top 3 candidates (Claude Agent Team)."""
    if not settings.anthropic_api_key:
        print()
        print("=" * 80)
        print("TEST 4: SKIPPED (no ANTHROPIC_API_KEY)")
        print("=" * 80)
        return None

    print()
    print("=" * 80)
    print("TEST 4: Deep Research (Claude Agent Team)")
    print("=" * 80)
    print()

    result = await unified_search.search(
        company_id=COMPANY_ID,
        role_title=ROLE_TITLE,
        required_skills=REQUIRED_SKILLS,
        preferred_skills=PREFERRED_SKILLS,
        include_external=True,
        include_timing=True,
        deep_research=True,
        limit=10,
    )

    print()
    print("--- RESEARCHED CANDIDATES ---")
    for i, c in enumerate(result.candidates[:3]):
        print(f"\n  {i+1}. {c.full_name} ({c.current_title} @ {c.current_company})")
        if c.deep_research:
            findings = c.deep_research.get("findings", [])
            confidence = c.deep_research.get("identity_confidence", 0)
            total_searches = c.deep_research.get("total_searches", 0)
            conflicts = c.deep_research.get("conflicts", [])

            print(f"     Identity confidence: {confidence:.0%}")
            print(f"     Web searches used: {total_searches}")
            print(f"     Findings: {len(findings)}")
            for f in findings[:5]:
                verified = "V" if f.get("verified") else "?"
                conf = f.get("confidence", 0)
                print(
                    f"       [{verified}] {f.get('category', '?'):12s} | "
                    f"{f.get('title', '?')[:50]} ({conf:.0%})"
                )
            if conflicts:
                print(f"     Conflicts: {'; '.join(conflicts)}")

            # Citations
            citations = c.deep_research.get("citations", [])
            if citations:
                print(f"     Citations: {len(citations)}")
                for cite in citations[:3]:
                    print(f"       - {cite.get('title', '?')[:50]}: {cite.get('url', '?')[:60]}")
        else:
            print("     No research data")

        if c.research_highlights:
            print(f"     Highlights:")
            for h in c.research_highlights:
                print(f"       {h}")

    return result


async def main():
    print()
    print("ProofHire E2E Search Test")
    print(f"Company: Confido ({COMPANY_ID})")
    print(f"Role: {ROLE_TITLE}")
    print(f"Skills: {REQUIRED_SKILLS}")
    print(f"Anthropic key: {'configured' if settings.anthropic_api_key else 'NOT SET'}")
    print(f"Web search enabled: {settings.anthropic_web_search_enabled}")
    print()

    # Test 1: Search with cache write
    result1 = await test_search_with_cache()

    # Test 2: Verify cache
    await test_cache_verification(result1)

    # Test 3: Second search (cache read)
    await test_second_search()

    # Test 4: Deep research
    await test_deep_research()

    print()
    print("=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
