"""
Apply Supabase integration migration.

Adds supabase_user_id field to org_profiles table.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.config import settings
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_column_exists() -> bool:
    """Check if supabase_user_id column already exists."""
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'org_profiles'
                AND column_name = 'supabase_user_id'
            """
            )
        )
        return result.first() is not None


async def apply_migration():
    """Apply the Supabase integration migration."""
    logger.info("=" * 60)
    logger.info("Applying Supabase Integration Migration")
    logger.info("=" * 60)

    try:
        # Check if already applied
        exists = await check_column_exists()

        if exists:
            logger.info("✓ Migration already applied (supabase_user_id column exists)")
            return

        logger.info("Adding supabase_user_id column...")

        async with engine.begin() as conn:
            # Add column
            await conn.execute(
                text(
                    """
                    ALTER TABLE org_profiles
                    ADD COLUMN supabase_user_id VARCHAR(255)
                """
                )
            )

            # Create index
            await conn.execute(
                text(
                    """
                    CREATE INDEX ix_org_profiles_supabase_user_id
                    ON org_profiles(supabase_user_id)
                """
                )
            )

        logger.info("✓ Migration applied successfully")

        # Verify
        exists = await check_column_exists()
        if exists:
            logger.info("✓ Verified: supabase_user_id column exists")
        else:
            logger.error("✗ Verification failed: column not found")

    except Exception as e:
        logger.error(f"✗ Migration failed: {e}", exc_info=True)
        raise
    finally:
        await engine.dispose()

    logger.info("=" * 60)
    logger.info("✓ Migration complete!")
    logger.info("=" * 60)
    logger.info("Next steps:")
    logger.info("1. Configure Supabase credentials in .env")
    logger.info("2. Link Slack workspaces: python scripts/link_supabase_user.py")
    logger.info("3. Test in Slack: @hermes")
    logger.info("=" * 60)


async def main():
    """Main function."""
    await apply_migration()


if __name__ == "__main__":
    asyncio.run(main())
