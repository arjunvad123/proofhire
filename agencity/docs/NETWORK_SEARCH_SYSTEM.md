# Agencity Network Search System

## Complete Documentation

**Last Updated:** 2025-02-11
**Status:** Active Development

---

## Table of Contents

1. [Overview](#overview)
2. [What We Built (Completed)](#what-we-built-completed)
3. [Problem Discovery](#problem-discovery)
4. [New Approach](#new-approach)
5. [Implementation Plan](#implementation-plan)
6. [Architecture](#architecture)
7. [API Reference](#api-reference)
8. [Database Schema](#database-schema)

---

## Overview

Agencity is a network-driven candidate search system. Instead of cold-searching for candidates like traditional recruiting tools, we leverage the founder's existing network to find **warm, reachable candidates** who are likely to respond and be a good fit.

### Core Principle

> "Your network is not a pathway to strangers. Your network IS the candidate pool."

---

## What We Built (Completed)

### Stage 0: Company Onboarding

**Purpose:** Allow companies to register and set up their account.

**Files:**
- `app/services/company_db.py` - Supabase database service
- `app/api/routes/companies.py` - Company API endpoints

**Features:**
- Company registration
- Company profile management
- API key generation

### Stage 1: Data Import (LinkedIn Connections)

**Purpose:** Import the founder's LinkedIn connections as the foundation of the network.

**Completed:**
- CSV import from LinkedIn export
- 3,637 connections imported to Supabase
- Data stored in `people` table with `is_from_network=true`

**Database:** Supabase (PostgreSQL)
- URL: `https://npqjuljzpjvcqmrgpyqj.supabase.co`
- Company ID (Agencity Demo): `66e42fdb-84f7-4805-ba15-4a3c3519b738`

**Data Fields per Connection:**
- `full_name` - Person's name
- `current_title` - Job title
- `current_company` - Employer
- `linkedin_url` - Profile URL
- `location` - Geographic location
- `is_from_network` - Boolean flag (true for imported connections)

### Stage 2: Initial Search System (V1)

**Purpose:** Search external APIs using network as "gateways" to find candidates.

**Files Created:**
```
app/search/
├── models.py              # Data models (SearchTarget, DiscoveredCandidate, etc.)
├── engine.py              # Main search orchestrator
├── analyzers/
│   └── network.py         # Classifies network nodes by type
├── generators/
│   └── query.py           # Generates API-specific queries
├── scoring/
│   ├── pathway.py         # Scores network nodes as gateways
│   └── ranker.py          # Ranks discovered candidates
└── sources/
    ├── base.py            # Base class for search sources
    ├── pdl.py             # People Data Labs integration
    ├── google.py          # Google Custom Search integration
    ├── github.py          # GitHub API integration
    └── perplexity.py      # Perplexity AI integration
```

**API Integrations:**
| Source | Status | API Key Location |
|--------|--------|------------------|
| People Data Labs (PDL) | ✅ Working (credits exhausted) | `.env` PDL_API_KEY |
| Google Custom Search | ✅ Working | `.env` GOOGLE_CSE_API_KEY |
| GitHub | ✅ Working | `.env` GITHUB_TOKEN |
| Perplexity AI | ✅ Working | `.env` PERPLEXITY_API_KEY |

**API Endpoints:**
- `POST /search` - Execute a search
- `GET /search/explain` - Explain search strategy without executing
- `GET /network/stats` - Get network statistics
- `GET /network/gateways` - List top network gateways

---

## Problem Discovery

### The Issue with V1

The initial search system found **famous, unreachable people** instead of warm candidates.

**Example Search Results (V1):**
- Zixuan He - Senior ML Engineer @ Pinterest
- Joey Z. - Senior Staff ML Engineer @ Uber
- Katerina Zanos - ML Engineer @ Disney

**Problems:**
1. These are "cold" candidates - anyone could find them via Google
2. They have **zero connection** to the founder's network
3. They won't respond to outreach (too many recruiters contact them)
4. The "network" was barely leveraged

**Root Cause:**
We were searching for "ML engineers at [company where connection works]" but:
- The companies (Legal 500, Compass Pathways) aren't tech companies
- The results were random LinkedIn profiles, not people actually connected to the network nodes
- We treated the network as a "hint" instead of the actual source

---

## New Approach

### Core Philosophy

```
OLD: Network → Gateway → Search APIs → Random Famous People (COLD)
NEW: Network → Candidates IN network → 2nd-degree via overlap → WARM paths only
```

### Tiered Candidate System

```
TIER 1: IN YOUR NETWORK
        People who match the role AND are direct connections
        → Highest response rate
        → Message directly

TIER 2: ONE INTRO AWAY
        People who share employment/school history with your connections
        → Warm intro possible
        → "You → Sarah → Candidate"

TIER 3: RECRUITER NETWORK
        Recruiters in your network who know active candidates
        → Highest signal (they know who's looking)
        → Ask them for referrals

TIER 4: COLD (deprioritized)
        External search results with no network connection
        → Only show if Tiers 1-3 are exhausted
```

### "Ready to Work" Signals

Not everyone is looking. Detect who is:

| Signal | Detection Method | Score |
|--------|------------------|-------|
| Tenure 3-4 years | Calculate from start date | +0.3 |
| "Open to Work" in title | Text match | +0.8 |
| "Consultant/Advisor" title | Text match | +0.5 |
| Company had layoffs | News API / manual list | +0.4 |
| Startup with no funding | Crunchbase API | +0.4 |
| Recently updated profile | Activity detection | +0.2 |

### Employment Overlap Graph

People who worked at the **same company at the same time** know each other.

```
Network Connection: Sarah (Google, 2019-2022)
                           ↓
                    Worked together
                           ↓
Search: ML Engineers who worked at Google 2019-2022
                           ↓
Result: People Sarah can actually introduce
```

---

## Implementation Plan

### Phase 1: Network-First Search ✅ (Building Now)

**Goal:** Search the 3,637 connections FIRST before going external.

**New Files:**
- `app/search/network_search.py` - Search within the network
- `app/search/readiness.py` - Score "ready to work" signals
- `app/search/warm_path.py` - Calculate warm intro paths

**Features:**
1. Filter network by role keywords (title matching)
2. Score by readiness signals
3. Return Tier 1 candidates

### Phase 2: Employment Overlap Graph

**Goal:** Find 2nd-degree connections through shared employers.

**Approach:**
1. For each network connection, extract work history
2. Use PDL to enrich with employment dates
3. Build edges: Person A ↔ Company (dates) ↔ Person B
4. Query: "Find ML engineers who overlapped at [company] with [network connection]"

**New Files:**
- `app/search/employment_graph.py` - Build and query the overlap graph
- `app/search/enrichment.py` - Enrich network with employment history

### Phase 3: Recruiter Identification

**Goal:** Identify recruiters in the network who can refer candidates.

**Approach:**
1. Filter network by recruiter-related titles
2. Classify by specialty (tech, finance, etc.)
3. Surface as "high-signal contacts" for any search

**New Files:**
- `app/search/recruiters.py` - Identify and classify recruiters

### Phase 4: Warm Path Algorithm

**Goal:** For any candidate, calculate the best intro path.

**Path Types:**
1. Direct connection (1st degree) - Warmth: 1.0
2. Shared employer + overlapping dates - Warmth: 0.85
3. Shared school + overlapping years - Warmth: 0.7
4. Same small startup (<50 people) - Warmth: 0.9
5. GitHub co-contributors - Warmth: 0.75
6. No connection - Warmth: 0.0

**New Files:**
- `app/search/warm_path.py` - Calculate warmth scores and paths

### Phase 5: Unified Search API

**Goal:** Single endpoint that returns tiered results.

**Response Format:**
```json
{
  "tier_1_network": [...],      // Direct connections matching role
  "tier_2_one_intro": [...],    // 2nd-degree with warm paths
  "tier_3_recruiters": [...],   // Recruiters to contact
  "tier_4_cold": [...],         // External results (deprioritized)
  "search_metadata": {
    "network_searched": 3637,
    "matches_in_network": 12,
    "warm_paths_found": 25,
    "recruiters_identified": 4
  }
}
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│                    (FastAPI - app/api/)                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Search Engine V2                           │
│                  (app/search/engine_v2.py)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Network    │  │  Employment │  │   Warm      │             │
│  │  Search     │  │  Graph      │  │   Path      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Readiness  │  │  Recruiter  │  │  External   │             │
│  │  Scoring    │  │  Finder     │  │  Sources    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Supabase   │  │  Pinecone   │  │  External   │             │
│  │  (People)   │  │  (Vectors)  │  │  APIs       │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Search Request
      │
      ▼
┌─────────────────┐
│ 1. Network      │ → Search 3,637 connections for role match
│    Search       │ → Score by readiness signals
└────────┬────────┘ → Return Tier 1 candidates
         │
         ▼
┌─────────────────┐
│ 2. Employment   │ → Get work history of network connections
│    Graph        │ → Find overlapping employees
└────────┬────────┘ → Return Tier 2 candidates with paths
         │
         ▼
┌─────────────────┐
│ 3. Recruiter    │ → Identify recruiters in network
│    Finder       │ → Return as Tier 3
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. External     │ → PDL, Google, Perplexity (if needed)
│    Search       │ → Calculate warm paths
└────────┬────────┘ → Return Tier 4 (only if connected)
         │
         ▼
   Tiered Response
```

---

## API Reference

### POST /api/v2/search

Execute a network-first search.

**Request:**
```json
{
  "company_id": "uuid",
  "role_title": "Machine Learning Engineer",
  "required_skills": ["Python", "PyTorch"],
  "preferred_backgrounds": ["Google", "Meta"],
  "locations": ["San Francisco"],
  "max_results": 50
}
```

**Response:**
```json
{
  "tier_1_network": [
    {
      "id": "uuid",
      "full_name": "John Smith",
      "current_title": "ML Engineer",
      "current_company": "Startup X",
      "linkedin_url": "...",
      "readiness_score": 0.75,
      "readiness_signals": ["3.5 year tenure", "company struggling"],
      "connection_type": "direct",
      "action": "Message directly"
    }
  ],
  "tier_2_one_intro": [
    {
      "id": "uuid",
      "full_name": "Jane Doe",
      "current_title": "Senior ML Engineer",
      "current_company": "Google",
      "linkedin_url": "...",
      "readiness_score": 0.6,
      "warm_path": {
        "via": "Sarah Kim",
        "relationship": "Worked together at Google 2020-2022",
        "warmth_score": 0.85
      },
      "action": "Ask Sarah for intro"
    }
  ],
  "tier_3_recruiters": [
    {
      "id": "uuid",
      "full_name": "Mike Johnson",
      "current_title": "Tech Recruiter",
      "current_company": "Hired.com",
      "specialty": "ML/AI Engineering",
      "action": "Ask for referrals"
    }
  ],
  "tier_4_cold": [...],
  "metadata": {
    "search_duration_seconds": 5.2,
    "network_size": 3637,
    "tier_1_count": 8,
    "tier_2_count": 23,
    "tier_3_count": 4,
    "tier_4_count": 15
  }
}
```

---

## Database Schema

### Supabase Tables

**people**
```sql
CREATE TABLE people (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES companies(id),
  full_name TEXT NOT NULL,
  email TEXT,
  linkedin_url TEXT,
  github_url TEXT,
  current_title TEXT,
  current_company TEXT,
  location TEXT,

  -- Network flags
  is_from_network BOOLEAN DEFAULT FALSE,
  is_from_existing_db BOOLEAN DEFAULT FALSE,
  is_from_people_search BOOLEAN DEFAULT FALSE,

  -- Employment history (for overlap graph)
  employment_history JSONB DEFAULT '[]',
  -- Format: [{"company": "Google", "title": "Engineer", "start": "2019-01", "end": "2022-03"}]

  -- Education
  education JSONB DEFAULT '[]',
  -- Format: [{"school": "Stanford", "degree": "MS CS", "year": 2018}]

  -- Skills
  skills TEXT[] DEFAULT '{}',

  -- Readiness signals
  readiness_score FLOAT DEFAULT 0,
  readiness_signals JSONB DEFAULT '[]',

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**warm_paths** (new table)
```sql
CREATE TABLE warm_paths (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES companies(id),
  candidate_id UUID REFERENCES people(id),
  via_person_id UUID REFERENCES people(id),
  path_type TEXT, -- 'shared_employer', 'shared_school', 'direct', etc.
  warmth_score FLOAT,
  relationship_description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Environment Variables

```bash
# Supabase
SUPABASE_URL=https://npqjuljzpjvcqmrgpyqj.supabase.co
SUPABASE_KEY=...

# Search APIs
PDL_API_KEY=...
GOOGLE_CSE_API_KEY=...
GOOGLE_CSE_ID=...
GITHUB_TOKEN=...
PERPLEXITY_API_KEY=...

# Pinecone (for vector search - future)
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=agencity-people
```

---

## File Structure

```
app/
├── api/
│   ├── router.py
│   └── routes/
│       ├── companies.py
│       ├── search.py          # V1 endpoints
│       └── search_v2.py       # V2 endpoints (new)
├── search/
│   ├── models.py              # Shared data models
│   ├── engine.py              # V1 engine
│   ├── engine_v2.py           # V2 engine (new)
│   ├── network_search.py      # Search within network (new)
│   ├── readiness.py           # Readiness scoring (new)
│   ├── employment_graph.py    # Overlap graph (new)
│   ├── warm_path.py           # Warm path calculator (new)
│   ├── recruiters.py          # Recruiter finder (new)
│   ├── analyzers/
│   │   └── network.py
│   ├── generators/
│   │   └── query.py
│   ├── scoring/
│   │   ├── pathway.py
│   │   └── ranker.py
│   └── sources/
│       ├── base.py
│       ├── pdl.py
│       ├── google.py
│       ├── github.py
│       └── perplexity.py
├── services/
│   └── company_db.py
└── config.py

docs/
└── NETWORK_SEARCH_SYSTEM.md   # This file
```

---

## Status

### Completed ✅

1. ✅ Documentation complete
2. ✅ Network-first search (`network_search.py`)
3. ✅ Readiness scoring (`readiness.py`)
4. ✅ Recruiter identification (`recruiters.py`)
5. ✅ Warm path algorithm (`warm_path.py`)
6. ✅ V2 Search Engine (`engine_v2.py`)
7. ✅ V2 API endpoints (`search_v2.py`)

### Pending ⏳

8. ⏳ Employment overlap graph (enrichment with work history dates)
9. ⏳ PDL enrichment for 2nd-degree connections
10. ⏳ Frontend integration
11. ⏳ Pinecone vector search integration

---

## Test Results (2025-02-11)

**Search: "Machine Learning Engineer" with skills Python, PyTorch, TensorFlow**

| Metric | Value |
|--------|-------|
| Network Searched | 1,000 connections |
| Tier 1 (In Network) | 63 candidates |
| Tier 3 (Recruiters) | 9 recruiters |
| Search Time | 1.15 seconds |

**Sample Tier 1 Candidates:**
- Nikhil Kulkarni - Applied AI Engineer @ Google (55% score, layoff signal)
- Maxim Podgore - Lead ML Engineer @ UC San Diego (50% score)
- Chetan Pawar - Founding AI Engineer @ Metalinked (55% score)

**Recruiters Found:**
- Mehak Verma (tech specialty)
- Alexis Rached, Lorena Bugden (general recruiting)

---

## Changelog

### 2025-02-11 (Evening)
- ✅ Implemented V2 search engine
- ✅ Created network_search.py for searching within network
- ✅ Created readiness.py for scoring "ready to move" signals
- ✅ Created recruiters.py for identifying recruiters
- ✅ Created warm_path.py for calculating intro paths
- ✅ Created engine_v2.py to orchestrate all components
- ✅ Created search_v2.py API routes
- ✅ Fixed Pydantic model to dict conversion
- ✅ Tested with 1,000 connections - found 63 Tier 1 candidates

### 2025-02-11 (Afternoon)
- Fixed PDL query format (match → term)
- Fixed GitHub org name sanitization
- Fixed Perplexity model name (sonar)
- V1 search working with 4 API sources

### 2025-02-11 (Morning)
- Documented complete system architecture
- Identified problems with V1 approach
- Designed V2 "network-first" approach

### Previous
- Stage 0: Company onboarding complete
- Stage 1: LinkedIn import complete (3,637 connections)
- Stage 2: V1 search system complete (4 API integrations)
