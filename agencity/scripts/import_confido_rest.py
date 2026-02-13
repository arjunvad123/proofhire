#!/usr/bin/env python3
"""
Import Confido onboarding data - REST API Edition

This ensures the legacy "Confido" example company has a proper
Organization Profile in the new system.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.org_profiles_db import org_profiles_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Copied from AGENCITY_ARCHITECTURE.md
CONFIDO_ID = "100b5ac1-1912-4970-a378-04d0169fd597"


async def import_confido():
    """Import Confido onboarding data using REST API."""
    logger.info("=" * 60)
    logger.info("Importing Confido Onboarding Data (REST API)")
    logger.info("=" * 60)

    # Step 1: Create or get profile
    logger.info("\n1. Creating/getting organization profile for Confido...")
    # We link it to the existing company_id if possible
    profile = await org_profiles_db.get_or_create_profile(
        slack_workspace_id="T_CONFIDO_DEMO",
        slack_workspace_name="Confido Demo Workspace",
        company_id=CONFIDO_ID
    )
    logger.info(f"✓ Profile ID: {profile['id']}")

    # Step 2: Import company data
    logger.info("\n2. Importing company data...")
    updated_profile = await org_profiles_db.import_onboarding_data(
        profile_id=profile["id"],
        company_name="Confido",
        company_hq_location="San Francisco, CA",
        company_size=50,
        product_description="AI-powered background checks and reference calls.",
        tech_stack=["Python", "Django", "React", "Postgres", "Redis"],
        hiring_priorities=[
            "Senior Software Engineer",
            "Founding Growth",
            "Head of Finance"
        ],
    )
    logger.info(f"✓ Updated profile: {updated_profile.get('company_name')}")

    # Step 3: Add hiring priorities
    logger.info("\n3. Adding hiring priorities...")
    await org_profiles_db.add_hiring_priority(
        org_profile_id=profile["id"],
        role_title="Senior Software Engineer",
        must_haves=[
            "5+ years Python/Django",
            "Experience scaling valid systems"
        ],
        nice_to_haves=[
            "React experience",
            "Fintech background"
        ],
        specific_work="Scale our background check automation engine.",
        success_criteria="Reduce manual review by 50% in 6 months."
    )
    logger.info("✓ Added hiring priority: Senior Software Engineer")

    # Step 4: Mark complete
    logger.info("\n4. Marking onboarding complete...")
    final_profile = await org_profiles_db.mark_onboarding_complete(profile["id"])
    logger.info(f"✓ Onboarding complete: {final_profile.get('onboarding_complete')}")

    logger.info("\n" + "=" * 60)
    logger.info("✓ Confido Import Complete!")
    logger.info("=" * 60)


async def main():
    try:
        await import_confido()
    except Exception as e:
        logger.error(f"✗ Import failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
