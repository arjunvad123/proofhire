# Agencity Changelog

## What's Been Built

### Phase 1: Core Backend (Complete)

**Conversation Engine** - `app/core/conversation_engine.py`
- GPT-4o powered intake conversation
- Smart follow-up questions based on context
- Automatic blueprint extraction when ready
- Question bank for different role types

**Role Blueprint Model** - `app/models/blueprint.py`
- Structured output: role_title, company_context, specific_work
- Success criteria, must-haves, nice-to-haves
- Location preferences, calibration examples

**LLM Service** - `app/services/llm.py`
- OpenAI GPT-4o integration
- Async API calls
- Embedding support for semantic search

**Context Manager** - `app/core/context_manager.py`
- OpenClaw-inspired multi-stage pruning
- Soft trim at 30%, hard clear at 50%
- Protected contexts (blueprint never pruned)

---

### Phase 2: Multi-Source Search (Complete)

**Search Engine** - `app/core/search_engine.py`
- Parallel search across 9 sources
- Deduplication across sources
- Candidate enrichment pipeline

**Data Sources Implemented:**

| Source | File | Status |
|--------|------|--------|
| Network (6,000+) | `app/sources/network.py` | Ready (needs DB) |
| GitHub | `app/sources/github.py` | Working |
| Clado (LinkedIn) | `app/sources/clado.py` | Ready (needs API key) |
| Pearch (LinkedIn) | `app/sources/pearch.py` | Ready (needs API key) |
| Devpost | `app/sources/devpost.py` | Working |
| Codeforces | `app/sources/codeforces.py` | Working |
| Stack Overflow | `app/sources/stackoverflow.py` | Working |
| HackerNews | `app/sources/hackernews.py` | Working |
| ProductHunt | `app/sources/producthunt.py` | Working |

---

### Phase 3: Honest Evaluation (Complete)

**Evaluation Engine** - `app/core/evaluation_engine.py`
- Known facts extraction (verifiable data)
- Observed signals (inferred from activity)
- Unknown identification (what we can't verify)
- "Why consider" generation
- "Next step" suggestions

**Key Principle:** No match scores shown to users. Only factual breakdown.

---

### Phase 4: API & Frontend (Complete)

**FastAPI Backend** - `app/main.py`
- `/conversations` endpoints
- `/conversations/{id}/message`
- Health check endpoint
- CORS configured for frontend

**Test Frontend** - `web/src/app/agencity/page.tsx`
- React chat interface
- Candidate cards display
- Connects to backend at localhost:8001

---

## What's In Progress

### Database Integration
- Need to connect PostgreSQL with 6,000+ candidates
- Schema design pending
- Waiting for SQL access

### Demo Preparation
- Demo plan created: `docs/demo/DEMO_PLAN.md`
- Need to identify hero candidates
- Frontend polish needed

---

## What's Planned

### Phase 5: Graph Network
- Entity model (Person, Company, School, Skill, Project)
- Relationship types (WORKS_AT, KNOWS, HAS_SKILL)
- Entity resolution (merge same person from multiple sources)
- Trust propagation scores

### Phase 6: Proactive Agent
- Clock-cycle triggers
- New candidate detection
- Automated recommendations
- Email/Slack notifications

### Phase 7: Two-Way Marketplace
- Candidate portal
- Job discovery for candidates
- Preference matching
- Privacy controls

---

## Configuration

**Environment Variables** (`.env`):
```
OPENAI_API_KEY=sk-proj-...
DEFAULT_MODEL=gpt-4o
GITHUB_TOKEN=ghp_...
```

**Ports:**
- Backend: 8001
- Frontend: 3000 (via Next.js)

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.11+) |
| LLM | OpenAI GPT-4o |
| Database | PostgreSQL + pgvector (planned) |
| Cache | Redis (planned) |
| Frontend | Next.js + React |
| Deployment | TBD |

---

## Known Issues

1. **NetworkSource needs database** - Currently returns empty results
2. **Clado/Pearch need API keys** - User needs to sign up
3. **Port 8001 conflicts** - Kill existing process before restart

---

## Date Log

| Date | What Changed |
|------|--------------|
| Session 1 | Initial backend structure, conversation engine |
| Session 2 | Added 9 data sources, evaluation engine |
| Session 3 | Documentation, demo planning |
