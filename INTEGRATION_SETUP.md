# Agencity ↔ ProofHire Integration Setup

## Overview

This document explains how to connect the Agencity candidate sourcing platform with the ProofHire evaluation system to create an end-to-end hiring solution.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTEGRATION FLOW                             │
└─────────────────────────────────────────────────────────────────┘

AGENCITY (Port 8001)                    PROOFHIRE (Port 8000)
┌──────────────────────┐                ┌──────────────────────┐
│  Web Dashboard       │                │  Web Dashboard       │
│  (Port 3001)         │                │  (Port 3000)         │
│                      │                │                      │
│  • Search            │                │  • Role Management   │
│  • Pipeline  ←───────┼────────────────┼─→ • Applications     │
│  • Network           │                │  • Simulations       │
└──────────────────────┘                │  • Briefs            │
           ↓                            └──────────────────────┘
┌──────────────────────┐                           ↓
│  Backend API         │                ┌──────────────────────┐
│                      │                │  Backend API         │
│  • Candidate Search  │                │                      │
│  • Warm Paths        │                │  • Proof Engine      │
│  • Feedback Loop     │                │  • Evidence Engine   │
└──────────────────────┘                │  • Simulation Runner │
           ↓                            └──────────────────────┘
┌──────────────────────┐
│  Supabase DB         │
│  • Network Data      │
│  • Candidates        │
│  • Linkages          │
└──────────────────────┘
```

---

## Environment Variables

### Agencity Web (`/agencity/web/.env.local`)

```bash
# Agencity Backend
NEXT_PUBLIC_API_URL=http://localhost:8001/api

# ProofHire Integration
NEXT_PUBLIC_PROOFHIRE_URL=http://localhost:8000/api
NEXT_PUBLIC_PROOFHIRE_WEB_URL=http://localhost:3000
```

### ProofHire Web (`/web/.env.local`)

```bash
# ProofHire Backend
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Agencity Integration (optional, for reverse lookups)
NEXT_PUBLIC_AGENCITY_URL=http://localhost:8001/api
```

### Agencity Backend (`/agencity/.env`)

```bash
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-key-here

# AI
OPENAI_API_KEY=sk-xxx

# ProofHire Integration
PROOFHIRE_API_URL=http://localhost:8000/api
PROOFHIRE_API_KEY=optional-api-key  # For webhook callbacks
```

### ProofHire Backend (`/backend/.env`)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://proofhire:password@localhost:5432/proofhire

# S3/MinIO
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=proofhire

# JWT
JWT_SECRET_KEY=your-secret-key

# LLM
ANTHROPIC_API_KEY=sk-ant-xxx

# Agencity Integration (optional)
AGENCITY_API_URL=http://localhost:8001/api
AGENCITY_WEBHOOK_SECRET=shared-secret  # For feedback webhooks
```

---

## Key Integration Points

### 1. Candidate Invitation Flow

**File:** `/agencity/web/src/lib/proofhire-integration.ts`

**Function:** `inviteCandidateToProofHire()`

**What it does:**
1. Creates a ProofHire application via API
2. Stores linkage in Agencity (candidate_id ↔ application_id)
3. Triggers ProofHire to send invitation email
4. Returns application ID for tracking

**API Calls:**
```typescript
// To ProofHire
POST http://localhost:8000/api/roles/{roleId}/apply
{
  "name": "Sarah Chen",
  "email": "sarah@example.com",
  "linkedin_url": "https://linkedin.com/in/sarachen",
  "github_url": "https://github.com/sarachen",
  "consent": true
}

// To Agencity (for linkage storage)
POST http://localhost:8001/api/linkages
{
  "company_id": "uuid",
  "agencity_candidate_id": "agc-001",
  "agencity_search_id": "search-123",
  "proofhire_application_id": "pf-app-001",
  "proofhire_role_id": "pf-role-001"
}
```

### 2. Status Tracking

**Function:** `getCandidateStatus()`

**What it does:**
1. Retrieves linkage from Agencity
2. Checks ProofHire application status
3. Returns unified status:
   - `not_invited`: No ProofHire application yet
   - `invited`: Application created, waiting for candidate
   - `in_simulation`: Candidate is taking the test
   - `completed`: Simulation finished
   - `brief_available`: Evaluation brief ready

**API Calls:**
```typescript
// Get ProofHire status
GET http://localhost:8000/api/applications/{applicationId}

// Get brief (if completed)
GET http://localhost:8000/api/applications/{applicationId}/brief
```

### 3. Feedback Loop

**Function:** `recordProofHireFeedback()`

**What it does:**
1. Records hiring outcome in Agencity
2. Feeds data to GRPO reward model
3. Improves future candidate rankings

**API Calls:**
```typescript
POST http://localhost:8001/api/feedback/action
{
  "company_id": "uuid",
  "candidate_id": "agc-001",
  "search_id": "search-123",
  "action": "hired",  // or "interviewed", "rejected"
  "proofhire_score": 85,
  "timestamp": "2026-02-13T..."
}
```

---

## Dashboard Integration

### Agencity Dashboard Changes

**New Page:** `/dashboard/pipeline`

**Features:**
- View all candidates from searches
- Track status across both systems
- Invite candidates to ProofHire
- View evaluation briefs when complete

**Navigation:**
```
Overview → Search → Pipeline → Intelligence → Network
                       ↑
                   New tab added
```

### ProofHire Dashboard

**Existing pages remain unchanged:**
- `/dashboard` - View roles and applications
- `/candidates/{id}` - View evaluation briefs

**Future enhancement:** Show Agencity warm path info in briefs

---

## Database Schema Extensions

### Agencity (Supabase)

**New Table:** `candidate_linkages`

```sql
CREATE TABLE candidate_linkages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(id),
  agencity_candidate_id UUID NOT NULL REFERENCES people(id),
  agencity_search_id UUID REFERENCES searches(id),
  proofhire_application_id TEXT NOT NULL,
  proofhire_role_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'linked',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(agencity_candidate_id)
);

CREATE INDEX idx_linkages_company ON candidate_linkages(company_id);
CREATE INDEX idx_linkages_proofhire_app ON candidate_linkages(proofhire_application_id);
```

### ProofHire (PostgreSQL)

**Optional Enhancement:** Add `source` field to applications

```sql
ALTER TABLE applications ADD COLUMN source TEXT DEFAULT 'direct';
ALTER TABLE applications ADD COLUMN source_metadata JSONB;

-- Example source_metadata for Agencity-sourced candidates:
{
  "agencity_candidate_id": "agc-001",
  "agencity_search_id": "search-123",
  "warm_path": {
    "type": "direct",
    "description": "Met at YC Demo Day"
  },
  "warmth_score": 1.0
}
```

---

## Testing the Integration

### Step 1: Start Both Systems

```bash
# Terminal 1: ProofHire
cd /Users/aidannguyen/Downloads/proofhire/proofhire
make up

# Terminal 2: Agencity
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity
npm run dev
```

### Step 2: Verify Services

```bash
# Check ProofHire API
curl http://localhost:8000/api/health
# Should return: {"status":"ok"}

# Check Agencity API
curl http://localhost:8001/api/health
# Should return: {"status":"healthy"}

# Check ProofHire Web
curl http://localhost:3000
# Should load HTML

# Check Agencity Web
curl http://localhost:3001
# Should load HTML
```

### Step 3: Test Integration

1. **Open Agencity Dashboard:**
   ```
   http://localhost:3001/dashboard
   ```

2. **Search for Candidates:**
   - Navigate to "Search" tab
   - Enter "ML Engineer"
   - Click "Search Network"
   - Should see results with tiers

3. **Navigate to Pipeline:**
   - Click "Pipeline" tab
   - Should see candidates in different stages

4. **Invite to ProofHire:**
   - Click on a candidate
   - Click "Invite to ProofHire"
   - Should create ProofHire application
   - Check ProofHire at `http://localhost:3000/dashboard`

5. **Complete Simulation:**
   - Candidate receives email
   - Completes simulation
   - Brief generated

6. **View Results in Agencity:**
   - Return to Agencity Pipeline
   - Candidate status updates to "Reviewed"
   - Click "View Evaluation Brief"
   - Opens ProofHire brief in new tab

---

## API Endpoint Reference

### Agencity Backend APIs

```bash
# Search candidates
POST /api/search
Body: { company_id, query, limit }
Returns: { candidates[], tiers, total_count }

# Get network stats
GET /api/v3/network/{company_id}/stats
Returns: { total_contacts, companies, schools, engineers }

# Store linkage
POST /api/linkages
Body: { company_id, agencity_candidate_id, proofhire_application_id, ... }
Returns: { id, status, created_at }

# Get linkage
GET /api/linkages/{agencity_candidate_id}
Returns: { agencity_candidate_id, proofhire_application_id, status }

# Record feedback
POST /api/feedback/action
Body: { company_id, candidate_id, action, ... }
Returns: { success: true }
```

### ProofHire Backend APIs

```bash
# Get roles
GET /api/orgs/{orgId}/roles
Returns: Role[]

# Create application
POST /api/roles/{roleId}/apply
Body: { name, email, linkedin_url, github_url, consent }
Returns: { id, role_id, status, created_at }

# Get application
GET /api/applications/{applicationId}
Returns: { id, role_id, status, ... }

# Get brief
GET /api/applications/{applicationId}/brief
Returns: { id, proven_claims[], unproven_claims[] }
```

---

## Troubleshooting

### Issue: "ProofHire API not reachable"

**Solution:**
```bash
# Check if ProofHire backend is running
docker-compose ps

# Check logs
docker-compose logs backend

# Verify API base URL
echo $NEXT_PUBLIC_PROOFHIRE_URL
```

### Issue: "CORS error when calling ProofHire"

**Solution:** Add Agencity origin to ProofHire CORS settings

```python
# In /backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # ProofHire web
        "http://localhost:3001",  # Agencity web  ← Add this
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "Linkage not found after invitation"

**Solution:** Check localStorage in browser

```javascript
// In browser console
Object.keys(localStorage).filter(k => k.startsWith('linkage_'))
// Should show: ["linkage_agc-001", ...]

// View specific linkage
JSON.parse(localStorage.getItem('linkage_agc-001'))
```

### Issue: "Brief not showing in Agencity"

**Solution:** Check ProofHire brief generation

```bash
# Check if brief exists
curl http://localhost:8000/api/applications/{app_id}/brief

# Check simulation status
curl http://localhost:8000/api/applications/{app_id}
# status should be "completed"
```

---

## Production Deployment

### Environment Variables (Production)

```bash
# Agencity Web
NEXT_PUBLIC_PROOFHIRE_URL=https://api.proofhire.com/api
NEXT_PUBLIC_PROOFHIRE_WEB_URL=https://proofhire.com

# ProofHire Backend
AGENCITY_API_URL=https://api.agencity.com/api
AGENCITY_WEBHOOK_SECRET=production-secret
```

### CORS Configuration

Both systems need to allow each other's origins:

**ProofHire:**
```python
allow_origins=[
    "https://agencity.com",
    "https://www.agencity.com",
]
```

**Agencity:**
```python
allow_origins=[
    "https://proofhire.com",
    "https://www.proofhire.com",
]
```

---

## Next Steps

1. **Week 1:**
   - [ ] Create Supabase `candidate_linkages` table
   - [ ] Implement linkage API endpoints in Agencity
   - [ ] Test invitation flow end-to-end

2. **Week 2:**
   - [ ] Add status polling for simulation updates
   - [ ] Create feedback webhook from ProofHire to Agencity
   - [ ] Test complete flow: search → invite → simulate → brief

3. **Week 3:**
   - [ ] Add warm path info to ProofHire briefs
   - [ ] Implement batch invite functionality
   - [ ] Add analytics dashboard

---

*Last Updated: February 13, 2026*
