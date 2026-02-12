# Quick Setup: Connect Everything to Supabase

## You Need: 5 Minutes ⏱️

**Status**: Your architecture is perfect! Just need to connect DATABASE_URL to Supabase.

---

## Step 1: Get Your Supabase Database Password

1. Go to: https://supabase.com/dashboard/project/npqjuljzpjvcqmrgpyqj/settings/database
2. Scroll to **Database Password** section
3. If you have it saved, great! If not:
   - Click **Reset Database Password**
   - Copy the new password
   - Save it securely

---

## Step 2: Update .env File

Open `/agencity/.env` and find the DATABASE_URL line (around line 73).

**Replace this:**
```bash
DATABASE_URL=postgresql+asyncpg://agencity:agencity@localhost:5432/agencity
```

**With this** (replace `YOUR_PASSWORD` with actual password):
```bash
DATABASE_URL=postgresql+asyncpg://postgres.npqjuljzpjvcqmrgpyqj:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

Save the file.

---

## Step 3: Run Database Migrations

This creates the new tables in Supabase (takes ~10 seconds):

```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

# Run migrations to create tables
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_migration_org_profiles
INFO  [alembic.runtime.migration] Running upgrade 001_initial_migration_org_profiles -> 002_add_supabase_user_id
```

---

## Step 4: Verify Everything Works

Test that all systems can access the database:

### Test 1: REST API (should already work)
```bash
python -c "
import asyncio
from app.services.company_db import company_db

async def test():
    people = await company_db.get_people(
        company_id='100b5ac1-1912-4970-a378-04d0169fd597',
        limit=5
    )
    print(f'✅ REST API: Found {len(people)} people')

asyncio.run(test())
"
```

### Test 2: Direct SQL (will work after DATABASE_URL update)
```bash
python -c "
import asyncio
from app.db.session import engine

async def test():
    async with engine.begin() as conn:
        # Check connection
        result = await conn.execute('SELECT current_database()')
        db = result.scalar()
        print(f'✅ Direct SQL: Connected to {db}')

        # Check people count
        result = await conn.execute('SELECT COUNT(*) FROM people')
        count = result.scalar()
        print(f'✅ Direct SQL: Found {count} people')

        # Check new tables
        result = await conn.execute('SELECT COUNT(*) FROM org_profiles')
        count = result.scalar()
        print(f'✅ Direct SQL: org_profiles table exists ({count} records)')

asyncio.run(test())
"
```

### Test 3: Import Greptile (will work after migrations)
```bash
python scripts/import_greptile.py
```

Expected output:
```
============================================================
Importing Greptile Onboarding Data
============================================================

1. Creating/getting organization profile for Greptile...
✓ Profile: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

2. Parsing job description...
✓ Parsed JD

3. Importing structured data...
✓ Imported

...

✓ Greptile Import Complete!
```

### Test 4: Network Search (should already work)
```bash
python scripts/search_confido_network.py
```

---

## What Just Happened?

### Before
```
Your App
├─ REST API → Supabase ✅ (working)
│   └─ people (3,637), companies, roles
│
└─ Direct SQL → localhost:5432 ❌ (broken)
    └─ org_profiles (missing)
```

### After
```
Your App → Supabase (everything unified!)
├─ REST API ✅
│   └─ people (3,637), companies, roles
│
└─ Direct SQL ✅
    └─ org_profiles, hiring_priorities, knowledge_entries
```

**One database. Two access methods. Both working.** 🎉

---

## Tables Created by Migrations

These new tables will be created in Supabase:

1. **`org_profiles`** - Organization profiles (Slack workspaces)
2. **`knowledge_entries`** - Learned facts about companies
3. **`hiring_priorities`** - Role-specific hiring criteria

These join the existing tables (created via REST API):
- `companies` - Client companies
- `people` - LinkedIn connections (3,637 for Confido)
- `roles` - Job positions
- `data_sources` - Import tracking

---

## Troubleshooting

### Error: "could not translate host name"
**Fix**: Check your DATABASE_URL - make sure you replaced the password correctly.

### Error: "password authentication failed"
**Fix**: Reset your database password in Supabase dashboard and update .env.

### Error: "relation does not exist"
**Fix**: Run `alembic upgrade head` to create the tables.

### Error: "No module named 'app'"
**Fix**: Make sure you're in the `/agencity` directory when running commands.

---

## What You DON'T Need to Do

❌ Install PostgreSQL on your computer
❌ Refactor any code
❌ Change your architecture
❌ Modify database schemas
❌ Update Supabase configuration
❌ Create new tables manually

Everything is ready! Just update the connection string and run migrations.

---

## Summary

| Task | Time | Status |
|------|------|--------|
| Get Supabase password | 1 min | 🔐 |
| Update .env | 1 min | ✏️ |
| Run migrations | 10 sec | ⚡ |
| Test everything | 2 min | ✅ |
| **Total** | **~5 min** | **🎉** |

No refactoring. No reinstalling. Just connect the dots! 🔗
