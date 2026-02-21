# Data Sources Audit - ProofHire/Agencity

**Date:** February 2026
**Purpose:** Identify reliable data sources for candidate validation pipeline
**Status:** Research/Audit Phase

---

## Executive Summary

The system has **15+ data source integrations** but only a subset provide consistently reliable data. This audit identifies what we can trust versus what needs validation.

### Source of Truth
**LinkedIn Connection Extraction** provides the only consistently reliable baseline:
- `linkedin_url` (verified)
- `full_name` (verified)
- `current_company` (parsed from headline)
- `current_title` (parsed from headline)

Everything else requires external verification/enrichment.

---

## Part 1: Primary Data Sources

### 1.1 LinkedIn Connection Extraction
**File:** `app/services/linkedin/connection_extractor.py`

| Attribute | Value |
|-----------|-------|
| Method | Browser automation (Playwright + stealth) |
| Cost | Free (proxy costs apply) |
| Rate Limits | 50 msg/day, 100 enrichments/day, 30-day session |
| Reliability | **HIGH** - direct from LinkedIn DOM |

**Fields Extracted:**
| Field | Reliability | Notes |
|-------|-------------|-------|
| `full_name` | HIGH | Multiple fallback selectors |
| `linkedin_url` | HIGH | Direct from href |
| `current_title` | MEDIUM | Parsed from "Title at Company" - can fail |
| `current_company` | MEDIUM | Same parsing issue |
| `headline` | MEDIUM | Raw text capture |
| `profile_image_url` | LOW | URLs expire |
| `connected_date` | MEDIUM | Text parsing varies |

**Parsing Issues:**
```python
# Current parser (brittle):
if ' at ' in occupation:
    parts = occupation.split(' at ', 1)  # Fails for "Sales at Scale at Meta"
if ' | ' in occupation:
    parts = occupation.split(' | ', 1)   # Alternative format
```

**Risks:**
- LinkedIn DOM changes break extraction
- Session invalidation from detection
- Rate limiting if aggressive

---

### 1.2 People Data Labs (PDL)
**File:** `app/services/external_search/pdl_client.py`

| Attribute | Value |
|-----------|-------|
| API | `https://api.peopledatalabs.com/v5` |
| Cost | ~$0.10 per enrichment |
| Daily Budget | $50 (configurable) |
| Database Size | 1.5B+ profiles |
| Reliability | **HIGH** for structured data |

**Endpoints:**
- `person/search` - SQL-like queries
- `person/enrich` - Lookup by LinkedIn URL

**Fields Returned:**
| Field | Reliability | Notes |
|-------|-------------|-------|
| `full_name` | VERY HIGH | Core identifier |
| `first_name/last_name` | VERY HIGH | Structured |
| `current_company` | MEDIUM-HIGH | May lag weeks behind reality |
| `current_title` | MEDIUM-HIGH | Same staleness issue |
| `experience[]` | VERY HIGH | Detailed with dates |
| `education[]` | VERY HIGH | Complete records |
| `skills[]` | MEDIUM | Top 20 only |
| `linkedin_url` | VERY HIGH | Direct from index |
| `github_url` | HIGH | When available |
| `match_score` | N/A | PDL does not return scores — returns `None`, must compute externally (see Part 9) |

**Best Use:** Enriching LinkedIn-extracted candidates with work history, education, skills.

---

### 1.3 Clado.ai
**File:** `app/services/external_search/clado_client.py`
**Status:** ✅ WORKING (Fixed 2026-02-20)

| Attribute | Value |
|-----------|-------|
| API | `https://search.clado.ai/api` |
| Cost | $0.01-0.02 per profile enrichment |
| Database Size | 800M+ LinkedIn profiles |
| Reliability | **MEDIUM-HIGH** (after fixes) |

**Endpoints (CORRECT):**
- `/api/enrich/linkedin` - Cached profile enrichment ($0.01)
- `/api/enrich/scrape` - Real-time scrape ($0.02)
- `/api/search/deep_research` - People search (async job-based)

**Fields Returned:**
| Field | Reliability | Notes |
|-------|-------------|-------|
| `full_name` | HIGH | From `firstName` + `lastName` |
| `linkedin_url` | HIGH | Direct |
| `experience[]` | HIGH | Full with dates (year/month) |
| `education[]` | HIGH | Full with dates |
| `skills[]` | HIGH | Array of skill names |
| `location` | HIGH | From `geo.full` |
| `headline` | HIGH | Direct |
| `certifications[]` | MEDIUM | When available |
| `github_url` | ❌ | Not available - use PDL |

**Search:**
- Regular search (`/api/search`) returns 0 results - deprecated/broken
- **Use Deep Research API** (`/api/search/deep_research`) - async job-based, 30-60 seconds
- Rate limit: 5 requests/minute

**Data Completeness (tested 2026-02-20):**
- Cached profile: 85% completeness
- Real-time scrape: 90% completeness

**Best Use:** Primary enrichment source (10x cheaper than PDL). Fall back to PDL for GitHub URLs or when Clado returns 404.

---

### 1.4 GitHub API
**File:** `app/sources/github.py`

| Attribute | Value |
|-----------|-------|
| API | GraphQL + REST |
| Cost | Free |
| Rate Limits | 60 requests/hour (unauthenticated), 5000/hour (authenticated) |
| Reliability | **HIGH** |

**Fields Returned:**
| Field | Reliability | Notes |
|-------|-------------|-------|
| `login` | VERY HIGH | GitHub username |
| `name` | HIGH | Display name |
| `location` | MEDIUM | User-entered, may be stale |
| `repos[]` | VERY HIGH | Name, description, language, stars, forks |
| `contribution_stats` | VERY HIGH | Commits, PRs, issues (90 days) |
| `total_contributions` | VERY HIGH | 1-year total |

**Best Use:** Validating technical skills via actual code/contributions. Cross-reference with PDL's `github_url`.

---

### 1.5 Perplexity Research
**File:** `app/services/research/perplexity_researcher.py`

| Attribute | Value |
|-----------|-------|
| API | `https://api.perplexity.ai/chat/completions` |
| Model | `sonar` (online search) |
| Cost | Per-token |
| Reliability | **VARIABLE** |

**What It Does:**
- Deep research on top 5 candidates
- Online search for verification
- Returns raw research + confidence score

**Returns:**
```json
{
  "raw_research": "Research findings...",
  "sources_checked": ["GitHub", "LinkedIn", "Publications"],
  "confidence": "high|medium"
}
```

**Issues:**
- Results not structured/parseable
- No guarantee findings match the actual person
- Expensive for bulk use

**Status: DEPRECATED — Do not use in scoring pipeline.**

The identity problem is fundamental: for common names, Perplexity returns research about the wrong person, which actively poisons scores with incorrect data. The `curation_engine.py` integration also has a `NameError` bug (`final_top_5`) that means results were never written back — so this was already dead code in production. See Part 9.3b for full rationale.

**Future consideration:** Could be reintroduced if we add programmatic identity verification (cross-check returned company/title/GitHub against PDL data). Not worth the effort now — PDL + GitHub already provide the verification signals we need.

---

## Part 2: Secondary Sources (Niche)

### 2.1 Devpost (Hackathons)
**File:** `app/sources/devpost.py`

| Attribute | Value |
|-----------|-------|
| Method | Web scraping (BeautifulSoup) |
| Cost | Free |
| Reliability | **LOW** - scraping is brittle |

**Returns:** Hackathon projects, participants, prizes won

**Risk:** HTML structure changes break extraction.

---

### 2.2 Stack Overflow
**File:** `app/sources/stackoverflow.py`

| Attribute | Value |
|-----------|-------|
| API | StackExchange API 2.3 |
| Cost | Free |
| Reliability | **MEDIUM** |

**Returns:** Top answerers by tag, reputation scores

**Best Use:** Validating expertise in specific technologies.

---

### 2.3 Codeforces
**File:** `app/sources/codeforces.py`

| Attribute | Value |
|-----------|-------|
| API | `https://codeforces.com/api` |
| Cost | Free |
| Reliability | **HIGH** |

**Returns:** Competitive programming ratings, ranks

**Rating Tiers:**
- Grandmaster: 2600+
- Master: 2200-2399
- Candidate Master: 1900-2199
- Expert: 1600-1899

**Best Use:** Validating algorithmic skills for ML/systems roles.

---

### 2.4 Hacker News
**File:** `app/sources/hackernews.py`

| Attribute | Value |
|-----------|-------|
| API | Algolia HN Search |
| Cost | Free |
| Reliability | **LOW** |

**Returns:** "Who wants to be hired" posts with extracted email/GitHub

**Issues:** Regex extraction is fragile, data is self-reported.

---

### 2.5 ProductHunt
**File:** `app/sources/producthunt.py`

| Attribute | Value |
|-----------|-------|
| API | GraphQL |
| Cost | API key required |
| Reliability | **MEDIUM** |

**Returns:** Product makers, products launched, vote counts

**Best Use:** Finding product-focused candidates.

---

## Part 3: Database Schema

### 3.1 People Table
```sql
CREATE TABLE people (
    id UUID PRIMARY KEY,
    company_id UUID,

    -- Identity (dedupe keys)
    email TEXT,
    linkedin_url TEXT,        -- Primary dedupe key
    github_url TEXT,

    -- Basic info
    full_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    headline TEXT,
    location TEXT,

    -- Current position
    current_company TEXT,
    current_title TEXT,

    -- Scoring
    trust_score FLOAT DEFAULT 0.5,
    relevance_score FLOAT,

    -- Source flags (UNRELIABLE - never validated)
    is_from_network BOOLEAN DEFAULT FALSE,
    is_from_existing_db BOOLEAN DEFAULT FALSE,
    is_from_people_search BOOLEAN DEFAULT FALSE,

    -- Timestamps
    first_seen TIMESTAMPTZ,
    last_enriched TIMESTAMPTZ
);
```

**Validation Issues:**
- `is_from_network` flag is set but never verified
- `trust_score` has no clear calculation
- No constraint on `linkedin_url` format

---

### 3.2 Person Enrichments Table
```sql
CREATE TABLE person_enrichments (
    id UUID PRIMARY KEY,
    person_id UUID NOT NULL,

    -- Structured data
    skills JSONB DEFAULT '[]',
    experience JSONB DEFAULT '[]',
    education JSONB DEFAULT '[]',
    projects JSONB DEFAULT '[]',
    signals JSONB DEFAULT '[]',

    -- Source tracking
    raw_enrichment JSONB,
    enrichment_source TEXT,  -- 'pdl', 'clado', 'manual'

    -- Timestamps
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

**Staleness:** Check `updated_at` - PDL data can be weeks old.

---

## Part 4: Reliability Matrix

### By Field

| Field | Best Source | Reliability | Cost | Notes |
|-------|-------------|-------------|------|-------|
| `linkedin_url` | LinkedIn Extraction | HIGH | Free | Source of truth |
| `full_name` | LinkedIn Extraction or PDL | HIGH | Free/$0.10 | Cross-verify |
| `current_company` | PDL | MEDIUM-HIGH | $0.10 | May lag reality |
| `current_title` | PDL | MEDIUM-HIGH | $0.10 | May lag reality |
| `experience[]` | PDL | VERY HIGH | $0.10 | Best source for history |
| `education[]` | PDL | VERY HIGH | $0.10 | Best source |
| `skills[]` | PDL + GitHub | MEDIUM-HIGH | $0.10 + Free | Verify via repos |
| `github_url` | PDL | HIGH | $0.10 | Then use GitHub API |
| `github_repos` | GitHub API | VERY HIGH | Free | Direct from source |
| `contribution_stats` | GitHub API | VERY HIGH | Free | Direct from source |
| `match_score` | NONE | N/A | N/A | Compute yourself |
| `is_from_network` | NONE | N/A | N/A | Never validated |

### By Use Case

| Use Case | Recommended Sources | Cost/Candidate |
|----------|---------------------|----------------|
| Identity verification | LinkedIn + PDL | $0.10 |
| Work history | PDL | $0.10 |
| Education verification | PDL | $0.10 |
| Technical skill validation | PDL → GitHub API | $0.10 |
| Competitive programming | Codeforces | Free |
| Product builder signal | ProductHunt | Free |
| ~~Deep research (top candidates)~~ | ~~Perplexity~~ | ~~$0.05-0.10~~ | **DEPRECATED** — identity mismatch problem |

---

## Part 5: What We Cannot Reliably Get

| Data Point | Why Unavailable |
|------------|-----------------|
| Active job seeker status | No reliable source - self-reported only |
| Salary expectations | No source |
| Contact email | Clado has endpoint but reliability unknown |
| Whether person is actually in founder's network | `is_from_network` flag never validated |
| Real-time job changes | All sources lag by days/weeks |
| Warm path validity | Based on stale company data |

---

## Part 6: Recommended Validation Pipeline

### Proposed Flow (Economics-Gated)

```
LinkedIn Extraction / Clado Discovery (Source of Truth)
         │
         ├─ linkedin_url ✓
         ├─ full_name ✓
         ├─ headline (raw text)
         │
         ▼
    Cheap Score (FREE — headline only)             ← NEW: eliminates ~50%
         │
         ├─ cheap_score >= 20? → Continue
         └─ cheap_score < 20?  → SKIP (save $0.10)
         │
         ▼
    Network Warmth Lookup (FREE)
         │
         ├─ Rank by cheap_score + warmth
         └─ Take top N (budget-gated)              ← NEW: unit economics gate
         │
         ▼
    PDL Enrichment ($0.10 each — only top N)
         │
         ├─ experience[] ← Work history with dates
         ├─ education[] ← Degrees, schools
         ├─ skills[] ← Top 20
         └─ github_url ← For technical validation
         │
         ▼
    GitHub Enrichment (Free, if github_url exists)
         │
         ├─ repos[] ← Actual projects
         ├─ languages ← Real tech stack
         └─ contribution_stats ← Activity level
         │
         ▼
    Full Score (Internal — all 4 components)
         │
         ├─ skills_fit ← PDL skills + GitHub repos
         ├─ experience_fit ← PDL experience + tenure
         ├─ warmth ← Network graph
         └─ timing ← ReadinessScorer signals
         │
         ▼
    Return top 20 ranked by MatchScore
```

### Cost Estimate Per Search (not per candidate)

| Stage | Candidates | Cost Each | Total |
|-------|-----------|-----------|-------|
| LinkedIn/Clado Discovery | 300 | $0 | $0 |
| Cheap Score Filter | 300 → 140 | $0 | $0 |
| PDL Enrichment (budget-gated) | top 100 | $0.10 | $10.00 |
| GitHub Enrichment | ~30 (have URL) | $0 | $0 |
| ~~Perplexity~~ | ~~5~~ | ~~$0.07~~ | ~~$0.35~~ | **CUT** — identity mismatch |
| **Total per search** | | | **~$10.00** |
| **Effective cost per ranked candidate** | top 20 returned | | **~$0.50** |

See Part 9 for the full enrichment funnel design and unit economics.

---

## Part 7: Known Bugs to Fix

| Bug | Location | Impact | Status |
|-----|----------|--------|--------|
| `match_score` hardcoded 0.8 | `pdl_client.py:258` | Fake relevance scores | ✅ FIXED - Now returns `None` |
| `personal_website` contains email | `pdl_client.py:257` | Wrong data | ✅ FIXED - Maps to `websites` field |
| Silent enrichment failures | `network_index.py:182-198` | Missing warm paths | ✅ FIXED - Proper logging + success flag |
| Naive company matching | `warm_path_finder.py:231-237` | False warm paths | ✅ FIXED - Added 70+ company aliases |
| Unvalidated `is_from_network` | `company_db.py` | Trust issues | 🔴 TODO - Add verification step |
| `final_top_5` NameError | `curation_engine.py:169` | Perplexity results fetched but never written back — Stage 5 is dead code | 🔴 TODO - Change to `final_top_research` |
| 3 overlapping scoring systems | See Part 9.1 | Inconsistent candidate rankings across pipelines | 🔴 TODO - Unify into `CandidateScorer` |

---

## Part 8: API Configuration Required

### Required API Keys
```bash
# Core (must have)
SUPABASE_URL=
SUPABASE_KEY=
PDL_API_KEY=           # For enrichment ($0.10/call)
GITHUB_TOKEN=          # For repo analysis

# Recommended
OPENAI_API_KEY=        # For embeddings
PERPLEXITY_API_KEY=    # For deep research

# Optional
CLADO_API_KEY=         # Cheaper but less reliable
PEARCH_API_KEY=        # Alternative to Clado
PINECONE_API_KEY=      # Vector search
```

### Budget Settings
```python
pdl_daily_budget_usd = 50.0  # ~500 enrichments/day
linkedin_daily_message_limit = 50
linkedin_daily_enrichment_limit = 100
```

---

## Part 9: Unified Match Scoring System (PROPOSAL)

**Status:** Proposed — replaces all existing scoring systems
**Goal:** Single source of truth for "how good is this candidate for this role?"

### 9.1 Problem: Three Overlapping Scoring Systems

The codebase currently has **three independent scoring pipelines** that evolved separately and produce inconsistent results:

| System | File | Output | Scale | Used By |
|--------|------|--------|-------|---------|
| **Legacy Core** | `core/evaluation_engine.py` | `relevance_score` | 0.0–1.0 | `core/search_engine.py` |
| **Network Ranker** | `search/scoring/ranker.py` | `final_score` | 0.0–1.0 | Network search pipeline |
| **Curation Engine** | `services/curation_engine.py` | `match_score` | 0–100 | Unified search, briefs |

Each uses different weights, different inputs, and different scales. A candidate can rank #1 in one system and #15 in another.

**Additional scorers that feed into these:**
- `PathwayScorer` (`search/scoring/pathway.py`) — scores network nodes, not candidates
- `ReadinessScorer` (`intelligence/timing/readiness_scorer.py`) — timing signals
- `ClaudeReasoningEngine` (`services/reasoning/claude_engine.py`) — LLM-based 4-agent scoring
- `RewardModel` (`services/rl/reward_model.py`) — GRPO learnable weights
- `UnifiedSearchEngine._calculate_fit` (`services/unified_search.py`) — keyword matching

### 9.2 The Enrichment Economics Problem

The scoring system above requires PDL enrichment ($0.10), GitHub data, and network analysis per candidate. But we can't afford to enrich everyone:

| Scenario | Candidates Found | Enrich All | Realistic Budget |
|----------|-----------------|------------|-----------------|
| Single role search | 200–500 | $20–50 | $5–10 |
| Batch search (5 roles) | 1,000–2,500 | $100–250 | $25–50 |
| Full network index | 5,000+ | $500+ | $50/day cap |

**The fix:** Score what you can for free first, then only spend money on candidates who pass a cheap filter.

### 9.3 Enrichment Funnel: Score Cheap, Enrich Smart

```
STAGE 0: Raw Candidates (FREE)
  Data: linkedin_url, full_name, headline (from LinkedIn extraction or Clado)
  Action: Compute "cheap score" from headline alone
  Filter: Drop candidates with cheap_score < 20
  Survival rate: ~40–60%
         │
         ▼
STAGE 1: Headline-Scored Pool (FREE)
  Data: Same as above + network graph lookup
  Action: Add warmth score (is this person in our network?)
  Filter: Rank by cheap_score + warmth, take top N
  N = min(budget / $0.10, 100)  ← unit economics gate
  Survival rate: top 50–100 candidates
         │
         ▼
STAGE 2: PDL Enrichment ($0.10 each)
  Data: Full experience[], education[], skills[], github_url
  Action: Compute full skills_fit + experience_fit scores
  Filter: Drop candidates with full_score < 40
  Survival rate: ~50–70% of enriched
         │
         ▼
STAGE 3: GitHub Enrichment (FREE, where github_url exists)
  Data: repos[], languages, contribution_stats
  Action: Validate technical skills, boost/penalize skills_fit
  Filter: None — just improves confidence
  Survival rate: 100% (additive data)
         │
         ▼
STAGE 4: Full Ranking (see 9.4a below)
  Data: All of the above — PDL skills/experience, GitHub repos, network graph, timing signals
  Action: Dedup across sources → compute all 4 MatchScore components → weighted total
  Sort: By total score descending
  Output: Top 20 candidates with full MatchScore objects, ready for brief

~~STAGE 5: Perplexity Deep Research Loop~~ — CUT (see 9.3b for rationale)
```

#### 9.3a Stage 4 Expanded: Full Ranking

At this point we have enriched candidates with PDL data, GitHub data (where available), network graph lookups, and timing signals. Now we compute the final composite score.

**What happens per candidate:**

```
For each enriched candidate:
    │
    ├─ 1. Compute skills_fit (0–100)
    │     Input: PDL skills[] + experience[].title + GitHub repos[].language
    │     Method: keyword overlap + skills intersection + GitHub language validation
    │     (see 9.7 for full formula)
    │
    ├─ 2. Compute experience_fit (0–100)
    │     Input: PDL experience[] (company, title, dates)
    │     Method: seniority match + tenure depth + company signal
    │     (see 9.8 for full formula)
    │
    ├─ 3. Compute warmth (0–100)
    │     Input: network_index + warm_path_finder results
    │     Method: connection degree lookup (1st=100, 2nd=50-70, cold=0)
    │     (see 9.9 for full formula)
    │
    ├─ 4. Compute timing (0–100)
    │     Input: ReadinessScorer (tenure cliff, layoff signals, profile activity)
    │     Method: additive signal scores
    │     (see 9.10 for full formula)
    │
    ├─ 5. Compute confidence (0.0–1.0)
    │     Input: Which data sources contributed
    │     Method: additive per-source (see 9.11)
    │
    └─ 6. Weighted total
          total = skills_fit*0.35 + experience_fit*0.30 + warmth*0.20 + timing*0.15
```

**Deduplication (runs before scoring):**

A candidate can appear from multiple sources (Clado + PDL + LinkedIn extraction + network graph). Merge before scoring:

```
Dedup key priority:
  1. linkedin_url  → highest confidence (same person)
  2. email         → high confidence
  3. github_url    → high confidence
  4. name + school → fuzzy fallback (same name + same alma mater)

When merging duplicates:
  - Keep richest data (PDL experience > Clado experience)
  - Union skills from all sources
  - Use max(warmth) across sources
  - Track all contributing sources in data_sources[]
```

**Final sort and cut:**

```python
scored = [scorer.score_full(c, job_requirements, network_ctx) for c in enriched]
scored.sort(key=lambda s: s.total, reverse=True)

# Top 20 go to the brief, rest are stored for future searches
final = scored[:20]
```

Why top 20: presenting 50 candidates dilutes quality. The founder needs a shortlist, not a firehose. Remaining candidates stay scored in the database — if a new search has overlapping requirements, they can be re-ranked without re-enriching.

#### 9.3b Stage 5: Perplexity Deep Research — CUT

**Status: Removed from pipeline. Do not implement.**

**Why it's cut:**

1. **Identity mismatch is unfixable at the prompt level.** Perplexity searches the open web for a name and tries to synthesize findings. For common names ("David Chen", "Sarah Kim"), it frequently returns research about the wrong person. The prompt says "use the LinkedIn URL to verify," but Perplexity has no way to reliably anchor to a specific person — it's a search engine, not an identity resolver.

2. **Wrong-person data is worse than no data.** If Perplexity returns GitHub repos belonging to a different David Chen, those repos get parsed into `technical_skills` and boost `skills_fit` — for the wrong person. This actively poisons the score. No data is better than wrong data.

3. **It was already dead code.** The `curation_engine.py` integration has a `NameError` bug on line 169 (`final_top_5` instead of `final_top_research`), so Perplexity results were fetched but never written back to candidates. Nothing in production actually uses these results.

4. **PDL + GitHub already cover the verification need.** PDL provides structured experience/education/skills with high reliability. GitHub API provides verified repos and contribution stats. These are deterministic, identity-anchored sources — no guessing required.

**What to do with existing code:**

- `app/services/research/perplexity_researcher.py` — keep the file but do not call from any pipeline
- `curation_engine.py` step 7 (Perplexity block) — remove or gate behind a feature flag (default off)
- `PERPLEXITY_API_KEY` — move to optional, not recommended

**Future replacement: Verified data provider (Stage 5 slot)**

The Stage 5 slot in the pipeline is reserved for a future verified data provider — something that returns structured, identity-anchored data rather than web-scraped guesses. Requirements for any replacement:

- **Identity-anchored:** Data is tied to a specific person via deterministic key (LinkedIn URL, email), not name matching
- **Structured output:** Returns fields we can programmatically score, not raw text to parse
- **Verifiable:** We can cross-check against PDL data to confirm identity
- **Cost-effective:** Must justify itself relative to what PDL + GitHub already give us for free/$0.10

Perplexity could be re-introduced only with programmatic identity verification layered on top, but a purpose-built verified data API is the better path.

### 9.4 Stage 0: The Cheap Score (FREE — No API Calls)

This is the key insight. **LinkedIn headlines and Clado results already contain enough signal to eliminate 40–60% of candidates before spending a dime.**

```python
def cheap_score(headline: str, job_requirements: JobRequirements) -> float:
    """Score 0–100 using only the headline string. No API calls."""
    score = 0.0

    headline_lower = headline.lower() if headline else ""

    # Title keyword match (0–50)
    title_words = job_requirements.title.lower().split()
    for word in title_words:
        if len(word) > 3 and word in headline_lower:
            score += 15  # Strong signal
    score = min(score, 50)

    # Skill keyword match (0–30)
    for skill in job_requirements.required_skills:
        if skill.lower() in headline_lower:
            score += 10
    score = min(score, 80)  # Cap keyword portion

    # Seniority match (0–20)
    if job_requirements.seniority:
        seniority_map = {
            "junior": ["junior", "jr", "associate", "entry"],
            "mid": ["mid", "intermediate"],
            "senior": ["senior", "sr", "lead"],
            "staff": ["staff", "principal", "distinguished"],
        }
        target_keywords = seniority_map.get(job_requirements.seniority, [])
        if any(kw in headline_lower for kw in target_keywords):
            score += 20
        # Penalty: looking for senior but headline says junior
        wrong_level = {"senior": ["junior", "intern"], "staff": ["junior", "entry"]}
        if any(kw in headline_lower for kw in wrong_level.get(job_requirements.seniority, [])):
            score -= 20

    return max(score, 0)
```

**Examples:**

| Headline | Job: "Senior Backend Engineer" (python, aws) | Cheap Score |
|----------|----------------------------------------------|-------------|
| "Senior Software Engineer at Stripe" | "senior" +20, "engineer" +15 | 35 |
| "Backend Developer - Python, AWS, K8s" | "backend" +15, "python" +10, "aws" +10 | 35 |
| "UX Designer at Google" | No matches | 0 |
| "Junior Frontend Intern" | "junior" penalty -20 | 0 |
| "Staff Engineer, Infrastructure" | "staff" +20, "engineer" +15 | 35 |
| "Marketing Manager at Meta" | No matches | 0 |

With a threshold of 20, this eliminates completely irrelevant candidates (designers, marketers, wrong seniority) for free.

### 9.5 Budget Gate: How Many to Enrich

```python
def calculate_enrichment_budget(
    candidates_after_cheap_filter: int,
    daily_budget_usd: float = 50.0,
    cost_per_enrichment: float = 0.10,
    active_searches: int = 1,
) -> int:
    """How many candidates can we afford to enrich for this search?"""

    budget_per_search = daily_budget_usd / active_searches
    max_from_budget = int(budget_per_search / cost_per_enrichment)

    # Never enrich more than 100 per search (diminishing returns)
    # Never enrich fewer than 20 (need enough for ranking)
    return max(20, min(max_from_budget, 100, candidates_after_cheap_filter))
```

| Daily Budget | Active Searches | Per-Search Budget | Enrichments |
|-------------|-----------------|-------------------|-------------|
| $50 | 1 | $50 | 100 (capped) |
| $50 | 3 | $16.67 | 100 (capped) |
| $50 | 10 | $5 | 50 |
| $10 | 5 | $2 | 20 (floor) |

**Decision logic for who gets enriched:**

```python
# After cheap scoring + warmth lookup
candidates.sort(key=lambda c: (c.cheap_score + c.warmth * 0.5), reverse=True)
to_enrich = candidates[:calculate_enrichment_budget(len(candidates))]
```

Priority order:
1. **High cheap_score + warm** — best ROI, likely fits AND we have an intro
2. **High cheap_score + cold** — likely fits, worth the $0.10 to confirm
3. **Low cheap_score + warm** — network connection but unclear fit, enrich to check
4. **Low cheap_score + cold** — skip entirely

### 9.6 Proposed: Single `CandidateScorer` Service

Replace all three systems with one scorer that operates at **two tiers**:

**File:** `app/services/scoring/candidate_scorer.py` (new)

#### Output Model

```python
class MatchScore(BaseModel):
    """Single canonical score for a candidate-role pair."""

    # Final composite (0–100)
    total: float                    # Weighted combination of all components

    # Component scores (each 0–100)
    skills_fit: float               # How well skills match requirements
    experience_fit: float           # Relevant experience depth
    warmth: float                   # Network proximity (0 = cold, 100 = direct connection)
    timing: float                   # Likelihood of being open to move

    # Confidence in the score itself (0.0–1.0)
    confidence: float               # Based on data completeness
    data_sources: list[str]         # Which sources contributed (e.g. ["pdl", "github", "linkedin"])

    # Breakdown for UI transparency
    reasoning: str                  # Human-readable explanation
```

#### Weighting

```python
WEIGHTS = {
    "skills_fit":     0.35,   # Most important — does the person have the skills?
    "experience_fit": 0.30,   # Relevant tenure, companies, seniority
    "warmth":         0.20,   # Network advantage — warm intro vs cold outreach
    "timing":         0.15,   # Are they likely open to a move?
}

total = sum(component * weight for component, weight in zip(scores, WEIGHTS.values()))
```

**Why these weights:**
- Skills + experience (65%) dominate because they're the strongest predictors of role fit
- Warmth (20%) is a real advantage but shouldn't override a bad fit
- Timing (15%) is a bonus signal — a great candidate with bad timing is still worth tracking

### 9.7 Component: `skills_fit` (0–100)

**Inputs:** Job requirements (skills, title keywords) + candidate data (PDL skills, GitHub repos, experience titles)

```
Score = keyword_match + skills_overlap + github_validation

keyword_match (0–40):
  - Each required keyword found in title/headline: +10 (max 4 matches)

skills_overlap (0–40):
  - required_skills ∩ candidate_skills / required_skills
  - Scaled to 0–40

github_validation (0–20):
  - Required language found in repos: +10
  - Active contributions (>50 in last year): +5
  - Stars on relevant repos: +5
  - (Only if github_url exists — otherwise this component is 0 and confidence is reduced)
```

**Data sources:** PDL `skills[]`, PDL `experience[].title`, GitHub `repos[].language`, GitHub `contribution_stats`

### 9.8 Component: `experience_fit` (0–100)

**Inputs:** Job requirements (seniority, years, target companies) + candidate data (PDL experience)

```
Score = seniority_match + tenure_depth + company_signal

seniority_match (0–40):
  - Title contains required seniority level (senior, staff, lead, etc.): 40
  - One level below: 25
  - Two+ levels below: 10
  - No title data: 0 (reduces confidence)

tenure_depth (0–30):
  - Years of relevant experience (sum of experience[].duration where title matches):
    - 0–1 years: 5
    - 1–3 years: 15
    - 3–5 years: 25
    - 5+ years: 30

company_signal (0–30):
  - Worked at a target-tier company (configurable list): +15
  - Worked at a company in same industry: +10
  - Company has >1000 employees (PDL company_size): +5
```

**Data sources:** PDL `experience[]` (company, title, dates), PDL `industry`

### 9.9 Component: `warmth` (0–100)

**Inputs:** Network graph data, connection extraction results

```
Score based on relationship to founder's network:

Direct connection (1st degree):                    100
  - Connected on LinkedIn, extraction confirmed

2nd degree via strong connector:                    70
  - Shares a company with a 1st-degree connection
  - Connector has been at company >1 year

2nd degree via weak connector:                      50
  - Connector was at same company but different time
  - Or connector has tenuous link

3rd degree / inferred:                              25
  - Same alumni network, same company but no direct link

Cold (no network path found):                        0
```

**Data sources:** LinkedIn connection extraction, `network_index`, `warm_path_finder` (with entity resolution)

### 9.10 Component: `timing` (0–100)

**Inputs:** Profile signals, company news, tenure data

Reuses `ReadinessScorer` logic but normalizes to 0–100 scale:

```
Score = tenure_signal + company_signal + profile_signal + activity_signal

tenure_signal (0–30):
  - Approaching 4-year vesting cliff: 30
  - Past cliff (4+ years): 20
  - Recent start (<1 year): 5
  - Mid-tenure (1–3 years): 10

company_signal (0–30):
  - Company in LAYOFF_COMPANIES list: 25–30
  - Company recently downsized (news signal, future data provider): 20
  - Stable company: 5

profile_signal (0–20):
  - "Open to Work" badge: 20
  - Headline contains "seeking", "available", "ex-": 15
  - "Consultant" or "Freelance" (recent transition): 10

activity_signal (0–20):
  - Profile updated in last 2 weeks: 20
  - Profile updated in last month: 10
  - No recent activity: 0
```

**Data sources:** `ReadinessScorer`, PDL `experience[0].start_date`

### 9.11 Confidence Score (0.0–1.0)

The confidence score reflects **how much data we have**, not how good the candidate is.

```python
def calculate_confidence(data_sources: list[str], candidate) -> float:
    confidence = 0.0

    # Base identity (required)
    if candidate.linkedin_url:
        confidence += 0.25

    # Enrichment data
    if "pdl" in data_sources:
        confidence += 0.35
        if len(candidate.experience) >= 2:
            confidence += 0.10  # Enough history to assess
    if "clado" in data_sources and "pdl" not in data_sources:
        confidence += 0.15      # Less reliable than PDL

    # Technical validation
    if "github" in data_sources:
        confidence += 0.20

    # Network data
    if candidate.warmth > 0:
        confidence += 0.10      # We know the network path

    return min(confidence, 1.0)
```

**Max confidence by data combination:**

| Sources Available | Max Confidence | Enough to present? |
|-------------------|---------------|-------------------|
| LinkedIn + PDL (2+ exp) + GitHub + warm | 1.0 | Yes |
| LinkedIn + PDL (2+ exp) + GitHub | 0.90 | Yes |
| LinkedIn + PDL (2+ exp) | 0.70 | Yes, with caveats |
| LinkedIn + PDL (thin profile) | 0.60 | Yes, with caveats |
| LinkedIn + Clado only | 0.40 | Needs PDL enrichment |
| LinkedIn only (headline) | 0.25 | Cheap score only |

| Confidence | Meaning | Action |
|------------|---------|--------|
| 0.8–1.0 | High — multiple sources verified | Ready for brief |
| 0.5–0.79 | Medium — core data present, gaps exist | Include with caveats |
| 0.3–0.49 | Low — minimal data, scores unreliable | Enrich before presenting |
| < 0.3 | Very Low — identity only | Do not present, queue for enrichment |

### 9.12 Migration Plan: Deprecating Old Scorers

| Old System | What Happens | Timeline |
|------------|-------------|----------|
| `evaluation_engine._compute_relevance` | **Remove** — internal-only, never shown | Phase 1 |
| `ranker.CandidateRanker` | **Absorb** — network proximity logic moves to `warmth` component | Phase 1 |
| `unified_search._calculate_fit` | **Replace** — simple keyword match → `skills_fit` component | Phase 1 |
| `unified_search._add_timing_signals` | **Replace** — fixed bonuses → `timing` component | Phase 1 |
| `curation_engine._calculate_fit` | **Replace** — rule-based → `skills_fit` + `experience_fit` | Phase 2 |
| `curation_engine` Claude agent swarm | **Keep as optional layer** — for top-N re-ranking only | Phase 2 |
| `perplexity_researcher` | **Cut** — identity mismatch problem, wrong-person data poisons scores | Now |
| `curation_engine` step 7 (Perplexity block) | **Remove** — also has `final_top_5` NameError, was dead code | Now |
| `ReadinessScorer` | **Keep** — feeds into `timing` component | Keep |
| `RewardModel` (GRPO) | **Keep** — learns weight adjustments from outcomes | Phase 3 |
| `PathwayScorer` | **Keep** — scores network nodes, not candidates (different purpose) | Keep |

### 9.13 Implementation: Where It Lives

```
app/services/scoring/
├── __init__.py              # Exports CandidateScorer, MatchScore, CheapScore
├── candidate_scorer.py      # Main orchestrator (both tiers)
├── cheap_scorer.py          # Stage 0: headline-only scoring (FREE)
├── enrichment_gate.py       # Budget calculation + enrichment priority ranking
├── components/
│   ├── skills.py            # skills_fit calculation (needs PDL/GitHub)
│   ├── experience.py        # experience_fit calculation (needs PDL)
│   ├── warmth.py            # warmth calculation (needs network graph)
│   └── timing.py            # timing calculation (wraps ReadinessScorer)
└── confidence.py            # Data completeness assessment
```

**Interface:**

```python
class CandidateScorer:
    def score_cheap(
        self,
        headline: str,
        job_requirements: JobRequirements,
    ) -> float:
        """Stage 0: Score 0–100 from headline alone. No API calls, no cost."""

    def select_for_enrichment(
        self,
        candidates: list[CheapScoredCandidate],
        daily_budget_usd: float = 50.0,
        active_searches: int = 1,
    ) -> list[CheapScoredCandidate]:
        """Stage 1: Pick which candidates are worth the $0.10 PDL call.
        Returns candidates sorted by enrichment priority."""

    async def score_full(
        self,
        candidate: PDLProfile | UnifiedCandidate,
        job_requirements: JobRequirements,
        network_context: Optional[NetworkContext] = None,
    ) -> MatchScore:
        """Stage 2+: Full score using all enriched data."""

    async def score_batch(
        self,
        candidates: list,
        job_requirements: JobRequirements,
        network_context: Optional[NetworkContext] = None,
    ) -> list[MatchScore]:
        """Full pipeline: cheap filter → enrich → full score → rank.
        Returns sorted by total descending."""
```

**`JobRequirements` model (input):**

```python
class JobRequirements(BaseModel):
    title: str                          # e.g. "Senior Backend Engineer"
    required_skills: list[str] = []     # e.g. ["python", "postgresql", "aws"]
    preferred_skills: list[str] = []    # e.g. ["kubernetes", "terraform"]
    min_years_experience: int = 0
    seniority: Optional[str] = None     # "junior", "mid", "senior", "staff", "principal"
    target_companies: list[str] = []    # Companies considered impressive for this role
    industry: Optional[str] = None
    location: Optional[str] = None
```

### 9.14 End-to-End Example

**Search:** "Senior Backend Engineer" — python, postgresql, aws

```
Stage 0: 300 candidates from Clado + LinkedIn extraction
  → cheap_score filter (threshold 20)
  → 140 survive (47%)                                    Cost: $0

Stage 1: 140 candidates ranked by cheap_score + warmth
  → Budget: $50/day, 2 active searches = $25 budget
  → Enrich top 100                                       Cost: $10.00

Stage 2: 100 candidates with full PDL data
  → full_score filter (threshold 40)
  → 68 survive (68%)                                     Cost: $0

Stage 3: 68 candidates, 31 have github_url
  → GitHub API enrichment for 31                          Cost: $0

Stage 4: 68 candidates fully scored, deduped, ranked
  → Return top 20 with full MatchScore objects             Cost: $0

TOTAL: $10.00 for 20 ranked candidates (vs $30.00 to enrich all 300)
```

**Example top result:**

```json
{
  "candidate": "Jane Smith",
  "total": 78.5,
  "skills_fit": 85,
  "experience_fit": 82,
  "warmth": 70,
  "timing": 55,
  "confidence": 0.85,
  "data_sources": ["linkedin", "pdl", "github"],
  "reasoning": "Strong skills match (Python, PostgreSQL, AWS all confirmed via PDL + GitHub repos). 6 years relevant experience at Stripe and Datadog. 2nd-degree connection via mutual at Stripe. Mid-tenure at current role (2 years) — moderate timing signal."
}
```

**Example candidate filtered at Stage 0 (saved $0.10):**

```json
{
  "candidate": "Bob Johnson",
  "headline": "Marketing Director at Acme Corp",
  "cheap_score": 0,
  "action": "SKIP — no title/skill overlap, not worth enriching"
}
```

---

## Part 10: Enrichment Provider Comparison (AUDIT)

**Last Updated:** 2026-02-20
**Goal:** Compare providers and define the optimal enrichment waterfall strategy.

### 10.1 Provider Overview

| Provider | Endpoint | Cost | Data Freshness | Database | Status |
|----------|----------|------|----------------|----------|--------|
| **Clado Get Profile** | `/api/profile` | $0.01 | Cached | 800M+ | ✅ Active |
| **Clado Scrape** | `/api/scrape` | $0.02 | Real-time | 800M+ | ✅ Active |
| **PDL** | `/person/enrich` | $0.10 | Cached | 1.5B+ | ✅ Active |
| **Netrows** | Various | €0.005 | Real-time | Unknown | ✅ New (Oct 2025) |
| **Proxycurl** | N/A | N/A | N/A | N/A | ❌ **SHUTDOWN** (LinkedIn lawsuit Jan 2025) |
| **Firecrawl** | N/A | N/A | N/A | N/A | ❌ No LinkedIn support |

### 10.2 Clado Endpoints (FIXED)

Clado has **three different enrichment endpoints**:

| Endpoint | Path | Cost | Returns | Use Case |
|----------|------|------|---------|----------|
| **Enrich LinkedIn** | `POST /api/enrich/linkedin` | 1 credit ($0.01) | Full profile from cache | Default enrichment |
| **Scrape Profile** | `POST /api/enrich/scrape` | 2 credits ($0.02) | Fresh data from LinkedIn | When cache is stale |
| **Get Contacts** | `GET /api/enrich/contacts?linkedin_url=...` | 4-14 credits | Email/phone only | Contact discovery |

**✅ FIXED (2026-02-20):** Endpoints updated to correct paths. See changelog entry #5.

**Correct endpoints for profile enrichment:**
- `/api/enrich/linkedin` - Cached profile with experience, education, skills ($0.01)
- `/api/enrich/scrape` - Real-time profile with same fields ($0.02)

### 10.3 Field Comparison by Endpoint

| Field | Clado Profile | Clado Scrape | PDL | Notes |
|-------|---------------|--------------|-----|-------|
| `full_name` | ✅ | ✅ | ✅ Structured | All good |
| `current_title` | ✅ | ✅ | ✅ | All good |
| `current_company` | ✅ | ✅ | ✅ | All good |
| `experience[]` | ✅ w/dates (YYYY-MM) | ✅ w/dates | ✅ w/dates | All have dates now |
| `education[]` | ✅ w/dates | ✅ w/dates | ✅ w/dates | All good |
| `skills[]` | ✅ | ✅ | ✅ Top 20 | All good |
| `location` | ✅ | ✅ | ✅ Structured | PDL more detailed |
| `github_url` | ❌ | ❌ | ✅ | **Only PDL** |
| `twitter_handle` | ✅ | ✅ | ✅ | All good |
| `posts[]` | ❌ | ✅ Recent posts | ❌ | Only Scrape |
| `certifications[]` | ✅ | ✅ | ❌ | Only Clado |
| `email` | ❌ (+$0.04) | ❌ (+$0.04) | ❌ (separate) | Extra cost |

### 10.4 Waterfall Enrichment Strategy (NEW)

**Problem:** PDL costs 10x more than Clado but has better coverage. How do we minimize cost while maximizing data quality?

**Solution:** Tiered waterfall with agentic reasoning.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENRICHMENT WATERFALL                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input: linkedin_url from LinkedIn extraction                   │
│                                                                 │
│  TIER 1: Clado Get Profile ($0.01)                             │
│  ├─ Try cached profile first                                   │
│  ├─ If success AND data complete → DONE                        │
│  └─ If 404 OR data incomplete → Continue                       │
│                                                                 │
│  TIER 2: Clado Scrape Profile ($0.02)                          │
│  ├─ Real-time scrape for fresh data                            │
│  ├─ If success AND data complete → DONE                        │
│  └─ If 404 OR restricted profile → Continue                    │
│                                                                 │
│  TIER 3: PDL Enrich ($0.10)                                    │
│  ├─ Largest database (1.5B profiles)                           │
│  ├─ Returns github_url (unique to PDL)                         │
│  └─ If success → DONE, else → Mark as unenrichable            │
│                                                                 │
│  Cost Analysis:                                                 │
│  ├─ Best case: $0.01 (Clado cache hit)                         │
│  ├─ Medium case: $0.03 (Clado cache miss → scrape)             │
│  ├─ Worst case: $0.13 (all three providers)                    │
│  └─ Average expected: ~$0.02-0.04 per candidate                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.5 Data Completeness Check

Before moving to next tier, check if we have enough data:

```python
def is_enrichment_complete(profile: dict, need_github: bool = False) -> bool:
    """Check if profile has enough data to skip further enrichment."""

    # Must have basic identity
    if not profile.get("full_name"):
        return False

    # Must have at least 1 experience entry with dates
    experience = profile.get("experience", [])
    if len(experience) < 1:
        return False
    if not experience[0].get("start_date"):
        return False  # No dates = need PDL

    # Must have skills for matching
    if len(profile.get("skills", [])) < 3:
        return False

    # If we need GitHub URL, only PDL has it
    if need_github and not profile.get("github_url"):
        return False

    return True
```

### 10.6 Agentic Enrichment Loop (PROPOSAL)

For complex cases, use LLM reasoning to decide enrichment strategy:

```python
async def agentic_enrich(
    linkedin_url: str,
    job_requirements: JobRequirements,
    budget_remaining: float,
) -> EnrichedCandidate:
    """
    Use agentic reasoning to decide enrichment strategy.

    The agent considers:
    1. What data do we already have?
    2. What data do we need for this specific role?
    3. Is it worth spending more to get better data?
    """

    # Start with cheapest option
    profile = await clado_get_profile(linkedin_url)

    if profile is None:
        # Agent decides: try scrape or go straight to PDL?
        decision = await agent_decide(
            context=f"Clado cache miss for {linkedin_url}",
            options=["clado_scrape ($0.02)", "pdl ($0.10)"],
            budget=budget_remaining,
        )

        if decision == "clado_scrape":
            profile = await clado_scrape_profile(linkedin_url)
            if profile is None:
                profile = await pdl_enrich(linkedin_url)
        else:
            profile = await pdl_enrich(linkedin_url)

    # Agent evaluates: is this data good enough?
    if not is_enrichment_complete(profile, need_github=is_technical_role(job_requirements)):
        # Try next tier
        ...

    return profile
```

### 10.7 Cost Comparison: Old vs New Strategy

**Old Strategy (PDL for everything):**
| Candidates | Cost | Total |
|------------|------|-------|
| 100 enrichments | $0.10 each | $10.00 |

**New Waterfall Strategy:**
| Tier | Candidates | Cost | Cumulative |
|------|------------|------|------------|
| Clado Profile (80% hit rate) | 80 | $0.01 | $0.80 |
| Clado Scrape (15% need) | 15 | $0.02 | $1.10 |
| PDL fallback (5% need) | 5 | $0.10 | $1.60 |
| **Total** | 100 | | **$1.60** |

**Savings: 84% cost reduction** ($10.00 → $1.60)

### 10.8 When to Force PDL

Always use PDL (skip Clado) when:
1. **Technical roles requiring GitHub validation** - Only PDL returns `github_url`
2. **High-priority candidates** - PDL has larger database, better coverage
3. **Clado rate-limited** - Fall back to PDL during Clado outages

### 10.9 Implementation Files

| File | Purpose | Status |
|------|---------|--------|
| `app/services/external_search/clado_client.py` | Clado API client | ✅ Fixed - endpoints, parsing, Deep Research |
| `app/services/external_search/pdl_client.py` | PDL API client | ✅ Fixed - match_score, personal_website |
| `app/services/validation/enrichment_service.py` | Waterfall orchestrator | ✅ Updated - Clado→PDL fallback |
| `app/services/network_index.py` | Network graph builder | ✅ Fixed - logging, success flags |
| `app/services/warm_path_finder.py` | Connection path finder | ✅ Fixed - 70+ company aliases |
| `scripts/audit_enrichment_providers.py` | Provider comparison tool | ✅ Working - tests all endpoints |

**Key methods in `clado_client.py`:**
- `get_profile()` → `/api/enrich/linkedin` (cached, $0.01)
- `scrape_profile()` → `/api/enrich/scrape` (real-time, $0.02)
- `search()` → Deep Research API by default
- `_parse_profile_response()` → handles nested response structure
- `_parse_deep_research_result()` → handles search result structure

### 10.10 Clado Search: Use Deep Research API

#### Problem: Regular Search Returns 0 Results
The regular Clado search endpoint (`POST /api/search`) returns 0 results for all queries,
even with valid API key and request format. Tested extensively:
- Different queries: "software engineers from UCSD", "founding engineers", "backend engineers"
- Different filters: location, seniority, titles
- Verified same requests work in Clado's playground UI

This appears to be an API limitation or deprecated endpoint.

#### Solution: Deep Research API (IMPLEMENTED)
The Deep Research API (`/api/search/deep_research`) works correctly and returns rich profile data.

**How it works:**
1. POST `/api/search/deep_research` with query → Returns `job_id`
2. Poll GET `/api/search/deep_research/{job_id}` until `status: completed`
3. Parse results with nested structure: `{profile: {...}, experience: [...], education: [...]}`

**Cost:** 1 credit per result returned (~$0.01)
**Time:** 30-60 seconds typical (async job processing)
**Rate Limit:** 5 requests/minute

**Verified Test Results (2026-02-20):**
```
Query: "software engineers from UCSD"
Results: 3 profiles found
- Ishaan Gulrajani (Software Engineer at OpenAI)
- Ryan O'Shea (SWE at Palantir)
- Brian Cheung (AI Researcher)
Completeness: 75-90% (full experience, education, skills)
```

**Implementation:**
```python
# Automatic - search() uses deep research by default
result = await clado_client.search("software engineers from UCSD", limit=10)

# Explicit deep research with custom polling
result = await clado_client.search(
    query,
    use_deep_research=True,
    poll_interval=2.0,      # Check every 2 seconds
    max_poll_time=120.0,    # Wait up to 2 minutes
)

# Force regular search (not recommended - returns 0)
result = await clado_client.search(query, use_deep_research=False)
```

**Deep Research Response Structure:**
```json
{
  "status": "completed",
  "results": [
    {
      "profile": {
        "id": 123,
        "name": "Jane Doe",
        "headline": "Senior Engineer at Google",
        "linkedin_url": "linkedin.com/in/janedoe",
        "skills": ["Python", "TensorFlow", "Kubernetes"]
      },
      "experience": [
        {
          "company": "Google",
          "title": "Senior Software Engineer",
          "start": {"year": 2020, "month": 3},
          "end": null,
          "current": true
        }
      ],
      "education": [
        {
          "school": "UC San Diego",
          "degree": "BS",
          "field": "Computer Science",
          "start": {"year": 2012},
          "end": {"year": 2016}
        }
      ]
    }
  ],
  "total": 3
}
```

**Test Commands:**
```bash
# Initiate deep research
curl -X POST "https://search.clado.ai/api/search/deep_research" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "software engineers from UCSD", "limit": 5}'

# Check status (replace JOB_ID)
curl -X GET "https://search.clado.ai/api/search/deep_research/JOB_ID" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 10.10 Data Quality Audit Script

To verify data quality, run this test:

```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity
python scripts/audit_enrichment_providers.py --linkedin-url "linkedin.com/in/test-user"
```

This script will:
1. Call Clado Profile, Clado Scrape, and PDL with the same LinkedIn URL
2. Compare fields side-by-side
3. Report missing/different data
4. Calculate "data completeness" score for each

---

## Appendix: External API Reference

| API | Base URL | Auth | Docs |
|-----|----------|------|------|
| PDL | `api.peopledatalabs.com/v5` | `X-Api-Key` header | peopledatalabs.com/docs |
| Clado | `search.clado.ai/api` | Bearer token | clado.ai/docs |
| GitHub | `api.github.com` | Bearer token | docs.github.com |
| Perplexity | `api.perplexity.ai` | Bearer token | docs.perplexity.ai |
| StackExchange | `api.stackexchange.com/2.3` | Query param | api.stackexchange.com |
| Codeforces | `codeforces.com/api` | None | codeforces.com/apiHelp |

---

## Next Steps

### Completed (2026-02-20)
1. ~~**Fix known bugs** (match_score, personal_website, silent failures)~~ ✅ DONE
2. ~~**Add entity resolution** for company name matching~~ ✅ DONE
3. ~~**Fix Clado API integration** (endpoints, parsing, search)~~ ✅ DONE
   - Fixed endpoint paths (`/api/enrich/linkedin`, `/api/enrich/scrape`)
   - Fixed response parsing for nested structure
   - Implemented Deep Research API for search
   - Verified 85-90% data completeness

### Remaining
4. **Cut Perplexity from pipeline** — remove curation_engine step 7, gate behind flag (Part 9.3b)
5. **Implement `CandidateScorer`** — unified scoring service with cheap score + full score tiers (Part 9)
6. **Implement enrichment gate** — budget-aware candidate selection (Part 9.5)
7. **Deprecate old scorers** — remove `evaluation_engine._compute_relevance`, absorb `CandidateRanker` (Part 9.12)
8. **Deprecate unreliable fields** (is_from_network, match_score from external APIs)
9. **Evaluate verified data providers** for Stage 5 slot — must be identity-anchored, structured (Part 9.3b)
10. **Integrate RL reward model** — feed `CandidateScorer` weights from hire/reject outcomes (Phase 3)

---

## Changelog

### 2026-02-20 - Clado Integration Complete Overhaul (Branch: `data`)

**Summary:** Fixed all Clado API integration issues. Profile enrichment now works (85-90% completeness).
Search now works via Deep Research API. See commits `c95980b`, `576b584`, `7c14dad`, `4874407`.

#### What Was Broken
1. **Endpoints returning 404** - Used `/api/profile` instead of `/api/enrich/linkedin`
2. **Response parsing failed** - Expected flat object, got nested `{data: {data: {...}}}`
3. **Field names wrong** - Expected `full_name`, API returns `firstName`+`lastName`
4. **Search returns 0** - Regular `/api/search` endpoint non-functional
5. **Skills parsing wrong** - Expected array of strings, got `[{name: "Python"}, ...]`
6. **Dates parsing wrong** - Expected `start_date`, got `{start: {year: 2020, month: 3}}`

#### All Fixes Applied

| Issue | File | Fix |
|-------|------|-----|
| Wrong endpoint paths | `clado_client.py` | `/api/profile` → `/api/enrich/linkedin` |
| Nested response | `clado_client.py` | Handle `{data: {data: {...}}}` |
| Field mapping | `clado_client.py` | Map all Clado fields correctly |
| Search broken | `clado_client.py` | Use Deep Research API |
| Skills array | `clado_client.py` | Parse `skills[].name` |
| Date parsing | `clado_client.py` | Build from `start.year` + `start.month` |

#### Verified Test Results

**Profile Enrichment (linkedin.com/in/hooda-nikhil):**
```
Clado Cached Profile:  85% completeness ($0.01)
Clado Real-time Scrape: 90% completeness ($0.02)
PDL Profile:           85% completeness ($0.10)
```

**People Search ("software engineers from UCSD"):**
```
Deep Research API: 3 results in ~45 seconds
- Ishaan Gulrajani (OpenAI)
- Ryan O'Shea (Palantir)
- Brian Cheung (AI Researcher)
```

---

### 2026-02-20 - Clado API Endpoint Fixes (Branch: `data`)

#### 5. Fixed Clado endpoint paths
**File:** `app/services/external_search/clado_client.py`

**Before:**
```python
# Wrong endpoints
f"{self.base_url}/profile"   # Returns 404
f"{self.base_url}/scrape"    # Returns 404
```

**After:**
```python
# Correct endpoints per Clado docs
f"{self.base_url}/enrich/linkedin"  # Cached profile ($0.01)
f"{self.base_url}/enrich/scrape"    # Real-time scrape ($0.02)
```

---

#### 6. Fixed Clado response parsing
**File:** `app/services/external_search/clado_client.py`

**Before:** Expected flat profile object
**After:** Handles nested structure `{data: {data: {profile_fields}}}`

**Field mappings fixed:**
| Expected | Actual Clado Field |
|----------|-------------------|
| `full_name` | `firstName` + `lastName` |
| `experience` | `fullPositions` |
| `education` | `educations` |
| `skills` | `skills[].name` |
| `location` | `geo.full` |
| `start_date` | `start.year` + `start.month` |

**Impact:** Profile enrichment now works with 85-90% completeness.

---

#### 7. Fixed Clado search response parsing
**File:** `app/services/external_search/clado_client.py`

**Before:**
```python
# Wrong field names
data.get("profiles", [])      # API returns "results"
data.get("total_matches", 0)  # API returns "total"
data.get("query_interpreted") # API returns "query"
```

**After:**
```python
data.get("results", [])
data.get("total", 0)
data.get("query", query)
```

**Note:** Regular search returns 0 results - use Deep Research API instead (see #8).

---

#### 8. Implemented Deep Research API for Clado search
**File:** `app/services/external_search/clado_client.py`

**Problem:** Regular `/api/search` returns 0 results for all queries.

**Solution:** Implemented async job-based Deep Research API:

```python
async def _deep_research_search(
    self,
    query: str,
    limit: int,
    poll_interval: float = 2.0,
    max_poll_time: float = 120.0,
) -> CladoSearchResult:
    """Search using Deep Research API (async job-based)."""

    # Step 1: Initiate deep research job
    response = await client.post(
        f"{self.base_url}/search/deep_research",
        headers=self._headers(),
        json={"query": query, "limit": limit},
    )
    job_id = response.json().get("job_id")

    # Step 2: Poll for completion
    while elapsed < max_poll_time:
        response = await client.get(
            f"{self.base_url}/search/deep_research/{job_id}",
            headers=self._headers(),
        )
        data = response.json()
        if data.get("status") == "completed":
            profiles = [self._parse_deep_research_result(r) for r in data.get("results", [])]
            return CladoSearchResult(profiles=profiles, total=len(profiles))
        await asyncio.sleep(poll_interval)
```

**Added method:** `_parse_deep_research_result()` - handles nested structure:
```python
def _parse_deep_research_result(self, result: dict) -> CladoProfile:
    """Parse deep research result: {profile: {...}, experience: [...]}"""
    profile_data = result.get("profile", {})
    experience_data = result.get("experience", [])
    education_data = result.get("education", [])

    # Parse experience with year/month date objects
    experience = []
    for exp in experience_data:
        start = exp.get("start", {}) or {}
        end = exp.get("end", {}) or {}
        start_date = f"{start['year']}-{start.get('month', 1):02d}" if start.get("year") else None
        # ...

    return CladoProfile(
        full_name=profile_data.get("name", ""),
        headline=profile_data.get("headline"),
        experience=experience,
        education=education,
        skills=profile_data.get("skills", []),
        data_source="clado_deep_research",
    )
```

**Default behavior changed:** `search()` now uses `use_deep_research=True` by default.

**Impact:** Clado search now returns results. Test query "software engineers from UCSD" returned 3 profiles.

---

### 2026-02-20 - Bug Fixes (Branch: `data`)

#### 1. Fixed PDL `match_score` hardcoded to 0.8
**File:** `app/services/external_search/pdl_client.py`

**Before:**
```python
match_score: float = 0.0
# ...
match_score=0.8  # PDL doesn't return scores, assume high relevance
```

**After:**
```python
match_score: Optional[float] = None  # None indicates "not computed"
# ...
match_score=None  # PDL doesn't return scores - must be computed externally
```

**Impact:** Consumers now know the score is not available rather than trusting a fake 0.8.

---

#### 2. Fixed PDL `personal_website` containing email
**File:** `app/services/external_search/pdl_client.py`

**Before:**
```python
personal_website=data.get("personal_emails", [None])[0] if data.get("personal_emails") else None,
```

**After:**
```python
personal_website=data.get("websites", [{}])[0].get("url") if data.get("websites") else None,
```

**Impact:** Field now correctly maps to actual website URLs from PDL response.

---

#### 3. Fixed silent enrichment failures in network_index
**File:** `app/services/network_index.py`

**Before:**
```python
async def _get_enrichments(self, company_id: str) -> dict:
    try:
        enrichments = await company_db._request(...)
        return {e.get("person_id"): e for e in enrichments}
    except Exception as e:
        print(f"Error fetching enrichments: {e}")
        return {}  # Silent failure!
```

**After:**
```python
async def _get_enrichments(self, company_id: str) -> tuple[dict, bool]:
    """Returns (enrichments_dict, success_flag)"""
    try:
        enrichments = await company_db._request(...)
        if enrichments is None:
            logger.warning("Enrichment fetch returned None for company_id=%s", company_id)
            return {}, False
        logger.info("Fetched %d enrichments for company_id=%s", len(enrichments), company_id)
        return {e.get("person_id"): e for e in enrichments}, True
    except Exception as e:
        logger.error("Failed to fetch enrichments: %s", str(e), exc_info=True)
        return {}, False
```

**Also added:** `enrichments_loaded: bool` field to `NetworkIndex` model so callers know if warm paths may be incomplete.

**Impact:** Failures are now logged with full context, and callers can detect incomplete data.

---

#### 4. Added company entity resolution for warm path matching
**File:** `app/services/warm_path_finder.py`

**Before:**
```python
def _companies_match(self, company1: str, company2: str) -> bool:
    n1 = network_index_service._normalize(company1)
    n2 = network_index_service._normalize(company2)
    return n1 == n2 or n1 in n2 or n2 in n1
```

**After:**
```python
# Added COMPANY_ALIASES dict with 70+ mappings:
COMPANY_ALIASES = {
    "facebook": "meta",
    "instagram": "meta",
    "linkedin": "microsoft",
    "github": "microsoft",
    "aws": "amazon",
    "youtube": "google",
    # ... etc
}

def _companies_match(self, company1: str, company2: str) -> bool:
    n1 = network_index_service._normalize(company1)
    n2 = network_index_service._normalize(company2)

    # Direct match
    if n1 == n2:
        return True

    # Resolve to canonical names
    canonical1 = COMPANY_ALIASES.get(n1, n1)
    canonical2 = COMPANY_ALIASES.get(n2, n2)

    if canonical1 == canonical2:
        return True

    # Substring fallback
    return n1 in n2 or n2 in n1
```

**Impact:** Now correctly matches:
- Facebook ↔ Meta ↔ Instagram ↔ WhatsApp
- Google ↔ Alphabet ↔ YouTube ↔ DeepMind
- Microsoft ↔ LinkedIn ↔ GitHub
- Amazon ↔ AWS ↔ Twitch
- And 60+ more company aliases
