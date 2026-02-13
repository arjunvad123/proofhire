#!/usr/bin/env python3
"""Find Waterloo candidates."""

import asyncio
import sys
sys.path.insert(0, "/Users/arjunvad/Desktop/proofhire/agencity")

from app.services.supabase import supabase


async def main():
    # Get candidates from Waterloo
    print("=== Waterloo candidates with GitHub ===")
    results = await supabase.search_candidates("Waterloo", limit=20)
    waterloo = [r for r in results if r.get("github_username")]

    print(f"Found {len(waterloo)} Waterloo candidates with GitHub:\n")
    for r in waterloo:
        skills = (r.get("skills") or "")[:80]
        print(f"  - {r.get('name')} (@{r.get('github_username')})")
        print(f"    Skills: {skills}...")
        print()


if __name__ == "__main__":
    asyncio.run(main())
