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
| `match_score` | **BROKEN** | Hardcoded to 0.8 |

**Known Bugs:**
```python
# Line 240 - match_score is fake:
match_score=0.8  # PDL doesn't return scores, assume high relevance

# Line 239 - personal_website contains email:
personal_website=profile.get("work_email")  # Bug: wrong field
```

**Best Use:** Enriching LinkedIn-extracted candidates with work history, education, skills.

---

### 1.3 Clado.ai
**File:** `app/services/external_search/clado_client.py`

| Attribute | Value |
|-----------|-------|
| API | `https://search.clado.ai/api` |
| Cost | ~$0.01 per result |
| Database Size | 800M+ LinkedIn profiles |
| Reliability | **MEDIUM** |

**Endpoints:**
- `/search` - Natural language queries
- `/enrich` - Profile enrichment by LinkedIn URL

**Fields Returned:**
| Field | Reliability | Notes |
|-------|-------------|-------|
| `full_name` | HIGH | From database |
| `linkedin_url` | HIGH | Direct |
| `experience[]` | MEDIUM | Less detailed than PDL |
| `education[]` | MEDIUM | |
| `skills[]` | MEDIUM | |
| `match_score` | **UNRELIABLE** | LLM-generated, subjective |
| `match_explanation` | **UNRELIABLE** | LLM hallucination risk |

**Search Types:**
- `fast`: 3-40 seconds
- `pro`: 30-300 seconds (more thorough)

**Best Use:** Volume discovery at low cost, but verify via PDL.

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

**Best Use:** Final verification of top candidates only, not bulk processing.

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
| Deep research (top candidates) | Perplexity | ~$0.05-0.10 |

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

### Proposed Flow

```
LinkedIn Extraction (Source of Truth)
         │
         ├─ linkedin_url ✓
         ├─ full_name ✓
         ├─ current_company (parsed)
         └─ current_title (parsed)
         │
         ▼
    PDL Enrichment ($0.10)
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
    Compute Scores (Internal)
         │
         ├─ fit_score ← Based on skills match
         ├─ experience_score ← Based on tenure/companies
         └─ activity_score ← Based on GitHub activity
         │
         ▼
    Top N: Perplexity Deep Research (~$0.05-0.10)
         │
         └─ Final verification before brief
```

### Cost Estimate Per Candidate

| Stage | Cost |
|-------|------|
| LinkedIn Extraction | $0 |
| PDL Enrichment | $0.10 |
| GitHub Enrichment | $0 |
| Perplexity (top 5 only) | $0.02 avg |
| **Total** | **~$0.12/candidate** |

---

## Part 7: Known Bugs to Fix

| Bug | Location | Impact | Fix |
|-----|----------|--------|-----|
| `match_score` hardcoded 0.8 | `pdl_client.py:240` | Fake relevance scores | Remove field or compute |
| `personal_website` contains email | `pdl_client.py:239` | Wrong data | Fix field mapping |
| Silent enrichment failures | `network_index.py:182-198` | Missing warm paths | Add error propagation |
| Naive company matching | `warm_path_finder.py:231-237` | False warm paths | Use entity resolution |
| Unvalidated `is_from_network` | `company_db.py` | Trust issues | Add verification step |

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

1. **Implement validation layer** that verifies LinkedIn-extracted data via PDL
2. **Fix known bugs** (match_score, personal_website, silent failures)
3. **Add entity resolution** for company name matching
4. **Deprecate unreliable fields** (is_from_network, match_score from APIs)
5. **Build confidence scoring** based on data completeness
