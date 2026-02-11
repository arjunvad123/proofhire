# Agencity Network Intelligence System

## Complete Documentation v2.0

**Last Updated:** 2025-02-11
**Status:** Active Development
**Version:** 2.0 (Network Intelligence)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Philosophy](#philosophy)
3. [What We've Built (Completed)](#what-weve-built-completed)
4. [The New Approach](#the-new-approach)
5. [System Architecture](#system-architecture)
6. [Implementation Plan](#implementation-plan)
7. [Data Models](#data-models)
8. [API Reference](#api-reference)
9. [Algorithms](#algorithms)
10. [Metrics & Success Criteria](#metrics--success-criteria)

---

## Executive Summary

### The Problem

Traditional recruiting tools search for candidates externally and reach out cold. Response rates are <5% because:
- Candidates are overwhelmed with recruiter spam
- No trust or relationship exists
- No differentiation from 100 other outreach messages

### The Solution

Agencity treats the founder's network as an **intelligence network**, not just a contact list.

**Key Insight:** Your 63 ML engineers have collectively worked with **thousands** of other ML engineers. They know who's brilliant, who's available, and who they'd personally vouch for.

**The Paradigm Shift:**
```
OLD: Search APIs → Find candidates → Cold outreach (5% response)
NEW: Activate network → Receive recommendations → Warm intros (60%+ response)
```

### The Four Pillars

| Pillar | Description | ROI |
|--------|-------------|-----|
| **Network Activation** | Ask network for recommendations | Highest signal, lowest tech |
| **Timing Intelligence** | Predict who's ready before they know | Novel, high conversion |
| **Former Colleague Expansion** | Find people who worked WITH your network | Scalable, warm paths |
| **Company Intelligence** | Monitor layoffs, funding, departures | Opportunistic timing |

---

## Philosophy

### Core Principles

1. **Network members are intelligence sources, not just candidates**
   - Each person knows 50-200 colleagues
   - They know who's actually good (not resume-good)
   - They know who's quietly unhappy

2. **Warm always beats cold**
   - A referral from a friend > 100 cold emails
   - Trust transfers through introductions
   - Response rates 10-20x higher

3. **Timing is everything**
   - Same person: "not interested" today, "very interested" after their 4-year vest
   - Pre-empt the competition by reaching out before "Open to Work"
   - Company troubles = opportunity to help people

4. **The best candidates aren't looking**
   - Top talent is happily employed
   - They don't respond to recruiters
   - Only reachable through trusted connections

5. **Ask, don't search**
   - "Who's the best ML engineer you've worked with?" > Any API query
   - Your network has already done the filtering
   - Leverage their judgment, not just their connections

---

## What We've Built (Completed)

### Stage 0: Company Onboarding ✅
- Company registration and profile
- API key generation
- Database schema in Supabase

### Stage 1: Data Import ✅
- LinkedIn CSV import
- 3,637 connections imported
- Stored in `people` table with `is_from_network=true`

### Stage 2: V1 Search System ✅
- 4 API integrations (PDL, Google CSE, GitHub, Perplexity)
- Network analyzer and pathway scorer
- Query generator for each API

**Problem Identified:** V1 found famous, unreachable people with no network connection.

### Stage 3: V2 Network-First Search ✅
- Search within network first (Tier 1)
- Readiness scoring (tenure, layoffs, title signals)
- Recruiter identification
- Warm path calculator

**Results:** Found 63 ML engineers in network, 9 recruiters

### Files Created

```
app/
├── api/routes/
│   ├── search.py          # V1 endpoints
│   └── search_v2.py       # V2 endpoints ✅
├── search/
│   ├── models.py          # Data models
│   ├── engine.py          # V1 engine
│   ├── engine_v2.py       # V2 engine ✅
│   ├── network_search.py  # Search within network ✅
│   ├── readiness.py       # Readiness scoring ✅
│   ├── recruiters.py      # Recruiter finder ✅
│   ├── warm_path.py       # Warm path calculator ✅
│   ├── analyzers/
│   │   └── network.py     # Node classification
│   ├── generators/
│   │   └── query.py       # API query generation
│   ├── scoring/
│   │   ├── pathway.py     # Pathway scoring
│   │   └── ranker.py      # Candidate ranking
│   └── sources/
│       ├── base.py
│       ├── pdl.py         # People Data Labs
│       ├── google.py      # Google Custom Search
│       ├── github.py      # GitHub API
│       └── perplexity.py  # Perplexity AI
└── services/
    └── company_db.py      # Supabase service
```

---

## The New Approach

### The Intelligence Network Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTELLIGENCE NETWORK                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    NETWORK ACTIVATION (Pillar 1)                     │   │
│  │                                                                      │   │
│  │  "Reverse Reference" - Ask network for recommendations               │   │
│  │  "Who's the best ML engineer you've ever worked with?"              │   │
│  │                                                                      │   │
│  │  → Highest signal (they've seen the person's actual work)           │   │
│  │  → Warm intro guaranteed (they recommended the person)              │   │
│  │  → Lowest tech (just needs messaging + tracking)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    TIMING INTELLIGENCE (Pillar 2)                    │   │
│  │                                                                      │   │
│  │  Predict readiness BEFORE they're actively looking                  │   │
│  │                                                                      │   │
│  │  Signals:                                                            │   │
│  │  • 4-year anniversary (vesting cliff) → reach out 2 months before   │   │
│  │  • Company layoffs announced → reach out immediately                │   │
│  │  • Manager departed → org instability, people looking               │   │
│  │  • Funding running low → startup might fail                         │   │
│  │                                                                      │   │
│  │  → Pre-empt competition (you're the only one reaching out)          │   │
│  │  → Higher conversion (catching them at decision point)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                 FORMER COLLEAGUE EXPANSION (Pillar 3)                │   │
│  │                                                                      │   │
│  │  Same company + Same time = They actually know each other           │   │
│  │                                                                      │   │
│  │  For each network member:                                           │   │
│  │  • Get their employment history (companies + dates)                 │   │
│  │  • Query: "ML engineers who worked at [company] [dates]"            │   │
│  │  • Filter: Now at different company (they moved)                    │   │
│  │  • Result: People they can personally introduce                     │   │
│  │                                                                      │   │
│  │  → Scalable (can find hundreds of warm connections)                 │   │
│  │  → Warm path is obvious ("You worked with them at Google")          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   COMPANY INTELLIGENCE (Pillar 4)                    │   │
│  │                                                                      │   │
│  │  Monitor companies where network members work                       │   │
│  │                                                                      │   │
│  │  Events to track:                                                   │   │
│  │  • Layoffs announced → "5 people in your network are affected"      │   │
│  │  • Acquisition → "Vesting accelerated, people might leave"          │   │
│  │  • Bad earnings → "Company struggling, morale low"                  │   │
│  │  • Exec departure → "Org instability"                               │   │
│  │  • No funding in 18mo → "Startup might be failing"                  │   │
│  │                                                                      │   │
│  │  → Opportunistic timing                                             │   │
│  │  → Help people when they need it                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Tiered Output

```
═══════════════════════════════════════════════════════════════════════════════
TIER 0: NETWORK RECOMMENDATIONS (Highest Signal)
═══════════════════════════════════════════════════════════════════════════════
People recommended directly by your network:

"Nikhil recommended: Sarah Chen"
  • Nikhil says: "Best ML engineer I worked with at Google"
  • Sarah's status: Recently left for Anthropic, might be recruitable
  • Action: Ask Nikhil to make intro

═══════════════════════════════════════════════════════════════════════════════
TIER 1: IN YOUR NETWORK (63 ML Engineers)
═══════════════════════════════════════════════════════════════════════════════
People directly connected to founder:

• Nikhil Kulkarni - Applied AI Engineer @ Google
  🔥 Timing: Company had layoffs, might be nervous
  ✅ Action: Message directly

═══════════════════════════════════════════════════════════════════════════════
TIER 2A: FORMER COLLEAGUES (Warm via Employment Overlap)
═══════════════════════════════════════════════════════════════════════════════
People who worked WITH your network members:

• James Park - ex-Google, now at Scale AI
  🤝 Via: Nikhil (worked together at Google 2021-2023)
  🔥 Timing: 2 years at Scale (might be ready to move)
  ✅ Action: Ask Nikhil for intro

═══════════════════════════════════════════════════════════════════════════════
TIER 2B: SCHOOL CONNECTIONS (Warm via Education Overlap)
═══════════════════════════════════════════════════════════════════════════════
People who went to school WITH your network members:

• Emily Wang - Stanford PhD, now at DeepMind
  🤝 Via: Maxim (same PhD cohort)
  ✅ Action: Ask Maxim for intro

═══════════════════════════════════════════════════════════════════════════════
TIER 2C: TIMING OPPORTUNITIES (Ready to Move)
═══════════════════════════════════════════════════════════════════════════════
People with strong readiness signals + warm path:

• Mike Liu - ML Engineer, 4 years at Stripe
  🔥 Timing: Vesting cliff in 2 months
  🤝 Via: [Network member who worked at Stripe]
  ✅ Action: Reach out now, before cliff

═══════════════════════════════════════════════════════════════════════════════
TIER 3: RECRUITERS (9 in Network)
═══════════════════════════════════════════════════════════════════════════════
Ask them for referrals - they know who's actively looking:

• Mehak Verma (tech specialty)
  ✅ Action: "Who's actively looking for ML roles right now?"

═══════════════════════════════════════════════════════════════════════════════
TIER 4: COLD (No Warm Path)
═══════════════════════════════════════════════════════════════════════════════
Only if above tiers exhausted. Low response rate expected.
```

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│                         (FastAPI - app/api/)                                │
│                                                                              │
│  POST /v3/search              - Full intelligence search                    │
│  POST /v3/activate            - Send activation requests to network         │
│  GET  /v3/recommendations     - Get recommendations received                │
│  GET  /v3/timing-alerts       - Get timing-based opportunities             │
│  GET  /v3/company-intelligence - Get company events affecting network      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INTELLIGENCE ENGINE                                  │
│                      (app/intelligence/engine.py)                           │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Network    │  │   Timing    │  │  Expansion  │  │  Company    │       │
│  │ Activation  │  │Intelligence │  │   Engine    │  │Intelligence │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Supabase   │  │   PDL API   │  │  News API   │  │ Crunchbase  │       │
│  │  (People)   │  │(Enrichment) │  │  (Events)   │  │ (Funding)   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Network Activation System
```
app/intelligence/
├── activation/
│   ├── reverse_reference.py    # "Who would you recommend?"
│   ├── referral_request.py     # "Can you post in your network?"
│   ├── community_access.py     # "Can you intro me to [community]?"
│   └── message_generator.py    # Personalized outreach messages
```

#### 2. Timing Intelligence System
```
app/intelligence/
├── timing/
│   ├── tenure_tracker.py       # Track time at company
│   ├── vesting_predictor.py    # Predict vesting cliffs
│   ├── readiness_scorer.py     # Combined readiness score
│   └── outreach_scheduler.py   # When to reach out
```

#### 3. Expansion Engine
```
app/intelligence/
├── expansion/
│   ├── colleague_expander.py   # Former colleague discovery
│   ├── school_expander.py      # School cohort discovery
│   ├── github_expander.py      # Code collaborator discovery
│   └── warm_path_finder.py     # Find paths through network
```

#### 4. Company Intelligence
```
app/intelligence/
├── company/
│   ├── event_monitor.py        # Monitor company events
│   ├── layoff_tracker.py       # Track layoff announcements
│   ├── funding_tracker.py      # Track funding/runway
│   └── alert_generator.py      # Generate alerts
```

---

## Implementation Plan

### Priority Order (by ROI)

| Phase | Pillar | ROI | Effort | Timeline |
|-------|--------|-----|--------|----------|
| 1 | Network Activation | Highest | Low | Week 1 |
| 2 | Timing Intelligence | High | Medium | Week 2 |
| 3 | Former Colleague Expansion | High | Medium | Week 3 |
| 4 | Company Intelligence | Medium | High | Week 4 |

### Phase 1: Network Activation (Week 1)

**Goal:** Enable "Reverse Reference" - asking network for recommendations

**Tasks:**

1.1 Create activation request system
```python
# Generate personalized asks for each network member
{
    "target": "Nikhil Kulkarni",
    "template": "reverse_reference",
    "message": "Hey Nikhil, I'm building the ML team at [Company]..."
}
```

1.2 Create recommendation tracking
```python
# Track recommendations received
{
    "recommender_id": "uuid",
    "recommended_person": {
        "name": "Sarah Chen",
        "linkedin": "...",
        "context": "Best ML engineer I worked with at Google"
    },
    "status": "pending_intro"
}
```

1.3 Create intro request generator
```python
# Generate intro requests
{
    "to": "Nikhil",
    "about": "Sarah Chen",
    "message": "Thanks for recommending Sarah! Would you be open to..."
}
```

**Deliverables:**
- `POST /v3/activate/reverse-reference` - Send asks to network
- `POST /v3/recommendations` - Record recommendations
- `GET /v3/recommendations` - View all recommendations
- Dashboard showing activation → recommendation → intro pipeline

### Phase 2: Timing Intelligence (Week 2)

**Goal:** Predict who's ready to move before they know it

**Tasks:**

2.1 Tenure tracking
```python
# For each person in network + discovered candidates
{
    "person_id": "uuid",
    "current_company": "Google",
    "start_date": "2021-03",
    "tenure_months": 35,
    "vesting_cliff_date": "2025-03",  # 4-year cliff
    "months_to_cliff": 2,
    "timing_score": 0.8  # High - approaching cliff
}
```

2.2 Readiness prediction
```python
# Combine signals into readiness score
signals = {
    "tenure_cliff_approaching": 0.3,
    "company_had_layoffs": 0.3,
    "manager_departed": 0.2,
    "title_signals": 0.1,  # "consultant", etc.
    "profile_updated_recently": 0.1
}
readiness_score = sum(signals.values())  # 0-1
```

2.3 Outreach scheduler
```python
# When to reach out
{
    "person_id": "uuid",
    "recommended_action": "reach_out_now",
    "reason": "Vesting cliff in 2 months",
    "urgency": "high"
}
```

**Deliverables:**
- `GET /v3/timing-alerts` - Get list of timing opportunities
- `GET /v3/timing/{person_id}` - Get timing analysis for person
- Alerts: "5 people approaching vesting cliff in next 60 days"

### Phase 3: Former Colleague Expansion (Week 3)

**Goal:** Find people who worked WITH network members

**Tasks:**

3.1 Employment history enrichment
```python
# Enrich network with employment history
# Use PDL to get work history with dates
{
    "person_id": "uuid",
    "employment_history": [
        {"company": "Google", "start": "2021-03", "end": "2024-01"},
        {"company": "Meta", "start": "2019-01", "end": "2021-02"}
    ]
}
```

3.2 Colleague discovery
```python
# For each network member's employment history
# Query PDL for overlapping employees
query = {
    "company": "Google",
    "dates": "2021-2024",
    "role": "ML Engineer",
    "filter": "no_longer_at_google"  # They moved
}
# Returns people who worked WITH network member
```

3.3 Warm path calculation
```python
# For each discovered candidate
{
    "candidate": "Sarah Chen",
    "warm_path": {
        "via": "Nikhil Kulkarni",
        "relationship": "Worked together at Google (2021-2023)",
        "overlap_months": 24,
        "warmth_score": 0.85
    }
}
```

**Deliverables:**
- `POST /v3/expand/colleagues` - Discover former colleagues
- Enrichment pipeline for employment history
- Warm path display for each candidate

### Phase 4: Company Intelligence (Week 4)

**Goal:** Monitor company events that affect network

**Tasks:**

4.1 Company tracking
```python
# Track companies where network members work
companies = {
    "Google": {"network_members": 5, "watch": True},
    "Meta": {"network_members": 3, "watch": True},
    "Stripe": {"network_members": 2, "watch": True}
}
```

4.2 Event monitoring
```python
# Monitor for events
events = [
    {"type": "layoff", "company": "Google", "date": "2024-01", "impact": 12000},
    {"type": "funding", "company": "StartupX", "date": "2024-06", "amount": 0},
    {"type": "exec_departure", "company": "Meta", "date": "2024-02"}
]
```

4.3 Alert generation
```python
# Generate alerts
{
    "alert_type": "layoff",
    "company": "Google",
    "network_impact": [
        {"name": "Nikhil", "likely_affected": True},
        {"name": "Sarah", "likely_affected": False}
    ],
    "recommended_action": "Check in on Nikhil, offer support"
}
```

**Deliverables:**
- `GET /v3/company-intelligence` - Get company events
- `GET /v3/company/{name}/alerts` - Get alerts for company
- Dashboard: "Companies in your network with recent events"

---

## Data Models

### Supabase Tables

#### `activation_requests`
```sql
CREATE TABLE activation_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    target_person_id UUID REFERENCES people(id),

    -- Request details
    template_type TEXT,  -- 'reverse_reference', 'referral_request', etc.
    message_content TEXT,

    -- Status
    status TEXT DEFAULT 'pending',  -- 'pending', 'sent', 'responded', 'no_response'
    sent_at TIMESTAMPTZ,
    responded_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `recommendations`
```sql
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),

    -- Who recommended
    recommender_id UUID REFERENCES people(id),
    activation_request_id UUID REFERENCES activation_requests(id),

    -- Who was recommended
    recommended_name TEXT NOT NULL,
    recommended_linkedin TEXT,
    recommended_email TEXT,
    recommended_context TEXT,  -- "Best ML engineer I worked with"

    -- Status
    status TEXT DEFAULT 'new',  -- 'new', 'intro_requested', 'intro_made', 'contacted', 'converted'

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `employment_history`
```sql
CREATE TABLE employment_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES people(id),

    company_name TEXT NOT NULL,
    title TEXT,
    start_date DATE,
    end_date DATE,  -- NULL if current
    is_current BOOLEAN DEFAULT FALSE,

    -- For colleague matching
    normalized_company TEXT,  -- Lowercase, cleaned

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `timing_signals`
```sql
CREATE TABLE timing_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES people(id),

    -- Tenure
    current_company TEXT,
    tenure_start DATE,
    tenure_months INTEGER,
    vesting_cliff_date DATE,
    months_to_cliff INTEGER,

    -- Signals
    company_had_layoffs BOOLEAN DEFAULT FALSE,
    layoff_date DATE,
    manager_departed BOOLEAN DEFAULT FALSE,
    title_signals TEXT[],  -- ['consultant', 'advisor', etc.]
    profile_updated_recently BOOLEAN DEFAULT FALSE,

    -- Score
    readiness_score FLOAT,
    recommended_action TEXT,
    action_urgency TEXT,  -- 'high', 'medium', 'low', 'wait'

    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `company_events`
```sql
CREATE TABLE company_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    company_name TEXT NOT NULL,
    normalized_name TEXT,

    event_type TEXT,  -- 'layoff', 'funding', 'acquisition', 'exec_departure'
    event_date DATE,
    event_details JSONB,  -- Flexible storage for event-specific data

    source_url TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `warm_paths`
```sql
CREATE TABLE warm_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),

    -- The candidate
    candidate_id UUID REFERENCES people(id),  -- NULL if not in our DB yet
    candidate_name TEXT,
    candidate_linkedin TEXT,

    -- The path
    via_person_id UUID REFERENCES people(id),
    path_type TEXT,  -- 'colleague', 'school', 'github', 'recommendation'
    relationship_description TEXT,
    overlap_details JSONB,  -- Company, dates, etc.

    warmth_score FLOAT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## API Reference

### V3 Endpoints (Intelligence System)

#### Network Activation

```
POST /api/v3/activate/reverse-reference
    Request:  { "company_id": "uuid", "target_ids": ["uuid", ...] }
    Response: { "requests_created": 10, "messages": [...] }

    Generates personalized "who would you recommend?" messages.

POST /api/v3/activate/referral-request
    Request:  { "company_id": "uuid", "target_id": "uuid", "community": "slack" }
    Response: { "message": "...", "suggested_post": "..." }

    Generates request for network member to post in their community.

GET /api/v3/recommendations/{company_id}
    Response: { "recommendations": [...], "stats": {...} }

    Get all recommendations received, with status.

POST /api/v3/recommendations
    Request:  { "recommender_id": "uuid", "recommended": {...} }
    Response: { "id": "uuid", "intro_request_message": "..." }

    Record a recommendation and generate intro request.
```

#### Timing Intelligence

```
GET /api/v3/timing-alerts/{company_id}
    Response: {
        "immediate": [...],      // Act now
        "upcoming": [...],       // Next 60 days
        "watch_list": [...]      // 6+ months
    }

    Get timing-based opportunities.

GET /api/v3/timing/person/{person_id}
    Response: {
        "tenure_months": 35,
        "vesting_cliff": "2025-03-01",
        "readiness_score": 0.8,
        "signals": [...],
        "recommended_action": "reach_out_now",
        "suggested_message": "..."
    }

    Get timing analysis for specific person.
```

#### Expansion

```
POST /api/v3/expand/colleagues/{company_id}
    Request:  { "network_member_ids": ["uuid", ...] }
    Response: {
        "discovered": 150,
        "with_warm_paths": 120,
        "candidates": [...]
    }

    Discover former colleagues of network members.

GET /api/v3/expand/school/{company_id}
    Response: { "school_connections": [...] }

    Discover school cohort connections.

GET /api/v3/warm-path/{candidate_linkedin}
    Request:  { "company_id": "uuid" }
    Response: {
        "paths": [
            { "via": "Nikhil", "warmth": 0.85, "relationship": "..." }
        ],
        "best_path": {...}
    }

    Find warm paths to any candidate.
```

#### Company Intelligence

```
GET /api/v3/company-intelligence/{company_id}
    Response: {
        "companies_watched": 25,
        "recent_events": [...],
        "network_impact": [...]
    }

    Get company events affecting network.

GET /api/v3/company/{company_name}/events
    Response: { "events": [...] }

    Get events for specific company.

POST /api/v3/company/watch
    Request:  { "company_id": "uuid", "company_names": [...] }
    Response: { "watching": [...] }

    Add companies to watch list.
```

---

## Algorithms

### Readiness Score Calculation

```python
def calculate_readiness_score(person: dict) -> float:
    score = 0.0

    # Tenure signals (30% weight)
    tenure_months = person.get('tenure_months', 0)
    if tenure_months >= 42 and tenure_months <= 48:  # Approaching 4-year cliff
        score += 0.30
    elif tenure_months >= 36 and tenure_months < 42:
        score += 0.20
    elif tenure_months >= 24:
        score += 0.10

    # Company signals (30% weight)
    if person.get('company_had_layoffs'):
        score += 0.30
    elif person.get('company_funding_low'):
        score += 0.25
    elif person.get('manager_departed'):
        score += 0.15

    # Title signals (20% weight)
    title = person.get('title', '').lower()
    if 'consultant' in title or 'advisor' in title:
        score += 0.20
    elif 'open to' in title or 'seeking' in title:
        score += 0.20
    elif 'ex-' in title or 'former' in title:
        score += 0.15

    # Activity signals (20% weight)
    if person.get('profile_updated_recently'):
        score += 0.10
    if person.get('actively_posting'):
        score += 0.05
    if person.get('open_to_work_badge'):
        score += 0.20

    return min(1.0, score)
```

### Warmth Score Calculation

```python
def calculate_warmth_score(candidate: dict, network_member: dict) -> float:
    # Direct connection
    if is_direct_connection(candidate, network_member):
        return 1.0

    # Same small startup (<50 people)
    if same_small_company(candidate, network_member):
        return 0.95

    # Recommended by network member
    if was_recommended_by(candidate, network_member):
        return 0.90

    # Same team at company
    if same_team(candidate, network_member):
        return 0.90

    # Same company, overlapping dates
    overlap = employment_overlap_months(candidate, network_member)
    if overlap >= 12:
        return 0.85
    elif overlap >= 6:
        return 0.75
    elif overlap > 0:
        return 0.60

    # Co-contributors on GitHub
    if github_collaborators(candidate, network_member):
        return 0.80

    # Co-authors on papers
    if paper_coauthors(candidate, network_member):
        return 0.85

    # Same school, overlapping years
    if school_overlap(candidate, network_member):
        return 0.70

    # Same industry only
    if same_industry(candidate, network_member):
        return 0.30

    # No connection
    return 0.0
```

### Candidate Ranking

```python
def rank_candidates(candidates: list, target: SearchTarget) -> list:
    for candidate in candidates:
        # Match score (40% weight)
        match_score = calculate_match_score(candidate, target)

        # Readiness score (30% weight)
        readiness_score = calculate_readiness_score(candidate)

        # Warmth score (30% weight)
        warmth_score = candidate.get('warmth_score', 0)

        # Combined score
        candidate['combined_score'] = (
            match_score * 0.40 +
            readiness_score * 0.30 +
            warmth_score * 0.30
        )

    # Sort by combined score
    return sorted(candidates, key=lambda x: x['combined_score'], reverse=True)
```

---

## Metrics & Success Criteria

### Key Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Activation Rate** | % of network members who respond to asks | >30% |
| **Recommendation Rate** | Recommendations per activation | >0.5 |
| **Intro Conversion** | % of intros that lead to conversation | >60% |
| **Timing Accuracy** | % of "ready" predictions that were accurate | >50% |
| **Warm Path Coverage** | % of candidates with warm path | >70% |
| **Response Rate (Warm)** | Response rate for warm outreach | >40% |
| **Response Rate (Cold)** | Response rate for cold outreach | <10% |

### Success Criteria

**Phase 1 (Network Activation):**
- Send activation requests to 50 network members
- Receive 25+ recommendations
- Convert 10+ recommendations to intros

**Phase 2 (Timing Intelligence):**
- Identify 20+ people approaching vesting cliff
- Achieve 50%+ response rate on pre-cliff outreach
- Track timing signal → actual move correlation

**Phase 3 (Expansion):**
- Discover 200+ former colleagues with warm paths
- Achieve 40%+ response rate on warm outreach
- Build employment history for 100+ network members

**Phase 4 (Company Intelligence):**
- Track 25+ companies
- Detect 10+ relevant events
- Generate 5+ actionable alerts

---

## File Structure (Planned)

```
app/
├── api/routes/
│   ├── search.py              # V1 (legacy)
│   ├── search_v2.py           # V2 (network-first)
│   └── intelligence.py        # V3 (intelligence system) [NEW]
│
├── intelligence/              # [NEW - All new files]
│   ├── engine.py              # Main orchestrator
│   │
│   ├── activation/
│   │   ├── __init__.py
│   │   ├── reverse_reference.py
│   │   ├── referral_request.py
│   │   ├── community_access.py
│   │   └── message_generator.py
│   │
│   ├── timing/
│   │   ├── __init__.py
│   │   ├── tenure_tracker.py
│   │   ├── vesting_predictor.py
│   │   ├── readiness_scorer.py
│   │   └── outreach_scheduler.py
│   │
│   ├── expansion/
│   │   ├── __init__.py
│   │   ├── colleague_expander.py
│   │   ├── school_expander.py
│   │   ├── github_expander.py
│   │   └── warm_path_finder.py
│   │
│   └── company/
│       ├── __init__.py
│       ├── event_monitor.py
│       ├── layoff_tracker.py
│       ├── funding_tracker.py
│       └── alert_generator.py
│
├── search/                    # Existing V2 system
│   └── ...
│
└── services/
    └── company_db.py
```

---

## Changelog

### 2025-02-11 (v2.0 Documentation)
- Created comprehensive documentation for Intelligence System
- Defined four pillars: Activation, Timing, Expansion, Company Intel
- Designed data models and API endpoints
- Created implementation plan with prioritization
- Defined success metrics and criteria

### Previous (v1.0)
- Built V1 search system (4 API integrations)
- Built V2 network-first search
- Found 63 ML engineers in network, 9 recruiters
- Identified problems with cold outreach approach

---

## Next Steps

1. ✅ Documentation complete
2. ✅ Phase 1: Network Activation - IMPLEMENTED
   - `app/intelligence/activation/reverse_reference.py` - Generate "who would you recommend?" asks
   - `app/intelligence/activation/message_generator.py` - Personalized outreach messages
   - `app/api/routes/intelligence.py` - V3 API endpoints
   - Database tables: `activation_requests`, `recommendations`
3. ✅ Phase 2: Timing Intelligence - IMPLEMENTED
   - `app/intelligence/timing/tenure_tracker.py` - Track tenure and milestone approaching
   - `app/intelligence/timing/vesting_predictor.py` - Predict vesting cliff dates
   - `app/intelligence/timing/readiness_scorer.py` - Combined readiness scoring
   - API endpoints: `/timing/alerts`, `/timing/network-analysis`, `/timing/tenure`, `/timing/vesting-cliffs`
   - Database tables: `timing_signals`, `employment_history`
4. ✅ Phase 3: Former Colleague Expansion - IMPLEMENTED
   - `app/intelligence/expansion/colleague_expander.py` - Find former colleagues via employment overlap
   - `app/intelligence/expansion/warm_path_finder.py` - Find all warm paths to any candidate
   - API endpoints: `/expansion/summary`, `/expansion/colleagues`, `/expansion/warm-paths`
   - Database tables: `warm_paths`, `employment_history`
5. ✅ Phase 4: Company Intelligence - IMPLEMENTED
   - `app/intelligence/company/layoff_tracker.py` - Track layoff announcements and network impact
   - `app/intelligence/company/event_monitor.py` - Monitor company events (layoffs, acquisitions, etc.)
   - `app/intelligence/company/alert_generator.py` - Generate actionable alerts
   - API endpoints: `/company/watched`, `/company/layoffs`, `/company/events`, `/company/alerts`, `/company/digest`, `/company/report`
   - Database tables: `company_events`

ALL FOUR PILLARS COMPLETE!
