#!/usr/bin/env python3
"""Debug the scoring to understand why Rohan isn't at the top."""

import asyncio
import sys
sys.path.insert(0, "/Users/arjunvad/Desktop/proofhire/agencity")

from app.services.supabase import supabase


async def main():
    # Get all candidates with GitHub from network
    all_candidates = []

    # Search for specific terms
    for term in ["langchain", "langgraph", "rag", "llm", "waterloo"]:
        results = await supabase.search_candidates(term, limit=20)
        all_candidates.extend(results)

    # Get candidates with GitHub
    github_candidates = await supabase.get_candidates(limit=50, with_github=True)
    all_candidates.extend(github_candidates)

    # Dedupe
    seen = set()
    unique = []
    for c in all_candidates:
        if c["id"] not in seen:
            seen.add(c["id"])
            unique.append(c)

    print(f"Total unique candidates: {len(unique)}\n")

    # Score each candidate
    ai_terms = ["langchain", "langgraph", "rag", "llm", "openai", "gpt", "anthropic",
                "prompt engineering", "vector", "embedding", "pytorch", "tensorflow"]
    location_prefs = ["waterloo", "remote"]

    scored = []
    for c in unique:
        score = 0
        skills = (c.get("skills") or "").lower()
        projects = (c.get("technical_projects") or "").lower()
        experience = (c.get("experience") or "").lower()
        combined = skills + " " + projects + " " + experience

        score_breakdown = []

        # AI terms
        for term in ai_terms:
            if term in combined:
                score += 20
                score_breakdown.append(f"+20 ({term})")

        # Location
        university = (c.get("university") or "").lower()
        location = (c.get("location") or "").lower()
        for pref in location_prefs:
            if pref in university or pref in location:
                score += 25
                score_breakdown.append(f"+25 (location: {pref})")

        # GitHub
        if c.get("github_username"):
            score += 10
            score_breakdown.append("+10 (github)")

        scored.append((score, c, score_breakdown))

    # Sort and show top 15
    scored.sort(key=lambda x: x[0], reverse=True)

    print("TOP 15 CANDIDATES BY SCORE:\n")
    for i, (score, c, breakdown) in enumerate(scored[:15], 1):
        print(f"{i}. {c.get('name')} - Score: {score}")
        print(f"   School: {c.get('university')}")
        print(f"   GitHub: @{c.get('github_username')}")
        print(f"   Breakdown: {', '.join(breakdown[:5])}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
