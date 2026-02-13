# Implementation Guide: End-to-End Slack Workflow

## Unified Search → Slack Delivery System

**Version 3.0** | February 12, 2026

---

## 1. System Overview

This guide documents how to implement the complete workflow from Slack mention to shortlist delivery, integrating the web frontend, Agencity backend, and Slack bot.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER TOUCHPOINTS                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   SLACK                         WEB                      API             │
│   ┌─────────────┐               ┌─────────────┐          ┌─────────┐    │
│   │ @hermes     │               │ /agencity   │          │ /api/v1 │    │
│   │ /hermes     │               │ dashboard   │          │ curation│    │
│   └──────┬──────┘               └──────┬──────┘          └────┬────┘    │
│          │                             │                      │         │
└──────────┼─────────────────────────────┼──────────────────────┼─────────┘
           │                             │                      │
           ▼                             ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGENCITY BACKEND                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    UNIFIED SEARCH ORCHESTRATOR                   │   │
│   │                                                                  │   │
│   │   ┌─────────────┐              ┌─────────────┐                   │   │
│   │   │  candidates │              │   people    │                   │   │
│   │   │  (Hermes)   │              │  (Network)  │                   │   │
│   │   │  1,375+     │              │   3,637     │                   │   │
│   │   └──────┬──────┘              └──────┬──────┘                   │   │
│   │          │                            │                          │   │
│   │          └────────────┬───────────────┘                          │   │
│   │                       ▼                                          │   │
│   │              ┌─────────────────┐                                 │   │
│   │              │  Deduplication  │                                 │   │
│   │              │   ~5,000 pool   │                                 │   │
│   │              └────────┬────────┘                                 │   │
│   │                       ▼                                          │   │
│   │              ┌─────────────────┐                                 │   │
│   │              │ Reasoning Engine│                                 │   │
│   │              │  Proof Briefs   │                                 │   │
│   │              └────────┬────────┘                                 │   │
│   │                       ▼                                          │   │
│   │              ┌─────────────────┐                                 │   │
│   │              │   Enrichment    │                                 │   │
│   │              │  Top 30 → PDL   │                                 │   │
│   │              │  Top 5 → PPX    │                                 │   │
│   │              └────────┬────────┘                                 │   │
│   │                       ▼                                          │   │
│   │              ┌─────────────────┐                                 │   │
│   │              │ Shortlist (12)  │                                 │   │
│   │              │ + Proof Briefs  │                                 │   │
│   │              └─────────────────┘                                 │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
           │                             │                      │
           ▼                             ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           SUPABASE                                       │
├─────────────────────────────────────────────────────────────────────────┤
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│   │ candidates  │  │   people    │  │    roles    │  │  companies  │   │
│   │  (Hermes)   │  │  (Network)  │  │             │  │             │   │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │
│   │proof_briefs │  │conversations│  │ org_profiles│                    │
│   └─────────────┘  └─────────────┘  └─────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Database Schema

### Core Tables (Actual Supabase Schema)

```sql
-- ============================================================
-- CANDIDATE SOURCES
-- ============================================================

-- Hermes: Opted-in candidates with verified data (1,378 rows)
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    skills TEXT,                      -- Comma-separated or structured
    location TEXT,
    education_level TEXT,             -- e.g., "Bachelor's", "Master's", "PhD"
    university TEXT,
    major TEXT[],                     -- Array of majors
    experience TEXT,                  -- Comma-separated internship experiences
    technical_projects TEXT,
    years_of_experience TEXT,         -- e.g., "0-1", "1-2", "3-5"
    role_type TEXT[],                 -- e.g., ["SWE", "ML", "AI"]
    job_type TEXT,                    -- "full-time", "part-time", "internship"

    -- GitHub integration
    github_username TEXT,
    github_user_id BIGINT,
    github_access_token TEXT,
    github_connected_at TIMESTAMPTZ,
    github_profile_url TEXT,
    github_email TEXT,
    github_name TEXT,
    github_avatar_url TEXT,

    -- Subscription (not relevant for search)
    subscription_tier TEXT DEFAULT 'free',
    subscription_status TEXT DEFAULT 'inactive',

    -- Resume data
    structured_resume_data JSONB,    -- LEGACY: migrated to resumes table
    resume_latex TEXT,

    -- Onboarding
    onboarding_completed BOOLEAN DEFAULT false,
    objectives TEXT[],

    -- Assessment provisioning
    provisioned_schema_name TEXT,
    assessment_repo_url TEXT,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Network: LinkedIn connections (7,274 rows)
CREATE TABLE people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),

    -- Identity
    full_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    linkedin_url TEXT,
    github_url TEXT,

    -- Current position
    headline TEXT,
    location TEXT,
    current_company TEXT,
    current_title TEXT,

    -- Metadata
    status TEXT,                      -- Person status in network
    trust_score DOUBLE PRECISION,
    relevance_score DOUBLE PRECISION,

    -- Source flags
    is_from_network BOOLEAN,          -- From LinkedIn import
    is_from_existing_db BOOLEAN,
    is_from_people_search BOOLEAN,

    -- Enrichment tracking
    pinecone_id TEXT,
    first_seen TIMESTAMPTZ,
    last_enriched TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enrichment data for people (0 rows currently - will be populated)
CREATE TABLE person_enrichments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES people(id),

    skills JSONB,
    experience JSONB,
    education JSONB,
    projects JSONB,
    signals JSONB,                    -- Career signals
    raw_enrichment JSONB,             -- Full API response

    enrichment_source TEXT,           -- 'pdl', 'perplexity', 'github'
    embedding_text TEXT,              -- For vector search

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- COMPANY & ROLES
-- ============================================================

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain TEXT,
    stage TEXT,                       -- Startup stage
    industry TEXT,
    tech_stack TEXT[],                -- Array of technologies
    team_size INTEGER,

    -- Founder info
    founder_email TEXT,
    founder_name TEXT,
    founder_linkedin_url TEXT,

    -- Import status
    linkedin_imported BOOLEAN,
    existing_db_imported BOOLEAN,
    onboarding_complete BOOLEAN,

    -- Pinecone namespace for vector search
    pinecone_namespace TEXT,

    -- Counts
    people_count INTEGER,
    roles_count INTEGER,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),

    title TEXT NOT NULL,
    level TEXT,                       -- 'junior', 'mid', 'senior', 'staff'
    department TEXT,
    description TEXT,
    location TEXT,

    -- Skills
    required_skills TEXT[],
    preferred_skills TEXT[],

    -- Experience
    years_experience_min INTEGER,
    years_experience_max INTEGER,

    -- Compensation
    salary_min INTEGER,
    salary_max INTEGER,

    status TEXT,                      -- 'active', 'draft', 'closed'

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- NETWORK INTELLIGENCE
-- ============================================================

-- Warm introduction paths (0 rows - will be computed)
CREATE TABLE warm_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),

    -- Target candidate
    candidate_id UUID,                -- Could be from candidates or people
    candidate_name TEXT,
    candidate_linkedin TEXT,

    -- Connector in network
    via_person_id UUID REFERENCES people(id),

    -- Path details
    path_type TEXT,                   -- 'same_company', 'same_school', 'mutual_connection'
    relationship_description TEXT,    -- Human-readable description
    overlap_details JSONB,            -- Structured overlap data
    warmth_score DOUBLE PRECISION,    -- 0-1 strength of connection

    created_at TIMESTAMPTZ DEFAULT now()
);

-- Timing signals for candidates (0 rows - will be computed)
CREATE TABLE timing_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES people(id),

    -- Tenure tracking
    current_company TEXT,
    tenure_start DATE,
    tenure_months INTEGER,

    -- Vesting signals
    vesting_cliff_date DATE,
    months_to_cliff INTEGER,

    -- Company signals
    company_had_layoffs BOOLEAN,
    layoff_date DATE,
    manager_departed BOOLEAN,

    -- Profile signals
    title_signals TEXT[],             -- e.g., ["open_to_work", "freelance"]
    profile_updated_recently BOOLEAN,

    -- Computed readiness
    readiness_score DOUBLE PRECISION, -- 0-1
    recommended_action TEXT,
    action_urgency TEXT,              -- 'high', 'medium', 'low'

    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Hiring priorities for roles (6 rows)
CREATE TABLE hiring_priorities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_profile_id UUID REFERENCES org_profiles(id),

    role_title VARCHAR,
    must_haves TEXT[],
    nice_to_haves TEXT[],
    dealbreakers TEXT[],

    specific_work TEXT,               -- Day-to-day work description
    success_criteria TEXT,            -- What success looks like

    context_json JSONB,               -- Additional context
    priority_level INTEGER,           -- Urgency ranking

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- AGENT REASONING & OUTPUT (NEW TABLES TO CREATE)
-- ============================================================

-- Links between Hermes candidates and Network people (deduplication)
CREATE TABLE candidate_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hermes_candidate_id UUID REFERENCES candidates(id),
    network_person_id UUID REFERENCES people(id),
    link_method TEXT,                 -- 'linkedin', 'email', 'github', 'name_match'
    link_confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Proof Briefs generated by the agent
CREATE TABLE proof_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Candidate reference (one or both)
    hermes_candidate_id UUID REFERENCES candidates(id),
    network_person_id UUID REFERENCES people(id),
    -- Context
    role_id UUID REFERENCES roles(id),
    company_id UUID REFERENCES companies(id),
    -- Assessment
    recommendation TEXT,              -- 'strong_consider', 'consider', 'weak_consider', 'pass'
    confidence FLOAT,
    match_score FLOAT,
    -- Evidence chain
    known_facts JSONB,
    observed_signals JSONB,
    unknowns JSONB,
    reasoning_chain JSONB,
    -- Actions
    warm_path JSONB,
    suggested_next_step TEXT,
    outreach_message TEXT,
    -- Metadata
    sources_used TEXT[],
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- CONVERSATIONS & SLACK
-- ============================================================

-- Conversation state (Slack threads or web sessions)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Source
    source TEXT NOT NULL,             -- 'slack', 'web'
    slack_channel TEXT,
    slack_thread_ts TEXT,
    web_session_id TEXT,
    -- Context
    company_id UUID REFERENCES companies(id),
    user_id TEXT,
    -- State
    status TEXT DEFAULT 'active',     -- 'active', 'completed', 'abandoned'
    role_blueprint JSONB,             -- Extracted role requirements
    messages JSONB,                   -- Conversation history
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Search sessions for analytics
CREATE TABLE search_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    company_id UUID REFERENCES companies(id),
    role_id UUID REFERENCES roles(id),
    -- Results
    hermes_searched INT,
    network_searched INT,
    duplicates_merged INT,
    shortlist_size INT,
    -- Timing
    duration_seconds FLOAT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Organization profiles (2 rows - for personalization)
CREATE TABLE org_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    supabase_user_id VARCHAR,

    -- Slack integration
    slack_workspace_id VARCHAR,
    slack_workspace_name VARCHAR,

    -- Company context
    company_name VARCHAR,
    company_hq_location VARCHAR,
    company_size INTEGER,
    company_stage VARCHAR,
    industry VARCHAR,
    product_description TEXT,

    -- Operating style preferences
    pace VARCHAR,                     -- 'high', 'medium', 'low'
    quality_bar VARCHAR,              -- 'high', 'medium', 'pragmatic'
    ambiguity VARCHAR,                -- 'high', 'medium', 'low'

    -- Hiring preferences
    tech_stack JSONB,
    hiring_priorities JSONB,
    preferred_schools JSONB,
    preferred_companies JSONB,
    avoid_patterns JSONB,
    extra_context JSONB,

    onboarding_complete BOOLEAN,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 3. Backend API Structure

### Directory Structure

```
agencity/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── slack.py              # Slack webhook handlers
│   │   │   ├── unified_search.py     # Unified search endpoint
│   │   │   ├── curation.py           # Curation endpoints
│   │   │   ├── conversations.py      # Conversation management
│   │   │   ├── companies.py          # Company CRUD
│   │   │   └── roles.py              # Role management
│   │   └── deps.py                   # Dependencies (auth, db)
│   ├── core/
│   │   ├── config.py                 # Settings & env vars
│   │   └── database.py               # Supabase client
│   ├── integrations/
│   │   ├── slack.py                  # Slack client wrapper
│   │   └── perplexity.py             # Perplexity API client
│   ├── services/
│   │   ├── unified_search.py         # Search orchestrator
│   │   ├── deduplication.py          # Candidate deduplication
│   │   ├── reasoning_engine.py       # Proof Brief generator
│   │   ├── conversation_engine.py    # Conversation handler
│   │   ├── shortlist_builder.py      # Shortlist generation
│   │   └── enrichment/
│   │       ├── pdl.py                # People Data Labs
│   │       └── perplexity.py         # Deep research
│   └── main.py                       # FastAPI app
```

### API Endpoints

```python
# ============================================================
# SLACK INTEGRATION
# ============================================================

@router.post("/api/slack/events")
async def slack_events(request: Request):
    """
    Handle Slack Events API webhooks.

    Events:
    - app_mention: @hermes mentions
    - message.im: Direct messages

    Flow:
    1. Verify signature
    2. Handle URL verification challenge
    3. Process event asynchronously
    4. Return 200 immediately (Slack timeout = 3s)
    """

@router.post("/api/slack/commands")
async def slack_commands(request: Request):
    """
    Handle /hermes slash commands.

    Commands:
    - /hermes [role description] - Start search
    - /hermes status - Show current search status
    - /hermes help - Show help
    """

@router.get("/api/slack/install")
async def slack_install():
    """Generate OAuth install URL."""

@router.get("/api/slack/oauth/callback")
async def slack_oauth_callback(code: str):
    """Handle OAuth callback, store tokens."""


# ============================================================
# UNIFIED SEARCH
# ============================================================

@router.post("/api/v1/unified/search")
async def unified_search(
    request: UnifiedSearchRequest,
    background_tasks: BackgroundTasks
) -> UnifiedSearchResponse:
    """
    Search across Hermes + Network sources.

    Request:
    {
        "company_id": "uuid",
        "role_blueprint": {
            "title": "Software Engineer",
            "required_skills": ["Python", "React"],
            "locations": ["San Francisco", "Remote"],
            "seniority": "mid"
        },
        "limit": 100
    }

    Response:
    {
        "search_id": "uuid",
        "status": "completed",
        "results": {
            "tier_1_warm_ready": [...],
            "tier_2_warm_intro": [...],
            "tier_3_hermes_cold": [...],
            "tier_4_network_cold": [...]
        },
        "stats": {
            "hermes_searched": 1375,
            "network_searched": 3637,
            "duplicates_merged": 120,
            "total_unique": 4892
        },
        "duration_seconds": 47.3
    }
    """

@router.post("/api/v1/unified/shortlist")
async def generate_shortlist(
    request: ShortlistRequest
) -> ShortlistResponse:
    """
    Generate a shortlist from search results.

    Request:
    {
        "search_id": "uuid",
        "target_size": 12,
        "tier_weights": {
            "tier_1": 0.50,
            "tier_2": 0.30,
            "tier_3": 0.15,
            "tier_4": 0.05
        }
    }

    Response:
    {
        "shortlist_id": "uuid",
        "candidates": [
            {
                "candidate": { ... },
                "proof_brief": { ... }
            }
        ],
        "total_candidates": 12
    }
    """


# ============================================================
# CONVERSATIONS
# ============================================================

@router.post("/api/conversations")
async def create_conversation(
    request: CreateConversationRequest
) -> Conversation:
    """
    Start a new conversation (Slack or web).

    Request:
    {
        "source": "slack",
        "slack_channel": "C123456",
        "slack_thread_ts": "1234567890.123456",
        "company_id": "uuid",
        "user_id": "U123456"
    }
    """

@router.post("/api/conversations/{conversation_id}/message")
async def add_message(
    conversation_id: str,
    request: MessageRequest
) -> ConversationResponse:
    """
    Process a message in the conversation.

    Request:
    {
        "message": "I need a prompt engineer for my AI startup"
    }

    Response:
    {
        "response": "What does your startup do specifically?",
        "needs_clarification": true,
        "role_blueprint": null,
        "search_triggered": false
    }

    OR (when ready to search):

    {
        "response": "Searching ~5,000 candidates...",
        "needs_clarification": false,
        "role_blueprint": { ... },
        "search_triggered": true,
        "search_id": "uuid"
    }
    """


# ============================================================
# PROOF BRIEFS
# ============================================================

@router.get("/api/v1/briefs/{brief_id}")
async def get_brief(brief_id: str) -> ProofBrief:
    """Get a single Proof Brief by ID."""

@router.get("/api/v1/candidates/{candidate_id}/brief")
async def get_candidate_brief(
    candidate_id: str,
    role_id: str
) -> ProofBrief:
    """Get or generate a Proof Brief for a candidate."""
```

---

## 4. Service Implementation

### 4.1 Unified Search Orchestrator

```python
# app/services/unified_search.py

from typing import List, Tuple
import asyncio
from datetime import datetime

from app.core.database import supabase
from app.services.deduplication import DeduplicationEngine
from app.services.reasoning_engine import ReasoningEngine
from app.services.enrichment.pdl import PDLEnricher
from app.services.enrichment.perplexity import PerplexityResearcher


class UnifiedSearchOrchestrator:
    """
    Orchestrates search across Hermes + Network sources.
    """

    def __init__(self):
        self.dedup = DeduplicationEngine()
        self.reasoning = ReasoningEngine()
        self.pdl = PDLEnricher()
        self.perplexity = PerplexityResearcher()

    async def search(
        self,
        company_id: str,
        role_blueprint: dict,
        limit: int = 100
    ) -> SearchResult:
        """
        Main search flow:
        1. Parallel search both sources
        2. Deduplicate
        3. Initial scoring
        4. Progressive enrichment
        5. Re-score
        6. Return tiered results
        """
        start_time = datetime.utcnow()

        # Step 1: Parallel search
        hermes_task = self._search_hermes(role_blueprint, limit)
        network_task = self._search_network(company_id, role_blueprint, limit)

        hermes_results, network_results = await asyncio.gather(
            hermes_task, network_task
        )

        # Step 2: Deduplicate
        unified = self.dedup.deduplicate(hermes_results, network_results)

        # Step 3: Initial scoring (pre-enrichment)
        scored = []
        for candidate in unified:
            brief = await self.reasoning.evaluate(candidate, role_blueprint)
            scored.append((candidate, brief))

        # Sort by score
        scored.sort(key=lambda x: x[1].match_score, reverse=True)

        # Step 4: Progressive enrichment
        # Top 30: PDL enrichment
        top_30 = scored[:30]
        enriched_30 = await self._enrich_batch_pdl(top_30)

        # Top 5: Deep research
        top_5 = enriched_30[:5]
        researched_5 = await self._deep_research_batch(top_5, role_blueprint)

        # Step 5: Re-score enriched candidates
        final_scored = []
        for candidate, _ in researched_5:
            updated_brief = await self.reasoning.evaluate(candidate, role_blueprint)
            final_scored.append((candidate, updated_brief))

        for candidate, _ in enriched_30[5:]:
            updated_brief = await self.reasoning.evaluate(candidate, role_blueprint)
            final_scored.append((candidate, updated_brief))

        # Add remaining non-enriched candidates
        final_scored.extend(scored[30:])

        # Sort final results
        final_scored.sort(key=lambda x: x[1].match_score, reverse=True)

        # Step 6: Tier results
        tiered = self._tier_results(final_scored)

        duration = (datetime.utcnow() - start_time).total_seconds()

        return SearchResult(
            tier_1_warm_ready=tiered['tier_1'],
            tier_2_warm_intro=tiered['tier_2'],
            tier_3_hermes_cold=tiered['tier_3'],
            tier_4_network_cold=tiered['tier_4'],
            stats=SearchStats(
                hermes_searched=len(hermes_results),
                network_searched=len(network_results),
                duplicates_merged=len(hermes_results) + len(network_results) - len(unified),
                total_unique=len(unified),
                enriched_count=min(30, len(unified)),
                researched_count=min(5, len(unified))
            ),
            duration_seconds=duration
        )

    async def _search_hermes(
        self,
        role_blueprint: dict,
        limit: int
    ) -> List[Candidate]:
        """Search the candidates table (Hermes)."""

        query = supabase.table("candidates").select("*")

        # Skill matching
        if role_blueprint.get('required_skills'):
            for skill in role_blueprint['required_skills'][:3]:
                query = query.or_(f"skills.cs.{{{skill}}}")

        # Location
        if role_blueprint.get('locations'):
            query = query.in_("location", role_blueprint['locations'])

        results = query.limit(limit).execute()

        return [
            Candidate(
                person_id=r['id'],
                full_name=r['name'],
                email=r.get('email'),
                linkedin_url=r.get('linkedin_url'),
                github_url=f"https://github.com/{r['github_username']}" if r.get('github_username') else None,
                location=r.get('location'),
                current_company=None,  # Hermes may not have this
                current_title=None,
                skills=r.get('skills', []),
                github_repos=r.get('github_repos', []),
                sources=['hermes'],
                primary_source='hermes',
                source_quality=0.95,
                opted_in=True,
                is_direct_connection=False,
                warmth_score=0.0,
                warm_path=None,
                data_completeness=self._calc_completeness(r)
            )
            for r in results.data
        ]

    async def _search_network(
        self,
        company_id: str,
        role_blueprint: dict,
        limit: int
    ) -> List[Candidate]:
        """Search the people table (Network)."""

        query = supabase.table("people").select("""
            *,
            person_enrichments(*)
        """).eq("company_id", company_id)

        # Title matching
        if role_blueprint.get('title'):
            query = query.ilike("current_title", f"%{role_blueprint['title']}%")

        results = query.limit(limit).execute()

        candidates = []
        for r in results.data:
            enrichment = r.get('person_enrichments', [{}])[0] if r.get('person_enrichments') else {}

            candidates.append(Candidate(
                person_id=r['id'],
                full_name=r['full_name'],
                email=r.get('email'),
                linkedin_url=r.get('linkedin_url'),
                github_url=None,
                location=r.get('location'),
                current_company=r.get('current_company'),
                current_title=r.get('current_title'),
                skills=enrichment.get('skills', []),
                github_repos=[],
                sources=['network'],
                primary_source='network',
                source_quality=0.70,
                opted_in=False,
                is_direct_connection=r.get('is_from_network', True),
                warmth_score=0.8 if r.get('is_from_network') else 0.3,
                warm_path=self._find_warm_path(r),
                data_completeness=self._calc_completeness(r)
            ))

        return candidates

    def _tier_results(
        self,
        scored: List[Tuple[Candidate, ProofBrief]]
    ) -> dict:
        """Organize results into tiers."""

        tiers = {
            'tier_1': [],  # Warm + Ready (direct connection OR opted-in)
            'tier_2': [],  # Warm Intro (has warm path)
            'tier_3': [],  # Hermes Cold (opted-in but no network)
            'tier_4': [],  # Network Cold (need verification)
        }

        for candidate, brief in scored:
            # Tier 1: Direct connection or opted-in with good confidence
            if (candidate.is_direct_connection or candidate.opted_in) and brief.confidence > 0.5:
                tiers['tier_1'].append((candidate, brief))

            # Tier 2: Has warm path
            elif candidate.warm_path and brief.confidence > 0.3:
                tiers['tier_2'].append((candidate, brief))

            # Tier 3: Hermes only (opted-in but no network connection)
            elif 'hermes' in candidate.sources and 'network' not in candidate.sources:
                tiers['tier_3'].append((candidate, brief))

            # Tier 4: Network only (needs enrichment/verification)
            else:
                tiers['tier_4'].append((candidate, brief))

        return tiers
```

### 4.2 Slack Integration

```python
# app/integrations/slack.py

import hashlib
import hmac
import time
from typing import Optional
import httpx

from app.core.config import settings


class SlackClient:
    """Slack API client with signature verification."""

    def __init__(self):
        self.token = settings.slack_bot_token
        self.signing_secret = settings.slack_signing_secret
        self.base_url = "https://slack.com/api"

    def verify_signature(
        self,
        timestamp: str,
        body: bytes,
        signature: str
    ) -> bool:
        """Verify Slack request signature."""

        # Check timestamp is recent (within 5 minutes)
        if abs(time.time() - int(timestamp)) > 60 * 5:
            return False

        # Compute signature
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        computed = 'v0=' + hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed, signature)

    async def post_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[list] = None
    ) -> dict:
        """Post a message to a channel."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat.postMessage",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "channel": channel,
                    "text": text,
                    "thread_ts": thread_ts,
                    "blocks": blocks
                }
            )
            return response.json()

    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        name: str
    ) -> dict:
        """Add an emoji reaction to a message."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/reactions.add",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "channel": channel,
                    "timestamp": timestamp,
                    "name": name
                }
            )
            return response.json()

    async def remove_reaction(
        self,
        channel: str,
        timestamp: str,
        name: str
    ) -> dict:
        """Remove an emoji reaction from a message."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/reactions.remove",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "channel": channel,
                    "timestamp": timestamp,
                    "name": name
                }
            )
            return response.json()


# app/api/routes/slack.py

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from app.integrations.slack import SlackClient
from app.services.conversation_engine import ConversationEngine
from app.services.unified_search import UnifiedSearchOrchestrator
from app.services.shortlist_builder import ShortlistBuilder

router = APIRouter(prefix="/api/slack", tags=["slack"])
slack = SlackClient()
conversation_engine = ConversationEngine()
search_orchestrator = UnifiedSearchOrchestrator()
shortlist_builder = ShortlistBuilder()


@router.post("/events")
async def handle_events(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle Slack Events API webhooks."""

    # Get raw body for signature verification
    body = await request.body()

    # Verify signature
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    if not slack.verify_signature(timestamp, body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse body
    data = await request.json()

    # Handle URL verification challenge
    if data.get("type") == "url_verification":
        return {"challenge": data["challenge"]}

    # Handle events
    if data.get("type") == "event_callback":
        event = data["event"]

        # Ignore bot messages
        if event.get("bot_id"):
            return {"ok": True}

        # Handle app_mention
        if event["type"] == "app_mention":
            background_tasks.add_task(
                handle_mention,
                channel=event["channel"],
                thread_ts=event.get("thread_ts") or event["ts"],
                user_id=event["user"],
                text=event["text"]
            )

        # Handle direct messages
        elif event["type"] == "message" and event.get("channel_type") == "im":
            background_tasks.add_task(
                handle_mention,
                channel=event["channel"],
                thread_ts=event.get("thread_ts") or event["ts"],
                user_id=event["user"],
                text=event["text"]
            )

    return {"ok": True}


async def handle_mention(
    channel: str,
    thread_ts: str,
    user_id: str,
    text: str
):
    """Process a @hermes mention or DM."""

    # Add thinking reaction
    await slack.add_reaction(channel, thread_ts, "thinking_face")

    try:
        # Clean @mention from text
        clean_text = text.replace("<@", "").split(">", 1)[-1].strip()

        # Get or create conversation
        conversation = await conversation_engine.get_or_create(
            source="slack",
            slack_channel=channel,
            slack_thread_ts=thread_ts,
            user_id=user_id
        )

        # Process message
        response = await conversation_engine.process_message(
            conversation_id=conversation.id,
            message=clean_text
        )

        if response.needs_clarification:
            # Ask clarifying questions
            await slack.post_message(
                channel=channel,
                text=response.question,
                thread_ts=thread_ts
            )

        elif response.role_blueprint:
            # Ready to search
            await slack.post_message(
                channel=channel,
                text=f"Searching ~5,000 candidates (Hermes + Network) for: *{response.role_blueprint['title']}*...",
                thread_ts=thread_ts
            )

            # Run search
            search_result = await search_orchestrator.search(
                company_id=conversation.company_id,
                role_blueprint=response.role_blueprint,
                limit=100
            )

            # Build shortlist
            shortlist = shortlist_builder.build(search_result, target_size=12)

            # Format for Slack
            blocks = shortlist_builder.format_for_slack(shortlist)

            # Deliver shortlist
            await slack.post_message(
                channel=channel,
                text=f"Found {len(shortlist.candidates)} candidates",
                thread_ts=thread_ts,
                blocks=blocks
            )

            # Send stats
            stats_text = (
                f"_Search complete:_\n"
                f"• Hermes candidates searched: {search_result.stats.hermes_searched}\n"
                f"• Network candidates searched: {search_result.stats.network_searched}\n"
                f"• Duplicates merged: {search_result.stats.duplicates_merged}\n"
                f"• Top 30 enriched, Top 5 deep researched\n"
                f"• Time: {search_result.duration_seconds:.1f}s"
            )
            await slack.post_message(
                channel=channel,
                text=stats_text,
                thread_ts=thread_ts
            )

        # Success reaction
        await slack.remove_reaction(channel, thread_ts, "thinking_face")
        await slack.add_reaction(channel, thread_ts, "white_check_mark")

    except Exception as e:
        # Error reaction
        await slack.remove_reaction(channel, thread_ts, "thinking_face")
        await slack.add_reaction(channel, thread_ts, "x")

        await slack.post_message(
            channel=channel,
            text=f"Something went wrong: {str(e)}",
            thread_ts=thread_ts
        )
```

### 4.3 Shortlist Builder

```python
# app/services/shortlist_builder.py

from typing import List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Shortlist:
    candidates: List[Tuple['Candidate', 'ProofBrief']]
    generated_at: datetime
    total_pool_searched: int


class ShortlistBuilder:
    """Builds and formats shortlists for delivery."""

    def build(
        self,
        search_result: 'SearchResult',
        target_size: int = 12
    ) -> Shortlist:
        """Build a shortlist from search results."""

        shortlist = []

        # Priority 1: Warm + Ready (50%)
        warm_ready_count = int(target_size * 0.50)
        shortlist.extend(search_result.tier_1_warm_ready[:warm_ready_count])

        # Priority 2: Warm Intro (30%)
        warm_intro_count = int(target_size * 0.30)
        shortlist.extend(search_result.tier_2_warm_intro[:warm_intro_count])

        # Priority 3: Hermes Cold (15%)
        hermes_cold_count = int(target_size * 0.15)
        shortlist.extend(search_result.tier_3_hermes_cold[:hermes_cold_count])

        # Fill remaining
        remaining = target_size - len(shortlist)
        all_remaining = (
            search_result.tier_1_warm_ready[warm_ready_count:] +
            search_result.tier_2_warm_intro[warm_intro_count:] +
            search_result.tier_3_hermes_cold[hermes_cold_count:] +
            search_result.tier_4_network_cold
        )
        all_remaining.sort(key=lambda x: x[1].match_score, reverse=True)
        shortlist.extend(all_remaining[:remaining])

        return Shortlist(
            candidates=shortlist,
            generated_at=datetime.utcnow(),
            total_pool_searched=search_result.stats.total_unique
        )

    def format_for_slack(self, shortlist: Shortlist) -> List[dict]:
        """Format shortlist as Slack blocks."""

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Shortlist: {len(shortlist.candidates)} candidates"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"_Searched {shortlist.total_pool_searched:,} candidates across Hermes + Network_"
                }
            },
            {"type": "divider"}
        ]

        for i, (candidate, brief) in enumerate(shortlist.candidates, 1):
            blocks.extend(self._format_candidate(i, candidate, brief))

        return blocks

    def _format_candidate(
        self,
        rank: int,
        candidate: 'Candidate',
        brief: 'ProofBrief'
    ) -> List[dict]:
        """Format a single candidate as Slack blocks."""

        # Confidence indicator
        if brief.confidence > 0.7:
            conf_emoji = ":large_green_circle:"
        elif brief.confidence > 0.4:
            conf_emoji = ":large_yellow_circle:"
        else:
            conf_emoji = ":red_circle:"

        # Source badges
        badges = []
        if 'hermes' in candidate.sources:
            badges.append(":card_file_box: Hermes")
        if 'network' in candidate.sources:
            badges.append(":link: Network")
        if len(candidate.sources) > 1:
            badges.append(":sparkles: Multi-source")

        # Build text sections
        header_text = (
            f"*#{rank} - {candidate.full_name}*\n"
            f"{candidate.current_title or 'Unknown'} @ {candidate.current_company or 'Unknown'}\n"
            f"Score: {brief.match_score:.0f}/100 {conf_emoji} ({brief.confidence:.0%} confidence)\n"
            f"_{' | '.join(badges)}_"
        )

        # Known facts
        facts_text = "*Known Facts:*\n"
        for fact in brief.known_facts[:3]:
            facts_text += f"  • {fact.fact}\n"

        # Signals
        strong_signals = [s for s in brief.observed_signals if s.strength == 'strong'][:2]
        if strong_signals:
            facts_text += "*Key Signals:*\n"
            for signal in strong_signals:
                facts_text += f"  • {signal.observation}\n"

        # Unknown
        if brief.unknowns:
            facts_text += f"*Unknown:* {brief.unknowns[0].what_we_dont_know}\n"

        # Warm path
        if brief.warm_path:
            facts_text += f"*Warm Path:* {brief.warm_path.description}\n"

        # Next step
        facts_text += f"*Next Step:* {brief.suggested_next_step}"

        return [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": header_text}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": facts_text}
            },
            {"type": "divider"}
        ]
```

---

## 5. Web Frontend Integration

### 5.1 Update API Client

```typescript
// web/src/lib/api.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// ============================================================
// UNIFIED SEARCH
// ============================================================

export interface RoleBlueprint {
  title: string;
  required_skills: string[];
  nice_to_have_skills?: string[];
  locations?: string[];
  seniority?: 'junior' | 'mid' | 'senior' | 'staff';
}

export interface UnifiedSearchRequest {
  company_id: string;
  role_blueprint: RoleBlueprint;
  limit?: number;
}

export interface Candidate {
  person_id: string;
  full_name: string;
  email?: string;
  linkedin_url?: string;
  github_url?: string;
  location?: string;
  current_company?: string;
  current_title?: string;
  skills: string[];
  sources: string[];
  source_quality: number;
  warmth_score: number;
  data_completeness: number;
}

export interface ProofBrief {
  candidate_id: string;
  candidate_name: string;
  recommendation: 'strong_consider' | 'consider' | 'weak_consider' | 'pass';
  confidence: number;
  match_score: number;
  known_facts: { fact: string; source: string; confidence: number }[];
  observed_signals: { observation: string; inference: string; strength: string }[];
  unknowns: { what_we_dont_know: string; why_it_matters: string; how_to_find_out: string }[];
  warm_path?: { description: string; connector_name: string };
  suggested_next_step: string;
  sources_used: string[];
}

export interface SearchStats {
  hermes_searched: number;
  network_searched: number;
  duplicates_merged: number;
  total_unique: number;
  enriched_count: number;
  researched_count: number;
}

export interface UnifiedSearchResponse {
  search_id: string;
  status: string;
  tier_1_warm_ready: { candidate: Candidate; proof_brief: ProofBrief }[];
  tier_2_warm_intro: { candidate: Candidate; proof_brief: ProofBrief }[];
  tier_3_hermes_cold: { candidate: Candidate; proof_brief: ProofBrief }[];
  tier_4_network_cold: { candidate: Candidate; proof_brief: ProofBrief }[];
  stats: SearchStats;
  duration_seconds: number;
}

export async function unifiedSearch(
  request: UnifiedSearchRequest
): Promise<UnifiedSearchResponse> {
  const response = await fetch(`${API_URL}/api/v1/unified/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error('Search failed');
  }

  return response.json();
}

// ============================================================
// SHORTLIST
// ============================================================

export interface ShortlistRequest {
  search_id: string;
  target_size?: number;
}

export interface Shortlist {
  shortlist_id: string;
  candidates: { candidate: Candidate; proof_brief: ProofBrief }[];
  total_pool_searched: number;
  generated_at: string;
}

export async function generateShortlist(
  request: ShortlistRequest
): Promise<Shortlist> {
  const response = await fetch(`${API_URL}/api/v1/unified/shortlist`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error('Shortlist generation failed');
  }

  return response.json();
}

// ============================================================
// CONVERSATIONS
// ============================================================

export interface Conversation {
  id: string;
  source: 'slack' | 'web';
  company_id: string;
  status: string;
  role_blueprint?: RoleBlueprint;
  messages: { role: 'user' | 'assistant'; content: string }[];
}

export interface ConversationResponse {
  response: string;
  needs_clarification: boolean;
  role_blueprint?: RoleBlueprint;
  search_triggered: boolean;
  search_id?: string;
}

export async function createConversation(
  company_id: string
): Promise<Conversation> {
  const response = await fetch(`${API_URL}/api/conversations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify({
      source: 'web',
      company_id
    })
  });

  if (!response.ok) {
    throw new Error('Failed to create conversation');
  }

  return response.json();
}

export async function sendMessage(
  conversation_id: string,
  message: string
): Promise<ConversationResponse> {
  const response = await fetch(`${API_URL}/api/conversations/${conversation_id}/message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify({ message })
  });

  if (!response.ok) {
    throw new Error('Failed to send message');
  }

  return response.json();
}
```

### 5.2 Agencity Page Updates

The existing `/agencity` page already has a chat interface. Update it to use the unified search:

```typescript
// web/src/app/agencity/page.tsx (key updates)

import {
  createConversation,
  sendMessage,
  unifiedSearch,
  Candidate,
  ProofBrief
} from '@/lib/api';

// Update the search results state to use ProofBrief
interface CandidateResult {
  candidate: Candidate;
  proof_brief: ProofBrief;
}

// Update the search handler
const handleSearch = async (roleBlueprint: RoleBlueprint) => {
  setSearchStatus('searching');

  try {
    const result = await unifiedSearch({
      company_id: companyId,
      role_blueprint: roleBlueprint,
      limit: 100
    });

    // Combine all tiers for display
    const allResults = [
      ...result.tier_1_warm_ready,
      ...result.tier_2_warm_intro,
      ...result.tier_3_hermes_cold,
      ...result.tier_4_network_cold
    ];

    setResults(allResults);
    setStats(result.stats);
    setSearchStatus('complete');

  } catch (error) {
    setSearchStatus('error');
    console.error('Search failed:', error);
  }
};

// Update the result card to show ProofBrief
const CandidateCard = ({ candidate, proof_brief }: CandidateResult) => (
  <div className="border rounded-lg p-4 mb-4">
    <div className="flex justify-between items-start">
      <div>
        <h3 className="font-semibold">{candidate.full_name}</h3>
        <p className="text-sm text-gray-600">
          {candidate.current_title} @ {candidate.current_company}
        </p>
      </div>
      <div className="text-right">
        <span className="text-lg font-bold">{proof_brief.match_score.toFixed(0)}</span>
        <span className="text-sm text-gray-500">/100</span>
        <div className="text-xs">
          {proof_brief.confidence > 0.7 ? '🟢' : proof_brief.confidence > 0.4 ? '🟡' : '🔴'}
          {' '}{(proof_brief.confidence * 100).toFixed(0)}% confidence
        </div>
      </div>
    </div>

    {/* Source badges */}
    <div className="flex gap-2 mt-2">
      {candidate.sources.includes('hermes') && (
        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
          📋 Hermes
        </span>
      )}
      {candidate.sources.includes('network') && (
        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
          🔗 Network
        </span>
      )}
      {candidate.sources.length > 1 && (
        <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
          ✨ Multi-source
        </span>
      )}
    </div>

    {/* Known Facts */}
    <div className="mt-3">
      <h4 className="text-sm font-medium">Known Facts</h4>
      <ul className="text-sm text-gray-600 ml-4 list-disc">
        {proof_brief.known_facts.slice(0, 3).map((fact, i) => (
          <li key={i}>{fact.fact}</li>
        ))}
      </ul>
    </div>

    {/* Signals */}
    {proof_brief.observed_signals.filter(s => s.strength === 'strong').length > 0 && (
      <div className="mt-2">
        <h4 className="text-sm font-medium">Key Signals</h4>
        <ul className="text-sm text-gray-600 ml-4 list-disc">
          {proof_brief.observed_signals
            .filter(s => s.strength === 'strong')
            .slice(0, 2)
            .map((signal, i) => (
              <li key={i}>{signal.observation}</li>
            ))}
        </ul>
      </div>
    )}

    {/* Unknown */}
    {proof_brief.unknowns.length > 0 && (
      <div className="mt-2 text-sm">
        <span className="font-medium">Unknown:</span>{' '}
        <span className="text-gray-600">{proof_brief.unknowns[0].what_we_dont_know}</span>
      </div>
    )}

    {/* Warm Path */}
    {proof_brief.warm_path && (
      <div className="mt-2 text-sm bg-yellow-50 p-2 rounded">
        <span className="font-medium">Warm Path:</span>{' '}
        {proof_brief.warm_path.description}
      </div>
    )}

    {/* Next Step */}
    <div className="mt-2 text-sm">
      <span className="font-medium">Next Step:</span>{' '}
      <span className="text-blue-600">{proof_brief.suggested_next_step}</span>
    </div>
  </div>
);
```

---

## 6. Environment Configuration

### Backend (.env)

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...

# Slack
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_SIGNING_SECRET=xxx

# Enrichment APIs
OPENAI_API_KEY=sk-xxx
PERPLEXITY_API_KEY=pplx-xxx

# Optional: People Data Labs
PDL_API_KEY=xxx

# Server
HOST=0.0.0.0
PORT=8001
DEBUG=false
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## 7. Deployment Checklist

### Phase 1: Database
- [ ] Run migration scripts to create tables
- [ ] Verify `candidates` table has Hermes data
- [ ] Verify `people` table has LinkedIn connections
- [ ] Create indexes for search performance

### Phase 2: Backend
- [ ] Implement `UnifiedSearchOrchestrator`
- [ ] Implement `DeduplicationEngine`
- [ ] Implement `ReasoningEngine`
- [ ] Implement `ShortlistBuilder`
- [ ] Implement Slack routes
- [ ] Test endpoints with curl/Postman

### Phase 3: Slack
- [ ] Create Slack app at api.slack.com
- [ ] Configure OAuth scopes
- [ ] Set up Event Subscriptions
- [ ] Add /hermes slash command
- [ ] Test with ngrok locally
- [ ] Deploy to production URL

### Phase 4: Frontend
- [ ] Update API client with new endpoints
- [ ] Update Agencity page to use unified search
- [ ] Display Proof Briefs properly
- [ ] Test conversation flow

### Phase 5: Testing
- [ ] Test Slack mention flow end-to-end
- [ ] Test web search flow end-to-end
- [ ] Verify deduplication works correctly
- [ ] Verify enrichment pipeline works
- [ ] Load test with full candidate pool

---

## 8. Example Flows

### Flow 1: Slack Mention

```
1. User: @hermes I need a prompt engineer for my AI startup

2. Hermes: (adds 🤔 reaction)
   I'll help you find prompt engineers. A few quick questions:
   1. What does your startup do specifically?
   2. What will this person work on day-to-day?

3. User: We're building a RAG-based writing assistant.
   They'll design prompts and improve output quality.

4. Hermes: Got it. Searching ~5,000 candidates (Hermes + Network)...

   [45 seconds later]

   Shortlist: 12 candidates
   _Searched 4,892 candidates across Hermes + Network_
   ─────────────────────────

   #1 - Sarah Chen
   ML Engineer @ OpenAI
   Score: 87/100 🟢 (85% confidence)
   _📋 Hermes | 🔗 Network | ✨ Multi-source_

   Known Facts:
     • 3 years prompt engineering at OpenAI
     • Published papers on LLM optimization

   Key Signals:
     • Recently updated LinkedIn

   Unknown: Current compensation expectations

   Warm Path: Connected via John (worked together at Google)

   Next Step: Ask John for intro, mention RAG project
   ─────────────────────────

   [... 11 more candidates ...]

   _Search complete:_
   • Hermes searched: 1,375
   • Network searched: 3,637
   • Duplicates merged: 120
   • Time: 47.3s

5. Hermes: (removes 🤔, adds ✅)
```

### Flow 2: Web Interface

```
1. User visits /agencity

2. User types: "I need a backend engineer with Python and FastAPI"

3. Agent asks: "What kind of product are you building?"

4. User responds: "A B2B SaaS platform for HR teams"

5. Agent triggers search:
   - Shows animated search across Hermes + Network
   - Displays progress bar

6. Results appear:
   - 12 candidates in shortlist
   - Each with Proof Brief
   - Tiered by warmth (Tier 1, 2, 3, 4)
   - Stats: 4,892 searched, 120 merged, 47s
```

---

## Version History

- **v3.0** (Feb 12, 2026): End-to-end implementation guide
  - Unified search across Hermes + Network
  - Slack workflow documentation
  - Web frontend integration
  - Proof Brief reasoning system

---

*Implementation Guide v3.0 | Agencity Team*
