# Database Setup Guide

## Current Status ✅

Your Supabase database is correctly set up and working! The LinkedIn CSV imports are successfully storing data in the `people` table.

**Stats:**
- **Company**: Confido (`100b5ac1-1912-4970-a378-04d0169fd597`)
- **People imported**: 3,637 LinkedIn connections
- **Database**: Supabase PostgreSQL at `npqjuljzpjvcqmrgpyqj.supabase.co`

---

## Three Database Access Methods

Your application uses Supabase in three different ways:

### 1. ✅ REST API (Working)
**Used by**: LinkedIn CSV imports, company management, search
**Connection**: Via `SUPABASE_URL` + `SUPABASE_KEY` (`.env` lines 32-33)
**Tables accessed**: `companies`, `people`, `roles`, `data_sources`

```python
# Example from app/services/company_db.py
from app.config import settings

base_url = settings.supabase_url  # https://npqjuljzpjvcqmrgpyqj.supabase.co
api_key = settings.supabase_key   # Your service role key
```

### 2. ⚠️ Direct PostgreSQL Connection (Needs Configuration)
**Used by**: `import_greptile.py`, Slack conversation system
**Connection**: Via `DATABASE_URL`
**Tables accessed**: `organization_profiles`, `hiring_priorities`, `knowledge_entries`

**Current issue**: Points to `localhost:5432` (local PostgreSQL that doesn't exist)
**Solution**: Update `DATABASE_URL` to point to Supabase Postgres directly

### 3. ❌ Global Candidates Table (Legacy - Don't Use)
**Table**: `candidates` (global, not company-specific)
**Issue**: `search_greptile.py` searches this table by mistake
**Solution**: Use `/api/v2/search/network/{company_id}` which searches the `people` table

---

## How to Fix DATABASE_URL

### Step 1: Get Your Supabase Connection String

1. Go to: https://supabase.com/dashboard/project/npqjuljzpjvcqmrgpyqj
2. Navigate to **Settings** → **Database**
3. Scroll to **Connection string** section
4. Select **Connection pooling** tab (recommended for serverless/high-concurrency)
5. Copy the URI (it looks like this):

```
postgresql://postgres.npqjuljzpjvcqmrgpyqj:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

6. Get your database password:
   - If you don't have it saved, click **Reset Database Password**
   - ⚠️ **Warning**: This will invalidate any existing connections using the old password

### Step 2: Update .env File

Open `.env` and find the `DATABASE_URL` line (near the bottom). Replace it with:

```bash
# For asyncpg (recommended - best performance)
DATABASE_URL=postgresql+asyncpg://postgres.npqjuljzpjvcqmrgpyqj:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# OR for psycopg2 (if you prefer)
DATABASE_URL=postgresql://postgres.npqjuljzpjvcqmrgpyqj:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Important**:
- Change `postgresql://` to `postgresql+asyncpg://` (adds async support)
- Replace `[YOUR-PASSWORD]` with your actual database password
- Port `6543` = Connection pooling (recommended)
- Port `5432` = Direct connection (use if pooling has issues)

### Step 3: Test the Connection

```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

# Test the direct PostgreSQL connection
python -c "
import asyncio
from app.db.session import engine

async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT current_database()')
        db_name = result.scalar()
        print(f'✅ Connected to database: {db_name}')

asyncio.run(test())
"
```

If successful, you should see:
```
✅ Connected to database: postgres
```

---

## Database Schema

### Tables in Supabase

```sql
-- Companies using Agencity
companies (
    id UUID PRIMARY KEY,
    name TEXT,
    founder_email TEXT,
    people_count INTEGER,  -- 3,637 for Confido
    ...
)

-- LinkedIn connections (company-specific)
people (
    id UUID PRIMARY KEY,
    company_id UUID,  -- Namespaced by company!
    full_name TEXT,
    email TEXT,
    linkedin_url TEXT,
    current_company TEXT,
    current_title TEXT,
    is_from_network BOOLEAN,  -- TRUE for LinkedIn imports
    ...
)

-- Import tracking
data_sources (
    id UUID PRIMARY KEY,
    company_id UUID,
    type TEXT,  -- 'linkedin_export' or 'company_database'
    records_created INTEGER,
    ...
)

-- Hiring positions
roles (
    id UUID PRIMARY KEY,
    company_id UUID,
    title TEXT,
    required_skills TEXT[],
    ...
)
```

### Tables Created by SQLAlchemy (for Slack system)

These tables will be created automatically when you run `import_greptile.py` with the correct `DATABASE_URL`:

```sql
organization_profiles (
    id UUID PRIMARY KEY,
    slack_workspace_id TEXT,
    company_name TEXT,
    ...
)

hiring_priorities (
    id UUID PRIMARY KEY,
    org_profile_id UUID,
    must_haves TEXT[],
    ...
)

knowledge_entries (
    id UUID PRIMARY KEY,
    org_profile_id UUID,
    category TEXT,
    content TEXT,
    ...
)
```

---

## How Each Script Uses the Database

### 1. LinkedIn CSV Import (`POST /api/companies/{id}/import/linkedin`)

```python
# Uses: Supabase REST API
# Writes to: people table (with company_id)
# Service: app/services/company_db.py

from app.data.importers.linkedin_csv import LinkedInImporter

importer = LinkedInImporter()
result = await importer.import_csv(
    company_id=company_id,
    csv_content=csv_text,
    filename="Connections.csv"
)
# Creates 3,637 records in people table for Confido
```

### 2. Greptile Import (`scripts/import_greptile.py`)

```python
# Uses: Direct PostgreSQL connection via SQLAlchemy
# Writes to: organization_profiles, hiring_priorities
# Requires: DATABASE_URL to be set correctly

from app.db.session import get_db_context

async with get_db_context() as db:
    # This creates tables and stores conversation data
    profile = await manager.get_or_create_profile(
        slack_workspace_id="T_GREPTILE_DEMO",
        slack_workspace_name="Greptile Demo Workspace",
    )
```

### 3. Search (`scripts/search_greptile.py` - OLD)

```python
# ❌ WRONG: Searches global 'candidates' table
POST /api/shortlists/search

# This searches 1,375 global candidates,
# NOT your 3,637 imported LinkedIn connections!
```

### 4. Network Search (`scripts/search_confido_network.py` - NEW ✅)

```python
# ✅ CORRECT: Searches company-specific 'people' table
from app.search.network_search import NetworkSearch

search = NetworkSearch(company_id)
results = await search.search(
    role_title='Software Engineer',
    required_skills=['TypeScript', 'Node.js'],
)
# Searches your 3,637 LinkedIn connections
```

---

## Quick Test Commands

### Test REST API Access (Should work already)
```bash
python -c "
import asyncio
from app.services.company_db import company_db

async def test():
    people = await company_db.get_people(
        company_id='100b5ac1-1912-4970-a378-04d0169fd597',
        limit=5
    )
    print(f'✅ Found {len(people)} people via REST API')

asyncio.run(test())
"
```

### Test Direct PostgreSQL Connection (After updating DATABASE_URL)
```bash
python scripts/import_greptile.py
```

### Test Network Search
```bash
python scripts/search_confido_network.py
```

---

## Recommended Search API Endpoints

### Use these instead of `search_greptile.py`:

1. **Network-only search** (fastest, searches your 3,637 connections):
   ```bash
   GET /api/v2/search/network/{company_id}?role_title=Software Engineer&skills=TypeScript,Node.js
   ```

2. **Full tiered search** (network + warm intros + recruiters + cold):
   ```bash
   POST /api/v2/search
   {
     "company_id": "100b5ac1-...",
     "role_title": "Software Engineer",
     "required_skills": ["TypeScript", "Node.js"]
   }
   ```

3. **Get network stats**:
   ```bash
   GET /api/v2/search/stats/{company_id}
   ```

---

## Summary

### ✅ What's Working
- Supabase is connected and working via REST API
- 3,637 LinkedIn connections imported for Confido
- Company data, roles, and data sources are stored correctly

### ⚠️ What Needs Fixing
1. **DATABASE_URL** - Update to point to Supabase Postgres (not localhost)
2. **Search scripts** - Use `search_confido_network.py` instead of `search_greptile.py`

### 📝 Action Items
1. Get your Supabase database password
2. Update `DATABASE_URL` in `.env`
3. Test with `python scripts/import_greptile.py`
4. Use the V2 search API endpoints for candidate search

---

**Next Steps**: Once you update `DATABASE_URL`, all three systems will be unified in Supabase Postgres! 🎉
