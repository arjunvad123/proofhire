# Candidate Curation System

## Overview

The Candidate Curation System automatically curates a shortlist of candidates for any role by:

1. **Searching** all network connections (e.g., 305 LinkedIn connections)
2. **Ranking** by fit to role (works even with incomplete data)
3. **Enriching** top candidates on-demand (only pay for what you need)
4. **Building** rich context for founder decisions

**Founder's job:** Review 10-15 curated candidates and decide: [Yes - Interview] or [Pass]

---

## Architecture

```
All Network Candidates (305)
    ↓
Initial Ranking (incomplete data OK)
    ↓
Top 30 Candidates
    ↓
On-Demand Enrichment (if needed)
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
✅ **Progressive enrichment** - Only enriches top candidates (saves cost)
✅ **Confidence tracking** - Knows when it needs more data
✅ **Rich context** - Tells founder WHY to consider each candidate
✅ **Explicit unknowns** - Shows what we DON'T know (honest assessment)

---

## How It Works

### 1. Fit Scoring (Works with Incomplete Data)

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
```

**Example:**

| Candidate | Skills Data? | Score | Confidence | Action |
|-----------|-------------|-------|------------|--------|
| Maya Patel | ✅ Yes | 87 | 0.85 | Use as-is |
| John Smith | ❌ No | 72 | 0.35 | Enrich on-demand |
| Sarah Lee | ✅ Yes | 91 | 0.90 | Use as-is |

### 2. On-Demand Enrichment

For top 30 candidates with confidence < 0.7:
- Call People Data Labs API (~$0.05/person)
- Add skills, full experience, education
- Re-calculate fit score with better data

**Cost:** ~$1-2 (vs. $15 to enrich everyone)

### 3. Rich Context Building

For final shortlist of 10-15, build:

```json
{
  "why_consider": [
    {
      "category": "Skills Match",
      "strength": "high",
      "points": [
        "✓ Python (3 years)",
        "✓ React - matches requirement",
        "~ Machine Learning - nice to have"
      ]
    },
    {
      "category": "Building Experience",
      "strength": "high",
      "points": [
        "✓ 15 GitHub repos",
        "✓ Won Best AI Project at SD Hacks 2024"
      ]
    }
  ],
  "unknowns": [
    "Professional work experience",
    "Interest in startups",
    "Salary expectations"
  ],
  "standout_signal": "Won Best AI Project at SD Hacks 2024",
  "warm_path": "Direct LinkedIn connection"
}
```

---

## Installation

### 1. Install Dependencies

```bash
cd agencity
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Copy example
cp .env.example .env

# Edit with your credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

### 3. Verify Database Schema

Make sure you have these tables in Supabase:
- `companies`
- `roles`
- `people`
- `person_enrichments` (optional - for enriched data)
- `company_umos` (optional - for culture fit)

---

## Usage

### Command Line Test

```bash
# List companies
python scripts/test_curation.py

# List roles for a company
python scripts/test_curation.py <company_id>

# Run curation for a role
python scripts/test_curation.py <company_id> <role_id>
```

**Example output:**

```
╔══════════════════════════════════════════════════════════════╗
║  SHORTLIST (10 candidates)                                   ║
╚══════════════════════════════════════════════════════════════╝

#1 - Maya Patel
────────────────────────────────────────────────────────────────
  Match Score: 87.0/100 (confidence: 0.85)
  Headline: CS @ UCSD | AI/ML Enthusiast
  Location: San Diego, CA

  WHY CONSIDER:
    Skills Match (HIGH)
      ✓ Python
      ✓ React
      ~ Machine Learning

    Building Experience (HIGH)
      ✓ 15 GitHub repos
      ✓ Won Best AI Project at SD Hacks 2024

  ⭐ STANDOUT: Won Best AI Project at SD Hacks 2024

  UNKNOWNS:
    • Professional experience
    • Startup interest

  WARM PATH: Direct LinkedIn connection
  Data Completeness: 75%
```

### API Usage

```python
from app.services.curation_engine import CandidateCurationEngine
from app.core.database import get_supabase_client

# Initialize
supabase = get_supabase_client()
engine = CandidateCurationEngine(supabase)

# Run curation
shortlist = await engine.curate(
    company_id="uuid-...",
    role_id="uuid-...",
    limit=15
)

# Review results
for candidate in shortlist:
    print(f"{candidate.full_name}: {candidate.match_score}/100")
    print(f"Why: {candidate.context.why_consider}")
    print(f"Don't know: {candidate.context.unknowns}")
```

### REST API

```bash
# Start FastAPI server
uvicorn app.main:app --reload --port 8001

# Curate candidates
curl -X POST http://localhost:8001/api/v1/curation/curate \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "uuid-...",
    "role_id": "uuid-...",
    "limit": 15
  }'
```

**Response:**

```json
{
  "shortlist": [
    {
      "person_id": "uuid-...",
      "full_name": "Maya Patel",
      "match_score": 87,
      "context": {
        "why_consider": [...],
        "unknowns": [...],
        "warm_path": "Direct LinkedIn connection"
      }
    }
  ],
  "total_searched": 305,
  "metadata": {
    "avg_match_score": 72,
    "enriched_count": 8,
    "avg_confidence": 0.78
  }
}
```

---

## How Scoring Works

### Skills Match (40%)

**With skills data:**
```python
matched_skills = ["Python", "React"]
required_skills = ["Python", "React", "TypeScript"]
score = 2/3 = 0.67 → 27/40 points
```

**Without skills data (conservative estimate):**
```python
if "engineer" in title and "engineer" in role:
    score = 0.5 → 20/40 points  # Medium estimate
    confidence = LOW
```

### Experience Match (30%)

**With experience data:**
```python
years = 3
required_min = 2, max = 5
# Within range → score = 0.8 → 24/30 points

# Plus bonuses:
# - Relevant title in history: +0.3
# - Top company: +0.2
```

**Without experience data:**
```python
if "senior" in title:
    estimate = 0.6 → 18/30 points
elif "junior" in title:
    estimate = 0.4 → 12/30 points
else:
    estimate = 0.5 → 15/30 points  # Mid-level assumption
```

### Culture Fit (20%)

Based on Company UMO:
- Preferred company backgrounds
- Must-have traits ("builder", "ship fast")
- Anti-patterns to avoid

### Signals (10%)

- Has GitHub profile: +3 points
- Has projects listed: +3 points
- High data completeness: +2 points
- Active contributor: +2 points

---

## Extending the System

### Add New Data Sources

```python
# app/services/enrichers/github_enricher.py

class GitHubEnricher:
    async def enrich(self, candidate: UnifiedCandidate):
        """Add GitHub data to candidate."""
        if not candidate.github_url:
            return candidate

        # Fetch GitHub data
        github_data = await fetch_github_api(candidate.github_url)

        # Add to candidate
        candidate.github_repos = github_data.repos
        candidate.github_stars = github_data.total_stars

        return candidate
```

### Customize Scoring

```python
# app/services/curation_engine.py

def _calculate_fit(self, candidate, role, company_dna, umo):
    # Adjust weights for your needs
    weights = {
        'skills': 0.5,      # Increase skills importance
        'experience': 0.2,  # Decrease experience importance
        'culture': 0.2,
        'signals': 0.1
    }
```

### Add Context Sections

```python
def _build_context(self, candidate, role, company_dna, umo):
    # Add custom section
    if candidate.hackathon_projects:
        why_consider.append(WhyConsiderPoint(
            category="Hackathon Experience",
            strength=MatchStrength.HIGH,
            points=[f"✓ {p.name}" for p in candidate.hackathon_projects]
        ))
```

---

## Data Completeness Guide

| Completeness | What You Have | What to Do |
|--------------|---------------|------------|
| 0-30% | Name, title only | **Enrich immediately** - too incomplete to rank well |
| 30-70% | Title + some skills/experience | **Enrich top candidates** - enough to rank, but improve accuracy for finalists |
| 70-100% | Full profile with skills, experience, projects | **Use as-is** - no enrichment needed |

---

## Cost Estimation

### Scenario: 305 network connections, hiring Software Engineer

**Traditional approach (enrich everyone first):**
- 305 people × $0.05 = **$15.25**
- Time: 2-3 hours (API calls + processing)

**Curation approach (progressive):**
- Initial rank: 305 people × $0 = **$0** (use existing data)
- Enrich top 30 with low confidence: 10 people × $0.05 = **$0.50**
- Total: **$0.50**
- Time: 5-10 minutes

**Savings: 97% cost reduction, 10x faster**

---

## Troubleshooting

### "No candidates found"

Check that you have people in the network:
```sql
SELECT COUNT(*) FROM people WHERE company_id = 'your-company-id';
```

### "Low match scores"

- Check role requirements are realistic
- Verify people table has current_title populated
- Consider enriching more candidates

### "All candidates have low confidence"

Most people missing enrichment data. Either:
1. Enrich top candidates manually
2. Run batch enrichment
3. Lower confidence threshold temporarily

---

## Next Steps

1. **Week 1:** Test with existing data (works today!)
2. **Week 2:** Add on-demand enrichment (PDL API)
3. **Week 3:** Add GitHub/DevPost fetchers
4. **Week 4:** Add candidate onboarding for warm leads

---

**Questions?** See `docs/architecture/DATA_NORMALIZATION_PLAN.md` for detailed architecture.
