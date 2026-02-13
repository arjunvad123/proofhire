#!/usr/bin/env python3
"""Find Rohan in the database."""

import asyncio
import sys
sys.path.insert(0, "/Users/arjunvad/Desktop/proofhire/agencity")

from app.services.supabase import supabase


async def main():
    # Search for Rohan by name
    results = await supabase.search_candidates("Rohan", limit=10)
    print(f"Found {len(results)} candidates named 'Rohan'")
    for r in results:
        print(f"  - {r.get('name')} ({r.get('university')}) - @{r.get('github_username')}")
        skills = (r.get("skills") or "")[:100]
        print(f"    Skills: {skills}...")
        projects = (r.get("technical_projects") or "")[:100]
        print(f"    Projects: {projects}...")
        print()

    # Also search for key AI terms
    print("\n=== Searching for 'langchain langgraph' ===")
    results = await supabase.search_candidates("langgraph", limit=5)
    for r in results:
        print(f"  - {r.get('name')} ({r.get('university')}) - @{r.get('github_username')}")


if __name__ == "__main__":
    asyncio.run(main())
