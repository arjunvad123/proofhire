# API Endpoints Needed for Integration

This document lists all API endpoints that need to be implemented or verified for the Agencity ↔ ProofHire integration to work.

---

## ✅ Already Exist (ProofHire)

These endpoints are already implemented in ProofHire backend:

### Authentication
```
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### Roles
```
GET  /api/orgs/{orgId}/roles
POST /api/orgs/{orgId}/roles
GET  /api/roles/{roleId}
```

### Applications
```
POST /api/roles/{roleId}/apply
GET  /api/applications/{applicationId}
GET  /api/roles/{roleId}/applications
```

### Simulations
```
POST /api/applications/{applicationId}/runs
GET  /api/runs/{runId}
POST /api/runs/{runId}/submit
```

### Briefs
```
GET  /api/applications/{applicationId}/brief
```

---

## ✅ Already Exist (Agencity)

These endpoints are already implemented in Agencity backend:

### Company Management
```
GET  /api/companies/{companyId}
POST /api/companies
```

### Roles
```
GET  /api/companies/{companyId}/roles
POST /api/companies/{companyId}/roles
```

### Search
```
POST /api/search
{
  "company_id": "uuid",
  "query": "ML Engineer",
  "limit": 50
}
→ Returns SearchResults with candidates by tier
```

### Network
```
GET  /api/v3/network/{companyId}/stats
→ Returns { total_contacts, companies, schools, engineers }
```

---

## ⚠️ Need to Implement (Agencity)

These new endpoints are needed for the integration:

### 1. Candidate Linkages

**Create Linkage**
```
POST /api/linkages
Content-Type: application/json

{
  "company_id": "uuid",
  "agencity_candidate_id": "uuid",
  "agencity_search_id": "uuid",  // optional
  "proofhire_application_id": "string",
  "proofhire_role_id": "string"
}

Response 201:
{
  "id": "uuid",
  "company_id": "uuid",
  "agencity_candidate_id": "uuid",
  "proofhire_application_id": "pf-app-001",
  "status": "linked",
  "created_at": "2026-02-13T...",
  "updated_at": "2026-02-13T..."
}
```

**Get Linkage by Agencity Candidate**
```
GET /api/linkages/candidate/{agencityCandidateId}

Response 200:
{
  "id": "uuid",
  "company_id": "uuid",
  "agencity_candidate_id": "uuid",
  "proofhire_application_id": "pf-app-001",
  "proofhire_role_id": "pf-role-001",
  "status": "simulation_complete",
  "created_at": "2026-02-13T...",
  "updated_at": "2026-02-13T..."
}

Response 404:
{
  "detail": "No linkage found for this candidate"
}
```

**Get All Linkages for Company**
```
GET /api/linkages/company/{companyId}?status=all

Response 200:
{
  "linkages": [
    {
      "id": "uuid",
      "agencity_candidate_id": "uuid",
      "candidate_name": "Sarah Chen",
      "candidate_email": "sarah@example.com",
      "proofhire_application_id": "pf-app-001",
      "status": "simulation_complete",
      "created_at": "2026-02-13T..."
    },
    ...
  ],
  "total": 42
}
```

**Update Linkage Status**
```
PATCH /api/linkages/{linkageId}
Content-Type: application/json

{
  "status": "simulation_complete"
}

Response 200:
{
  "id": "uuid",
  "status": "simulation_complete",
  "updated_at": "2026-02-13T..."
}
```

### 2. Feedback for RL

**Record Feedback Action**
```
POST /api/feedback/action
Content-Type: application/json

{
  "company_id": "uuid",
  "candidate_id": "uuid",
  "search_id": "uuid",  // optional
  "action": "hired",  // hired | interviewed | contacted | rejected | ignored
  "proofhire_score": 85,  // optional, 0-100
  "proofhire_application_id": "pf-app-001",  // optional
  "notes": "Strong technical skills",  // optional
  "timestamp": "2026-02-13T..."
}

Response 201:
{
  "id": "uuid",
  "action": "hired",
  "recorded_at": "2026-02-13T..."
}
```

**Get Feedback Stats**
```
GET /api/feedback/stats/{companyId}

Response 200:
{
  "total_feedback": 127,
  "by_action": {
    "hired": 12,
    "interviewed": 34,
    "contacted": 56,
    "rejected": 18,
    "ignored": 7
  },
  "proofhire_integration": {
    "total_invited": 45,
    "total_completed": 38,
    "completion_rate": 0.844,
    "avg_score": 82.5
  }
}
```

### 3. Pipeline View

**Get Pipeline Candidates**
```
GET /api/pipeline/{companyId}?status=all&sort=date&limit=50

Query Params:
- status: all | sourced | contacted | invited | in_simulation | reviewed
- sort: date | score | status
- limit: number (default 50)

Response 200:
{
  "candidates": [
    {
      "id": "uuid",
      "agencity_candidate_id": "uuid",
      "name": "Sarah Chen",
      "email": "sarah@example.com",
      "title": "Senior ML Engineer",
      "company": "Google",
      "warmth_score": 1.0,
      "warmth_level": "network",
      "warm_path": {
        "type": "direct",
        "description": "Met at YC Demo Day 2022"
      },
      "status": "reviewed",
      "sourced_at": "2026-02-10T...",
      "contacted_at": "2026-02-11T...",
      "invited_at": "2026-02-12T...",
      "proofhire_linkage": {
        "application_id": "pf-app-001",
        "role_id": "pf-role-001",
        "simulation_status": "completed",
        "brief_available": true
      }
    },
    ...
  ],
  "total": 127,
  "by_status": {
    "sourced": 45,
    "contacted": 32,
    "invited": 18,
    "in_simulation": 7,
    "reviewed": 25
  }
}
```

---

## 🔄 Webhooks (Future Enhancement)

For real-time updates from ProofHire → Agencity:

### ProofHire Sends Webhook on Events

**Simulation Started**
```
POST https://agencity.com/api/webhooks/proofhire
X-ProofHire-Signature: sha256=...
Content-Type: application/json

{
  "event": "simulation.started",
  "timestamp": "2026-02-13T...",
  "data": {
    "application_id": "pf-app-001",
    "candidate_email": "sarah@example.com",
    "started_at": "2026-02-13T..."
  }
}
```

**Simulation Completed**
```
POST https://agencity.com/api/webhooks/proofhire
X-ProofHire-Signature: sha256=...

{
  "event": "simulation.completed",
  "timestamp": "2026-02-13T...",
  "data": {
    "application_id": "pf-app-001",
    "candidate_email": "sarah@example.com",
    "completed_at": "2026-02-13T...",
    "brief_available": true
  }
}
```

**Brief Generated**
```
POST https://agencity.com/api/webhooks/proofhire
X-ProofHire-Signature: sha256=...

{
  "event": "brief.generated",
  "timestamp": "2026-02-13T...",
  "data": {
    "application_id": "pf-app-001",
    "candidate_email": "sarah@example.com",
    "brief_id": "brief-001",
    "proven_claims_count": 8,
    "unproven_claims_count": 2,
    "overall_score": 85
  }
}
```

### Agencity Webhook Handler

**Endpoint in Agencity:**
```
POST /api/webhooks/proofhire
X-ProofHire-Signature: sha256=...  // HMAC verification
Content-Type: application/json

Response 200:
{
  "received": true,
  "processed_at": "2026-02-13T..."
}
```

**Implementation:**
```python
# In Agencity backend
@app.post("/api/webhooks/proofhire")
async def handle_proofhire_webhook(
    request: Request,
    signature: str = Header(alias="X-ProofHire-Signature")
):
    # 1. Verify signature
    body = await request.body()
    expected_sig = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if signature != f"sha256={expected_sig}":
        raise HTTPException(401, "Invalid signature")

    # 2. Parse webhook
    data = await request.json()
    event_type = data["event"]

    # 3. Update linkage status
    if event_type == "simulation.completed":
        app_id = data["data"]["application_id"]
        await update_linkage_by_proofhire_app(
            app_id,
            status="simulation_complete"
        )

    return {"received": True}
```

---

## 🗄️ Database Tables Needed

### Agencity: `candidate_linkages`

```sql
CREATE TABLE candidate_linkages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  agencity_candidate_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
  agencity_search_id UUID REFERENCES searches(id) ON DELETE SET NULL,

  -- ProofHire references
  proofhire_application_id TEXT NOT NULL,
  proofhire_role_id TEXT NOT NULL,

  -- Status tracking
  status TEXT NOT NULL DEFAULT 'linked',
  -- Possible statuses: linked, simulation_pending, simulation_in_progress, simulation_complete, evaluated

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Constraints
  CONSTRAINT unique_agencity_candidate UNIQUE(agencity_candidate_id),
  CONSTRAINT unique_proofhire_application UNIQUE(proofhire_application_id)
);

-- Indexes
CREATE INDEX idx_linkages_company ON candidate_linkages(company_id);
CREATE INDEX idx_linkages_status ON candidate_linkages(status);
CREATE INDEX idx_linkages_proofhire_app ON candidate_linkages(proofhire_application_id);

-- Auto-update timestamp
CREATE TRIGGER update_linkages_updated_at
  BEFORE UPDATE ON candidate_linkages
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
```

### Agencity: `feedback_actions`

```sql
CREATE TABLE feedback_actions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  candidate_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
  search_id UUID REFERENCES searches(id) ON DELETE SET NULL,

  -- Action details
  action TEXT NOT NULL,
  -- Possible actions: hired, interviewed, contacted, saved, rejected, ignored

  -- ProofHire integration
  proofhire_application_id TEXT,
  proofhire_score INTEGER,  -- 0-100

  -- Additional context
  notes TEXT,
  metadata JSONB,

  -- Timestamp
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_feedback_company ON feedback_actions(company_id);
CREATE INDEX idx_feedback_candidate ON feedback_actions(candidate_id);
CREATE INDEX idx_feedback_search ON feedback_actions(search_id);
CREATE INDEX idx_feedback_action ON feedback_actions(action);
CREATE INDEX idx_feedback_created_at ON feedback_actions(created_at DESC);
```

---

## ⚙️ Implementation Priority

### Phase 1: Core Integration (Week 1)
1. ✅ Create `candidate_linkages` table
2. ✅ Implement POST /api/linkages
3. ✅ Implement GET /api/linkages/candidate/{id}
4. ✅ Test invitation flow

### Phase 2: Pipeline View (Week 2)
1. ✅ Implement GET /api/pipeline/{companyId}
2. ✅ Update Pipeline UI to use real data
3. ✅ Test status tracking

### Phase 3: Feedback Loop (Week 3)
1. ✅ Create `feedback_actions` table
2. ✅ Implement POST /api/feedback/action
3. ✅ Implement GET /api/feedback/stats
4. ✅ Connect to GRPO model

### Phase 4: Real-time Updates (Week 4)
1. ⏳ Implement webhook handler
2. ⏳ Add signature verification
3. ⏳ Test end-to-end with ProofHire

---

## 🧪 Testing the Endpoints

### Manual Testing with cURL

```bash
# 1. Create linkage
curl -X POST http://localhost:8001/api/linkages \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "agencity_candidate_id": "123e4567-e89b-12d3-a456-426614174000",
    "proofhire_application_id": "pf-app-001",
    "proofhire_role_id": "pf-role-001"
  }'

# 2. Get linkage
curl http://localhost:8001/api/linkages/candidate/123e4567-e89b-12d3-a456-426614174000

# 3. Get pipeline
curl http://localhost:8001/api/pipeline/550e8400-e29b-41d4-a716-446655440000

# 4. Record feedback
curl -X POST http://localhost:8001/api/feedback/action \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
    "action": "hired",
    "proofhire_score": 85
  }'
```

---

## 📝 API Response Examples

### Successful Linkage Creation
```json
{
  "id": "789e0123-e89b-12d3-a456-426614174000",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "agencity_candidate_id": "123e4567-e89b-12d3-a456-426614174000",
  "proofhire_application_id": "pf-app-001",
  "proofhire_role_id": "pf-role-001",
  "status": "linked",
  "created_at": "2026-02-13T10:30:00Z",
  "updated_at": "2026-02-13T10:30:00Z"
}
```

### Pipeline Response with Multiple Candidates
```json
{
  "candidates": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Sarah Chen",
      "email": "sarah@example.com",
      "title": "Senior ML Engineer",
      "company": "Google",
      "warmth_score": 1.0,
      "warmth_level": "network",
      "status": "reviewed",
      "sourced_at": "2026-02-10T08:00:00Z",
      "contacted_at": "2026-02-11T09:30:00Z",
      "invited_at": "2026-02-12T10:15:00Z",
      "proofhire_linkage": {
        "application_id": "pf-app-001",
        "simulation_status": "completed",
        "brief_available": true
      }
    }
  ],
  "total": 1,
  "by_status": {
    "sourced": 0,
    "contacted": 0,
    "invited": 0,
    "in_simulation": 0,
    "reviewed": 1
  }
}
```

---

*Last Updated: February 13, 2026*
