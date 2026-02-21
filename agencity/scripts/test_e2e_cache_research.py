"""
E2E test for the unified search pipeline with cache + research agent team.

Conservative on API usage:
- Single search (no redundant second search — cache is verified inline)
- Deep research only if explicitly requested via --research flag
- Clado enrichment capped at 3 candidates
- Limit results to 10

Usage:
    python scripts/test_e2e_cache_research.py              # search only (no deep research)
    python scripts/test_e2e_cache_research.py --research    # search + deep research on top 3
"""

import argparse
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


def print_candidates(candidates, max_show=10):
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


async def test_search(run_research: bool = False):
    """Single search with optional deep research."""
    print("=" * 80)
    print(f"SEARCH {'+ RESEARCH ' if run_research else ''}(conservative mode)")
    print("=" * 80)
    print()

    result = await unified_search.search(
        company_id=COMPANY_ID,
        role_title=ROLE_TITLE,
        required_skills=REQUIRED_SKILLS,
        preferred_skills=PREFERRED_SKILLS,
        include_external=True,
        include_timing=True,
        deep_research=run_research,
        limit=10,
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

    print(f"--- TOP {min(10, len(result.candidates))} CANDIDATES ---")
    print_candidates(result.candidates)

    # --- Inline cache verification (no extra API calls) ---
    ext_urls = [
        c.linkedin_url
        for c in result.candidates
        if c.linkedin_url and c.source == "external"
    ]

    if ext_urls:
        print("--- CACHE CHECK ---")
        cached = await company_db.get_cached_external_candidates(ext_urls, max_age_days=1)
        print(f"  External with LinkedIn URLs: {len(ext_urls)}")
        print(f"  Cache hits: {len(cached)} / {len(ext_urls)}")
        if len(cached) == len(ext_urls):
            print(f"  PASS: All cached")
        else:
            print(f"  PARTIAL: {len(ext_urls) - len(cached)} not in cache")
        print()

    # --- Research details (only if run_research was True) ---
    if run_research:
        print("--- RESEARCH DETAILS ---")
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
    parser = argparse.ArgumentParser(description="E2E search test (conservative API usage)")
    parser.add_argument("--research", action="store_true", help="Run deep research on top 3")
    args = parser.parse_args()

    print()
    print("ProofHire E2E Search Test")
    print(f"Company: Confido ({COMPANY_ID})")
    print(f"Role: {ROLE_TITLE}")
    print(f"Skills: {REQUIRED_SKILLS}")
    print(f"Research: {'ON' if args.research else 'OFF (use --research to enable)'}")
    print()

    await test_search(run_research=args.research)

    print("=" * 80)
    print("DONE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
