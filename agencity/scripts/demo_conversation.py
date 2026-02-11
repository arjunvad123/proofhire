#!/usr/bin/env python3
"""
Full demo conversation flow.
Simulates a founder looking for a prompt engineer.
"""

import httpx
import time

BASE_URL = "http://localhost:8001/api"


def demo():
    """Run the full demo conversation."""
    print("="*70)
    print("AGENCITY DEMO: Finding a Prompt Engineer")
    print("="*70)
    print()

    # Step 1: Start conversation
    print("FOUNDER: Starting conversation...")
    response = httpx.post(
        f"{BASE_URL}/conversations",
        json={
            "user_id": "demo-founder-1",
            "initial_message": "I need a prompt engineer for my AI startup"
        },
        timeout=60.0,
    )

    data = response.json()
    conversation_id = data["id"]
    print(f"\nAGENCITY: {data['message']}")
    print(f"\n[Status: {data['status']}]")
    print()

    # Step 2: Answer follow-up questions
    responses = [
        "We're building an AI tutoring platform for college students. We use LLMs to generate personalized study plans.",
        "This person will build and optimize our RAG pipeline. They'll work on prompt engineering, context management, and evaluation.",
        "By day 60, they should have shipped our core RAG system that can answer questions about course materials accurately.",
        "We had a great hire who could ship fast and iterate based on feedback. Bad hires got stuck in analysis paralysis.",
        "Waterloo or remote. We love Waterloo grads.",
    ]

    for i, response_text in enumerate(responses):
        print(f"FOUNDER: {response_text}")
        print()

        response = httpx.post(
            f"{BASE_URL}/conversations/{conversation_id}/message",
            json={"content": response_text},
            timeout=120.0,
        )

        data = response.json()
        print(f"AGENCITY: {data['message']}")
        print(f"\n[Status: {data['status']}]")

        if data.get("blueprint"):
            print("\n[BLUEPRINT EXTRACTED]")
            bp = data["blueprint"]
            print(f"  Role: {bp.get('role_title')}")
            print(f"  Must-haves: {bp.get('must_haves')}")
            print(f"  Nice-to-haves: {bp.get('nice_to_haves')}")
            break

        print()
        time.sleep(1)

    # Step 3: Trigger search with blueprint
    if data.get("blueprint"):
        print()
        print("="*70)
        print("SEARCHING FOR CANDIDATES...")
        print("="*70)
        print()

        search_response = httpx.post(
            f"{BASE_URL}/shortlists/search",
            json={"blueprint": data["blueprint"]},
            timeout=120.0,
        )

        shortlist = search_response.json()

        print(f"Sources searched: {shortlist['sources_searched']}")
        print(f"Total candidates found: {shortlist['total_searched']}")
        print(f"Returning top {len(shortlist['candidates'])} candidates")
        print()

        for i, c in enumerate(shortlist["candidates"], 1):
            print("="*70)
            print(f"CANDIDATE #{i}: {c['name']}")
            print(f"             {c['tagline']}")
            print("="*70)
            print()

            print("KNOWN FACTS:")
            for f in c["known_facts"]:
                print(f"  ✓ {f}")
            print()

            print("OBSERVED SIGNALS:")
            for s in c["observed_signals"]:
                print(f"  → {s}")
            print()

            print("UNKNOWN (verify in conversation):")
            for u in c["unknown"]:
                print(f"  ? {u}")
            print()

            print("WHY CONSIDER:")
            print(f"  {c['why_consider']}")
            print()

            print("SUGGESTED NEXT STEP:")
            print(f"  {c['next_step']}")
            print()

    print()
    print("="*70)
    print("DEMO COMPLETE")
    print("="*70)


if __name__ == "__main__":
    demo()
