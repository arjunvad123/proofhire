# Agencity Demo - Quick Start Guide

Get the full end-to-end demo working in 5 minutes with your existing Confido data!

## What You Have

✅ **Confido company with real data:**
- Company ID: `100b5ac1-1912-4970-a378-04d0169fd597`
- 3,637 candidates from LinkedIn imports
- All candidates from network (warm connections)

✅ **New API endpoints implemented:**
- Pipeline view
- Candidate linkages
- Feedback tracking

## Step 1: Apply Database Migration (30 seconds)

The integration needs two new tables. Run this SQL in Supabase:

1. Go to: https://supabase.com/dashboard/project/npqjuljzpjvcqmrgpyqj/editor
2. Click "New query"
3. Copy and paste this:

```sql
-- AGENCITY ↔ PROOFHIRE INTEGRATION TABLES

CREATE TABLE IF NOT EXISTS candidate_linkages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    agencity_candidate_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    agencity_search_id UUID,
    proofhire_application_id TEXT NOT NULL,
    proofhire_role_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'linked',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_agencity_candidate UNIQUE(agencity_candidate_id),
    CONSTRAINT unique_proofhire_application UNIQUE(proofhire_application_id)
);

CREATE INDEX IF NOT EXISTS idx_linkages_company ON candidate_linkages(company_id);
CREATE INDEX IF NOT EXISTS idx_linkages_status ON candidate_linkages(status);
CREATE INDEX IF NOT EXISTS idx_linkages_proofhire_app ON candidate_linkages(proofhire_application_id);

CREATE TABLE IF NOT EXISTS feedback_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    search_id UUID,
    action TEXT NOT NULL,
    proofhire_application_id TEXT,
    proofhire_score INTEGER,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_company ON feedback_actions(company_id);
CREATE INDEX IF NOT EXISTS idx_feedback_candidate ON feedback_actions(candidate_id);

ALTER TABLE candidate_linkages ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_actions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for service role" ON candidate_linkages FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON feedback_actions FOR ALL USING (true);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_linkages_updated_at
    BEFORE UPDATE ON candidate_linkages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

4. Click "Run" or press Cmd+Enter

## Step 2: Start Backend (1 minute)

```bash
cd proofhire/agencity

# Make sure dependencies are installed
pip install -r requirements.txt

# Start the backend
uvicorn app.main:app --reload --port 8001
```

Backend will be at: http://localhost:8001

## Step 3: Start Frontend (1 minute)

```bash
cd proofhire/agencity/web

# Install dependencies (first time only)
npm install

# Start the dev server
npm run dev
```

Frontend will be at: http://localhost:3001

## Step 4: View the Demo

Open your browser to: http://localhost:3001/dashboard

### What You'll See:

1. **Dashboard (Home)**
   - Network stats (3,637 connections)
   - Quick actions

2. **Pipeline View** (`/dashboard/pipeline`)
   - All 3,637 Confido candidates
   - Status breakdown (sourced, invited, in_simulation, reviewed)
   - Each candidate shows:
     - Name, title, company
     - Warmth level (network/warm/cold)
     - Actions: "Invite to ProofHire", "Add Note", etc.

3. **Search** (`/dashboard/search`)
   - Search through candidates
   - Filter and rank

## Step 5: Test the Integration

Open a new terminal and run the test script:

```bash
cd proofhire/agencity
python scripts/test_demo_with_existing_data.py
```

This will:
- ✅ Fetch Confido's pipeline
- ✅ Create a test linkage
- ✅ Update linkage status
- ✅ Record feedback
- ✅ Show stats

## Troubleshooting

### "Connection refused" on port 8001
→ Backend not running. Start with: `uvicorn app.main:app --port 8001`

### "Connection refused" on port 3001
→ Frontend not running. Start with: `npm run dev` in `agencity/web`

### "Table doesn't exist" error
→ Run the SQL migration (Step 1)

### Dashboard shows "Complete onboarding"
→ Fixed! Dashboard now defaults to Confido company

### No candidates showing
→ Check:
1. Backend is running on port 8001
2. Supabase env vars are set (`.env` file)
3. Company ID is correct: `100b5ac1-1912-4970-a378-04d0169fd597`

## What's Pre-Configured

The frontend now automatically:
- Uses Confido company ID if no onboarding state
- Shows "Confido" in the sidebar
- Loads all 3,637 candidates in pipeline

No onboarding required! Just start the servers and go to the dashboard.

## API Endpoints Available

### Test them with cURL:

```bash
# Get pipeline
curl http://localhost:8001/api/pipeline/100b5ac1-1912-4970-a378-04d0169fd597

# Health check
curl http://localhost:8001/health

# API docs
open http://localhost:8001/docs
```

## Next Steps

1. ✅ View candidates in pipeline
2. ⏳ Click "Invite to ProofHire" on a candidate
3. ⏳ Connect to ProofHire backend to create application
4. ⏳ View evaluation briefs

---

**Ready to demo? Just run Steps 1-3 and you're live!**

*Total time: ~5 minutes*
