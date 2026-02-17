#!/usr/bin/env python3
"""
Test script for regenerating AI summaries.

Usage:
    python test_regenerate_summary.py <person_id> <role_id>

Example:
    python test_regenerate_summary.py "abc-123" "role-456"
"""

import sys
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"


async def regenerate_summary(person_id: str, role_id: str):
    """Call the regenerate summary endpoint."""
    url = f"{BASE_URL}/v1/curation/candidate/{person_id}/regenerate-summary"
    params = {"role_id": role_id}

    print(f"Regenerating AI summary for candidate {person_id}...")
    print(f"URL: {url}")
    print(f"Role: {role_id}\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, params=params)
            response.raise_for_status()

            result = response.json()

            print("✅ SUCCESS!\n")
            print(f"Candidate: {result['full_name']}")
            print(f"Status: {result['status']}\n")

            ai_summary = result['ai_summary']

            print("=" * 80)
            print("AI SUMMARY")
            print("=" * 80)

            print("\n📊 Overall Assessment:")
            print(f"   {ai_summary['overall_assessment']}\n")

            print("✅ Why Consider:")
            for i, point in enumerate(ai_summary['why_consider'], 1):
                print(f"   {i}. {point}")

            print("\n⚠️  Concerns:")
            for i, concern in enumerate(ai_summary['concerns'], 1):
                print(f"   {i}. {concern}")

            print("\n❓ Unknowns:")
            for i, unknown in enumerate(ai_summary['unknowns'], 1):
                print(f"   {i}. {unknown}")

            print("\n" + "=" * 80)
            print("DETAILED REASONING")
            print("=" * 80)

            print("\n🔧 Skills:")
            print(f"   {ai_summary['skill_reasoning']}")

            print("\n📈 Trajectory:")
            print(f"   {ai_summary['trajectory_reasoning']}")

            print("\n🎯 Fit:")
            print(f"   {ai_summary['fit_reasoning']}")

            print("\n⏰ Timing:")
            print(f"   {ai_summary['timing_reasoning']}")

            print("\n" + "=" * 80)

            # Save to file
            output_file = f"ai_summary_{person_id}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Full response saved to: {output_file}")

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error {e.response.status_code}")
            print(f"Response: {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python test_regenerate_summary.py <person_id> <role_id>")
        print("\nExample:")
        print("  python test_regenerate_summary.py 'abc-123' 'role-456'")
        sys.exit(1)

    person_id = sys.argv[1]
    role_id = sys.argv[2]

    asyncio.run(regenerate_summary(person_id, role_id))


if __name__ == "__main__":
    main()
