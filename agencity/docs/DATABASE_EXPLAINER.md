# Database Connection Explained

## Why Do I Need DATABASE_URL?

**Short answer**: You don't need a local PostgreSQL server. You just need to point `DATABASE_URL` to your **existing Supabase database** instead of `localhost`.

---

## The Confusion: Two Ways to Access the Same Database

Your Supabase project provides **ONE PostgreSQL database** that can be accessed in **TWO ways**:

```
┌─────────────────────────────────────────────────┐
│         SUPABASE (Your Database)                │
│                                                 │
│  ┌───────────────────────────────────────┐     │
│  │      PostgreSQL Database              │     │
│  │                                       │     │
│  │  Tables:                              │     │
│  │  - companies                          │     │
│  │  - people (3,637 LinkedIn imports)    │     │
│  │  - roles                              │     │
│  │  - data_sources                       │     │
│  │  - organization_profiles (new)        │     │
│  │  - hiring_priorities (new)            │     │
│  └───────────────────────────────────────┘     │
│           ▲                    ▲                │
│           │                    │                │
│    ┌──────┴────────┐    ┌─────┴──────────┐     │
│    │   REST API    │    │   PostgreSQL   │     │
│    │   Port 443    │    │   Port 6543    │     │
│    └───────────────┘    └────────────────┘     │
└─────────────────────────────────────────────────┘
         │                        │
         │                        │
         ▼                        ▼

   METHOD 1                  METHOD 2
   --------                  --------
   REST API                  Direct SQL
   (HTTP requests)           (PostgreSQL protocol)

   Used by:                  Used by:
   - LinkedIn CSV import     - import_greptile.py
   - company_db.py           - SQLAlchemy ORM
   - Most search features    - Database migrations

   Config:                   Config:
   SUPABASE_URL=https://...  DATABASE_URL=postgresql+asyncpg://...
   SUPABASE_KEY=eyJ...       (Direct PostgreSQL connection)
```

---

## Method 1: REST API (What You're Using Now ✅)

### Configuration
```bash
SUPABASE_URL=https://npqjuljzpjvcqmrgpyqj.supabase.co
SUPABASE_KEY=eyJhbGci...
```

### How It Works
```python
# app/services/company_db.py
import httpx

async def get_people(company_id):
    url = f"{SUPABASE_URL}/rest/v1/people"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    response = await httpx.get(url, headers=headers, params={
        "company_id": f"eq.{company_id}"
    })
    return response.json()
```

### Pros
- ✅ No connection pooling issues
- ✅ Works through firewalls
- ✅ Built-in authentication
- ✅ Automatic JSON serialization

### Cons
- ❌ Can't use SQLAlchemy ORM
- ❌ More verbose for complex queries
- ❌ Limited to REST operations

---

## Method 2: Direct PostgreSQL Connection (What You Need to Configure)

### Configuration
```bash
# This is WRONG (tries to connect to your computer):
DATABASE_URL=postgresql+asyncpg://agencity:agencity@localhost:5432/agencity
                                                      ^^^^^^^^^^^
                                                  Your computer (doesn't exist!)

# This is CORRECT (connects to Supabase):
DATABASE_URL=postgresql+asyncpg://postgres.npqjuljzpjvcqmrgpyqj:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
                                                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                                          Supabase's PostgreSQL server (exists!)
```

### How It Works
```python
# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(DATABASE_URL)

async def query():
    async with engine.begin() as conn:
        result = await conn.execute("SELECT * FROM people WHERE company_id = $1")
        return result.fetchall()
```

### Pros
- ✅ Full SQL power
- ✅ SQLAlchemy ORM (models, migrations)
- ✅ Complex joins and transactions
- ✅ Can use Alembic for migrations

### Cons
- ❌ Requires connection pooling setup
- ❌ More complex configuration
- ❌ Direct PostgreSQL port access needed

---

## Breaking Down the Connection String

### The Wrong One (Localhost)
```
postgresql+asyncpg://agencity:agencity@localhost:5432/agencity
│              │     │          │       │         │      └─ Database name
│              │     │          │       │         └──────── Port number
│              │     │          │       └────────────────── Server location (YOUR COMPUTER)
│              │     │          └────────────────────────── Password
│              │     └───────────────────────────────────── Username
│              └─────────────────────────────────────────── Async driver
└────────────────────────────────────────────────────────── Protocol
```

This tries to connect to:
- **Server**: Your computer (`localhost`)
- **Port**: 5432 (PostgreSQL default)
- **Database**: `agencity`
- **User**: `agencity`
- **Password**: `agencity`

**Problem**: You don't have PostgreSQL installed on your computer, so this fails!

### The Correct One (Supabase)
```
postgresql+asyncpg://postgres.npqjuljzpjvcqmrgpyqj:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
│              │     │                            │          │                                     │    └─ Database name
│              │     │                            │          │                                     └────── Port (pooler)
│              │     │                            │          └────────────────────────────────────────── Supabase server
│              │     │                            └───────────────────────────────────────────────────── Your DB password
│              │     └────────────────────────────────────────────────────────────────────────────────── Project username
│              └──────────────────────────────────────────────────────────────────────────────────────── Async driver
└─────────────────────────────────────────────────────────────────────────────────────────────────────── Protocol
```

This connects to:
- **Server**: Supabase's server in AWS (`aws-0-us-east-1.pooler.supabase.com`)
- **Port**: 6543 (Supabase's connection pooler)
- **Database**: `postgres` (Supabase's default database)
- **User**: `postgres.npqjuljzpjvcqmrgpyqj` (your project-specific user)
- **Password**: Your actual Supabase database password

**Result**: Connects to the same database where your 3,637 LinkedIn imports are! ✅

---

## Why Two Methods?

Different parts of your app use different methods:

| Component | Method | Why |
|-----------|--------|-----|
| LinkedIn CSV Import | REST API | Simple CRUD operations, built-in |
| Company Management | REST API | Easy to use, no connection pooling |
| Search (people table) | REST API | Fast queries, JSON responses |
| `import_greptile.py` | Direct SQL | Uses SQLAlchemy ORM models |
| Slack conversation system | Direct SQL | Complex relationships, migrations |
| Database migrations | Direct SQL | Need to run CREATE TABLE, ALTER, etc. |

---

## Do I Need to Install PostgreSQL?

**No!** You already have PostgreSQL - it's running inside Supabase.

Think of it like this:

```
❌ OLD WAY (Local Development):
   Install PostgreSQL on your computer
   └─> localhost:5432
   └─> Have to manage it yourself
   └─> Data only on your computer

✅ NEW WAY (Supabase):
   PostgreSQL already running in the cloud
   └─> aws-0-us-east-1.pooler.supabase.com:6543
   └─> Supabase manages it
   └─> Data accessible from anywhere
   └─> Automatic backups
   └─> Free plan included!
```

---

## What You Need to Do

### Step 1: Get Your Supabase Database Password

1. Go to: https://supabase.com/dashboard/project/npqjuljzpjvcqmrgpyqj/settings/database
2. Look for **Database Password** section
3. If you don't have it saved:
   - Click **Reset Database Password**
   - Copy the new password
   - Save it somewhere safe (password manager)

### Step 2: Update Your .env File

Find this line in `/agencity/.env`:
```bash
DATABASE_URL=postgresql+asyncpg://agencity:agencity@localhost:5432/agencity
```

Replace it with (using your actual password):
```bash
DATABASE_URL=postgresql+asyncpg://postgres.npqjuljzpjvcqmrgpyqj:YOUR_ACTUAL_PASSWORD_HERE@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Step 3: Test It

```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

python -c "
import asyncio
from app.db.session import engine

async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT current_database(), current_user')
        row = result.fetchone()
        print(f'✅ Connected to database: {row[0]}')
        print(f'✅ Connected as user: {row[1]}')
        print()
        print('Testing table access...')
        result2 = await conn.execute('SELECT COUNT(*) FROM people')
        count = result2.scalar()
        print(f'✅ Found {count} people in database')

asyncio.run(test())
"
```

Expected output:
```
✅ Connected to database: postgres
✅ Connected as user: postgres
Testing table access...
✅ Found 3637 people in database
```

---

## Connection String Components Explained

### Protocol: `postgresql+asyncpg://`
- `postgresql` = PostgreSQL database
- `+asyncpg` = Use the `asyncpg` driver (for async Python)
- Alternative: `postgresql+psycopg2://` (sync driver)

### Username: `postgres.npqjuljzpjvcqmrgpyqj`
- Format: `postgres.{project-ref}`
- This is your project-specific admin user
- Created automatically by Supabase

### Password: `[YOUR_PASSWORD]`
- You set this when creating the project
- Can be reset in Supabase dashboard
- Keep it secret!

### Host: `aws-0-us-east-1.pooler.supabase.com`
- Supabase's connection pooler in AWS
- Region: `us-east-1` (US East)
- Alternative: Direct connection (different host)

### Port: `6543`
- Supabase's connection pooler port (recommended)
- Alternative: `5432` (direct connection, slower)

### Database: `postgres`
- Supabase's default database name
- All your tables are in here

---

## Common Questions

### Q: Why not just use the REST API for everything?

**A:** SQLAlchemy (which needs `DATABASE_URL`) provides:
- **Type safety**: Python models match database schema
- **Migrations**: Automatic schema updates with Alembic
- **Complex queries**: Easier to write joins and subqueries
- **ORM features**: Relationships, lazy loading, etc.

The Slack conversation system (`import_greptile.py`) uses SQLAlchemy models, so it needs direct PostgreSQL access.

### Q: Is Supabase just PostgreSQL?

**A:** Supabase = PostgreSQL + extras:
- PostgreSQL database (the core)
- REST API (PostgREST)
- Authentication (GoTrue)
- Storage (for files)
- Realtime (websockets)
- Dashboard UI

You can use it as "just PostgreSQL" if you want!

### Q: Will this cost money?

**A:** Supabase free tier includes:
- 500 MB database storage
- 1 GB file storage
- 2 GB bandwidth
- 50,000 monthly active users

Your 3,637 people in the database use ~3-5 MB of storage, so you're well within the free tier! 🎉

### Q: What if I want to develop locally?

**A:** You can still use Supabase! Two options:

1. **Connect to Supabase from localhost** (what we're doing)
   - Your app runs locally
   - Database is in Supabase cloud
   - Works great for development

2. **Run local Supabase** (advanced)
   ```bash
   npx supabase start
   ```
   - Full Supabase stack locally in Docker
   - Useful for offline development

---

## Summary

### Before (Broken ❌)
```
Your App → localhost:5432 → PostgreSQL not found ❌
```

### After (Working ✅)
```
Your App → aws-0-us-east-1.pooler.supabase.com:6543 → Supabase PostgreSQL ✅
                                                          └─> 3,637 people
                                                          └─> companies
                                                          └─> roles
```

**Bottom line**: You're not setting up a new database - you're just pointing the `DATABASE_URL` to the database you're **already using** via the REST API! 🎯
