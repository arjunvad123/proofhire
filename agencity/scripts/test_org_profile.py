"""
Test script for organization profile management.

Demonstrates creating and managing organization profiles.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.profile_manager import ProfileManager
from app.db.session import get_db_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_profile_crud():
    """Test CRUD operations for organization profiles."""
    logger.info("=" * 60)
    logger.info("Testing Organization Profile Management")
    logger.info("=" * 60)

    async with get_db_context() as db:
        manager = ProfileManager(db)

        # Test 1: Create new profile
        logger.info("\n1. Creating new organization profile...")
        profile = await manager.get_or_create_profile(
            slack_workspace_id="T12345678",
            slack_workspace_name="Test Workspace",
        )
        logger.info(f"✓ Created profile: {profile.id}")
        logger.info(f"  - Workspace: {profile.slack_workspace_id}")
        logger.info(f"  - Onboarding complete: {profile.onboarding_complete}")

        # Test 2: Get existing profile
        logger.info("\n2. Getting existing profile...")
        existing = await manager.get_or_create_profile(
            slack_workspace_id="T12345678",
            slack_workspace_name="Test Workspace",
        )
        logger.info(f"✓ Retrieved existing profile: {existing.id}")
        assert existing.id == profile.id, "Should return same profile"

        # Test 3: Update profile with company data
        logger.info("\n3. Updating profile with company data...")
        updated = await manager.update_profile(
            profile.id,
            {
                "company_name": "Acme AI",
                "company_hq_location": "San Francisco, CA",
                "company_size": 15,
                "company_stage": "seed",
                "product_description": "AI-powered hiring for early-stage startups",
                "tech_stack": ["python", "react", "postgresql"],
                "hiring_priorities": [
                    "Strong CS fundamentals",
                    "Builder mindset",
                    "Early-stage startup experience",
                ],
            },
        )
        logger.info(f"✓ Updated profile: {updated.company_name}")
        logger.info(f"  - Location: {updated.company_hq_location}")
        logger.info(f"  - Size: {updated.company_size}")
        logger.info(f"  - Tech stack: {', '.join(updated.tech_stack)}")

        # Test 4: Add knowledge entries
        logger.info("\n4. Adding knowledge entries...")
        knowledge1 = await manager.add_knowledge(
            org_profile_id=profile.id,
            category="successful_pattern",
            content="Candidates from top CS schools (MIT, Stanford, CMU) have high success rate",
            source="conversation",
            confidence=0.9,
        )
        logger.info(f"✓ Added knowledge entry: {knowledge1.id}")

        knowledge2 = await manager.add_knowledge(
            org_profile_id=profile.id,
            category="red_flag",
            content="Avoid candidates who only worked at large companies with no startup experience",
            source="feedback",
            confidence=0.8,
        )
        logger.info(f"✓ Added knowledge entry: {knowledge2.id}")

        # Test 5: Retrieve knowledge
        logger.info("\n5. Retrieving knowledge entries...")
        all_knowledge = await manager.get_knowledge(profile.id)
        logger.info(f"✓ Found {len(all_knowledge)} knowledge entries")
        for k in all_knowledge:
            logger.info(f"  - [{k.category}] {k.content[:50]}...")

        # Test 6: Import onboarding data
        logger.info("\n6. Importing onboarding data...")
        imported = await manager.import_onboarding_data(
            profile_id=profile.id,
            company_name="Acme AI (Updated)",
            product_description="Building the future of AI-powered recruitment",
            hiring_priorities=[
                "Top-tier CS education",
                "Hackathon experience",
                "Open source contributions",
            ],
        )
        logger.info(f"✓ Imported onboarding data")
        logger.info(f"  - Company: {imported.company_name}")
        logger.info(f"  - Priorities: {', '.join(imported.hiring_priorities)}")

        # Test 7: Mark onboarding complete
        logger.info("\n7. Marking onboarding complete...")
        success = await manager.mark_onboarding_complete(profile.id)
        logger.info(f"✓ Onboarding complete: {success}")

        # Final verification
        logger.info("\n8. Final profile state...")
        final = await manager.get_profile_by_workspace("T12345678")
        logger.info(f"✓ Profile: {final.company_name}")
        logger.info(f"  - Onboarding complete: {final.onboarding_complete}")
        logger.info(f"  - Tech stack: {', '.join(final.tech_stack)}")
        logger.info(f"  - Hiring priorities: {len(final.hiring_priorities)} items")

    logger.info("\n" + "=" * 60)
    logger.info("✓ All tests passed!")
    logger.info("=" * 60)


async def main():
    """Main test function."""
    try:
        await test_profile_crud()
    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
