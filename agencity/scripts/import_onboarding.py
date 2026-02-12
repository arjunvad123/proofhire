"""
Import onboarding data into organization profile.

This script demonstrates how to import existing onboarding data
(job description, company info, etc.) into an org profile.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.profile_manager import ProfileManager
from app.db.session import get_db_context
from app.services.onboarding_import import OnboardingImporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example job description
SAMPLE_JOB_DESCRIPTION = """
We're building ProofHire, an AI-powered hiring platform for early-stage startups.

We need a Full Stack Engineer who can move fast and ship quality code.
You'll be working on:
- Building the candidate search engine (Python + PostgreSQL)
- Creating the frontend dashboard (React + TypeScript)
- Integrating with Slack for our agent (@hermes)

You'll be successful if you can:
- Ship features end-to-end with minimal supervision
- Write clean, maintainable code
- Work well in a fast-paced startup environment

Must-haves:
- Strong CS fundamentals
- 2+ years of full-stack experience
- Experience with Python and React
- Previous startup experience (ideally seed/Series A)

Nice-to-haves:
- Experience with LLM/AI applications
- Open source contributions
- Top CS school (MIT, Stanford, CMU, Berkeley, etc.)

We're a 15-person team based in San Francisco, well-funded seed stage.
We move fast and ship daily. If you thrive in 0→1 environments, let's talk.
"""


async def import_sample_data():
    """Import sample onboarding data."""
    logger.info("=" * 60)
    logger.info("Importing Onboarding Data")
    logger.info("=" * 60)

    async with get_db_context() as db:
        manager = ProfileManager(db)
        importer = OnboardingImporter()

        # Step 1: Create or get profile for a Slack workspace
        logger.info("\n1. Creating/getting organization profile...")
        profile = await manager.get_or_create_profile(
            slack_workspace_id="T_PROOFHIRE_DEMO",
            slack_workspace_name="ProofHire Demo Workspace",
        )
        logger.info(f"✓ Profile: {profile.id}")

        # Step 2: Parse job description
        logger.info("\n2. Parsing job description...")
        logger.info(f"Job description length: {len(SAMPLE_JOB_DESCRIPTION)} chars")

        jd_data = await importer.parse_job_description(SAMPLE_JOB_DESCRIPTION)
        logger.info(f"✓ Extracted from job description:")
        for key, value in jd_data.items():
            if isinstance(value, list):
                logger.info(f"  - {key}: {len(value)} items")
            else:
                logger.info(f"  - {key}: {str(value)[:60]}...")

        # Step 3: Import structured data
        logger.info("\n3. Importing structured data...")
        profile_data = await importer.import_from_structured_data(
            job_description=SAMPLE_JOB_DESCRIPTION,
            company_name="ProofHire",
            company_hq_location="San Francisco",
            company_size="15",  # Can be string
            tech_stack=["python", "react", "postgresql", "typescript"],
        )

        logger.info(f"✓ Normalized profile data:")
        logger.info(f"  - Company: {profile_data.get('company_name')}")
        logger.info(f"  - Location: {profile_data.get('company_hq_location')}")
        logger.info(f"  - Size: {profile_data.get('company_size')}")
        logger.info(f"  - Stage: {profile_data.get('company_stage')}")
        logger.info(
            f"  - Tech stack: {', '.join(profile_data.get('tech_stack', []))}"
        )

        # Step 4: Extract hiring priorities
        logger.info("\n4. Extracting hiring priorities...")
        priorities = await importer.extract_hiring_priorities(
            SAMPLE_JOB_DESCRIPTION
        )
        logger.info(f"✓ Top hiring priorities:")
        for i, priority in enumerate(priorities, 1):
            logger.info(f"  {i}. {priority}")

        # Step 5: Update profile with all data
        logger.info("\n5. Updating organization profile...")
        updated = await manager.import_onboarding_data(
            profile_id=profile.id,
            company_name=profile_data.get("company_name"),
            company_hq_location=profile_data.get("company_hq_location"),
            company_size=profile_data.get("company_size"),
            product_description=profile_data.get("product_description"),
            tech_stack=profile_data.get("tech_stack"),
            hiring_priorities=priorities,
        )

        logger.info(f"✓ Profile updated:")
        logger.info(f"  - ID: {updated.id}")
        logger.info(f"  - Company: {updated.company_name}")
        logger.info(f"  - Location: {updated.company_hq_location}")
        logger.info(f"  - Size: {updated.company_size} people")
        logger.info(f"  - Stage: {updated.company_stage}")
        logger.info(f"  - Product: {updated.product_description[:60]}...")
        logger.info(f"  - Tech: {', '.join(updated.tech_stack)}")
        logger.info(
            f"  - Priorities: {', '.join(updated.hiring_priorities[:2])}..."
        )

        # Step 6: Add some example knowledge
        logger.info("\n6. Adding knowledge entries...")
        await manager.add_knowledge(
            org_profile_id=profile.id,
            category="successful_pattern",
            content="Engineers from top CS schools (MIT, Stanford) with startup experience have high success rate",
            source="manual",
            confidence=0.9,
        )

        await manager.add_knowledge(
            org_profile_id=profile.id,
            category="red_flag",
            content="Candidates who only worked at large tech companies struggle with ambiguity and fast pace",
            source="manual",
            confidence=0.8,
        )

        knowledge = await manager.get_knowledge(profile.id)
        logger.info(f"✓ Added {len(knowledge)} knowledge entries")

        # Step 7: Mark onboarding complete
        logger.info("\n7. Marking onboarding complete...")
        await manager.mark_onboarding_complete(profile.id)
        logger.info("✓ Onboarding marked as complete")

        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("✓ Import Complete!")
        logger.info("=" * 60)
        logger.info(f"\nProfile ID: {profile.id}")
        logger.info(f"Workspace: {profile.slack_workspace_id}")
        logger.info(f"Company: {profile.company_name}")
        logger.info(f"Onboarding: {'Complete' if profile.onboarding_complete else 'Incomplete'}")
        logger.info(
            f"\nThis profile is now ready to enhance candidate searches in Slack!"
        )
        logger.info(
            "When @hermes is mentioned in this workspace, it will use this context."
        )


async def main():
    """Main import function."""
    try:
        await import_sample_data()
    except Exception as e:
        logger.error(f"✗ Import failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
