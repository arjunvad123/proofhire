#!/usr/bin/env python3
"""
Enrichment Provider Audit Script

Compares data quality between PDL and Clado for the same LinkedIn URL.
Tests both Clado endpoints (get_profile and scrape_profile) and PDL.

Use this to verify which provider returns better data for your use case.

Usage:
    python scripts/audit_enrichment_providers.py --linkedin-url "linkedin.com/in/username"
    python scripts/audit_enrichment_providers.py --linkedin-url "linkedin.com/in/username" --output json
    python scripts/audit_enrichment_providers.py --linkedin-url "linkedin.com/in/username" --output detailed
"""

import asyncio
import argparse
import json
import sys
from typing import Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.external_search.pdl_client import pdl_client, PDLProfile
from app.services.external_search.clado_client import clado_client, CladoProfile


def calculate_completeness(profile: dict) -> float:
    """Calculate data completeness score (0-100)."""
    score = 0.0
    weights = {
        "full_name": 10,
        "current_title": 10,
        "current_company": 10,
        "location": 5,
        "experience": 20,  # +5 per entry, max 20
        "education": 15,   # +5 per entry, max 15
        "skills": 15,      # +1 per skill, max 15
        "github_url": 10,
        "linkedin_url": 5,
    }

    if profile.get("full_name"):
        score += weights["full_name"]
    if profile.get("current_title"):
        score += weights["current_title"]
    if profile.get("current_company"):
        score += weights["current_company"]
    if profile.get("location"):
        score += weights["location"]
    if profile.get("linkedin_url"):
        score += weights["linkedin_url"]
    if profile.get("github_url"):
        score += weights["github_url"]

    # Experience: +5 per entry, max 20
    exp_count = len(profile.get("experience", []))
    score += min(exp_count * 5, weights["experience"])

    # Education: +5 per entry, max 15
    edu_count = len(profile.get("education", []))
    score += min(edu_count * 5, weights["education"])

    # Skills: +1 per skill, max 15
    skills_count = len(profile.get("skills", []))
    score += min(skills_count, weights["skills"])

    return score


def profile_to_dict(profile) -> dict:
    """Convert profile object to dict for comparison."""
    if hasattr(profile, "model_dump"):
        return profile.model_dump()
    elif hasattr(profile, "dict"):
        return profile.dict()
    return dict(profile)


def compare_field(field_name: str, pdl_value, clado_value) -> dict:
    """Compare a single field between providers."""
    pdl_has = pdl_value is not None and pdl_value != [] and pdl_value != ""
    clado_has = clado_value is not None and clado_value != [] and clado_value != ""

    if isinstance(pdl_value, list):
        pdl_count = len(pdl_value)
        clado_count = len(clado_value) if isinstance(clado_value, list) else 0
        return {
            "field": field_name,
            "pdl_has": pdl_has,
            "clado_has": clado_has,
            "pdl_count": pdl_count,
            "clado_count": clado_count,
            "winner": "pdl" if pdl_count > clado_count else ("clado" if clado_count > pdl_count else "tie"),
        }

    match = str(pdl_value).lower().strip() == str(clado_value).lower().strip() if pdl_has and clado_has else False

    return {
        "field": field_name,
        "pdl_has": pdl_has,
        "clado_has": clado_has,
        "pdl_value": str(pdl_value)[:100] if pdl_has else None,
        "clado_value": str(clado_value)[:100] if clado_has else None,
        "match": match,
        "winner": "pdl" if pdl_has and not clado_has else ("clado" if clado_has and not pdl_has else ("tie" if match else "different")),
    }


async def audit_providers(linkedin_url: str) -> dict:
    """
    Audit all providers/endpoints for the same LinkedIn URL.

    Tests:
    - Clado get_profile ($0.01) - cached data
    - Clado scrape_profile ($0.02) - real-time scrape
    - PDL enrich_profile ($0.10)

    Returns comparison data.
    """
    results = {
        "linkedin_url": linkedin_url,
        "clado_profile": {"status": "pending", "profile": None, "completeness": 0, "cost_usd": 0.01},
        "clado_scrape": {"status": "pending", "profile": None, "completeness": 0, "cost_usd": 0.02},
        "pdl": {"status": "pending", "profile": None, "completeness": 0, "cost_usd": 0.10},
        "comparison": [],
        "summary": {},
    }

    # Clean URL
    clean_url = linkedin_url.replace("https://", "").replace("http://", "").replace("www.", "")

    # Try Clado get_profile (cached, $0.01)
    print(f"\n🔍 Fetching from Clado (cached profile, $0.01)...")
    if not clado_client.enabled:
        print("   ❌ Clado API key not configured")
        results["clado_profile"]["status"] = "disabled"
    else:
        try:
            clado_profile = await clado_client.get_profile(linkedin_url)
            if clado_profile:
                results["clado_profile"]["status"] = "success"
                results["clado_profile"]["profile"] = profile_to_dict(clado_profile)
                results["clado_profile"]["completeness"] = calculate_completeness(results["clado_profile"]["profile"])
                print(f"   ✅ Clado cached profile returned (completeness: {results['clado_profile']['completeness']:.0f}%)")
            else:
                results["clado_profile"]["status"] = "not_found"
                print("   ⚠️ Clado cache miss (profile not in database)")
        except Exception as e:
            results["clado_profile"]["status"] = "error"
            results["clado_profile"]["error"] = str(e)
            print(f"   ❌ Clado get_profile error: {e}")

    # Try Clado scrape_profile (real-time, $0.02)
    print(f"\n🔍 Fetching from Clado (real-time scrape, $0.02)...")
    if not clado_client.enabled:
        print("   ❌ Clado API key not configured")
        results["clado_scrape"]["status"] = "disabled"
    else:
        try:
            clado_scrape = await clado_client.scrape_profile(linkedin_url)
            if clado_scrape:
                results["clado_scrape"]["status"] = "success"
                results["clado_scrape"]["profile"] = profile_to_dict(clado_scrape)
                results["clado_scrape"]["completeness"] = calculate_completeness(results["clado_scrape"]["profile"])
                print(f"   ✅ Clado scrape returned (completeness: {results['clado_scrape']['completeness']:.0f}%)")
            else:
                results["clado_scrape"]["status"] = "not_found"
                print("   ⚠️ Clado scrape returned no data")
        except Exception as e:
            results["clado_scrape"]["status"] = "error"
            results["clado_scrape"]["error"] = str(e)
            print(f"   ❌ Clado scrape error: {e}")

    # Try PDL
    print(f"\n🔍 Fetching from PDL ($0.10)...")
    if not pdl_client.enabled:
        print("   ❌ PDL API key not configured")
        results["pdl"]["status"] = "disabled"
    else:
        try:
            pdl_profile = await pdl_client.enrich_profile(linkedin_url)
            if pdl_profile:
                results["pdl"]["status"] = "success"
                results["pdl"]["profile"] = profile_to_dict(pdl_profile)
                results["pdl"]["completeness"] = calculate_completeness(results["pdl"]["profile"])
                print(f"   ✅ PDL returned profile (completeness: {results['pdl']['completeness']:.0f}%)")
            else:
                results["pdl"]["status"] = "not_found"
                print("   ⚠️ PDL returned no data (404)")
        except Exception as e:
            results["pdl"]["status"] = "error"
            results["pdl"]["error"] = str(e)
            print(f"   ❌ PDL error: {e}")

    # Determine best Clado result for comparison
    clado_best = None
    clado_best_source = None
    if results["clado_scrape"]["profile"]:
        clado_best = results["clado_scrape"]["profile"]
        clado_best_source = "clado_scrape"
    elif results["clado_profile"]["profile"]:
        clado_best = results["clado_profile"]["profile"]
        clado_best_source = "clado_profile"

    # Compare fields: Clado (best) vs PDL
    if results["pdl"]["profile"] and clado_best:
        pdl_p = results["pdl"]["profile"]

        fields_to_compare = [
            "full_name",
            "current_title",
            "current_company",
            "location",
            "headline",
            "experience",
            "education",
            "skills",
            "github_url",
            "twitter_url",
            "personal_website",
        ]

        for field in fields_to_compare:
            comparison = compare_field(
                field,
                pdl_p.get(field),
                clado_best.get(field),
            )
            results["comparison"].append(comparison)

        # Summary
        pdl_wins = sum(1 for c in results["comparison"] if c["winner"] == "pdl")
        clado_wins = sum(1 for c in results["comparison"] if c["winner"] == "clado")
        ties = sum(1 for c in results["comparison"] if c["winner"] in ["tie", "different"])

        clado_completeness = results["clado_scrape"]["completeness"] or results["clado_profile"]["completeness"]

        results["summary"] = {
            "pdl_wins": pdl_wins,
            "clado_wins": clado_wins,
            "ties": ties,
            "pdl_completeness": results["pdl"]["completeness"],
            "clado_profile_completeness": results["clado_profile"]["completeness"],
            "clado_scrape_completeness": results["clado_scrape"]["completeness"],
            "clado_best_source": clado_best_source,
            "recommended": "pdl" if results["pdl"]["completeness"] > clado_completeness else clado_best_source,
            "cost_analysis": {
                "clado_profile_only": 0.01,
                "clado_with_fallback": 0.03,
                "pdl_only": 0.10,
                "recommended_strategy": "clado_profile -> clado_scrape -> pdl",
            }
        }
    elif results["pdl"]["profile"]:
        results["summary"] = {
            "pdl_completeness": results["pdl"]["completeness"],
            "recommended": "pdl",
            "note": "Clado returned no data",
        }
    elif clado_best:
        results["summary"] = {
            "clado_completeness": results["clado_scrape"]["completeness"] or results["clado_profile"]["completeness"],
            "clado_best_source": clado_best_source,
            "recommended": clado_best_source,
            "note": "PDL returned no data",
        }

    return results


def print_comparison_table(results: dict):
    """Print a human-readable comparison table."""
    print("\n" + "=" * 70)
    print("ENRICHMENT PROVIDER AUDIT RESULTS")
    print("=" * 70)
    print(f"LinkedIn URL: {results['linkedin_url']}")
    print()

    # Status
    print("Provider Status:")
    print(f"  Clado Profile (cached, $0.01):  {results['clado_profile']['status']}")
    print(f"  Clado Scrape (real-time, $0.02): {results['clado_scrape']['status']}")
    print(f"  PDL ($0.10):                     {results['pdl']['status']}")
    print()

    # Completeness
    has_data = results["pdl"]["profile"] or results["clado_profile"]["profile"] or results["clado_scrape"]["profile"]
    if has_data:
        print("Data Completeness:")
        print(f"  Clado Profile: {results['clado_profile']['completeness']:.0f}%")
        print(f"  Clado Scrape:  {results['clado_scrape']['completeness']:.0f}%")
        print(f"  PDL:           {results['pdl']['completeness']:.0f}%")
        print()

    # Field comparison
    if results["comparison"]:
        print("Field Comparison:")
        print("-" * 70)
        print(f"{'Field':<20} {'PDL':<15} {'Clado':<15} {'Winner':<10}")
        print("-" * 70)

        for comp in results["comparison"]:
            field = comp["field"]

            if "pdl_count" in comp:  # List field
                pdl_val = f"{comp['pdl_count']} items"
                clado_val = f"{comp['clado_count']} items"
            else:  # Scalar field
                pdl_val = "✓" if comp["pdl_has"] else "✗"
                clado_val = "✓" if comp["clado_has"] else "✗"

            winner = comp["winner"].upper()
            if winner == "TIE":
                winner = "="
            elif winner == "DIFFERENT":
                winner = "≠"

            print(f"{field:<20} {pdl_val:<15} {clado_val:<15} {winner:<10}")

        print("-" * 70)

    # Summary
    if results["summary"]:
        print()
        print("Summary:")
        if "pdl_wins" in results["summary"]:
            print(f"  PDL wins:   {results['summary']['pdl_wins']}")
            print(f"  Clado wins: {results['summary']['clado_wins']}")
            print(f"  Ties:       {results['summary']['ties']}")
        if results["summary"].get("note"):
            print(f"  Note: {results['summary']['note']}")
        print()
        print(f"  🏆 Recommended: {results['summary']['recommended'].upper()}")
        if "cost_analysis" in results["summary"]:
            print()
            print("Cost Analysis:")
            cost = results["summary"]["cost_analysis"]
            print(f"  Clado Profile only:  ${cost['clado_profile_only']:.2f}")
            print(f"  Clado with fallback: ${cost['clado_with_fallback']:.2f}")
            print(f"  PDL only:            ${cost['pdl_only']:.2f}")
            print(f"  Recommended: {cost['recommended_strategy']}")

    print("=" * 70)


def print_detailed_profiles(results: dict):
    """Print detailed profile data from each provider."""
    print("\n" + "=" * 70)
    print("DETAILED PROFILE DATA")
    print("=" * 70)

    def print_profile(p: dict, label: str, cost: float):
        print(f"\n📊 {label} (${cost:.2f}):")
        print("-" * 50)
        print(f"  Name:    {p.get('full_name')}")
        print(f"  Title:   {p.get('current_title')}")
        print(f"  Company: {p.get('current_company')}")
        print(f"  Location:{p.get('location')}")
        print(f"  GitHub:  {p.get('github_url')}")
        print()
        print(f"  Experience ({len(p.get('experience', []))} entries):")
        for exp in p.get("experience", [])[:3]:
            print(f"    - {exp.get('title')} at {exp.get('company')}")
            if exp.get("start_date"):
                print(f"      {exp.get('start_date')} to {exp.get('end_date', 'present')}")
            elif exp.get("duration"):
                print(f"      Duration: {exp.get('duration')}")
        print()
        print(f"  Education ({len(p.get('education', []))} entries):")
        for edu in p.get("education", [])[:2]:
            print(f"    - {edu.get('school')}: {edu.get('degree')} in {edu.get('field')}")
        print()
        print(f"  Skills ({len(p.get('skills', []))} total): {', '.join(p.get('skills', [])[:10])}")

    if results["clado_profile"]["profile"]:
        print_profile(results["clado_profile"]["profile"], "Clado Cached Profile", 0.01)

    if results["clado_scrape"]["profile"]:
        print_profile(results["clado_scrape"]["profile"], "Clado Real-time Scrape", 0.02)

    if results["pdl"]["profile"]:
        print_profile(results["pdl"]["profile"], "PDL Profile", 0.10)


async def main():
    parser = argparse.ArgumentParser(description="Audit enrichment providers")
    parser.add_argument("--linkedin-url", required=True, help="LinkedIn URL to test")
    parser.add_argument("--output", choices=["table", "json", "detailed"], default="table",
                        help="Output format (default: table)")

    args = parser.parse_args()

    results = await audit_providers(args.linkedin_url)

    if args.output == "json":
        print(json.dumps(results, indent=2))
    elif args.output == "detailed":
        print_comparison_table(results)
        print_detailed_profiles(results)
    else:
        print_comparison_table(results)


if __name__ == "__main__":
    asyncio.run(main())
