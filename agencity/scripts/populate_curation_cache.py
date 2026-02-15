#!/usr/bin/env python3
"""
Script to populate curation cache for all companies/roles.

This should be run:
1. After importing candidates
2. When new roles are created
3. As a daily cron job to refresh caches

Usage:
    # Generate cache for all companies
    python scripts/populate_curation_cache.py

    # Force refresh all caches
    python scripts/populate_curation_cache.py --force

    # Generate for specific company
    python scripts/populate_curation_cache.py --company <company_id>

    # Generate for specific role
    python scripts/populate_curation_cache.py --role <company_id> <role_id>
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.workers.curation_cache_worker import (
    generate_all_caches,
    generate_caches_for_company,
    generate_cache_for_role,
    cleanup_expired_caches
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_banner():
    print("\n" + "="*70)
    print("  🎯 CURATION CACHE GENERATOR")
    print("="*70 + "\n")


def print_result(result):
    print("\n" + "-"*70)
    print("📊 RESULTS:")
    print("-"*70)

    if result.get("status") == "completed":
        print(f"✅ Status: Success")
        print(f"📈 Companies Processed: {result.get('companies_processed', 0)}")
        print(f"📋 Total Roles: {result.get('total_roles_processed', 0)}")
        print(f"✓  Successful: {result.get('total_success', 0)}")
        print(f"✗  Failed: {result.get('total_failed', 0)}")
    elif result.get("status") == "success":
        print(f"✅ Status: Success")
        if "cached_count" in result:
            print(f"📋 Cached Candidates: {result.get('cached_count')}")
            print(f"🕐 Expires At: {result.get('expires_at')}")
    elif result.get("status") == "no_companies":
        print("⚠️  No companies found in database")
    elif result.get("status") == "no_roles":
        print("⚠️  No roles to cache")
    else:
        print(f"❌ Status: {result.get('status')}")
        if "error" in result:
            print(f"❌ Error: {result.get('error')}")

    print("-"*70 + "\n")


async def main():
    print_banner()

    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    try:
        if command == "--help" or command == "-h":
            print(__doc__)
            return

        elif command == "cleanup":
            logger.info("🧹 Cleaning up expired caches...")
            result = await cleanup_expired_caches()
            print_result(result)

        elif command == "--company" and len(sys.argv) >= 3:
            company_id = sys.argv[2]
            force = "--force" in sys.argv
            logger.info(f"🏢 Generating cache for company: {company_id}")
            if force:
                logger.info("🔄 Force refresh enabled")
            result = await generate_caches_for_company(company_id, force_refresh=force)
            print_result(result)

        elif command == "--role" and len(sys.argv) >= 4:
            company_id = sys.argv[2]
            role_id = sys.argv[3]
            force = "--force" in sys.argv
            logger.info(f"📋 Generating cache for role: {role_id}")
            if force:
                logger.info("🔄 Force refresh enabled")
            result = await generate_cache_for_role(company_id, role_id, force_refresh=force)
            print_result(result)

        else:
            # Default: generate all caches
            force = "--force" in command or "--force" in sys.argv
            logger.info("🌐 Generating caches for ALL companies and roles...")
            if force:
                logger.info("🔄 Force refresh enabled - regenerating all caches")
            result = await generate_all_caches(force_refresh=force)
            print_result(result)

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
