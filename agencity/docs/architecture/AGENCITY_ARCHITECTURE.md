
Folder highlights
Agencity documents detail an AI hiring agent using RL-trained reasoning and Proof Briefs to evaluate candidates proactively, as seen in the Feb 2026 feasibility review.

# Agencity: Network Intelligence System Architecture

## Complete Technical Documentation with Confido Example

---

## 1. System Overview

Agencity is a **Network Intelligence Platform** that helps companies hire through their professional networks. Instead of cold outreach, it leverages warm introductions and timing intelligence to find the best candidates at the right moment.

### Core Philosophy
- **Network-First**: Your best hires come through people you already know
- **Timing Matters**: Knowing when someone is ready to move is as important as finding them
- **Warm > Cold**: A warm introduction converts 10x better than cold outreach

---

## 2. The Four Pillars of Intelligence

### Pillar 1: Network Activation (Reverse Reference)
**Question**: "Who in my network can recommend candidates for this role?"

Instead of searching for candidates directly, we identify **connectors** - people in your network who are well-positioned to recommend others. This creates a "who would you recommend?" workflow.

**Confido Example**:
```
Role: Software Engineer
Top Connectors Found:
1. Sarah Chen (Engineering Manager @ Stripe) - Priority: 0.85
   "Hey Sarah, you've worked with so many great engineers at Stripe.
   We're looking for a software engineer at Confido - would you know
   anyone who might be a good fit?"
```

### Pillar 2: Timing Intelligence
**Question**: "Who in my network might be ready to make a move?"

We analyze signals that indicate career transition readiness:
- **Layoff Exposure**: Company has announced layoffs
- **Tenure Patterns**: 2+ years at current role (likely to consider new opportunities)
- **Activity Signals**: Profile updates, job searching behavior

**Confido Example**:
```
High Urgency Candidates (Layoff-Affected):
- Mike Johnson (Senior Engineer @ Stripe) - Company had layoffs in Jan 2024
- Lisa Park (Backend Dev @ Meta) - Role elimination announced

Medium Urgency (Long Tenure):
- James Wilson (4.5 years at Google) - Likely ready for new challenge
```

### Pillar 3: Network Expansion
**Question**: "Who should I add to my network to improve hiring reach?"

Identifies gaps in network coverage by role type, seniority, and company.

### Pillar 4: Company Intelligence
**Question**: "What's happening at companies where my candidates work?"

Tracks company events (layoffs, funding, acquisitions) that affect hiring timing.

---

## 3. Data Architecture

### Database: Supabase (PostgreSQL)

```
+---------------------------------------------------------------------+
|                         SUPABASE DATABASE                           |
+---------------------------------------------------------------------+
|                                                                     |
|  +-----------+    +-----------+    +-------------------------+      |
|  | companies |--->|   roles   |    |        people           |      |
|  +-----------+    +-----------+    +-------------------------+      |
|  | id        |    | id        |    | id                      |      |
|  | name      |    | company_id|    | company_id              |      |
|  | domain    |    | title     |    | full_name               |      |
|  | industry  |    | level     |    | email                   |      |
|  | tech_stack|    | department|    | linkedin_url            |      |
|  | team_size |    | required_ |    | current_company         |      |
|  | founder_  |    |   skills  |    | current_title           |      |
|  |   email   |    | status    |    | headline                |      |
|  |people_cnt |    +-----------+    | location                |      |
|  +-----------+                     | trust_score             |      |
|                                    | is_from_network         |      |
|  +---------------------+           | skills (jsonb)          |      |
|  |   data_sources      |           | experience (jsonb)      |      |
|  +---------------------+           | education (jsonb)       |      |
|  | id                  |           | enrichment_data (jsonb) |      |
|  | company_id          |           +-------------------------+      |
|  | type (linkedin/csv) |                                            |
|  | status              |                                            |
|  | records_created     |                                            |
|  +---------------------+                                            |
|                                                                     |
+---------------------------------------------------------------------+
```

### Confido's Data

```
Company: Confido (100b5ac1-1912-4970-a378-04d0169fd597)
+-- 305 people imported from LinkedIn connections
+-- 4 active roles:
|   +-- Software Engineer
|   +-- Senior Sales Development Representative
|   +-- Head of Finance
|   +-- Founding Growth
+-- Network Stats:
    +-- Total connections: 305
    +-- Engineers: 89
    +-- Top companies: Google (12), Meta (8), Stripe (7)
    +-- Average seniority: 3.2
```

---

## 4. Search System Architecture

### The Tiered Search Model

When you search for "Software Engineer", the system returns candidates in 4 tiers:

```
+---------------------------------------------------------------------+
|                     SEARCH: "Software Engineer"                     |
+---------------------------------------------------------------------+
|                                                                     |
|  TIER 1: DIRECT NETWORK (Warmth: 100%)                              |
|  +---------------------------------------------------------------+  |
|  | People you're directly connected to who match the role        |  |
|  | - Already have relationship                                   |  |
|  | - Can reach out directly                                      |  |
|  | Example: "John Doe - You connected at YC Demo Day"            |  |
|  +---------------------------------------------------------------+  |
|                           |                                         |
|                           v                                         |
|  TIER 2: WARM INTRO (Warmth: 50-80%)                                |
|  +---------------------------------------------------------------+  |
|  | People one degree away - a connection can introduce you       |  |
|  | - Shared company history (worked together)                    |  |
|  | - Shared school (alumni network)                              |  |
|  | Example: "Jane Smith - Sarah (your connection) worked with    |  |
|  |          her at Stripe 2019-2021"                             |  |
|  +---------------------------------------------------------------+  |
|                           |                                         |
|                           v                                         |
|  TIER 3: RECRUITERS (Specialty Match)                               |
|  +---------------------------------------------------------------+  |
|  | Technical recruiters in your network who specialize in        |  |
|  | the role you're hiring for                                    |  |
|  | - Can source candidates externally                            |  |
|  | - Have existing candidate pipelines                           |  |
|  | Example: "Alex Recruiter - Specializes in backend engineers"  |  |
|  +---------------------------------------------------------------+  |
|                           |                                         |
|                           v                                         |
|  TIER 4: COLD OUTREACH (Warmth: 0%)                                 |
|  +---------------------------------------------------------------+  |
|  | Qualified candidates with no warm path                        |  |
|  | - Matched by skills/experience only                           |  |
|  | - Requires cold outreach or finding alternative warm paths    |  |
|  | Example: "Bob Engineer - No connection, but strong match"     |  |
|  +---------------------------------------------------------------+  |
|                                                                     |
+---------------------------------------------------------------------+
```

### Confido Search Results

```
Search: "Software Engineer"
Network Size: 305 connections
Total Candidates Found: 81

Results by Tier:
+-- Tier 1 (Direct Network): 31 candidates
+-- Tier 2 (Warm Intro):     24 candidates
+-- Tier 3 (Recruiters):      1 recruiter
+-- Tier 4 (Cold):           25 candidates

Primary Recommendation:
"Start with your 31 direct connections - they already know you
 and are most likely to respond positively."
```

### Scoring Algorithm

Each candidate gets three scores that combine into a final ranking:

```python
combined_score = (
    0.4 * match_score +      # How well they match the role
    0.3 * warmth_score +     # How strong the connection is
    0.3 * readiness_score    # How likely they are to be open to opportunities
)
```

**Match Score** (0-100):
- Skills overlap with required skills
- Experience level match
- Industry relevance
- Title similarity

**Warmth Score** (0-100):
- Tier 1: 100 (direct connection)
- Tier 2: 50-80 (based on connector strength)
- Tier 3: 40 (recruiter relationship)
- Tier 4: 0 (no warm path)

**Readiness Score** (0-100):
- Layoff at current company: +40
- Tenure > 3 years: +20
- Recent profile updates: +15
- Job searching signals: +25

---

## 5. API Architecture

### Backend: FastAPI (Python)

```
+---------------------------------------------------------------------+
|                    FASTAPI BACKEND (Port 8001)                      |
+---------------------------------------------------------------------+
|                                                                     |
|  /api                                                               |
|  +-- /companies                                                     |
|  |   +-- POST   /                    Create company                 |
|  |   +-- GET    /{id}                Get company with stats         |
|  |   +-- PATCH  /{id}                Update company                 |
|  |   +-- GET    /{id}/roles          List roles                     |
|  |   +-- POST   /{id}/roles          Create role                    |
|  |   +-- POST   /{id}/import/linkedin   Import LinkedIn CSV         |
|  |   +-- GET    /{id}/network/stats  Get network statistics         |
|  |                                                                  |
|  +-- /v2/search                                                     |
|  |   +-- POST   /                    Tiered candidate search        |
|  |                                                                  |
|  +-- /v3                                                            |
|      +-- /timing/network-analysis/{company_id}  Timing alerts       |
|      +-- /company/layoffs/{company_id}          Layoff exposure     |
|      +-- /company/digest/{company_id}           Daily digest        |
|      +-- /activate/reverse-reference            Network activation  |
|                                                                     |
+---------------------------------------------------------------------+
```

### Frontend: Next.js 16 (React)

```
+---------------------------------------------------------------------+
|                    NEXT.JS FRONTEND (Port 3000)                     |
+---------------------------------------------------------------------+
|                                                                     |
|  /                          Landing page                            |
|  /onboarding                Multi-step company setup                |
|  /dashboard                                                         |
|  +-- /                      Overview (stats, quick actions)         |
|  +-- /search                Tiered candidate search UI              |
|  +-- /intelligence          Timing alerts, layoff exposure          |
|  +-- /network               Network activation messages             |
|  +-- /settings              Company settings, roles                 |
|                                                                     |
|  State Management:                                                  |
|  +-- localStorage['onboarding-state'] = {                           |
|        companyId: "100b5ac1-...",                                   |
|        company: { name, domain, ... },                              |
|        roles: [...],                                                |
|        linkedinImport: { records_created: 305 }                     |
|      }                                                              |
|                                                                     |
+---------------------------------------------------------------------+
```

---

## 6. Data Flow: Complete Example

### Confido Hiring a Software Engineer

```
+--------------------------------------------------------------------------+
| STEP 1: SETUP                                                            |
| User visits /public/setup.html -> localStorage populated with Confido ID |
| Redirects to /dashboard                                                  |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
| STEP 2: DASHBOARD LOADS                                                  |
| Frontend reads companyId from localStorage                               |
| Parallel API calls:                                                      |
|   - GET /companies/{id} -> Company info                                  |
|   - GET /companies/{id}/roles -> 4 roles                                 |
|   - GET /companies/{id}/network/stats -> 305 connections                 |
|   - GET /v3/company/digest/{id} -> Today's priority actions              |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
| STEP 3: USER SEARCHES                                                    |
| Clicks "Find Candidates" for Software Engineer role                      |
| POST /v2/search { company_id, role_title: "Software Engineer" }          |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
| STEP 4: SEARCH ENGINE PROCESSES                                          |
|                                                                          |
|  4a. Query Supabase for all 305 people                                   |
|                                                                          |
|  4b. For each person, calculate:                                         |
|      - match_score = skills_overlap + title_similarity + experience      |
|      - warmth_score = network_distance + shared_history                  |
|      - readiness_score = layoff_signals + tenure + activity              |
|      - combined_score = 0.4*match + 0.3*warmth + 0.3*readiness           |
|                                                                          |
|  4c. Bucket into tiers:                                                  |
|      - Tier 1: is_from_network=true, match_score > 60                    |
|      - Tier 2: has warm_path, warmth > 40                                |
|      - Tier 3: is_recruiter=true                                         |
|      - Tier 4: remaining qualified candidates                            |
|                                                                          |
|  4d. Sort each tier by combined_score DESC                               |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
| STEP 5: RESULTS DISPLAYED                                                |
|                                                                          |
|  Tier 1: Direct Network (31)                                             |
|  +--------------------------------------------------------------------+  |
|  | John Smith - Senior Software Engineer @ Google                     |  |
|  | Score: 87% | Match: 92% | Warmth: 100% | Readiness: 65%            |  |
|  | Why: "5 years backend experience, Python expert, you know him"     |  |
|  | Action: "Reach out directly - you connected at YC Demo Day"        |  |
|  +--------------------------------------------------------------------+  |
|                                                                          |
|  Tier 2: Warm Intro (24)                                                 |
|  +--------------------------------------------------------------------+  |
|  | Jane Doe - Backend Engineer @ Stripe                                |  |
|  | Score: 78% | Match: 85% | Warmth: 60% | Readiness: 80%             |  |
|  | Why: "Strong Python/Go skills, fintech experience"                 |  |
|  | Warm Path: "Sarah Chen worked with her at Stripe (2019-2021)"      |  |
|  | Action: "Ask Sarah for an introduction"                            |  |
|  +--------------------------------------------------------------------+  |
|                                                                          |
+--------------------------------------------------------------------------+
```

---

## 7. Intelligence Features Detail

### Timing Intelligence Page

Shows candidates organized by urgency level:

```
HIGH URGENCY (Act within 1 week)
+--------------------------------------------------------------------+
| [!] Mike Johnson - Senior Engineer @ Stripe                        |
|    Signal: Company announced layoffs affecting his department      |
|    Readiness Score: 95                                             |
|    Recommended Action: "Reach out immediately - timing is critical"|
+--------------------------------------------------------------------+

MEDIUM URGENCY (Act within 1 month)
+--------------------------------------------------------------------+
| [*] Lisa Park - Staff Engineer @ Google                            |
|    Signal: 4+ years at current role, updated LinkedIn recently     |
|    Readiness Score: 72                                             |
|    Recommended Action: "Good time to reconnect, likely exploring"  |
+--------------------------------------------------------------------+
```

### Layoff Exposure Analysis

Shows which companies in your network have had layoffs:

```
LAYOFF EXPOSURE SUMMARY
---------------------------------------------------
Your network: 305 people
Affected by recent layoffs: 23 people (7.5%)
Companies with layoffs: 5

BY COMPANY:
+--------------------------------------------------------------------+
| Stripe - 8 connections affected                                    |
| Layoff Date: January 2024 | Scale: 15% workforce                   |
| Urgency: HIGH                                                      |
| People: Mike J., Sarah L., James K., ...                           |
+--------------------------------------------------------------------+
| Meta - 5 connections affected                                      |
| Layoff Date: February 2024 | Scale: 10% workforce                  |
| Urgency: HIGH                                                      |
| People: Lisa P., Tom R., ...                                       |
+--------------------------------------------------------------------+
```

### Network Activation Messages

Pre-generated outreach messages for your connectors:

```
ROLE: Software Engineer
TOP CONNECTORS TO ACTIVATE:

1. Sarah Chen (Engineering Manager @ Stripe)
   Priority Score: 0.85
   Reason: "Manages 12 engineers, strong hiring network"

   Generated Message:
   +--------------------------------------------------------------------+
   | "Hey Sarah! Hope you're doing well. Quick question - we're         |
   | looking for a software engineer at Confido. Given your             |
   | experience at Stripe, would you know anyone who might be           |
   | a good fit? Looking for someone with strong backend skills         |
   | and fintech interest. Would really appreciate any                  |
   | recommendations!"                                                  |
   +--------------------------------------------------------------------+
   [Copy Message] [Open LinkedIn]
```

---

## 8. Technology Stack

### Backend
- **Runtime**: Python 3.11+
- **Framework**: FastAPI (async)
- **Database**: Supabase (PostgreSQL + REST API)
- **Vector Search**: Pinecone (for semantic candidate matching)
- **LLM**: OpenAI GPT-4 (for message generation, analysis)
- **Enrichment**: People Data Labs, Perplexity

### Frontend
- **Framework**: Next.js 16 (App Router)
- **Styling**: Tailwind CSS
- **State**: React hooks + localStorage
- **API Client**: Fetch with typed responses

### Infrastructure
- **Hosting**: Vercel (frontend), Railway/Fly.io (backend)
- **Database**: Supabase (managed PostgreSQL)
- **Vector DB**: Pinecone (managed)

---

## 9. API Reference

### Search Endpoint

```bash
POST /api/v2/search
Content-Type: application/json

{
  "company_id": "100b5ac1-1912-4970-a378-04d0169fd597",
  "role_title": "Software Engineer",
  "limit": 20
}

Response:
{
  "tier_1_network": [...],      # Direct connections
  "tier_2_one_intro": [...],    # Warm introductions
  "tier_3_recruiters": [...],   # Relevant recruiters
  "tier_4_cold": [...],         # Cold candidates
  "search_target": "Software Engineer",
  "search_duration_seconds": 1.23,
  "network_size": 305,
  "total_candidates": 81,
  "tier_1_count": 31,
  "tier_2_count": 24,
  "tier_3_count": 1,
  "tier_4_count": 25,
  "primary_recommendation": "Start with your 31 direct connections..."
}
```

### Timing Intelligence Endpoint

```bash
GET /api/v3/timing/network-analysis/{company_id}?limit=20

Response:
{
  "company_id": "100b5ac1-...",
  "total_analyzed": 305,
  "candidates_with_signals": 47,
  "by_urgency": {
    "high": [...],
    "medium": [...],
    "low": [...]
  }
}
```

### Layoff Exposure Endpoint

```bash
GET /api/v3/company/layoffs/{company_id}

Response:
{
  "total_network_members": 305,
  "affected_members": 23,
  "affected_percentage": 7.5,
  "companies_with_layoffs": 5,
  "by_company": {
    "Stripe": {
      "count": 8,
      "urgency": "high",
      "layoff_date": "2024-01-15",
      "scale": "15%",
      "members": [...]
    }
  }
}
```

---

## 10. File Structure

```
agencity/
+-- app/                          # Backend (FastAPI)
|   +-- api/
|   |   +-- routes/
|   |       +-- companies.py      # Company CRUD, imports
|   |       +-- search.py         # V2 tiered search
|   |       +-- intelligence.py   # V3 timing, layoffs
|   +-- core/
|   |   +-- config.py            # Settings, env vars
|   |   +-- database.py          # Supabase client
|   +-- services/
|   |   +-- search_v2.py         # Search engine
|   |   +-- timing_intel.py      # Timing analysis
|   |   +-- network_activation.py # Reverse reference
|   +-- main.py                   # FastAPI app entry
|
+-- web/                          # Frontend (Next.js)
|   +-- src/
|   |   +-- app/
|   |   |   +-- dashboard/
|   |   |   |   +-- page.tsx     # Overview
|   |   |   |   +-- search/      # Search UI
|   |   |   |   +-- intelligence/# Timing dashboard
|   |   |   |   +-- network/     # Activation messages
|   |   |   |   +-- settings/    # Company settings
|   |   |   +-- onboarding/      # Setup flow
|   |   +-- lib/
|   |   |   +-- api.ts           # API client
|   |   +-- components/          # Reusable UI
|   +-- public/
|       +-- setup.html           # Quick setup page
|
+-- docs/                         # Documentation
|   +-- architecture/            # System docs
|
+-- .env                         # Environment variables
```

---

## 11. Quick Start

### For Confido (Already Set Up)

1. Visit: `http://localhost:3000/setup.html`
2. Click "Set Up Dashboard"
3. You're in! Data already loaded.

### For New Companies

1. Complete onboarding at `/onboarding`
2. Upload LinkedIn connections CSV
3. Add roles you're hiring for
4. Start searching!

---

## 12. Key Metrics to Track

- **Search Efficiency**: Candidates contacted / Hires made
- **Tier Effectiveness**: % of hires from each tier
- **Network Utilization**: % of network contacted
- **Timing Accuracy**: % of "high urgency" that were actually open to opportunities
- **Message Response Rate**: % of activation messages that got responses

---

*Generated for Confido - Company ID: 100b5ac1-1912-4970-a378-04d0169fd597*
*305 connections | 4 active roles | Network Intelligence active*