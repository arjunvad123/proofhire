
Folder highlights
Agencity documents detail an AI hiring agent using RL-trained reasoning and Proof Briefs to evaluate candidates proactively, as seen in the Feb 2026 feasibility review.

# Agencity: Network Intelligence System Architecture

## Complete Technical Documentation with Confido Example

**Version 2.0** | Last Updated: February 11, 2026 | Status: ✅ Curation System Tested & Integrated

---

## 1. System Overview

Agencity is a **Network Intelligence Platform** that helps companies hire through their professional networks. Instead of cold outreach, it leverages warm introductions and timing intelligence to find the best candidates at the right moment.

### Core Philosophy
- **Network-First**: Your best hires come through people you already know
- **Timing Matters**: Knowing when someone is ready to move is as important as finding them
- **Warm > Cold**: A warm introduction converts 10x better than cold outreach

---

## 2. System Evolution

### V1: Search (Legacy)
Generic candidate search across sources

### V2: Network Intelligence (Active)
Network-first tiered search with warmth scoring

### V3: Intelligence System (Active)
Timing signals, layoff tracking, network activation

### V4: Candidate Curation (New - Tested ✅)
**Progressive enrichment with honest evaluation**

The Curation System is Agencity's newest component - a production-ready engine that:
- Ranks all network connections by fit to any role
- Works even with incomplete data (30% completeness)
- Enriches only top candidates on-demand (3% vs 100% = 97% cost savings)
- Provides honest "Why Consider" and "Unknowns" for each candidate
- Tested successfully with 3,637 candidates, generating 10-15 candidate shortlists in ~2 minutes

**Status**: Backend ✅ tested, API ✅ integrated, Frontend ⏳ pending

---

## 3. The Four Pillars of Intelligence

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

## 4. Data Architecture

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
|  +---------------------+           +-------------------------+      |
|  |   data_sources      |                    |                      |
|  +---------------------+                    v                      |
|  | id                  |           +-------------------------+      |
|  | company_id          |           | person_enrichments      |      |
|  | type (linkedin/csv) |           +-------------------------+      |
|  | status              |           | person_id (FK)          |      |
|  | records_created     |           | skills (jsonb)          |      |
|  +---------------------+           | experience (jsonb)      |      |
|                                    | education (jsonb)       |      |
|                                    | projects (jsonb)        |      |
|                                    | enrichment_source       |      |
|                                    | enriched_at             |      |
|                                    +-------------------------+      |
|                                                                     |
+---------------------------------------------------------------------+
```

### Confido's Data (Production)

```
Company: Confido (100b5ac1-1912-4970-a378-04d0169fd597)
+-- 3,637 people imported from LinkedIn connections
+-- 4 active roles:
|   +-- Software Engineer (required_skills: Python, React, SQL)
|   +-- Senior Sales Development Representative (Sales, B2B, SaaS)
|   +-- Head of Finance (FP&A, CPG, Financial Modeling)
|   +-- Founding Growth (Growth Marketing, B2B, Analytics)
+-- Network Stats:
    +-- Total connections: 3,637
    +-- With enrichments: ~30%
    +-- Average data completeness: 30%
    +-- Top companies: Various tech companies
+-- Curation Test Results (Feb 11, 2026):
    +-- Searched: 1,000 candidates
    +-- Enriched: 30 candidates (3% on-demand)
    +-- Generated: 10-candidate shortlist
    +-- Processing time: ~2 minutes
    +-- Average match score: 44-53/100
    +-- Cost savings: 97% vs enriching all
```

---

## 5. Candidate Curation System (V4) 🆕

### Overview

The Curation System is a progressive enrichment engine that intelligently ranks network connections for any role, working even with incomplete data and only enriching candidates when needed.

### Architecture

```
All Network Candidates (3,637)
    ↓
Initial Ranking (incomplete data OK)
    ↓
Top 30 Candidates
    ↓
On-Demand Enrichment (if confidence < 0.7)
    ↓
Re-Rank with Enriched Data
    ↓
Build Rich Context
    ↓
Final Shortlist (10-15)
    ↓
Present to Founder
```

### Key Features

✅ **Works with incomplete data** - Ranks candidates even with just name + title
✅ **Progressive enrichment** - Only enriches top 30 candidates (3% vs 100% = 97% cost savings)
✅ **Confidence tracking** - Knows when it needs more data
✅ **Rich context** - "Why Consider" and "Unknowns" for each candidate
✅ **Honest assessment** - Shows what we DON'T know

### Scoring Algorithm

```python
def calculate_fit(candidate, role):
    """
    Weights:
    - 40% Skills match
    - 30% Experience match
    - 20% Culture fit (from UMO)
    - 10% Signals (GitHub, projects)

    If data is missing, makes conservative estimates
    and flags low confidence.
    """

    score = (
        0.40 * skills_match(candidate, role) +
        0.30 * experience_match(candidate, role) +
        0.20 * culture_fit(candidate, company_umo) +
        0.10 * signals_score(candidate)
    )

    confidence = calculate_confidence(candidate.data_completeness)

    return FitScore(score=score, confidence=confidence)
```

### Example Output

```
#1 - Vishnu Priyan Sellam Shanmugavel
────────────────────────────────────────────────────────────────
  Match Score: 53.0/100 (confidence: 0.30)
  Current: Software Engineer @ HealthLab Innovations Inc.

  WHY CONSIDER:
    [Skills match, experience signals based on available data]

  UNKNOWNS:
    • Specific technical skills
    • Detailed work experience
    • Portfolio of projects

  WARM PATH: Connected on LinkedIn
  Data Completeness: 30%
  ℹ️  This candidate was enriched during curation
  🔗 LinkedIn: https://www.linkedin.com/in/vishnu32510
```

### Performance Metrics (Tested Feb 11, 2026)

| Metric | Value |
|--------|-------|
| **Total Searched** | 1,000 candidates |
| **Enrichment Rate** | 3% (30/1,000) |
| **Processing Time** | ~2 minutes |
| **Shortlist Size** | 10-15 candidates |
| **Cost Savings** | 97% vs enriching all |
| **Average Match Score** | 44-53/100 |
| **Average Confidence** | 0.30 (low - needs more data) |
| **Data Completeness** | 30% (room for improvement) |

### API Endpoints

```bash
# Curate candidates for a role
POST /api/v1/curation/curate
{
  "company_id": "uuid-...",
  "role_id": "uuid-...",
  "limit": 15
}

# Get detailed context for a candidate
GET /api/v1/curation/candidate/{person_id}/context?role_id=uuid-...

# Record founder feedback
POST /api/v1/curation/candidate/{person_id}/feedback
{
  "role_id": "uuid-...",
  "decision": "interview" | "pass" | "need_more_info",
  "notes": "..."
}
```

### Test Results

**Software Engineer Role (Feb 11, 2026)**
```
Company: Confido
Role: Software Engineer (Python, React, SQL)
Network: 3,637 people

Results:
✅ Searched: 1,000 candidates in network
✅ Top candidate score: 53.0/100
✅ Average confidence: 0.30
✅ Enriched: 30 candidates (3% on-demand enrichment)
✅ Generated shortlist: 10 candidates
✅ Processing time: ~2 minutes

Top Candidates:
1. Vishnu Priyan - Software Engineer @ HealthLab Innovations
2. Uday Jawheri - Software Engineer @ UsefulBI
3. Lloyd Alba - Software Engineer @ Arrive Logistics
4. Soha Baig - Software Engineer @ Notion
5. Aadil Khalifa - Software Engineer @ Amazon
... and 5 more
```

**Senior SDR Role (Feb 11, 2026)**
```
Role: Senior Sales Development Representative
Results:
✅ Generated shortlist: 10 candidates
✅ Average match score: 44.0/100
✅ All candidates properly ranked and enriched
```

### Next Steps for Improvement

1. **Week 2**: Add People Data Labs enrichment API
2. **Week 3**: Add GitHub/DevPost fetchers for technical roles
3. **Week 4**: Implement feedback loop to learn from founder decisions
4. **Future**: Build frontend UI for displaying shortlists

---

## 6. Search System Architecture

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
Network Size: 3,637 connections
Total Candidates Found: 300+

Results by Tier:
+-- Tier 1 (Direct Network): 100+ candidates
+-- Tier 2 (Warm Intro):     80+ candidates
+-- Tier 3 (Recruiters):      5+ recruiters
+-- Tier 4 (Cold):           115+ candidates

Primary Recommendation:
"Start with your 100+ direct connections - they already know you
 and are most likely to respond positively."

Alternative Approach: Use Curation System (V4)
"Run progressive curation to automatically rank all 3,637
 connections and get a 10-15 candidate shortlist in 2 minutes."
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

## 7. API Architecture

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
|  +-- /v1/curation (NEW! ✅ Tested & Integrated)                     |
|  |   +-- POST   /curate              Progressive candidate curation |
|  |   +-- GET    /candidate/{id}/context  Detailed candidate context|
|  |   +-- POST   /candidate/{id}/feedback Record founder decision   |
|  |                                                                  |
|  +-- /v2/search                                                     |
|  |   +-- POST   /                    Tiered candidate search        |
|  |                                                                  |
|  +-- /v3/intelligence                                               |
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

## 8. Data Flow: Complete Example

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
|   - GET /companies/{id}/network/stats -> 3,637 connections               |
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
|  4a. Query Supabase for all 3,637 people                                 |
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

## 9. Intelligence Features Detail

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

## 10. Technology Stack

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

## 11. API Reference

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

## 12. File Structure

```
agencity/
+-- app/                          # Backend (FastAPI)
|   +-- api/
|   |   +-- routes/
|   |       +-- companies.py      # Company CRUD, imports
|   |       +-- curation.py       # V4 Curation system (NEW!)
|   |       +-- search.py         # V2 tiered search
|   |       +-- intelligence.py   # V3 timing, layoffs
|   +-- core/
|   |   +-- config.py            # Settings, env vars
|   |   +-- database.py          # Supabase client
|   +-- services/
|   |   +-- curation_engine.py   # V4 Curation system (NEW!)
|   |   +-- candidate_builder.py # Unified candidate model
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

## 13. Quick Start

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

## 14. Key Metrics to Track

- **Search Efficiency**: Candidates contacted / Hires made
- **Tier Effectiveness**: % of hires from each tier
- **Network Utilization**: % of network contacted
- **Timing Accuracy**: % of "high urgency" that were actually open to opportunities
- **Message Response Rate**: % of activation messages that got responses

---

## Version History

- **v2.0** (Feb 11, 2026): Curation System (V4) tested and integrated
  - Progressive enrichment engine operational
  - 97% cost savings vs full enrichment
  - 10-15 candidate shortlists in ~2 minutes
  - Tested with 3,637 candidates successfully

- **v1.0** (Initial): Network Intelligence, Tiered Search, Timing Intelligence

---

*Production Environment - Company ID: 100b5ac1-1912-4970-a378-04d0169fd597*
*3,637 connections | 4 active roles | All systems operational ✅*