#!/usr/bin/env python3
"""
Verification script for PDL-only enrichment + Claude reasoning implementation.

This script checks:
1. No RapidAPI imports exist
2. PDL-only enrichment method exists
3. Claude reasoning method exists
4. Proper integration in curate() method
"""

import ast
import sys
from pathlib import Path


def check_file_syntax(filepath):
    """Check if Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True, "✓ Syntax valid"
    except SyntaxError as e:
        return False, f"✗ Syntax error: {e}"


def check_no_rapidapi_imports(filepath):
    """Check that RapidAPI imports have been removed."""
    with open(filepath, 'r') as f:
        content = f.read()

    if 'rapidapi_linkedin_client' in content.lower():
        return False, "✗ Found RapidAPI import"

    if 'RapidAPILinkedInClient' in content:
        return False, "✗ Found RapidAPILinkedInClient class usage"

    return True, "✓ No RapidAPI imports found"


def check_method_exists(filepath, method_name):
    """Check if a method exists in the file."""
    with open(filepath, 'r') as f:
        content = f.read()

    if f"async def {method_name}" in content or f"def {method_name}" in content:
        return True, f"✓ Method {method_name} exists"

    return False, f"✗ Method {method_name} not found"


def check_config_no_rapidapi(filepath):
    """Check that config.py doesn't have RapidAPI settings."""
    with open(filepath, 'r') as f:
        content = f.read()

    if 'rapidapi_key' in content:
        return False, "✗ Found rapidapi_key in config"

    if 'rapidapi_linkedin_provider' in content:
        return False, "✗ Found rapidapi_linkedin_provider in config"

    return True, "✓ No RapidAPI config found"


def main():
    print("=" * 70)
    print("PDL-Only Enrichment + Claude Reasoning Implementation Verification")
    print("=" * 70)
    print()

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    curation_engine_path = project_root / "app/services/curation_engine.py"
    config_path = project_root / "app/config.py"

    all_passed = True

    # Check 1: Syntax validation
    print("1. Syntax Validation")
    print("-" * 70)

    passed, msg = check_file_syntax(curation_engine_path)
    print(f"   curation_engine.py: {msg}")
    all_passed = all_passed and passed

    passed, msg = check_file_syntax(config_path)
    print(f"   config.py: {msg}")
    all_passed = all_passed and passed
    print()

    # Check 2: RapidAPI removal
    print("2. RapidAPI Removal")
    print("-" * 70)

    passed, msg = check_no_rapidapi_imports(curation_engine_path)
    print(f"   curation_engine.py: {msg}")
    all_passed = all_passed and passed

    passed, msg = check_config_no_rapidapi(config_path)
    print(f"   config.py: {msg}")
    all_passed = all_passed and passed
    print()

    # Check 3: New methods exist
    print("3. New Methods Implementation")
    print("-" * 70)

    passed, msg = check_method_exists(curation_engine_path, "_enrich_candidates_pdl_only")
    print(f"   {msg}")
    all_passed = all_passed and passed

    passed, msg = check_method_exists(curation_engine_path, "_score_with_claude_reasoning")
    print(f"   {msg}")
    all_passed = all_passed and passed
    print()

    # Check 4: Integration points
    print("4. Integration Points")
    print("-" * 70)

    with open(curation_engine_path, 'r') as f:
        content = f.read()

    # Check for PDL enrichment call
    if "await self._enrich_candidates_pdl_only" in content:
        print("   ✓ PDL enrichment integrated in curate() method")
    else:
        print("   ✗ PDL enrichment NOT called in curate() method")
        all_passed = False

    # Check for Claude reasoning call
    if "await self._score_with_claude_reasoning" in content:
        print("   ✓ Claude reasoning integrated in curate() method")
    else:
        print("   ✗ Claude reasoning NOT called in curate() method")
        all_passed = False

    # Check for weighted scoring
    if "claude_score * 0.7" in content and "fit_score * 0.3" in content:
        print("   ✓ Weighted scoring (70% Claude, 30% rule-based) implemented")
    else:
        print("   ⚠️  Weighted scoring not found (check implementation)")

    print()

    # Check 5: Cost optimization
    print("5. Cost Optimization")
    print("-" * 70)

    if "top_5 = ranked_candidates[:5]" in content:
        print("   ✓ Enriching top 5 candidates (not top 10)")
    else:
        print("   ⚠️  Top 5 strategy not found")

    if "cache_hits" in content:
        print("   ✓ Cache hit tracking implemented")
    else:
        print("   ⚠️  Cache hit tracking not found")

    print()

    # Final summary
    print("=" * 70)
    if all_passed:
        print("✅ ALL CRITICAL CHECKS PASSED")
        print()
        print("Next steps:")
        print("1. Test with a real role using the curation engine")
        print("2. Monitor costs using the SQL query in IMPLEMENTATION_SUMMARY.md")
        print("3. Compare Claude-enhanced scores vs. rule-based scores")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please review the failed checks above and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
