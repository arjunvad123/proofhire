# Agencity Database Setup

This document describes the database setup for persistent company context in the Slack agent.

## Overview

The Slack agent (@hermes) now uses PostgreSQL to store:
- **Organization Profiles**: Company information tied to Slack workspaces
- **Knowledge Accumulation**: Hiring patterns, successful traits, red flags

This enables the agent to:
- Remember company context across conversations
- Improve candidate matching over time
- Provide personalized responses based on company data

## Database Schema

### `org_profiles` Table

Stores company context for each Slack workspace:

```sql
CREATE TABLE org_profiles (
    id UUID PRIMARY KEY,
    slack_workspace_id VARCHAR(255) UNIQUE NOT NULL,
    slack_workspace_name VARCHAR(255),

    -- Company info
    company_name VARCHAR(255),
    company_hq_location VARCHAR(255),
    company_size INTEGER,
    company_stage VARCHAR(100),
    industry VARCHAR(255),
    product_description TEXT,

    -- Operating style
    pace VARCHAR(50),
    quality_bar VARCHAR(50),
    ambiguity VARCHAR(50),
    tech_stack JSONB DEFAULT '[]',

    -- Hiring preferences
    hiring_priorities JSONB DEFAULT '[]',
    preferred_schools JSONB DEFAULT '[]',
    preferred_companies JSONB DEFAULT '[]',
    avoid_patterns JSONB DEFAULT '[]',

    -- Metadata
    extra_context JSONB DEFAULT '{}',
    onboarding_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `org_knowledge` Table

Stores accumulated knowledge about hiring patterns:

```sql
CREATE TABLE org_knowledge (
    id UUID PRIMARY KEY,
    org_profile_id UUID REFERENCES org_profiles(id) ON DELETE CASCADE,

    category VARCHAR(100) NOT NULL,  -- successful_pattern, red_flag, calibration
    content TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,    -- conversation, manual, feedback
    confidence FLOAT DEFAULT 1.0,

    context_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_slack_user VARCHAR(255)
);
```

## Setup Instructions

### 1. Prerequisites

- PostgreSQL 12+ running locally or remotely
- Python 3.11+
- Agencity dependencies installed

### 2. Configure Database URL

Set the database URL in `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://agencity:agencity@localhost:5432/agencity
```

### 3. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE agencity;
CREATE USER agencity WITH PASSWORD 'agencity';
GRANT ALL PRIVILEGES ON DATABASE agencity TO agencity;
```

### 4. Run Migrations

```bash
# Run the setup script
python scripts/setup_db.py
```

This will:
- Test database connection
- Create all tables
- Verify schema

### 5. Test the Setup

```bash
# Test CRUD operations
python scripts/test_org_profile.py
```

## Usage

### In Slack Bot

The Slack bot automatically:

1. **Gets workspace info** when @hermes is mentioned
2. **Creates/loads org profile** for the workspace
3. **Passes context to LLM** when generating blueprints
4. **Improves responses** based on company data

```python
# In slack.py - handle_mention()
async with get_db_context() as db:
    profile_manager = ProfileManager(db)
    org_profile = await profile_manager.get_or_create_profile(
        slack_workspace_id=workspace_id,
        slack_workspace_name=workspace_name,
    )

# Pass to conversation engine
result = await self.conversation_engine.process_message(
    conversation,
    clean_text,
    org_profile=org_profile,  # <-- Company context
)
```

### Importing Onboarding Data

Use the `OnboardingImporter` service to parse job descriptions and company info:

```python
from app.services.onboarding_import import OnboardingImporter
from app.core.profile_manager import ProfileManager
from app.db.session import get_db_context

async with get_db_context() as db:
    manager = ProfileManager(db)
    importer = OnboardingImporter()

    # Parse job description
    profile_data = await importer.import_from_structured_data(
        job_description="We're building AI tools for developers...",
        company_name="Acme AI",
        company_hq_location="San Francisco",
        company_size=15,
        tech_stack=["python", "react", "postgresql"],
    )

    # Update profile
    await manager.import_onboarding_data(
        profile_id=profile.id,
        **profile_data
    )
```

### Adding Knowledge

Track successful patterns and red flags:

```python
# After positive feedback on a candidate
await manager.add_knowledge(
    org_profile_id=profile.id,
    category="successful_pattern",
    content="MIT CS grads with hackathon experience perform well",
    source="feedback",
    confidence=0.9,
)

# After negative feedback
await manager.add_knowledge(
    org_profile_id=profile.id,
    category="red_flag",
    content="Avoid candidates with only FAANG experience, no startup exposure",
    source="conversation",
    confidence=0.8,
)
```

## Data Flow

```
Slack Message (@hermes mention)
    ↓
Extract workspace_id from event
    ↓
ProfileManager.get_or_create_profile()
    ↓
Load OrgProfile from database
    ↓
Pass to ConversationEngine
    ↓
Format org context for LLM
    ↓
Generate blueprint with company context
    ↓
Search for candidates (improved matching)
```

## Migration from In-Memory

The system supports graceful degradation:

- If database is unavailable, conversations work without persistent context
- Existing in-memory conversations continue to work
- No breaking changes to Slack functionality

## Verification

### Check Tables Created

```sql
-- List all tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';

-- Should show: org_profiles, org_knowledge
```

### Check Profile Data

```sql
-- View all profiles
SELECT id, slack_workspace_id, company_name, onboarding_complete
FROM org_profiles;

-- View knowledge entries
SELECT org_profile_id, category, content
FROM org_knowledge
ORDER BY created_at DESC
LIMIT 10;
```

### Test Query Performance

```sql
-- Should be fast (< 50ms)
EXPLAIN ANALYZE
SELECT * FROM org_profiles
WHERE slack_workspace_id = 'T12345678';
```

## Troubleshooting

### Connection Errors

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Fix:**
- Verify PostgreSQL is running: `pg_isready`
- Check database URL in `.env`
- Ensure user has correct permissions

### Table Creation Errors

```
sqlalchemy.exc.ProgrammingError: relation "org_profiles" already exists
```

**Fix:**
- Drop existing tables: `DROP TABLE org_knowledge, org_profiles CASCADE;`
- Re-run setup script: `python scripts/setup_db.py`

### Import Errors

```
ModuleNotFoundError: No module named 'app.db.models'
```

**Fix:**
- Ensure you're in the agencity directory
- Run from project root: `PYTHONPATH=. python scripts/setup_db.py`

## Next Steps

1. **Run Initial Setup**
   ```bash
   python scripts/setup_db.py
   python scripts/test_org_profile.py
   ```

2. **Import Onboarding Data** (if available)
   - Create script to import from your source
   - Use `OnboardingImporter` service

3. **Test in Slack**
   - Mention @hermes in a Slack channel
   - Verify profile is created/loaded
   - Check logs for "Loaded org profile for workspace..."

4. **Monitor Performance**
   - Check database query logs
   - Verify p95 latency < 50ms
   - Monitor connection pool usage

## Success Criteria

✅ PostgreSQL connected and tables created
✅ OrgProfile can be created/updated for Slack workspaces
✅ Conversation engine includes company context in prompts
✅ Conversations persist across server restarts (TODO: implement)
✅ Database queries perform well (< 50ms p95)
✅ No breaking changes to existing Slack functionality
