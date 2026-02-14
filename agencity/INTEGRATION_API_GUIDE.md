# Agencity ↔ ProofHire Integration API Guide

This guide covers the new API endpoints implemented for the Agencity-ProofHire integration.

## Quick Start

### 1. Apply Database Migration

First, create the new tables in Supabase:

```bash
# In Supabase SQL Editor, run:
cat agencity/supabase/migrations/002_integration_tables.sql
```

Or apply via command line if you have Supabase CLI:

```bash
supabase db push
```

### 2. Start the Agencity Backend

```bash
cd agencity
uvicorn app.main:app --reload --port 8001
```

### 3. Test the Endpoints

The new endpoints are available at `http://localhost:8001/api/`

---

## API Endpoints

### 1. Create Linkage

**POST /api/linkages**

Create a linkage between an Agencity candidate and a ProofHire application.

```bash
curl -X POST http://localhost:8001/api/linkages \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "agencity_candidate_id": "123e4567-e89b-12d3-a456-426614174000",
    "proofhire_application_id": "pf-app-001",
    "proofhire_role_id": "pf-role-001"
  }'
```

**Response (201):**
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

---

### 2. Get Linkage by Candidate

**GET /api/linkages/candidate/{candidate_id}**

Get the linkage for a specific Agencity candidate.

```bash
curl http://localhost:8001/api/linkages/candidate/123e4567-e89b-12d3-a456-426614174000
```

**Response (200):**
```json
{
  "id": "789e0123-e89b-12d3-a456-426614174000",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "agencity_candidate_id": "123e4567-e89b-12d3-a456-426614174000",
  "proofhire_application_id": "pf-app-001",
  "proofhire_role_id": "pf-role-001",
  "status": "simulation_complete",
  "created_at": "2026-02-13T10:30:00Z",
  "updated_at": "2026-02-13T11:00:00Z"
}
```

---

### 3. Get Linkage by Application

**GET /api/linkages/application/{application_id}**

Get linkage by ProofHire application ID (useful for webhooks).

```bash
curl http://localhost:8001/api/linkages/application/pf-app-001
```

---

### 4. Get Company Linkages

**GET /api/linkages/company/{company_id}**

Get all linkages for a company, with candidate info.

```bash
curl http://localhost:8001/api/linkages/company/550e8400-e29b-41d4-a716-446655440000?status=all
```

**Query Parameters:**
- `status` (optional): Filter by status (default: all)

**Response (200):**
```json
{
  "linkages": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174000",
      "agencity_candidate_id": "123e4567-e89b-12d3-a456-426614174000",
      "candidate_name": "Sarah Chen",
      "candidate_email": "sarah@example.com",
      "proofhire_application_id": "pf-app-001",
      "proofhire_role_id": "pf-role-001",
      "status": "simulation_complete",
      "created_at": "2026-02-13T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### 5. Update Linkage Status

**PATCH /api/linkages/{linkage_id}**

Update the status of a linkage (e.g., when simulation completes).

```bash
curl -X PATCH http://localhost:8001/api/linkages/789e0123-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "simulation_complete"
  }'
```

**Valid Statuses:**
- `linked`
- `simulation_pending`
- `simulation_in_progress`
- `simulation_complete`
- `evaluated`

---

### 6. Record Feedback Action

**POST /api/feedback/action**

Record a hiring decision for reinforcement learning.

```bash
curl -X POST http://localhost:8001/api/feedback/action \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
    "action": "hired",
    "proofhire_score": 85,
    "proofhire_application_id": "pf-app-001",
    "notes": "Strong technical skills"
  }'
```

**Valid Actions:**
- `hired`
- `interviewed`
- `contacted`
- `saved`
- `rejected`
- `ignored`

**Response (201):**
```json
{
  "id": "abc123...",
  "action": "hired",
  "recorded_at": "2026-02-13T12:00:00Z"
}
```

---

### 7. Get Feedback Stats

**GET /api/feedback/stats/{company_id}**

Get feedback statistics for a company.

```bash
curl http://localhost:8001/api/feedback/stats/550e8400-e29b-41d4-a716-446655440000
```

**Response (200):**
```json
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

---

### 8. Get Pipeline

**GET /api/pipeline/{company_id}**

Get all candidates in the pipeline with their ProofHire linkage status.

```bash
curl "http://localhost:8001/api/pipeline/550e8400-e29b-41d4-a716-446655440000?status=all&sort=date&limit=50"
```

**Query Parameters:**
- `status` (optional): `all`, `sourced`, `contacted`, `invited`, `in_simulation`, `reviewed`
- `sort` (optional): `date`, `score`, `status`
- `limit` (optional): 1-200 (default: 50)

**Response (200):**
```json
{
  "candidates": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "agencity_candidate_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Sarah Chen",
      "email": "sarah@example.com",
      "title": "Senior ML Engineer",
      "company": "Google",
      "warmth_score": 1.0,
      "warmth_level": "network",
      "warm_path": {
        "type": "network",
        "description": "From founder's network"
      },
      "status": "reviewed",
      "sourced_at": "2026-02-10T08:00:00Z",
      "contacted_at": null,
      "invited_at": "2026-02-12T10:15:00Z",
      "proofhire_linkage": {
        "application_id": "pf-app-001",
        "role_id": "pf-role-001",
        "simulation_status": "simulation_complete",
        "brief_available": true
      }
    }
  ],
  "total": 1,
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

## Integration Flow

### End-to-End Flow

1. **Founder searches for candidates in Agencity**
   ```
   POST /api/search
   ```

2. **Founder views pipeline**
   ```
   GET /api/pipeline/{companyId}
   ```

3. **Founder clicks "Invite to ProofHire" on a candidate**
   ```
   POST /api/linkages
   ```

4. **Candidate receives email and takes simulation** (ProofHire side)

5. **ProofHire sends webhook to update status** (future)
   ```
   PATCH /api/linkages/{linkageId}
   status: "simulation_complete"
   ```

6. **Founder views brief in Agencity** (fetches from ProofHire)
   ```
   GET /api/pipeline/{companyId}
   # Shows linkage with brief_available: true
   ```

7. **Founder makes hiring decision**
   ```
   POST /api/feedback/action
   action: "hired"
   ```

---

## Error Responses

All endpoints return standard HTTP error codes:

**400 Bad Request**
```json
{
  "detail": "Invalid request parameters"
}
```

**404 Not Found**
```json
{
  "detail": "Resource not found"
}
```

**409 Conflict**
```json
{
  "detail": "Linkage already exists for this candidate"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error message"
}
```

---

## Testing

### Run Backend Tests

```bash
cd agencity
pytest tests/test_integration_api.py -v
```

### API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## Database Schema

### `candidate_linkages` Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| company_id | UUID | Reference to companies |
| agencity_candidate_id | UUID | Reference to people |
| agencity_search_id | UUID | Optional search reference |
| proofhire_application_id | TEXT | ProofHire app ID |
| proofhire_role_id | TEXT | ProofHire role ID |
| status | TEXT | Current status |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Update timestamp |

### `feedback_actions` Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| company_id | UUID | Reference to companies |
| candidate_id | UUID | Reference to people |
| search_id | UUID | Optional search reference |
| action | TEXT | Feedback action |
| proofhire_score | INTEGER | Score 0-100 |
| proofhire_application_id | TEXT | ProofHire app ID |
| notes | TEXT | Additional notes |
| metadata | JSONB | Additional data |
| created_at | TIMESTAMPTZ | Timestamp |

---

## Next Steps

1. **Apply the migration** to create the tables
2. **Start the backend** and test the endpoints
3. **Update the frontend** to use these endpoints
4. **Implement webhooks** for real-time status updates (future)
5. **Add authentication** for production use

---

*Last Updated: February 13, 2026*
