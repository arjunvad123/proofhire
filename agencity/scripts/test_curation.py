"""
Test script for candidate curation.

Usage:
    python scripts/test_curation.py <company_id> <role_id>

Example:
    python scripts/test_curation.py 100b5ac1-1912-4970-a378-04d0169fd597 role-uuid-here
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_supabase_client
from app.services.curation_engine import CandidateCurationEngine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_curation(company_id: str, role_id: str):
    """Test the curation engine."""

    print(f"\n{'='*80}")
    print(f"CANDIDATE CURATION TEST")
    print(f"{'='*80}\n")

    # Initialize engine
    supabase = get_supabase_client()
    engine = CandidateCurationEngine(supabase)

    # Run curation
    print(f"Company ID: {company_id}")
    print(f"Role ID: {role_id}")
    print(f"\nStarting curation...\n")

    shortlist = await engine.curate(
        company_id=company_id,
        role_id=role_id,
        limit=10  # Top 10 for testing
    )

    # Display results
    print(f"\n{'='*80}")
    print(f"SHORTLIST ({len(shortlist)} candidates)")
    print(f"{'='*80}\n")

    for i, candidate in enumerate(shortlist, 1):
        print(f"#{i} - {candidate.full_name}")
        print(f"{'─'*80}")
        print(f"  Match Score: {candidate.match_score:.1f}/100 (confidence: {candidate.fit_confidence:.2f})")

        if candidate.headline:
            print(f"  Headline: {candidate.headline}")
        if candidate.location:
            print(f"  Location: {candidate.location}")
        if candidate.current_title and candidate.current_company:
            print(f"  Current: {candidate.current_title} @ {candidate.current_company}")

        print(f"\n  WHY CONSIDER:")
        for section in candidate.context.why_consider:
            print(f"    {section.category} ({section.strength.upper()})")
            for point in section.points[:3]:  # Show first 3
                print(f"      {point}")

        if candidate.context.standout_signal:
            print(f"\n  ⭐ STANDOUT: {candidate.context.standout_signal}")

        print(f"\n  UNKNOWNS:")
        for unknown in candidate.context.unknowns[:3]:  # Show first 3
            print(f"    • {unknown}")

        print(f"\n  WARM PATH: {candidate.context.warm_path}")

        print(f"  Data Completeness: {candidate.data_completeness:.0%}")
        if candidate.was_enriched:
            print(f"  ℹ️  This candidate was enriched during curation")

        if candidate.linkedin_url:
            print(f"  🔗 LinkedIn: {candidate.linkedin_url}")

        print()

    # Summary stats
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total candidates curated: {len(shortlist)}")
    print(f"Average match score: {sum(c.match_score for c in shortlist) / len(shortlist):.1f}")
    print(f"Average confidence: {sum(c.fit_confidence for c in shortlist) / len(shortlist):.2f}")
    print(f"Candidates enriched: {sum(1 for c in shortlist if c.was_enriched)}")
    print(f"Average data completeness: {sum(c.data_completeness for c in shortlist) / len(shortlist):.0%}")


async def list_companies():
    """List available companies."""
    supabase = get_supabase_client()

    response = supabase.table('companies').select('id, name, people_count').execute()

    print(f"\n{'='*80}")
    print(f"AVAILABLE COMPANIES")
    print(f"{'='*80}\n")

    for company in response.data:
        print(f"  {company['name']}")
        print(f"    ID: {company['id']}")
        print(f"    People: {company.get('people_count', 0)}")
        print()


async def list_roles(company_id: str):
    """List roles for a company."""
    supabase = get_supabase_client()

    response = supabase.table('roles')\
        .select('id, title, required_skills')\
        .eq('company_id', company_id)\
        .execute()

    print(f"\n{'='*80}")
    print(f"ROLES FOR COMPANY")
    print(f"{'='*80}\n")

    for role in response.data:
        print(f"  {role['title']}")
        print(f"    ID: {role['id']}")
        if role.get('required_skills'):
            print(f"    Skills: {', '.join(role['required_skills'][:5])}")
        print()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No args - list companies
        asyncio.run(list_companies())
        print("Usage: python scripts/test_curation.py <company_id> <role_id>")
        print("   or: python scripts/test_curation.py <company_id> list")

    elif len(sys.argv) == 2:
        # One arg - list roles for company
        asyncio.run(list_roles(sys.argv[1]))
        print("\nUsage: python scripts/test_curation.py <company_id> <role_id>")

    elif len(sys.argv) == 3:
        # Two args - run curation
        company_id = sys.argv[1]
        role_id = sys.argv[2]

        try:
            asyncio.run(test_curation(company_id, role_id))
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    else:
        print("Usage: python scripts/test_curation.py <company_id> <role_id>")
