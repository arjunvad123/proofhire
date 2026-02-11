# Agencity Backend Architecture

## Overview

Build the simplest thing that works end-to-end, then iterate.

```
User Input → Conversation Engine → Role Blueprint → Search Engine → Evaluation → Shortlist
                                                          ↑
                                              [Multiple Data Sources]
```

---

## Core Components

### 1. Conversation Engine
**Purpose:** Understand what the founder actually needs.

```
Input:  "I need a prompt engineer for my startup"
Output: Structured Role Blueprint (JSON)
```

**How it works:**
- LLM-powered conversation
- Has a "question bank" for different role types
- Decides when it has enough context (heuristic: can fill out Blueprint)
- Outputs structured data, not just chat

**Key logic:**
```python
class ConversationEngine:
    def get_next_question(self, context: dict) -> str | None:
        """Returns next question, or None if we have enough context."""

    def extract_blueprint(self, conversation: list) -> RoleBlueprint:
        """Extracts structured blueprint from conversation."""

    def has_enough_context(self, context: dict) -> bool:
        """Checks if we can generate a useful blueprint."""
```

**Blueprint schema:**
```python
class RoleBlueprint:
    role_title: str                    # "Prompt Engineer"
    company_context: str               # What the startup does
    specific_work: str                 # What they'll actually build
    success_criteria: str              # What success looks like (day 60)
    must_haves: list[str]              # Non-negotiables
    nice_to_haves: list[str]           # Preferences
    avoid: list[str]                   # Red flags / anti-patterns
    location_preferences: list[str]    # Schools, cities, remote
    calibration_examples: list[str]    # Good/bad hire patterns
```

---

### 2. Search Engine
**Purpose:** Find candidates from multiple sources.

```
Input:  Role Blueprint
Output: List of raw CandidateData
```

**Data sources (MVP priority order):**

| Priority | Source | How to access |
|----------|--------|---------------|
| P0 | Our network (6,000+) | PostgreSQL query |
| P1 | GitHub | GitHub API |
| P2 | Hackathons | Devpost API / scrape |
| P3 | University clubs | Manual curation / scrape |
| P4 | LinkedIn | Manual / future API |

**How it works:**
```python
class SearchEngine:
    def search(self, blueprint: RoleBlueprint) -> list[CandidateData]:
        """Searches all sources, returns raw candidate data."""

        results = []

        # Search our network first (fastest, highest quality)
        results += self.search_network(blueprint)

        # Enrich with GitHub data
        results = self.enrich_github(results)

        # Search external sources
        results += self.search_github_users(blueprint)
        results += self.search_hackathons(blueprint)

        return self.dedupe(results)
```

**CandidateData schema:**
```python
class CandidateData:
    # Identity
    name: str
    email: str | None

    # Known facts (verifiable)
    school: str | None
    major: str | None
    graduation_year: int | None
    location: str | None
    clubs: list[str]
    courses: list[str]

    # Observed signals (from APIs)
    github_username: str | None
    github_repos: list[RepoData]
    github_activity: ActivityStats
    hackathons: list[HackathonData]
    projects: list[ProjectData]

    # Source tracking
    sources: list[str]  # Where we found this person
```

---

### 3. Evaluation Engine
**Purpose:** Honestly assess candidates against the blueprint.

```
Input:  CandidateData + RoleBlueprint
Output: EvaluatedCandidate (with known/unknown breakdown)
```

**Key principle: NO CLAIMS WE CAN'T VERIFY.**

```python
class EvaluationEngine:
    def evaluate(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint
    ) -> EvaluatedCandidate:
        """Evaluates candidate honestly against blueprint."""

        return EvaluatedCandidate(
            candidate=candidate,
            known_facts=self.extract_known_facts(candidate),
            observed_signals=self.extract_signals(candidate, blueprint),
            unknown=self.identify_unknowns(candidate, blueprint),
            why_consider=self.generate_why(candidate, blueprint),
            next_step=self.suggest_next_step(candidate, blueprint),
            relevance_score=self.compute_relevance(candidate, blueprint),  # Internal only
        )
```

**EvaluatedCandidate schema:**
```python
class EvaluatedCandidate:
    candidate: CandidateData

    # The honest breakdown
    known_facts: list[str]       # "UCSD CS, Class of 2026"
    observed_signals: list[str]  # "2 ML projects on GitHub"
    unknown: list[str]           # "Actual prompt engineering depth"

    # Reasoning
    why_consider: str            # Connection to blueprint
    next_step: str               # What to ask/verify

    # Internal (not shown as "match score")
    relevance_score: float       # For ranking only
```

**Evaluation logic (LLM-assisted):**
```python
def extract_signals(self, candidate: CandidateData, blueprint: RoleBlueprint) -> list[str]:
    """
    Look at candidate data and extract signals relevant to blueprint.

    Example:
    - Blueprint says: "prompt engineer, production-focused"
    - Candidate has: GitHub repo with LLM API calls
    - Signal: "GitHub: repo using Claude API for code generation"
    """

def identify_unknowns(self, candidate: CandidateData, blueprint: RoleBlueprint) -> list[str]:
    """
    What does the blueprint require that we CAN'T verify from available data?

    Example:
    - Blueprint says: "success = ships fast"
    - We have: GitHub activity (commits)
    - But we DON'T have: actual shipping speed in team context
    - Unknown: "Shipping speed in team environment"
    """
```

---

### 4. Shortlist Generator
**Purpose:** Rank and format candidates for presentation.

```python
class ShortlistGenerator:
    def generate(
        self,
        candidates: list[EvaluatedCandidate],
        blueprint: RoleBlueprint,
        limit: int = 5
    ) -> Shortlist:
        """Generates ranked shortlist."""

        # Rank by relevance (internal score)
        ranked = sorted(candidates, key=lambda c: c.relevance_score, reverse=True)

        # Take top N
        top = ranked[:limit]

        # Format for output (no scores shown)
        return Shortlist(
            blueprint=blueprint,
            candidates=top,
            search_sources=self.get_sources_used(),
            generated_at=datetime.now(),
        )
```

---

## Data Models

```python
# Core models

class Conversation:
    id: str
    user_id: str
    messages: list[Message]
    blueprint: RoleBlueprint | None
    status: str  # "in_progress", "complete"
    created_at: datetime

class Message:
    role: str  # "user" or "agent"
    content: str
    timestamp: datetime

class Candidate:
    id: str
    name: str
    email: str | None
    data: CandidateData  # JSON blob
    sources: list[str]
    created_at: datetime
    updated_at: datetime

class Shortlist:
    id: str
    conversation_id: str
    blueprint: RoleBlueprint
    candidates: list[EvaluatedCandidate]
    feedback: list[CandidateFeedback]  # User's yes/no
    created_at: datetime

class CandidateFeedback:
    candidate_id: str
    decision: str  # "interested", "pass", "hired"
    reason: str | None
    created_at: datetime
```

---

## Tech Stack (MVP)

| Component | Technology | Why |
|-----------|------------|-----|
| API | FastAPI (Python) | Fast to build, async, good typing |
| Database | PostgreSQL | Relational, good for candidates |
| Cache | Redis | Session state, rate limiting |
| LLM | Claude API | Conversation, evaluation reasoning |
| Search | PostgreSQL full-text + pgvector | Start simple |
| Queue | Redis Queue (RQ) | Async search jobs |
| Storage | S3 | Candidate artifacts if needed |

---

## API Endpoints

```
# Conversation
POST   /conversations              # Start new conversation
POST   /conversations/{id}/message # Send message, get response
GET    /conversations/{id}         # Get conversation state
GET    /conversations/{id}/blueprint # Get extracted blueprint

# Search & Shortlist
POST   /conversations/{id}/search  # Trigger search (async)
GET    /shortlists/{id}            # Get shortlist results
POST   /shortlists/{id}/feedback   # Submit feedback on candidate

# Candidates (internal)
GET    /candidates                 # List candidates in network
POST   /candidates                 # Add candidate to network
GET    /candidates/{id}            # Get candidate details
```

---

## Directory Structure

```
agencity/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── conversations.py
│   │   │   ├── shortlists.py
│   │   │   └── candidates.py
│   │   └── router.py
│   │
│   ├── core/
│   │   ├── conversation_engine.py
│   │   ├── search_engine.py
│   │   ├── evaluation_engine.py
│   │   └── shortlist_generator.py
│   │
│   ├── models/
│   │   ├── conversation.py
│   │   ├── candidate.py
│   │   ├── blueprint.py
│   │   └── shortlist.py
│   │
│   ├── services/
│   │   ├── llm.py              # Claude API wrapper
│   │   ├── github.py           # GitHub API
│   │   ├── hackathons.py       # Devpost, etc.
│   │   └── enrichment.py       # Data enrichment
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── repositories/
│   │       ├── conversations.py
│   │       ├── candidates.py
│   │       └── shortlists.py
│   │
│   ├── config.py
│   └── main.py
│
├── tests/
├── scripts/
│   └── seed_candidates.py      # Load initial 6,000 candidates
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## MVP Build Order

### Week 1: Core Conversation
1. Set up FastAPI project structure
2. Implement Conversation Engine with Claude
3. Basic question flow (hardcoded for prompt engineer)
4. Blueprint extraction
5. Test: Can we get from vague input to structured blueprint?

### Week 2: Search (Network Only)
1. PostgreSQL schema for candidates
2. Seed script to load candidates
3. Basic search (filter by school, skills, keywords)
4. Full-text search on candidate data
5. Test: Can we find relevant candidates from our network?

### Week 3: Evaluation
1. Implement Evaluation Engine
2. Known facts extraction
3. Signal extraction (LLM-assisted)
4. Unknown identification
5. Why consider + next step generation
6. Test: Is the output honest and useful?

### Week 4: End-to-End + Polish
1. Shortlist generation and ranking
2. API endpoints for full flow
3. Feedback collection
4. Connect to frontend demo
5. Test: Full flow works end-to-end

### Week 5+: Expand
- GitHub API integration
- Hackathon data (Devpost)
- University club scraping
- Feedback loop (improve ranking)

---

## Key Design Decisions

### 1. LLM for reasoning, not for everything
- Use Claude for: conversation, understanding intent, generating "why consider"
- Don't use Claude for: search, ranking, database queries
- Keep it cheap and fast

### 2. Honest by design
- Never compute a "match score" to show users
- Always categorize info as known/observed/unknown
- If we can't verify it, say "unknown"

### 3. Start with our network
- MVP searches only our 6,000 candidates
- Much faster to build than API integrations
- Higher quality (opted-in candidates)
- Add external sources in v2

### 4. Async search
- Search can be slow (multiple sources)
- Return immediately, poll for results
- Better UX

### 5. Feedback is gold
- Collect yes/no on every candidate
- Collect reasons when possible
- Use to improve ranking over time

---

## What We're NOT Building (MVP)

- ❌ Real-time LinkedIn scraping
- ❌ Automated outreach
- ❌ Calendar integration
- ❌ ATS features
- ❌ Team collaboration
- ❌ Complex permissions
- ❌ RL training pipeline (future)

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/agencity

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# GitHub (for v2)
GITHUB_TOKEN=ghp_...

# App
APP_ENV=development
SECRET_KEY=...
```

---

## Next Steps

1. **Create the repo structure** (I can do this now)
2. **Implement Conversation Engine** (most critical - the intake)
3. **Set up candidate database** (need to seed the 6,000)
4. **Build basic search** (filter + full-text)
5. **Add evaluation** (LLM-assisted honest assessment)
6. **Connect to frontend** (the demo we built)

---

## Questions to Answer

1. **Where are the 6,000 candidates?** Do we have a database/CSV to import?
2. **What fields do we have for each candidate?** School, GitHub, email?
3. **Do we have GitHub tokens?** For API access
4. **Hosting?** Vercel for frontend, Railway/Render for backend?
5. **Domain?** agencity.com?
