#!/usr/bin/env python3
"""
Test script to verify Supabase connection and data retrieval.
"""

import asyncio
import sys
sys.path.insert(0, "/Users/arjunvad/Desktop/proofhire/agencity")

from app.services.supabase import supabase
from app.sources.network import NetworkSource
from app.models.blueprint import RoleBlueprint


async def test_supabase_connection():
    """Test basic Supabase connectivity."""
    print("=== Testing Supabase Connection ===\n")

    # Test 1: Get candidates
    print("1. Getting candidates...")
    candidates = await supabase.get_candidates(limit=3)
    print(f"   Found {len(candidates)} candidates")
    if candidates:
        print(f"   First candidate: {candidates[0].get('name')} ({candidates[0].get('university')})")

    # Test 2: Get candidates with GitHub
    print("\n2. Getting candidates with GitHub...")
    github_candidates = await supabase.get_candidates(limit=3, with_github=True)
    print(f"   Found {len(github_candidates)} candidates with GitHub")
    if github_candidates:
        c = github_candidates[0]
        print(f"   First: {c.get('name')} - @{c.get('github_username')}")

    # Test 3: Search candidates
    print("\n3. Searching for 'langchain'...")
    search_results = await supabase.search_candidates("langchain", limit=3)
    print(f"   Found {len(search_results)} results")
    for r in search_results:
        print(f"   - {r.get('name')} ({r.get('university')})")

    # Test 4: Get demo candidates
    print("\n4. Getting top demo candidates...")
    demo = await supabase.get_top_candidates_for_demo(limit=5)
    print(f"   Found {len(demo)} demo candidates")
    for d in demo:
        repos = d.get("github_repos", [])
        stars = sum(r.get("stargazers_count", 0) for r in repos)
        print(f"   - {d.get('name')} ({d.get('university')}) - {stars} total stars")


async def test_network_source():
    """Test NetworkSource integration."""
    print("\n\n=== Testing NetworkSource ===\n")

    source = NetworkSource()

    # Test 1: Is available
    print("1. Checking availability...")
    available = await source.is_available()
    print(f"   Available: {available}")

    # Test 2: Search with blueprint
    print("\n2. Searching for 'prompt engineer'...")
    blueprint = RoleBlueprint(
        role_title="Prompt Engineer",
        company_context="AI startup building LLM applications",
        specific_work="Build and optimize LLM prompts, RAG systems",
        success_criteria="Ship production RAG system in 60 days",
        must_haves=["LLM", "Python", "RAG"],
        nice_to_haves=["LangChain", "FastAPI", "TypeScript"],
        location_preferences=["Waterloo", "Remote"],
    )

    candidates = await source.search(blueprint, limit=5)
    print(f"   Found {len(candidates)} candidates")

    for c in candidates:
        print(f"\n   {c.name}")
        print(f"   - School: {c.school}")
        print(f"   - GitHub: @{c.github_username}")
        print(f"   - Skills: {', '.join(c.skills[:5])}...")
        if c.github_repos:
            print(f"   - Top repo: {c.github_repos[0].name} ({c.github_repos[0].stars} stars)")

    # Test 3: Get demo candidates
    print("\n3. Getting demo candidates...")
    demo = await source.get_demo_candidates(limit=3)
    print(f"   Found {len(demo)} demo candidates")


async def main():
    """Run all tests."""
    try:
        await test_supabase_connection()
        await test_network_source()
        print("\n\n✅ All tests passed!")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
