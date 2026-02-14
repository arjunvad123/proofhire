# Demo Setup Guide - Agencity with Confido Data

This guide will help you set up the end-to-end demo using your existing Confido company data.

## Current Data Status

✅ **Already in Supabase:**
- 3 org_profiles (including Confido)
- 5 companies (including Confido: `100b5ac1-1912-4970-a378-04d0169fd597`)
- 7,274 people (3,637 for Confido company)
- 4 data_sources

## Quick Setup (5 minutes)

### Step 1: Add Integration Tables to Supabase

The integration endpoints need two new tables to work. Run this in your Supabase SQL Editor:

1. Go to: https://supabase.com/dashboard/project/npqjuljzpjvcqmrgpyqj/editor
2. Click "New query"
3. Copy and paste the SQL from: `agencity/supabase/migrations/002_integration_tables.sql`
4. Click "Run"

**OR** use the Supabase CLI:
```bash
cd agencity
supabase db push
```

This creates:
- `candidate_linkages` - Links Agencity candidates → ProofHire applications
- `feedback_actions` - Records hiring decisions for RL training

### Step 2: Start Agencity Backend

```bash
cd agencity

# Install dependencies if needed
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8001
```

The new integration endpoints will be available at: `http://localhost:8001/api/`

### Step 3: Start Agencity Frontend

```bash
cd agencity/web

# Install dependencies if needed
npm install

# Start the dev server
npm run dev
```

The dashboard will be available at: `http://localhost:3001/dashboard`

### Step 4: Test the Integration

Run the test script to verify everything works:

```bash
cd agencity
python scripts/test_demo_with_existing_data.py
```

This will:
1. ✅ Fetch pipeline candidates for Confido
2. ✅ Create a linkage to ProofHire
3. ✅ Update linkage status
4. ✅ Record feedback
5. ✅ Get feedback stats

---

## What the Demo Shows

### 1. Pipeline View (`/dashboard/pipeline`)

Shows all 3,637 candidates for Confido with:
- Name, title, company
- Warmth level (network vs cold)
- Status (sourced → invited → in_simulation → reviewed)
- ProofHire linkage info (when invited)

### 2. Invite to ProofHire Flow

When you click "Invite to ProofHire" on a candidate:
1. Creates linkage in `candidate_linkages` table
2. Sends candidate to ProofHire (would call ProofHire API)
3. Updates status as simulation progresses
4. Shows brief when complete

### 3. Feedback Loop

After reviewing a candidate's ProofHire brief:
1. Click "Hired", "Rejected", etc.
2. Records decision in `feedback_actions` table
3. Includes ProofHire score
4. Used for reinforcement learning

---

## API Endpoints Available

### Pipeline
```bash
# Get all candidates for Confido
curl http://localhost:8001/api/pipeline/100b5ac1-1912-4970-a378-04d0169fd597
```

### Linkages
```bash
# Create linkage
curl -X POST http://localhost:8001/api/linkages \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "100b5ac1-1912-4970-a378-04d0169fd597",
    "agencity_candidate_id": "<candidate-id>",
    "proofhire_application_id": "pf-app-001",
    "proofhire_role_id": "pf-role-001"
  }'

# Get linkage for candidate
curl http://localhost:8001/api/linkages/candidate/<candidate-id>

# Update linkage status
curl -X PATCH http://localhost:8001/api/linkages/<linkage-id> \
  -H "Content-Type: application/json" \
  -d '{"status": "simulation_complete"}'
```

### Feedback
```bash
# Record feedback
curl -X POST http://localhost:8001/api/feedback/action \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "100b5ac1-1912-4970-a378-04d0169fd597",
    "candidate_id": "<candidate-id>",
    "action": "hired",
    "proofhire_score": 85
  }'

# Get feedback stats
curl http://localhost:8001/api/feedback/stats/100b5ac1-1912-4970-a378-04d0169fd597
```

---

## Demo Flow

### Scenario: Confido is hiring an ML Engineer

1. **Search Phase** (existing functionality)
   - Founder searches for "ML Engineer" in Agencity
   - Gets ranked candidates from their network
   - Sees warm paths and timing signals

2. **Pipeline View** (NEW!)
   - Navigate to `/dashboard/pipeline`
   - See all 3,637 candidates for Confido
   - Filter by warmth level, status, etc.

3. **Invite to ProofHire** (NEW!)
   - Click "Invite to ProofHire" on top candidate
   - System creates linkage
   - Candidate receives simulation invite
   - Status updates to "invited"

4. **Simulation** (ProofHire side)
   - Candidate takes coding simulation
   - ProofHire proof engine runs
   - Brief is generated with proven claims
   - Status updates to "reviewed"

5. **Review Brief** (NEW!)
   - Founder sees "View Brief" button in pipeline
   - Opens ProofHire brief with:
     - Proven claims (e.g., "Writes clean, tested code")
     - Evidence artifacts (diffs, test logs)
     - Overall score

6. **Make Decision** (NEW!)
   - Founder clicks "Hire", "Interview", or "Reject"
   - Feedback recorded for RL training
   - Pipeline updates

---

## Troubleshooting

### "Table doesn't exist" error
→ Run the migration SQL (Step 1 above)

### "Connection refused" on port 8001
→ Make sure Agencity backend is running: `uvicorn app.main:app --port 8001`

### No candidates showing in pipeline
→ Check that Confido company ID is correct: `100b5ac1-1912-4970-a378-04d0169fd597`

### API returns 500 error
→ Check Supabase connection: `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

---

## Next Steps

1. ✅ **Apply migration** to create tables
2. ✅ **Test API endpoints** with test script
3. ⏳ **Update frontend** to use new endpoints
4. ⏳ **Connect to ProofHire** backend for real simulations
5. ⏳ **Add webhooks** for real-time updates

---

## File Structure

```
agencity/
├── supabase/
│   └── migrations/
│       └── 002_integration_tables.sql  ← NEW! Migration SQL
├── app/
│   ├── api/
│   │   ├── models/
│   │   │   └── integration.py          ← NEW! Pydantic models
│   │   └── routes/
│   │       └── integration.py          ← NEW! API endpoints
│   └── main.py                         ← Updated with new routes
├── scripts/
│   └── test_demo_with_existing_data.py ← NEW! Test script
├── DEMO_SETUP.md                       ← This file
└── INTEGRATION_API_GUIDE.md            ← Detailed API docs
```

---

*Ready to demo? Follow the steps above and you'll have a working end-to-end flow in 5 minutes!*
