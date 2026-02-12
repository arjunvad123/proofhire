#!/usr/bin/env python3
"""
Search Confido's LinkedIn network (people table) for candidates.

This searches the company-specific `people` table, not the global `candidates` table.
"""

import asyncio
import httpx
from app.config import settings

# Confido's company ID
COMPANY_ID = "100b5ac1-1912-4970-a378-04d0169fd597"

# Search criteria from Greptile JD
SEARCH_KEYWORDS = [
    "typescript", "node", "nodejs", "aws", "lambda", "postgres",
    "nextjs", "software engineer", "full stack", "backend"
]


async def search_people_network():
    """Search the people table for candidates matching Greptile's needs."""

    url = f'{settings.supabase_url}/rest/v1/people'
    headers = {
        'apikey': settings.supabase_key,
        'Authorization': f'Bearer {settings.supabase_key}',
    }

    # Get all people for this company
    params = {
        'company_id': f'eq.{COMPANY_ID}',
        'limit': 100,  # Increase to get more results
        'select': 'id,full_name,current_title,current_company,email,linkedin_url,headline,location'
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=30.0)
        people = response.json()

        print(f"Searching Confido's network of {len(people)} people...")
        print("=" * 80)
        print()

        # Simple keyword matching (can be enhanced)
        matches = []
        for person in people:
            score = 0
            matched_keywords = []

            # Combine all text fields
            text = " ".join([
                person.get('current_title') or '',
                person.get('current_company') or '',
                person.get('headline') or '',
            ]).lower()

            # Score based on keyword matches
            for keyword in SEARCH_KEYWORDS:
                if keyword.lower() in text:
                    score += 1
                    matched_keywords.append(keyword)

            if score > 0:
                matches.append({
                    'person': person,
                    'score': score,
                    'keywords': matched_keywords
                })

        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)

        print(f"Found {len(matches)} candidates with matching keywords\n")

        # Display top matches
        for i, match in enumerate(matches[:10], 1):
            person = match['person']
            print(f"{i}. {person.get('full_name')}")
            print(f"   {person.get('current_title')} @ {person.get('current_company')}")
            if person.get('headline'):
                print(f"   {person.get('headline')}")
            if person.get('location'):
                print(f"   Location: {person.get('location')}")
            print(f"   Match Score: {match['score']} (Keywords: {', '.join(match['keywords'])})")
            if person.get('linkedin_url'):
                print(f"   LinkedIn: {person.get('linkedin_url')}")
            print()


if __name__ == "__main__":
    asyncio.run(search_people_network())
