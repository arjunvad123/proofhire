"""End-to-end search test — runs the full unified pipeline."""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from app.services.unified_search import unified_search


async def run():
    result = await unified_search.search(
        company_id="100b5ac1-1912-4970-a378-04d0169fd597",
        role_title="Founding Engineer",
        required_skills=["Python", "React", "TypeScript"],
        preferred_skills=["FastAPI", "Next.js"],
        location="San Francisco",
        include_external=True,
        include_timing=True,
        deep_research=False,  # skip perplexity for now
        limit=15,
    )

    print("\n" + "=" * 80)
    print("SEARCH RESULTS")
    print("=" * 80)
    print(f"Duration: {result.search_duration_seconds}s")
    print(f"Network size: {result.network_size} contacts, {result.network_companies} companies")
    print(f"Total found: {result.total_found}")
    print(f"Tier 1 (network): {result.tier_1_count}")
    print(f"Tier 2 (warm external): {result.tier_2_count}")
    print(f"Tier 3 (cold external): {result.tier_3_count}")
    print(f"High urgency: {result.high_urgency_count}")

    print("\n--- Provider Stats ---")
    print(json.dumps(result.external_provider_stats, indent=2))
    print("\n--- Provider Health ---")
    print(json.dumps(result.external_provider_health, indent=2))
    if result.external_diagnostics:
        print("\n--- Diagnostics ---")
        for d in result.external_diagnostics:
            print(f"  ! {d}")

    print("\n--- TOP CANDIDATES ---")
    for i, c in enumerate(result.candidates[:15]):
        print(f"\n#{i+1} [Tier {c.tier}] {c.full_name}")
        print(f"   Title: {c.current_title} @ {c.current_company}")
        print(f"   Location: {c.location}")
        print(f"   LinkedIn: {c.linkedin_url}")
        print(f"   Skills: {c.skills[:6]}")
        print(
            f"   Scores: fit={c.fit_score:.0f} warmth={c.warmth_score:.0f} "
            f"timing={c.timing_score:.0f} COMBINED={c.combined_score:.1f}"
        )
        print(f"   Source: {c.source} | Urgency: {c.timing_urgency} | Confidence: {c.confidence}")
        if c.warm_path:
            print(
                f"   Warm Path: {c.warm_path.path_type} via "
                f"{c.warm_path.connector.full_name} ({c.warm_path.relationship})"
            )
        print(f"   Why: {c.why_consider[:2]}")
        if c.unknowns and c.unknowns != ["None identified"]:
            print(f"   Unknowns: {c.unknowns}")


if __name__ == "__main__":
    asyncio.run(run())
