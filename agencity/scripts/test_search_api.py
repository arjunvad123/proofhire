#!/usr/bin/env python3
"""Test the search API endpoint."""

import httpx
import json

blueprint = {
    "role_title": "Prompt Engineer",
    "company_context": "AI startup building LLM applications",
    "specific_work": "Build and optimize LLM prompts, RAG systems",
    "success_criteria": "Ship production RAG system in 60 days",
    "must_haves": ["LLM", "Python", "RAG"],
    "nice_to_haves": ["LangChain", "FastAPI", "TypeScript"],
    "location_preferences": ["Waterloo", "Remote"],
}

response = httpx.post(
    "http://localhost:8001/api/shortlists/search",
    json={"blueprint": blueprint},
    timeout=60.0,
)

print(f"Status: {response.status_code}")
print()

if response.status_code == 200:
    data = response.json()
    print(f"Sources searched: {data['sources_searched']}")
    print(f"Total searched: {data['total_searched']}")
    print(f"Candidates found: {len(data['candidates'])}")
    print()

    for i, c in enumerate(data["candidates"], 1):
        print(f"{'='*60}")
        print(f"#{i} {c['name']}")
        print(f"   {c['tagline']}")
        print()
        print("   KNOWN FACTS:")
        for f in c["known_facts"]:
            print(f"   - {f}")
        print()
        print("   OBSERVED SIGNALS:")
        for s in c["observed_signals"]:
            print(f"   - {s}")
        print()
        print("   UNKNOWN:")
        for u in c["unknown"]:
            print(f"   - {u}")
        print()
        print(f"   WHY CONSIDER: {c['why_consider'][:150]}...")
        print()
        print(f"   NEXT STEP: {c['next_step'][:150]}...")
        print()
else:
    print(f"Error: {response.text}")
