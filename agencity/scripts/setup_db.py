"""
Database setup and migration script.

Run this to initialize the database and create tables.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.config import settings
from app.db.base import Base
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    logger.info(f"Database URL: {settings.database_url}")

    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✓ Tables created successfully")

            # Verify tables exist
            result = await conn.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """
                )
            )
            tables = [row[0] for row in result]
            logger.info(f"✓ Tables in database: {', '.join(tables)}")

    except Exception as e:
        logger.error(f"✗ Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()


async def test_connection():
    """Test database connection."""
    logger.info("Testing database connection...")

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✓ Connected to PostgreSQL: {version}")
            return True
    except Exception as e:
        logger.error(f"✗ Failed to connect to database: {e}")
        logger.error(f"Database URL: {settings.database_url}")
        return False
    finally:
        await engine.dispose()


async def main():
    """Main setup function."""
    logger.info("=" * 60)
    logger.info("Agencity Database Setup")
    logger.info("=" * 60)

    # Test connection first
    if not await test_connection():
        logger.error("Cannot proceed without database connection")
        logger.error("Please ensure PostgreSQL is running and credentials are correct")
        return

    # Create tables
    await create_tables()

    logger.info("=" * 60)
    logger.info("✓ Database setup complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
