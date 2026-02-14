#!/usr/bin/env python3
"""
Test Agencity integration endpoints with existing Confido data.

This script demonstrates the end-to-end flow using real data from Supabase.
"""

import os
import sys
import requests
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configuration
AGENCITY_API_URL = "http://localhost:8001/api"
CONFIDO_COMPANY_ID = "100b5ac1-1912-4970-a378-04d0169fd597"


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def test_pipeline_endpoint():
    """Test the pipeline endpoint with existing Confido data."""
    print_section("1. Testing Pipeline Endpoint")

    url = f"{AGENCITY_API_URL}/pipeline/{CONFIDO_COMPANY_ID}"
    params = {
        "status": "all",
        "sort": "score",
        "limit": 10
    }

    print(f"GET {url}")
    print(f"Params: {params}\n")

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Found {data['total']} candidates")
        print(f"\nStatus breakdown:")
        for status, count in data['by_status'].items():
            print(f"  - {status}: {count}")

        if data['candidates']:
            print(f"\nFirst candidate:")
            candidate = data['candidates'][0]
            print(f"  Name: {candidate['name']}")
            print(f"  Title: {candidate.get('title', 'N/A')}")
            print(f"  Company: {candidate.get('company', 'N/A')}")
            print(f"  Warmth Level: {candidate['warmth_level']}")
            print(f"  Status: {candidate['status']}")

        return data['candidates'][:3] if data['candidates'] else []
    else:
        print(f"❌ FAILED! Status: {response.status_code}")
        print(f"Error: {response.text}")
        return []


def test_create_linkage(candidate_id: str):
    """Test creating a linkage."""
    print_section("2. Testing Create Linkage")

    url = f"{AGENCITY_API_URL}/linkages"
    payload = {
        "company_id": CONFIDO_COMPANY_ID,
        "agencity_candidate_id": candidate_id,
        "proofhire_application_id": f"pf-app-demo-{candidate_id[:8]}",
        "proofhire_role_id": "pf-role-001-demo"
    }

    print(f"POST {url}")
    print(f"Payload: {payload}\n")

    response = requests.post(url, json=payload)

    if response.status_code == 201:
        data = response.json()
        print(f"✅ SUCCESS! Created linkage")
        print(f"  Linkage ID: {data['id']}")
        print(f"  Status: {data['status']}")
        print(f"  Created: {data['created_at']}")
        return data
    elif response.status_code == 409:
        print(f"⚠️  Linkage already exists")
        # Try to get the existing linkage
        get_url = f"{AGENCITY_API_URL}/linkages/candidate/{candidate_id}"
        get_response = requests.get(get_url)
        if get_response.status_code == 200:
            return get_response.json()
    else:
        print(f"❌ FAILED! Status: {response.status_code}")
        print(f"Error: {response.text}")

    return None


def test_update_linkage(linkage_id: str):
    """Test updating a linkage status."""
    print_section("3. Testing Update Linkage")

    url = f"{AGENCITY_API_URL}/linkages/{linkage_id}"
    payload = {
        "status": "simulation_complete"
    }

    print(f"PATCH {url}")
    print(f"Payload: {payload}\n")

    response = requests.patch(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Updated linkage")
        print(f"  New Status: {data['status']}")
        print(f"  Updated: {data['updated_at']}")
        return data
    else:
        print(f"❌ FAILED! Status: {response.status_code}")
        print(f"Error: {response.text}")
        return None


def test_record_feedback(candidate_id: str):
    """Test recording feedback."""
    print_section("4. Testing Record Feedback")

    url = f"{AGENCITY_API_URL}/feedback/action"
    payload = {
        "company_id": CONFIDO_COMPANY_ID,
        "candidate_id": candidate_id,
        "action": "interviewed",
        "proofhire_score": 85,
        "proofhire_application_id": f"pf-app-demo-{candidate_id[:8]}",
        "notes": "Strong technical skills, good culture fit"
    }

    print(f"POST {url}")
    print(f"Payload: {payload}\n")

    response = requests.post(url, json=payload)

    if response.status_code == 201:
        data = response.json()
        print(f"✅ SUCCESS! Recorded feedback")
        print(f"  Feedback ID: {data['id']}")
        print(f"  Action: {data['action']}")
        return data
    else:
        print(f"❌ FAILED! Status: {response.status_code}")
        print(f"Error: {response.text}")
        return None


def test_feedback_stats():
    """Test getting feedback stats."""
    print_section("5. Testing Feedback Stats")

    url = f"{AGENCITY_API_URL}/feedback/stats/{CONFIDO_COMPANY_ID}"

    print(f"GET {url}\n")

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Got feedback stats")
        print(f"  Total Feedback: {data['total_feedback']}")
        print(f"\n  By Action:")
        for action, count in data['by_action'].items():
            print(f"    - {action}: {count}")

        proofhire = data['proofhire_integration']
        print(f"\n  ProofHire Integration:")
        print(f"    - Total Invited: {proofhire['total_invited']}")
        print(f"    - Total Completed: {proofhire['total_completed']}")
        print(f"    - Completion Rate: {proofhire['completion_rate']:.2%}")
        if proofhire['avg_score']:
            print(f"    - Avg Score: {proofhire['avg_score']:.1f}")

        return data
    else:
        print(f"❌ FAILED! Status: {response.status_code}")
        print(f"Error: {response.text}")
        return None


def main():
    """Run all integration tests."""
    print_section("AGENCITY INTEGRATION API TESTS")
    print(f"Testing with Confido company: {CONFIDO_COMPANY_ID}")
    print(f"API Base URL: {AGENCITY_API_URL}")

    # Test 1: Get pipeline
    candidates = test_pipeline_endpoint()

    if not candidates:
        print("\n⚠️  No candidates found. Cannot continue with linkage tests.")
        return

    # Use first candidate for linkage tests
    test_candidate = candidates[0]
    candidate_id = test_candidate['id']

    print(f"\nUsing candidate for linkage tests:")
    print(f"  Name: {test_candidate['name']}")
    print(f"  ID: {candidate_id}")

    # Test 2: Create linkage
    linkage = test_create_linkage(candidate_id)

    if linkage:
        # Test 3: Update linkage
        test_update_linkage(linkage['id'])

        # Test 4: Record feedback
        test_record_feedback(candidate_id)

    # Test 5: Get feedback stats
    test_feedback_stats()

    print_section("TESTS COMPLETE")
    print("✅ All integration endpoints are working!")
    print("\nNext steps:")
    print("  1. View pipeline in dashboard: http://localhost:3001/dashboard/pipeline")
    print("  2. Click 'Invite to ProofHire' to test the full flow")
    print("  3. View briefs when simulations complete")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
