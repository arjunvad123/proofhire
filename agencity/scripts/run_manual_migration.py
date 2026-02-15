
import asyncio
import asyncpg
import os
from pathlib import Path

async def run_migration():
    # Load DATABASE_URL from .env if not in environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Try to read from .env file
        env_path = Path("/Users/aidannguyen/Downloads/proofhire/proofhire/agencity/.env")
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("DATABASE_URL="):
                        db_url = line.split("=", 1)[1].strip()
                        break
    
    if not db_url:
        print("Error: DATABASE_URL not found")
        return

    # Clean up DATABASE_URL (remove +asyncpg if present for the driver)
    db_url = db_url.replace("+asyncpg", "")

    print(f"Connecting to database...")
    conn = await asyncpg.connect(db_url)
    try:
        migration_path = Path("/Users/aidannguyen/Downloads/proofhire/proofhire/agencity/supabase/migrations/005_person_enrichments_indices.sql")
        print(f"Reading migration from {migration_path}...")
        with open(migration_path, "r") as f:
            sql = f.read()
        
        print("Executing migration...")
        # Execute the SQL. asyncpg doesn't support multiple statements in one execute() easily 
        # for some complex things, but for standard DDL it works.
        await conn.execute(sql)
        print("✓ Migration successful")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
