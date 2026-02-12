"""
Link Slack workspace to Supabase user - REST API Edition

This script helps you connect a Slack workspace to a Supabase user
and sync their onboarding data into the org profile.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.org_profiles_db import org_profiles_db
from app.services.supabase_sync import SupabaseSyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def link_by_user_id(
    slack_workspace_id: str,
    supabase_user_id: str,
    slack_workspace_name: str | None = None,
):
    """Link by Supabase user ID."""
    logger.info("=" * 60)
    logger.info("Linking Slack Workspace to Supabase User (REST API)")
    logger.info("=" * 60)
    logger.info(f"Slack Workspace: {slack_workspace_id}")
    logger.info(f"Supabase User ID: {supabase_user_id}")

    sync_service = SupabaseSyncService()

    # Get or create profile
    logger.info("\n1. Getting/creating org profile...")
    profile = await org_profiles_db.get_or_create_profile(
        slack_workspace_id=slack_workspace_id,
        slack_workspace_name=slack_workspace_name,
        supabase_user_id=supabase_user_id,
    )
    logger.info(f"✓ Profile ID: {profile['id']}")

    # Sync from Supabase
    logger.info("\n2. Syncing data from Supabase...")
    success = await sync_service.link_profile_to_supabase_user(
        profile['id'], supabase_user_id
    )

    if success:
        # Get updated profile
        profile = await org_profiles_db.get_profile_by_id(profile['id'])

        logger.info("\n3. ✓ Sync complete!")
        logger.info("=" * 60)
        logger.info("Profile Summary:")
        logger.info("=" * 60)
        logger.info(f"ID: {profile['id']}")
        logger.info(f"Slack Workspace: {profile.get('slack_workspace_id')}")
        logger.info(f"Supabase User: {profile.get('supabase_user_id')}")
        logger.info(f"Company: {profile.get('company_name') or 'Not set'}")
        product = profile.get('product_description')
        logger.info(
            f"Product: {product[:60] if product else 'Not set'}..."
        )
        tech_stack = profile.get('tech_stack', [])
        logger.info(
            f"Tech Stack: {', '.join(tech_stack) if tech_stack else 'Not set'}"
        )
        priorities = profile.get('hiring_priorities', [])
        logger.info(
            f"Priorities: {', '.join(priorities[:2]) if priorities else 'Not set'}..."
        )
        logger.info(f"Onboarding: {'Complete' if profile.get('onboarding_complete') else 'Incomplete'}")
        logger.info("=" * 60)

        return True
    else:
        logger.error("✗ Sync failed")
        return False


async def link_by_company_name(
    slack_workspace_id: str,
    company_name: str,
    slack_workspace_name: str | None = None,
):
    """Link by company name (search Supabase)."""
    logger.info("=" * 60)
    logger.info("Linking Slack Workspace to Supabase User (by company name)")
    logger.info("=" * 60)
    logger.info(f"Slack Workspace: {slack_workspace_id}")
    logger.info(f"Company Name: {company_name}")

    sync_service = SupabaseSyncService()

    # Get or create profile
    logger.info("\n1. Getting/creating org profile...")
    profile = await org_profiles_db.get_or_create_profile(
        slack_workspace_id=slack_workspace_id,
        slack_workspace_name=slack_workspace_name,
    )
    logger.info(f"✓ Profile ID: {profile['id']}")

    # Find and link by company name
    logger.info("\n2. Searching for Supabase user...")
    success = await sync_service.find_and_link_by_company_name(
        profile['id'], company_name
    )

    if success:
        # Get updated profile
        profile = await org_profiles_db.get_profile_by_id(profile['id'])

        logger.info("\n3. ✓ Sync complete!")
        logger.info("=" * 60)
        logger.info("Profile Summary:")
        logger.info("=" * 60)
        logger.info(f"ID: {profile['id']}")
        logger.info(f"Slack Workspace: {profile.get('slack_workspace_id')}")
        logger.info(f"Supabase User: {profile.get('supabase_user_id')}")
        logger.info(f"Company: {profile.get('company_name') or 'Not set'}")
        product = profile.get('product_description')
        logger.info(
            f"Product: {product[:60] if product else 'Not set'}..."
        )
        tech_stack = profile.get('tech_stack', [])
        logger.info(
            f"Tech Stack: {', '.join(tech_stack) if tech_stack else 'Not set'}"
        )
        priorities = profile.get('hiring_priorities', [])
        logger.info(
            f"Priorities: {', '.join(priorities[:2]) if priorities else 'Not set'}..."
        )
        logger.info(f"Onboarding: {'Complete' if profile.get('onboarding_complete') else 'Incomplete'}")
        logger.info("=" * 60)

        return True
    else:
        logger.error("✗ Sync failed - user not found")
        return False


async def main():
    """Main function."""
    # Example usage - update these values
    # Option 1: Link by Supabase user ID
    # await link_by_user_id(
    #     slack_workspace_id="T12345678",
    #     supabase_user_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    #     slack_workspace_name="My Company Workspace",
    # )

    # Option 2: Link by company name (searches Supabase)
    # await link_by_company_name(
    #     slack_workspace_id="T12345678",
    #     company_name="Acme AI",
    #     slack_workspace_name="Acme Workspace",
    # )

    logger.info("=" * 60)
    logger.info("Supabase Linking Script")
    logger.info("=" * 60)
    logger.info("Usage:")
    logger.info("1. Edit this script and uncomment one of the examples")
    logger.info("2. Update with your Slack workspace ID and Supabase user ID/company")
    logger.info("3. Run: python scripts/link_supabase_user.py")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
