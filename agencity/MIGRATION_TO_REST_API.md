# Migration Guide: Unify Database Under REST API

## Goal
Remove all `DATABASE_URL` dependencies and use **only** Supabase REST API for everything.

---

## ✅ Step 1: Create Tables in Supabase (Do This First!)

1. Go to: https://supabase.com/dashboard/project/npqjuljzpjvcqmrgpyqj/editor
2. Click **"New query"**
3. Open `CREATE_TABLES.sql` in this directory
4. Copy the ENTIRE file
5. Paste into Supabase SQL editor
6. Click **"Run"** or press `Cmd+Enter`
7. Verify you see: `✅ SUCCESS! All 3 tables created.`

---

## ✅ Step 2: Test New REST API Service

Run the new REST API version of import_greptile:

```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

python scripts/import_greptile_rest.py
```

Expected output:
```
============================================================
Importing Greptile Onboarding Data (REST API)
============================================================

1. Creating/getting organization profile for Greptile...
✓ Profile ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

2. Importing company data...
✓ Updated profile: Greptile

3. Adding hiring priorities for Software Engineer role...
✓ Added hiring priority: Software Engineer (Generalist)

4. Adding knowledge entries...
✓ Added cultural fit knowledge
✓ Added technical challenge knowledge
✓ Added company trajectory knowledge

5. Marking onboarding complete...
✓ Onboarding complete: True

============================================================
✓ Greptile Import Complete!
============================================================
```

---

## ✅ Step 3: Update Existing Code

### Files That Need Changes

| Old File | What It Does | Action |
|----------|--------------|--------|
| `app/core/profile_manager.py` | Manages org profiles via SQLAlchemy | **DELETE** (replaced by `org_profiles_db.py`) |
| `scripts/import_greptile.py` | Imports demo data via SQLAlchemy | **DELETE** (replaced by `import_greptile_rest.py`) |
| `app/db/session.py` | SQLAlchemy engine/session | **DELETE** (no longer needed) |
| `app/db/models.py` | SQLAlchemy ORM models | **DELETE** (no longer needed) |
| `alembic/` | Database migrations | **DELETE** (tables created via SQL) |
| `alembic.ini` | Alembic config | **DELETE** |

### Files to Update (Replace SQLAlchemy Imports)

Search for these imports and replace them:

**OLD (SQLAlchemy):**
```python
from app.core.profile_manager import ProfileManager
from app.db.session import get_db_context
from app.db.models import OrgProfile, OrgKnowledge
```

**NEW (REST API):**
```python
from app.services.org_profiles_db import org_profiles_db
```

---

## ✅ Step 4: Remove DATABASE_URL

### Update `.env` File

Remove or comment out the DATABASE_URL line:

```bash
# OLD - DELETE THIS LINE:
# DATABASE_URL=postgresql+asyncpg://postgres.npqjuljzpjvcqmrgpyqj:oQTnkyAq7Gv3VFZZ@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# No longer needed! Everything uses REST API now.
```

### Update `.env.example`

```bash
# Remove DATABASE_URL from the example file too
```

### Update `app/config.py`

Remove the `database_url` field:

```python
# DELETE THIS:
# database_url: str = Field(default="postgresql+asyncpg://...")
```

---

## ✅ Step 5: Remove SQLAlchemy Dependencies

### Update `pyproject.toml`

Remove these dependencies:

```toml
# DELETE THESE:
# sqlalchemy = "^2.0.0"
# alembic = "^1.13.0"
# asyncpg = "^0.29.0"
```

### Reinstall Dependencies

```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

pip install -e .
```

---

## 📊 What You'll Have After Migration

### Single Database Access Pattern

```
┌─────────────────────────────────────────────────────┐
│              SUPABASE POSTGRESQL                    │
│                                                     │
│  All Tables (Accessed via REST API):               │
│  ┌────────────────────────────────────────────┐    │
│  │ Network Tables                             │    │
│  │ • companies                                │    │
│  │ • people (3,637 for Confido)               │    │
│  │ • roles                                    │    │
│  │ • data_sources                             │    │
│  └────────────────────────────────────────────┘    │
│                                                     │
│  ┌────────────────────────────────────────────┐    │
│  │ Profile Tables (NEW!)                      │    │
│  │ • org_profiles                             │    │
│  │ • org_knowledge                            │    │
│  │ • hiring_priorities                        │    │
│  └────────────────────────────────────────────┘    │
│                                                     │
│         ▲                                           │
└─────────┼───────────────────────────────────────────┘
          │
    REST API Only
  (SUPABASE_URL + KEY)
          │
    ┌─────┴──────────────────────────────┐
    │     Your Application               │
    │                                    │
    │  ✅ company_db (existing)          │
    │  ✅ org_profiles_db (NEW!)         │
    │                                    │
    │  ❌ No DATABASE_URL needed         │
    │  ❌ No SQLAlchemy                  │
    │  ❌ No password issues             │
    └────────────────────────────────────┘
```

### Benefits

| Before (Mixed) | After (Unified) |
|----------------|-----------------|
| 2 authentication methods | ✅ 1 authentication method (SUPABASE_KEY) |
| 2 database access patterns | ✅ 1 access pattern (REST API) |
| DATABASE_URL password issues | ✅ No password needed |
| SQLAlchemy + Alembic complexity | ✅ Simple HTTP requests |
| Need to run migrations | ✅ Just run SQL once |
| Local dev requires PostgreSQL | ✅ Works with just API key |

---

## 🧪 Testing Checklist

After migration, test these:

### 1. Greptile Import (Profile System)
```bash
python scripts/import_greptile_rest.py
```
Expected: ✅ Success message with profile ID

### 2. LinkedIn Import (Network System)
```bash
# This should still work (already uses REST API)
curl -X POST http://localhost:8001/api/companies/100b5ac1-1912-4970-a378-04d0169fd597/import/linkedin \
  -F "file=@Connections.csv"
```

### 3. Search Network
```bash
curl "http://localhost:8001/api/v2/search/network/100b5ac1-1912-4970-a378-04d0169fd597?role_title=Software%20Engineer&limit=5"
```

### 4. Get Org Profile
```bash
python -c "
import asyncio
from app.services.org_profiles_db import org_profiles_db

async def test():
    profile = await org_profiles_db.get_profile_by_slack_workspace('T_GREPTILE_DEMO')
    print(f'✅ Profile: {profile[\"company_name\"]}')

asyncio.run(test())
"
```

All should return ✅ success!

---

## 📝 Code Examples

### Old Way (SQLAlchemy) ❌

```python
from app.db.session import get_db_context
from app.core.profile_manager import ProfileManager

async with get_db_context() as db:
    manager = ProfileManager(db)
    profile = await manager.get_or_create_profile(
        slack_workspace_id="T_DEMO",
        slack_workspace_name="Demo Workspace"
    )
```

### New Way (REST API) ✅

```python
from app.services.org_profiles_db import org_profiles_db

profile = await org_profiles_db.get_or_create_profile(
    slack_workspace_id="T_DEMO",
    slack_workspace_name="Demo Workspace"
)
```

**Simpler!** No database session management, no connection pooling, no password issues.

---

## 🚨 Common Issues

### Issue: "Table does not exist"
**Solution**: You forgot Step 1. Run `CREATE_TABLES.sql` in Supabase SQL editor.

### Issue: "Unauthorized" or "Invalid API key"
**Solution**: Check that `SUPABASE_KEY` in `.env` is the **service_role** key, not the anon key.

### Issue: "Module not found: app.db.session"
**Solution**: Good! You successfully removed SQLAlchemy. Update any imports to use `org_profiles_db` instead.

---

## ✨ Summary

**Before:**
- 2 database systems (REST + SQLAlchemy)
- DATABASE_URL password always failing
- Complex setup with migrations

**After:**
- 1 database system (REST API only)
- No passwords needed (just SUPABASE_KEY)
- Simple setup - just run one SQL file

**Everything unified under Supabase REST API!** 🎉
