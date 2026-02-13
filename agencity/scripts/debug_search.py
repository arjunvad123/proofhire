#!/usr/bin/env python3
"""Debug the search to see what NetworkSource returns."""

import asyncio
import sys
sys.path.insert(0, "/Users/arjunvad/Desktop/proofhire/agencity")

from app.sources.network import NetworkSource
from app.models.blueprint import RoleBlueprint


async def main():
    blueprint = RoleBlueprint(
        role_title="Prompt Engineer",
        company_context="AI startup building LLM applications",
        specific_work="Build and optimize LLM prompts, RAG systems",
        success_criteria="Ship production RAG system in 60 days",
        must_haves=["LLM", "Python", "RAG"],
        nice_to_haves=["LangChain", "FastAPI", "TypeScript"],
        location_preferences=["Waterloo", "Remote"],
    )

    source = NetworkSource()
    candidates = await source.search(blueprint, limit=10)

    print(f"NetworkSource returned {len(candidates)} candidates:\n")
    for i, c in enumerate(candidates, 1):
        print(f"{i}. {c.name}")
        print(f"   School: {c.school}")
        print(f"   GitHub: @{c.github_username}")
        skills_str = ", ".join(c.skills[:5]) if c.skills else "N/A"
        print(f"   Skills: {skills_str}")
        if c.github_repos:
            repos = [(r.name, r.stars) for r in c.github_repos[:3]]
            print(f"   Repos: {repos}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
