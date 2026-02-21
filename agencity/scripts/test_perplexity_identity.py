"""Test Perplexity identity conflation problem.

Runs deep research on the top 3 candidates to see
how Perplexity handles disambiguation.
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from app.services.research.perplexity_researcher import PerplexityResearcher
from app.config import settings


class FakeCandidate:
    def __init__(self, name, title, company, linkedin_url, location=None):
        self.full_name = name
        self.current_title = title
        self.current_company = company
        self.linkedin_url = linkedin_url
        self.location = location


async def run():
    researcher = PerplexityResearcher(settings.perplexity_api_key)

    # Test candidates — mix of common and unique names
    candidates = [
        FakeCandidate(
            "Aarush Agrawal",
            "Software Development Engineer",
            "Amazon",
            "https://www.linkedin.com/in/aarush-agrawal-",
            "San Francisco",
        ),
        FakeCandidate(
            "Frank Li",
            "Software Engineer (VIVA Glint)",
            "Microsoft",
            "https://www.linkedin.com/in/123frank",
            "Greater Toronto Area, Canada",
        ),
        FakeCandidate(
            "Minh Trinh",
            "Software Engineer",
            "Syllable AI",
            "https://www.linkedin.com/in/m-trinh",
            "San Francisco Bay Area",
        ),
    ]

    for c in candidates:
        print(f"\n{'='*80}")
        print(f"RESEARCHING: {c.full_name} ({c.current_title} @ {c.current_company})")
        print(f"LinkedIn: {c.linkedin_url}")
        print(f"Location: {c.location}")
        print("=" * 80)

        # Show the query being sent
        query = researcher._build_research_query(c, "Founding Engineer", ["Python", "React", "TypeScript"])
        print(f"\n--- QUERY SENT ---")
        print(query[:500])
        print("...")

        # Run research
        result = await researcher.research_candidate(c, "Founding Engineer", ["Python", "React", "TypeScript"])

        print(f"\n--- RAW RESPONSE ---")
        raw = result.get("raw_research", "")
        print(raw[:1500])
        if len(raw) > 1500:
            print(f"\n... ({len(raw)} total chars)")

        print(f"\n--- METADATA ---")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Method: {result.get('research_method')}")


if __name__ == "__main__":
    asyncio.run(run())
