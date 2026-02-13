#!/usr/bin/env python3
"""
Test search API with Greptile's exact requirements.
"""

import httpx
import json

# The blueprint derived from the Greptile JD
blueprint = {
    # Core Identity
    "role_title": "Software Engineer (Generalist)",
    "company_context": "Greptile (W24) - AI code review agent. Small, tight-knit, in-person SF team. High chaos, high growth.",
    
    # What they actually do
    "specific_work": "Build agents that autonomously validate code changes. Solve hard problems: LLM memory, multi-language indexing, semantic search.",
    "success_criteria": "Ship features end-to-end. Catch bugs in thousands of repos. Thrive in chaos.",
    
    # Requirements
    "must_haves": [
        "1+ years experience",
        "TypeScript",
        "Node.js",
        "AWS (ECS/Lambda)",
        "Postgres",
        "NextJS",
        "In-person SF (US citizen/visa)"
    ],
    
    "nice_to_haves": [
        "LLM applied experience",
        "Semantic search / Embeddings",
        "DevOps experience",
        "B.S. CS degree"
    ],
    
    "avoid": [
        "Remote-only candidates",
        "Consultants/agencies",
        "Pure frontend devs (need full stack/backend depth)"
    ],
    
    "location_preferences": ["San Francisco"],
    
    # Calibration
    "calibration_examples": [
        "Ideal: Someone who scaled systems at Stripe/Figma but wants earlier stage chaos.",
        "Ideal: Strong generalist, moves extremely fast."
    ]
}

print("Searching with Greptile blueprint...")
print("-" * 60)
print(json.dumps(blueprint, indent=2))
print("-" * 60)

try:
    response = httpx.post(
        "http://localhost:8001/api/shortli1sts/search",
        json={"blueprint": blueprint},
        timeout=60.0,
    )

    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        
        # Handle response format (SearchResponse vs Shortlist)
        candidates = data.get("candidates", [])
        
        print(f"\nFound {len(candidates)} candidates matching criteria:\n")

        for i, item in enumerate(candidates, 1):
            c = item.get("candidate", {})
            eval_data = item
            
            print(f"{'='*60}")
            print(f"#{i} {c.get('name', 'Unknown')}")
            print(f"   {c.get('current_title', '')} @ {c.get('current_company', '')}")
            print(f"   Relevance: {eval_data.get('relevance_score', 0):.2f}")
            print()
            
            print("   WHY CONSIDER:")
            print(f"   {eval_data.get('why_consider', 'N/A')}")
            print()
            
            print("   OBSERVED SIGNALS:")
            for s in eval_data.get("observed_signals", []):
                print(f"   - {s}")
            print()
            
            print("   UNKNOWN (To Verify):")
            for u in eval_data.get("unknown", []):
                print(f"   - {u}")
            print()
    else:
        print(f"Error: {response.text}")

except httpx.ConnectError:
    print("\nError: Could not connect to backend at http://localhost:8001")
    print("Make sure the server is running:\ncd proofhire/agencity && uvicorn app.main:app --port 8001")
except Exception as e:
    print(f"\nError: {e}")
