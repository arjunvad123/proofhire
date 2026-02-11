# Agencity Backend Specification

## Overview

Backend for Agencity - the AI hiring agent that finds people you can't search for.

**Core Flow:**
```
Conversation → Role Blueprint → Multi-Source Search → Honest Evaluation → Shortlist
```

---

## 1. Context Management (Learned from OpenClaw)

### 1.1 Multi-Stage Context Pruning

```python
class ContextManager:
    """
    Manages conversation context with intelligent pruning.
    Prevents context overflow while preserving critical information.
    """

    # Thresholds (as % of max context window)
    SOFT_TRIM_RATIO = 0.3    # Trigger soft compression at 30%
    HARD_CLEAR_RATIO = 0.5   # Trigger hard removal at 50%

    # What to keep
    PROTECTED_CONTEXTS = [
        "role_blueprint",      # Never prune the extracted blueprint
        "company_context",     # Never prune startup description
        "calibration_examples" # Never prune good/bad hire patterns
    ]

    def prune(self, context: ConversationContext) -> ConversationContext:
        """
        Multi-stage pruning strategy:
        1. Soft trim: Compress middle, keep head/tail of tool results
        2. Hard clear: Replace old content with placeholders
        """
        usage_ratio = self.get_usage_ratio(context)

        if usage_ratio > self.HARD_CLEAR_RATIO:
            return self.hard_clear(context)
        elif usage_ratio > self.SOFT_TRIM_RATIO:
            return self.soft_trim(context)
        return context

    def soft_trim(self, context: ConversationContext) -> ConversationContext:
        """
        Compress non-essential parts:
        - Keep first 1500 chars + last 1500 chars of long tool outputs
        - Summarize old conversation turns
        - Preserve all protected contexts
        """
        pass

    def hard_clear(self, context: ConversationContext) -> ConversationContext:
        """
        Replace old content with placeholders:
        - "[Candidate search results from earlier - 12 candidates found]"
        - "[Previous conversation about role requirements - see blueprint]"
        """
        pass
```

### 1.2 Token Budget Allocation

```python
class TokenBudget:
    """
    Allocate token budget across context sources.
    Total budget depends on model (Claude: ~180k, but keep headroom).
    """

    MAX_CONTEXT = 100_000  # Conservative limit with response headroom

    ALLOCATIONS = {
        "system_prompt": 2_000,
        "role_blueprint": 3_000,
        "conversation_history": 15_000,
        "candidate_data": 50_000,      # Main budget for search results
        "evaluation_context": 20_000,
        "response_headroom": 10_000,
    }

    def allocate(self, query_type: str) -> dict[str, int]:
        """
        Dynamic allocation based on query type:
        - "intake": More budget for conversation
        - "search": More budget for candidate data
        - "evaluate": More budget for evaluation context
        """
        pass
```

---

## 2. RAG System (Hybrid Search)

### 2.1 Architecture

```
Query → [Keyword Search] + [Vector Search] → Merge → Re-rank → Top-K Results
```

### 2.2 Implementation

```python
class HybridRAG:
    """
    Combines keyword search (fast, precise) with vector search (semantic).
    """

    def __init__(self, pg_client, embedding_model):
        self.pg = pg_client           # PostgreSQL with pgvector
        self.embedder = embedding_model

    async def search(
        self,
        query: str,
        blueprint: RoleBlueprint,
        limit: int = 50
    ) -> list[CandidateData]:
        """
        1. Generate embeddings for query + blueprint
        2. Run keyword search (full-text, filters)
        3. Run vector search (semantic similarity)
        4. Merge with weighted scoring
        5. Re-rank based on blueprint criteria
        """

        # Parallel searches
        keyword_results = await self.keyword_search(query, blueprint)
        vector_results = await self.vector_search(query, blueprint)

        # Merge and dedupe
        merged = self.merge_results(keyword_results, vector_results)

        # Re-rank based on blueprint
        reranked = await self.rerank(merged, blueprint)

        return reranked[:limit]

    async def keyword_search(
        self,
        query: str,
        blueprint: RoleBlueprint
    ) -> list[SearchResult]:
        """
        PostgreSQL full-text search with filters:
        - Schools in location_preferences
        - Skills in must_haves
        - Exclude patterns in avoid
        """
        # Use ts_query with weights
        pass

    async def vector_search(
        self,
        query: str,
        blueprint: RoleBlueprint
    ) -> list[SearchResult]:
        """
        pgvector similarity search:
        - Embed: role_title + specific_work + success_criteria
        - Search against candidate embeddings
        """
        embedding = await self.embedder.embed(
            f"{blueprint.role_title} {blueprint.specific_work}"
        )
        # cosine similarity search
        pass

    def merge_results(
        self,
        keyword: list[SearchResult],
        vector: list[SearchResult]
    ) -> list[SearchResult]:
        """
        Weighted merge:
        - Keyword match: 0.4 weight (precision)
        - Vector match: 0.6 weight (semantic understanding)
        - Boost if in both result sets
        """
        pass
```

### 2.3 Embedding Strategy

```python
class CandidateEmbedder:
    """
    Generate embeddings for candidate profiles.
    Embed structured data as natural language for better semantic matching.
    """

    def embed_candidate(self, candidate: CandidateData) -> list[float]:
        """
        Convert structured data to embeddable text:

        "Maya Patel is a Computer Science student at UCSD, Class of 2026.
        Active in Triton AI club. Has 2 ML projects on GitHub including
        one that uses LLM APIs. Won Best AI Project at SD Hacks 2024.
        Interests: machine learning, LLMs, prompt engineering."
        """
        text = self.to_natural_language(candidate)
        return self.model.embed(text)
```

---

## 3. Data Sources

### 3.1 Source Priority Matrix

| Priority | Source | Coverage | Freshness | API Access | Cost |
|----------|--------|----------|-----------|------------|------|
| P0 | Our Network | 6,000+ | Real-time | Direct DB | Free |
| P1 | GitHub | 100M+ devs | Daily | GraphQL API | Rate limited |
| P2 | Devpost | 2M+ hackers | Weekly | REST + Scrape | Free |
| P3 | University Clubs | Variable | Manual | Scrape | Free |
| P4 | PDL Enrichment | 1.5B profiles | On-demand | REST API | $0.03-0.10/call |

### 3.2 Source Implementations

```python
# Base interface
class DataSource(ABC):
    @abstractmethod
    async def search(self, blueprint: RoleBlueprint) -> list[CandidateData]:
        pass

    @abstractmethod
    async def enrich(self, candidate: CandidateData) -> CandidateData:
        pass

# GitHub implementation
class GitHubSource(DataSource):
    """
    Search GitHub for developers matching blueprint.
    Uses GraphQL API for efficiency.
    """

    async def search(self, blueprint: RoleBlueprint) -> list[CandidateData]:
        """
        Search strategies:
        1. Repo search: Find repos matching skills, get contributors
        2. User search: Search by location, language, bio keywords
        3. Stars/forks: Find people who starred relevant repos
        """
        pass

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """
        For each candidate with github_username:
        - Fetch contribution history (last 12 months)
        - Analyze top repos (languages, descriptions)
        - Check for README quality, documentation
        - Look for LLM/AI related projects
        """
        query = """
        query($username: String!) {
            user(login: $username) {
                contributionsCollection {
                    totalCommitContributions
                    totalPullRequestContributions
                    contributionCalendar {
                        totalContributions
                    }
                }
                repositories(first: 10, orderBy: {field: STARGAZERS_COUNT, direction: DESC}) {
                    nodes {
                        name
                        description
                        primaryLanguage { name }
                        stargazerCount
                    }
                }
            }
        }
        """
        pass

# Devpost implementation
class DevpostSource(DataSource):
    """
    Search hackathon projects and participants.
    Great for finding builders who ship fast.
    """

    async def search(self, blueprint: RoleBlueprint) -> list[CandidateData]:
        """
        1. Search hackathon projects by tech/topic
        2. Find winners and notable submissions
        3. Extract team member profiles
        """
        pass

# People Data Labs enrichment
class PDLEnricher:
    """
    Enrich candidate data with professional info.
    Use sparingly - costs $0.03-0.10 per call.
    """

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """
        Enrich with:
        - Verified email
        - Current company/role
        - Education details
        - Skills from LinkedIn
        """
        # Only call if we have email or LinkedIn URL
        if not candidate.email and not candidate.linkedin_url:
            return candidate

        response = await self.client.person.enrich(
            email=candidate.email,
            linkedin_url=candidate.linkedin_url
        )

        # Merge enriched data
        pass
```

### 3.3 Data Freshness & Caching

```python
class SourceCache:
    """
    Cache source data with appropriate TTLs.
    Balance freshness vs. API costs.
    """

    TTL_CONFIG = {
        "github_profile": timedelta(days=7),      # Profiles change slowly
        "github_repos": timedelta(days=1),        # Repos change more often
        "devpost_projects": timedelta(days=30),   # Hackathons are static
        "pdl_enrichment": timedelta(days=90),     # Expensive, cache longer
        "our_network": timedelta(minutes=5),      # Our data, keep fresh
    }
```

---

## 4. People Search API Integration

### 4.1 Recommended: People Data Labs

```python
class PeopleDataLabsClient:
    """
    People Data Labs API client.
    Use for enrichment, not bulk search (cost-effective).
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.peopledatalabs.com/v5"

    async def enrich_person(
        self,
        email: str = None,
        linkedin_url: str = None,
        github_url: str = None,
        name: str = None,
        company: str = None
    ) -> dict | None:
        """
        Enrich a person record.

        Returns:
        {
            "full_name": "Maya Patel",
            "emails": [{"address": "maya@example.com", "type": "current"}],
            "education": [{"school": {"name": "UC San Diego"}, "degrees": ["BS"]}],
            "experience": [...],
            "skills": ["python", "machine learning", ...],
            "linkedin_url": "...",
            "github_url": "..."
        }
        """
        pass

    async def search_people(
        self,
        query: dict,
        size: int = 100
    ) -> list[dict]:
        """
        Search for people matching criteria.

        Example query:
        {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"location_country": "united states"}},
                        {"term": {"education.school.name": "UC San Diego"}},
                        {"exists": {"field": "github_url"}}
                    ]
                }
            }
        }

        Note: Expensive for bulk - use sparingly.
        """
        pass
```

### 4.2 Cost Management

```python
class EnrichmentBudget:
    """
    Manage enrichment API costs.
    Only enrich candidates that pass initial filters.
    """

    DAILY_BUDGET_USD = 50.0
    COST_PER_ENRICHMENT = 0.05  # Average PDL cost

    async def should_enrich(self, candidate: CandidateData) -> bool:
        """
        Only enrich if:
        1. Within daily budget
        2. Candidate passes initial relevance threshold
        3. We don't already have this data cached
        """
        if await self.is_cached(candidate):
            return False

        if not await self.has_budget():
            return False

        # Only enrich candidates that look promising
        if candidate.initial_relevance_score < 0.5:
            return False

        return True
```

---

## 5. LLM Integration (Claude)

### 5.1 Modular Prompt System

```python
class PromptBuilder:
    """
    Build prompts from modular components.
    Inspired by OpenClaw's context assembly.
    """

    def build_conversation_prompt(
        self,
        conversation: list[Message],
        blueprint: RoleBlueprint | None
    ) -> str:
        """
        Prompt for intake conversation.
        Goal: Extract enough context to build blueprint.
        """
        return f"""You are a hiring expert helping founders find the right candidates.

Your goal is to understand what they actually need - not just the job title, but:
- What will this person actually build/do?
- What does success look like by day 60?
- What patterns have worked or failed before?
- Any location/school preferences?

Ask focused follow-up questions until you can fill out a complete Role Blueprint.
Don't ask more than 2-3 questions at a time. Be conversational.

When you have enough context, respond with ONLY a JSON blueprint:
```json
{{"role_title": "...", "company_context": "...", ...}}
```

{self.format_conversation(conversation)}
"""

    def build_evaluation_prompt(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint
    ) -> str:
        """
        Prompt for honest candidate evaluation.
        Separates known facts from inferences.
        """
        return f"""Evaluate this candidate against the role blueprint.

IMPORTANT: Be honest about what you know vs. don't know.
- Known Facts: Verifiable from the data (school, projects, etc.)
- Observed Signals: What we can infer from behavior (GitHub activity, etc.)
- Unknown: What we can't verify from this data alone

Role Blueprint:
{json.dumps(blueprint.dict(), indent=2)}

Candidate Data:
{json.dumps(candidate.dict(), indent=2)}

Respond with:
```json
{{
    "known_facts": ["UCSD CS 2026", "Member of Triton AI club", ...],
    "observed_signals": ["2 ML projects on GitHub", "Active contributor", ...],
    "unknown": ["Actual skill depth", "Work style", "Interest in startups", ...],
    "why_consider": "Brief connection to what the founder described",
    "next_step": "Specific question to ask in first conversation"
}}
```
"""
```

### 5.2 Conversation State Machine

```python
class ConversationEngine:
    """
    Manages the intake conversation flow.
    Decides when we have enough context for a blueprint.
    """

    REQUIRED_FIELDS = [
        "role_title",
        "company_context",
        "specific_work",
        "success_criteria"
    ]

    HELPFUL_FIELDS = [
        "must_haves",
        "nice_to_haves",
        "avoid",
        "location_preferences",
        "calibration_examples"
    ]

    async def process_message(
        self,
        conversation_id: str,
        user_message: str
    ) -> ConversationResponse:
        """
        Process user message and decide next action:
        1. Ask more questions (not enough context)
        2. Extract blueprint (have enough context)
        3. Trigger search (blueprint complete)
        """
        conversation = await self.get_conversation(conversation_id)
        conversation.add_message("user", user_message)

        # Try to extract partial blueprint
        partial_blueprint = await self.extract_partial(conversation)

        # Check if we have enough
        if self.has_enough_context(partial_blueprint):
            # Complete the blueprint
            blueprint = await self.finalize_blueprint(conversation)

            # Trigger search
            await self.trigger_search(conversation_id, blueprint)

            return ConversationResponse(
                message="Got it! I have enough context. Let me search for candidates...",
                blueprint=blueprint,
                status="searching"
            )

        # Need more context - ask follow-up
        next_question = await self.get_next_question(
            conversation,
            partial_blueprint
        )

        return ConversationResponse(
            message=next_question,
            status="intake"
        )

    def has_enough_context(self, blueprint: RoleBlueprint | None) -> bool:
        """
        Check if blueprint has all required fields with substance.
        """
        if not blueprint:
            return False

        for field in self.REQUIRED_FIELDS:
            value = getattr(blueprint, field, None)
            if not value or len(str(value)) < 10:
                return False

        return True
```

---

## 6. Evaluation Engine

### 6.1 Honest Assessment Framework

```python
class EvaluationEngine:
    """
    Evaluates candidates honestly against blueprint.
    Key principle: NO CLAIMS WE CAN'T VERIFY.
    """

    async def evaluate(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint
    ) -> EvaluatedCandidate:
        """
        Three-tier evaluation:
        1. Known Facts - Verifiable from data
        2. Observed Signals - Reasonable inferences
        3. Unknown - What we can't determine
        """

        known_facts = self.extract_known_facts(candidate)
        observed_signals = await self.extract_signals(candidate, blueprint)
        unknown = self.identify_unknowns(candidate, blueprint)

        why_consider = await self.generate_why(candidate, blueprint)
        next_step = await self.suggest_next_step(candidate, blueprint, unknown)

        # Internal relevance score (not shown to user)
        relevance = self.compute_relevance(
            candidate, blueprint, known_facts, observed_signals
        )

        return EvaluatedCandidate(
            candidate=candidate,
            known_facts=known_facts,
            observed_signals=observed_signals,
            unknown=unknown,
            why_consider=why_consider,
            next_step=next_step,
            relevance_score=relevance
        )

    def extract_known_facts(self, candidate: CandidateData) -> list[str]:
        """
        Extract only verifiable facts:
        - School name + graduation year
        - Club memberships (if from official source)
        - GitHub username existence
        - Hackathon participation (if from Devpost)
        """
        facts = []

        if candidate.school and candidate.graduation_year:
            facts.append(f"{candidate.school}, Class of {candidate.graduation_year}")

        if candidate.major:
            facts.append(f"{candidate.major} major")

        for club in candidate.clubs:
            facts.append(f"Member of {club}")

        if candidate.github_username:
            facts.append(f"GitHub profile: {candidate.github_username}")

        return facts

    async def extract_signals(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint
    ) -> list[str]:
        """
        Extract signals relevant to blueprint.
        These are observations, not claims.

        Example:
        - "2 repositories with LLM API usage" (not "strong LLM skills")
        - "Committed 5 days/week over past 3 months" (not "dedicated developer")
        """
        signals = []

        # GitHub signals
        if candidate.github_repos:
            # Count repos matching blueprint skills
            relevant_repos = self.filter_relevant_repos(
                candidate.github_repos,
                blueprint.must_haves
            )
            if relevant_repos:
                signals.append(
                    f"GitHub: {len(relevant_repos)} projects related to {blueprint.role_title}"
                )

            # Activity pattern
            if candidate.github_activity:
                if candidate.github_activity.commits_last_90_days > 50:
                    signals.append("Active GitHub contributor (50+ commits in 90 days)")

        # Hackathon signals
        if candidate.hackathons:
            for h in candidate.hackathons:
                if h.won_prize:
                    signals.append(f"Won {h.prize} at {h.name}")
                else:
                    signals.append(f"Built project at {h.name}")

        return signals

    def identify_unknowns(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint
    ) -> list[str]:
        """
        What does the blueprint require that we CAN'T verify?
        This is where we're honest about our limitations.
        """
        unknowns = []

        # Always unknown from public data
        unknowns.append("Actual skill depth (need to verify in conversation)")
        unknowns.append("Work style and communication")
        unknowns.append("Interest in this specific opportunity")

        # Blueprint-specific unknowns
        if "fast" in blueprint.success_criteria.lower():
            unknowns.append("Shipping speed in team environment")

        if "production" in blueprint.specific_work.lower():
            unknowns.append("Production system experience")

        return unknowns
```

---

## 7. Directory Structure

```
agencity/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── conversations.py
│   │   │   ├── search.py
│   │   │   ├── shortlists.py
│   │   │   └── candidates.py
│   │   └── router.py
│   │
│   ├── core/
│   │   ├── context_manager.py      # Multi-stage pruning
│   │   ├── conversation_engine.py  # Intake flow
│   │   ├── search_engine.py        # Multi-source search
│   │   ├── evaluation_engine.py    # Honest assessment
│   │   ├── shortlist_generator.py  # Ranking + output
│   │   └── prompt_builder.py       # Modular prompts
│   │
│   ├── rag/
│   │   ├── hybrid_search.py        # Keyword + vector
│   │   ├── embedder.py             # Candidate embeddings
│   │   └── reranker.py             # Blueprint-based reranking
│   │
│   ├── sources/
│   │   ├── base.py                 # DataSource interface
│   │   ├── network.py              # Our 6,000+ candidates
│   │   ├── github.py               # GitHub API
│   │   ├── devpost.py              # Hackathon data
│   │   ├── pdl.py                  # People Data Labs
│   │   └── cache.py                # Source caching
│   │
│   ├── models/
│   │   ├── conversation.py
│   │   ├── candidate.py
│   │   ├── blueprint.py
│   │   └── evaluation.py
│   │
│   ├── services/
│   │   ├── llm.py                  # Claude API wrapper
│   │   └── enrichment.py           # PDL + GitHub enrichment
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── repositories/
│   │
│   ├── config.py
│   └── main.py
│
├── tests/
├── scripts/
│   └── seed_candidates.py
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 8. Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| API | FastAPI | Async, good typing |
| Database | PostgreSQL + pgvector | Relational + vector search |
| Cache | Redis | Context state, rate limiting |
| LLM | Claude API | Best reasoning, long context |
| Embeddings | Voyage AI or OpenAI | Good quality, reasonable cost |
| Queue | Redis Queue | Async search jobs |
| Storage | S3 | Candidate artifacts |

---

## 9. MVP Build Order

### Week 1: Foundation
1. Set up FastAPI project with PostgreSQL + pgvector
2. Implement ContextManager with pruning
3. Basic ConversationEngine with Claude
4. Blueprint extraction

### Week 2: Search
1. Implement HybridRAG (keyword + vector)
2. Build NetworkSource (our 6,000 candidates)
3. Build GitHubSource (API integration)
4. Source caching layer

### Week 3: Evaluation
1. Implement EvaluationEngine
2. Known facts extraction
3. Signal extraction (LLM-assisted)
4. Unknown identification
5. Shortlist generation

### Week 4: Integration
1. End-to-end flow testing
2. DevpostSource integration
3. PDL enrichment (cost-managed)
4. Connect to frontend demo
5. Polish and launch

---

## 10. Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/agencity

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# Embeddings
VOYAGE_API_KEY=...  # or OPENAI_API_KEY

# Data Sources
GITHUB_TOKEN=ghp_...
PDL_API_KEY=...

# App
APP_ENV=development
SECRET_KEY=...
```
