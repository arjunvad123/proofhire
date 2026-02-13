"""
Script to view imported organization profiles and their knowledge - REST API Edition
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.org_profiles_db import org_profiles_db
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def view_profiles():
    """View all imported organization profiles."""
    logger.info("=" * 60)
    logger.info("Imported Organization Profiles (REST API)")
    logger.info("=" * 60)

    # Get all profiles via REST API
    from app.config import settings
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.supabase_url}/rest/v1/org_profiles",
            headers={
                "apikey": settings.supabase_key,
                "Authorization": f"Bearer {settings.supabase_key}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        profiles = response.json()

    logger.info(f"Found {len(profiles)} profiles:")

    for profile in profiles:
        logger.info("\n" + "-" * 40)
        logger.info(f"Company: {profile.get('company_name', 'N/A')}")
        logger.info(f"ID: {profile['id']}")
        logger.info(f"Location: {profile.get('company_hq_location', 'N/A')}")
        logger.info(f"Size: {profile.get('company_size', 'N/A')}")
        tech_stack = profile.get('tech_stack', [])
        if tech_stack:
            logger.info(f"Tech Stack: {', '.join(tech_stack)}")

        logger.info("\nHiring Priorities:")
        priorities = profile.get('hiring_priorities', [])
        for priority in priorities:
            logger.info(f"  - {priority}")

        # Get knowledge
        knowledge = await org_profiles_db.get_knowledge(profile['id'])
        if knowledge:
            logger.info("\nKnowledge / Context:")
            for k in knowledge:
                logger.info(f"  [{k['category']}] {k['content']}")

        logger.info("-" * 40)

async def main():
    try:
        await view_profiles()
    except Exception as e:
        logger.error(f"✗ Failed to view profiles: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
