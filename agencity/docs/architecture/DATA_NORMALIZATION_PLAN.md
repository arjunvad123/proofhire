# Data Normalization Plan: Unify Before Aggregating

## Problem Statement

Before we can aggregate external sources (GitHub, DevPost), we need to solve the **base data inconsistency** problem:

- **`people` table**: Has basic identity (name, title, company, LinkedIn URL)
- **`person_enrichments` table**: Has rich data (experience, education, skills, projects) BUT:
  - ❌ Not all people have enrichments
  - ❌ Enrichment completeness varies widely
  - ❌ Data format is inconsistent (some JSONB arrays, some null)
  - ❌ Source quality varies (CSV import vs. API enrichment vs. manual)

## Current State Assessment

### What We Have

```
305 LinkedIn Connections (from CSV import)
├── All have: people record (name, current title/company, LinkedIn URL)
├── Some have: person_enrichments record
│   ├── experience: [{"company": "...", "title": "...", "start_date": ...}]
│   ├── education: [{"school": "...", "degree": "...", "field": "..."}]
│   ├── skills: ["Python", "React", ...]
│   └── projects: [...]
└── Many have: Incomplete or missing enrichment data
```

### Data Quality Issues

| Field | Coverage | Quality | Issue |
|-------|----------|---------|-------|
| `full_name` | 100% | ✅ High | From CSV |
| `current_title` | ~90% | ⚠️ Medium | Some outdated |
| `current_company` | ~90% | ⚠️ Medium | Some outdated |
| `linkedin_url` | 100% | ✅ High | From CSV |
| `experience` | ~40%? | ❓ Unknown | Only if enriched |
| `education` | ~40%? | ❓ Unknown | Only if enriched |
| `skills` | ~30%? | ❓ Unknown | Only if enriched |
| `projects` | ~10%? | ❓ Unknown | Rarely populated |
| `github_url` | ~5%? | ❓ Unknown | Rarely populated |

## Step-by-Step Normalization Plan

### Phase 1: Assess Current Data (Week 1)

**Goal**: Understand what we actually have

#### 1.1 Data Audit Script

```sql
-- Check coverage of person_enrichments
SELECT
    COUNT(DISTINCT p.id) as total_people,
    COUNT(DISTINCT pe.person_id) as people_with_enrichments,
    ROUND(COUNT(DISTINCT pe.person_id)::float / COUNT(DISTINCT p.id) * 100, 2) as enrichment_coverage_pct
FROM people p
LEFT JOIN person_enrichments pe ON p.id = pe.person_id;

-- Check which fields are populated
SELECT
    COUNT(*) FILTER (WHERE jsonb_array_length(skills) > 0) as has_skills,
    COUNT(*) FILTER (WHERE jsonb_array_length(experience) > 0) as has_experience,
    COUNT(*) FILTER (WHERE jsonb_array_length(education) > 0) as has_education,
    COUNT(*) FILTER (WHERE jsonb_array_length(projects) > 0) as has_projects
FROM person_enrichments;

-- Check LinkedIn URL coverage
SELECT
    COUNT(*) as total_people,
    COUNT(*) FILTER (WHERE linkedin_url IS NOT NULL) as has_linkedin_url,
    COUNT(*) FILTER (WHERE github_url IS NOT NULL) as has_github_url
FROM people;
```

#### 1.2 Sample Data Inspection

```python
# scripts/audit_data_quality.py

from supabase import create_client
import json

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get sample person with enrichments
response = supabase.table('people')\
    .select('*, person_enrichments(*)')\
    .limit(10)\
    .execute()

for person in response.data:
    print(f"\n{'='*60}")
    print(f"Name: {person['full_name']}")
    print(f"Current: {person.get('current_title')} @ {person.get('current_company')}")
    print(f"LinkedIn: {person.get('linkedin_url')}")
    print(f"GitHub: {person.get('github_url')}")

    enrichment = person.get('person_enrichments')
    if enrichment:
        print(f"\n✅ HAS ENRICHMENT:")
        print(f"  - Skills: {len(enrichment.get('skills', []))} items")
        print(f"  - Experience: {len(enrichment.get('experience', []))} jobs")
        print(f"  - Education: {len(enrichment.get('education', []))} schools")
        print(f"  - Projects: {len(enrichment.get('projects', []))} projects")
        print(f"  - Source: {enrichment.get('enrichment_source')}")

        # Show sample experience
        if enrichment.get('experience'):
            print(f"\n  Sample Experience:")
            for exp in enrichment['experience'][:2]:
                print(f"    • {exp.get('title')} @ {exp.get('company')}")
    else:
        print(f"\n❌ NO ENRICHMENT - Only basic data from people table")

# Count by enrichment source
enrichments = supabase.table('person_enrichments')\
    .select('enrichment_source')\
    .execute()

sources = {}
for e in enrichments.data:
    source = e.get('enrichment_source', 'unknown')
    sources[source] = sources.get(source, 0) + 1

print(f"\n{'='*60}")
print("Enrichment Sources:")
for source, count in sources.items():
    print(f"  {source}: {count}")
```

**Output this script to understand:**
- What % have enrichments?
- What format is the data in?
- Where did it come from?

---

### Phase 2: Create Unified Candidate Model (Week 1)

**Goal**: Define ONE canonical structure for candidate data

#### 2.1 Unified Data Model

```python
# app/models/candidate.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CandidateExperience(BaseModel):
    """Normalized experience entry."""
    company: str
    title: str
    start_date: Optional[str]  # "2020-01" or "2020" or None
    end_date: Optional[str]     # None = current
    duration_months: Optional[int]
    description: Optional[str]
    location: Optional[str]
    source: str  # "linkedin", "enrichment", "manual"

class CandidateEducation(BaseModel):
    """Normalized education entry."""
    school: str
    degree: Optional[str]  # "BS", "MS", "PhD", etc.
    field: Optional[str]   # "Computer Science", etc.
    start_year: Optional[int]
    end_year: Optional[int]
    gpa: Optional[str]
    activities: Optional[str]
    source: str

class CandidateProject(BaseModel):
    """Normalized project entry."""
    name: str
    description: Optional[str]
    tech_stack: List[str]
    github_url: Optional[str]
    demo_url: Optional[str]
    source: str  # "linkedin", "github", "devpost", "manual"

class UnifiedCandidate(BaseModel):
    """
    Unified candidate profile.

    This is the single source of truth for candidate data.
    All downstream processes use this model.
    """
    # Identity (from people table)
    person_id: str
    full_name: str
    email: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]

    # Current (from people table)
    headline: Optional[str]
    location: Optional[str]
    current_company: Optional[str]
    current_title: Optional[str]

    # Experience (from person_enrichments OR people table)
    experience: List[CandidateExperience]

    # Education (from person_enrichments)
    education: List[CandidateEducation]

    # Skills (from person_enrichments, deduplicated)
    skills: List[str]

    # Projects (from person_enrichments, github, devpost)
    projects: List[CandidateProject]

    # Metadata
    data_completeness: float  # 0-1 score
    last_updated: datetime
    sources_used: List[str]   # ["people", "enrichments", "github"]

class CandidateBuilder:
    """Builds UnifiedCandidate from database records."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def build(self, person_id: str) -> UnifiedCandidate:
        """
        Build unified candidate from all available data sources.

        Priority order:
        1. person_enrichments (if exists)
        2. people table (fallback)
        3. Fill missing with None
        """

        # Fetch person
        person_response = self.supabase.table('people')\
            .select('*')\
            .eq('id', person_id)\
            .single()\
            .execute()

        person = person_response.data

        # Fetch enrichments (may not exist)
        enrichment_response = self.supabase.table('person_enrichments')\
            .select('*')\
            .eq('person_id', person_id)\
            .execute()

        enrichment = enrichment_response.data[0] if enrichment_response.data else None

        # Build unified profile
        return UnifiedCandidate(
            person_id=person['id'],
            full_name=person['full_name'],
            email=person.get('email'),
            linkedin_url=person.get('linkedin_url'),
            github_url=person.get('github_url'),
            headline=person.get('headline'),
            location=person.get('location'),
            current_company=person.get('current_company'),
            current_title=person.get('current_title'),

            # Experience: Use enrichment if available, else synthesize from current
            experience=self._build_experience(person, enrichment),

            # Education: From enrichment only
            education=self._build_education(enrichment),

            # Skills: From enrichment, normalized
            skills=self._build_skills(enrichment),

            # Projects: From enrichment
            projects=self._build_projects(enrichment),

            # Metadata
            data_completeness=self._calculate_completeness(person, enrichment),
            last_updated=datetime.now(),
            sources_used=self._get_sources_used(person, enrichment)
        )

    def _build_experience(
        self,
        person: dict,
        enrichment: Optional[dict]
    ) -> List[CandidateExperience]:
        """Build experience list."""

        experiences = []

        # Try enrichment first
        if enrichment and enrichment.get('experience'):
            for exp in enrichment['experience']:
                experiences.append(CandidateExperience(
                    company=exp.get('company', ''),
                    title=exp.get('title', ''),
                    start_date=self._normalize_date(exp.get('start_date')),
                    end_date=self._normalize_date(exp.get('end_date')),
                    duration_months=exp.get('duration_months'),
                    description=exp.get('description'),
                    location=exp.get('location'),
                    source='enrichment'
                ))

        # If no enrichment, synthesize from people.current_*
        elif person.get('current_company') and person.get('current_title'):
            experiences.append(CandidateExperience(
                company=person['current_company'],
                title=person['current_title'],
                start_date=None,
                end_date=None,  # Current
                duration_months=None,
                description=None,
                location=person.get('location'),
                source='people'
            ))

        return experiences

    def _build_education(self, enrichment: Optional[dict]) -> List[CandidateEducation]:
        """Build education list."""

        if not enrichment or not enrichment.get('education'):
            return []

        education_list = []
        for edu in enrichment['education']:
            # Handle both dict and string formats
            if isinstance(edu, dict):
                school_name = edu.get('school', '')
                if isinstance(school_name, dict):
                    school_name = school_name.get('name', '')
            else:
                school_name = str(edu)
                edu = {}  # Empty dict for other fields

            if school_name:
                education_list.append(CandidateEducation(
                    school=school_name,
                    degree=edu.get('degree'),
                    field=edu.get('field') or edu.get('field_of_study'),
                    start_year=self._extract_year(edu.get('start_date')),
                    end_year=self._extract_year(edu.get('end_date')),
                    gpa=edu.get('gpa'),
                    activities=edu.get('activities'),
                    source='enrichment'
                ))

        return education_list

    def _build_skills(self, enrichment: Optional[dict]) -> List[str]:
        """Build normalized skills list."""

        if not enrichment or not enrichment.get('skills'):
            return []

        skills = enrichment['skills']

        # Handle both list of strings and list of dicts
        normalized = []
        for skill in skills:
            if isinstance(skill, dict):
                normalized.append(skill.get('name', str(skill)))
            else:
                normalized.append(str(skill))

        # Deduplicate and sort
        return sorted(list(set(normalized)))

    def _build_projects(self, enrichment: Optional[dict]) -> List[CandidateProject]:
        """Build projects list."""

        if not enrichment or not enrichment.get('projects'):
            return []

        projects = []
        for proj in enrichment['projects']:
            projects.append(CandidateProject(
                name=proj.get('name', ''),
                description=proj.get('description'),
                tech_stack=proj.get('tech_stack', []),
                github_url=proj.get('github_url'),
                demo_url=proj.get('demo_url'),
                source='enrichment'
            ))

        return projects

    def _calculate_completeness(self, person: dict, enrichment: Optional[dict]) -> float:
        """Calculate profile completeness (0-1)."""

        score = 0.0
        total_fields = 10

        # Basic fields (from people)
        if person.get('email'): score += 1
        if person.get('linkedin_url'): score += 1
        if person.get('headline'): score += 1
        if person.get('location'): score += 1
        if person.get('current_company'): score += 1
        if person.get('current_title'): score += 1

        # Rich fields (from enrichment)
        if enrichment:
            if enrichment.get('experience'): score += 1
            if enrichment.get('education'): score += 1
            if enrichment.get('skills'): score += 1
            if enrichment.get('projects'): score += 1

        return score / total_fields

    def _get_sources_used(self, person: dict, enrichment: Optional[dict]) -> List[str]:
        """List which data sources were used."""
        sources = ['people']
        if enrichment:
            sources.append('enrichments')
        return sources

    def _normalize_date(self, date_val) -> Optional[str]:
        """Normalize date to YYYY-MM or YYYY format."""
        if not date_val:
            return None
        if isinstance(date_val, dict):
            year = date_val.get('year')
            month = date_val.get('month')
            if year and month:
                return f"{year}-{month:02d}"
            elif year:
                return str(year)
        elif isinstance(date_val, str):
            return date_val[:7] if len(date_val) >= 7 else date_val[:4]
        return None

    def _extract_year(self, date_val) -> Optional[int]:
        """Extract year from date value."""
        if not date_val:
            return None
        if isinstance(date_val, dict):
            return date_val.get('year')
        elif isinstance(date_val, str):
            try:
                return int(date_val[:4])
            except:
                return None
        return None
```

---

### Phase 3: Normalize Existing Data (Week 2)

**Goal**: Convert all existing data into UnifiedCandidate format

#### 3.1 Batch Normalization Script

```python
# scripts/normalize_all_candidates.py

import asyncio
from app.models.candidate import CandidateBuilder
from supabase import create_client

async def normalize_all():
    """Build unified profiles for all people."""

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    builder = CandidateBuilder(supabase)

    # Get all people
    response = supabase.table('people').select('id, full_name').execute()
    people = response.data

    print(f"Found {len(people)} people to normalize")

    results = {
        'total': len(people),
        'success': 0,
        'has_enrichment': 0,
        'no_enrichment': 0,
        'completeness_scores': []
    }

    for person in people:
        try:
            # Build unified profile
            unified = await builder.build(person['id'])

            # Track stats
            results['success'] += 1
            if 'enrichments' in unified.sources_used:
                results['has_enrichment'] += 1
            else:
                results['no_enrichment'] += 1

            results['completeness_scores'].append(unified.data_completeness)

            print(f"✓ {unified.full_name}: {len(unified.experience)} exp, {len(unified.education)} edu, {len(unified.skills)} skills")

        except Exception as e:
            print(f"✗ Failed {person['full_name']}: {e}")

    # Summary
    avg_completeness = sum(results['completeness_scores']) / len(results['completeness_scores'])

    print(f"\n{'='*60}")
    print(f"Normalization Complete:")
    print(f"  Total: {results['total']}")
    print(f"  Success: {results['success']}")
    print(f"  With enrichment: {results['has_enrichment']} ({results['has_enrichment']/results['total']*100:.1f}%)")
    print(f"  Without enrichment: {results['no_enrichment']} ({results['no_enrichment']/results['total']*100:.1f}%)")
    print(f"  Avg completeness: {avg_completeness:.2f}")

if __name__ == "__main__":
    asyncio.run(normalize_all())
```

#### 3.2 Create Normalized View

```sql
-- Create materialized view for quick access to unified profiles
CREATE MATERIALIZED VIEW unified_candidates AS
SELECT
    p.id as person_id,
    p.full_name,
    p.email,
    p.linkedin_url,
    p.github_url,
    p.headline,
    p.location,
    p.current_company,
    p.current_title,

    -- From enrichments
    COALESCE(pe.experience, '[]'::jsonb) as experience,
    COALESCE(pe.education, '[]'::jsonb) as education,
    COALESCE(pe.skills, '[]'::jsonb) as skills,
    COALESCE(pe.projects, '[]'::jsonb) as projects,

    -- Metadata
    CASE
        WHEN pe.person_id IS NOT NULL THEN 'enrichments'
        ELSE 'people_only'
    END as data_source,

    -- Completeness calculation
    (
        CASE WHEN p.email IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN p.linkedin_url IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN p.headline IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN p.location IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN p.current_company IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN p.current_title IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN pe.experience IS NOT NULL AND jsonb_array_length(pe.experience) > 0 THEN 1 ELSE 0 END +
        CASE WHEN pe.education IS NOT NULL AND jsonb_array_length(pe.education) > 0 THEN 1 ELSE 0 END +
        CASE WHEN pe.skills IS NOT NULL AND jsonb_array_length(pe.skills) > 0 THEN 1 ELSE 0 END +
        CASE WHEN pe.projects IS NOT NULL AND jsonb_array_length(pe.projects) > 0 THEN 1 ELSE 0 END
    ) / 10.0 as data_completeness

FROM people p
LEFT JOIN person_enrichments pe ON p.id = pe.person_id;

-- Index for fast queries
CREATE INDEX idx_unified_candidates_completeness ON unified_candidates(data_completeness DESC);
CREATE INDEX idx_unified_candidates_person_id ON unified_candidates(person_id);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_unified_candidates()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY unified_candidates;
END;
$$ LANGUAGE plpgsql;
```

---

### Phase 4: Fill Gaps (Week 2-3)

**Goal**: Enrich profiles that are missing data

#### 4.1 Identify Low-Completeness Profiles

```sql
-- Find candidates with low completeness
SELECT
    person_id,
    full_name,
    current_company,
    linkedin_url,
    data_completeness
FROM unified_candidates
WHERE data_completeness < 0.5
ORDER BY data_completeness ASC
LIMIT 50;
```

#### 4.2 Enrichment Strategy

```python
# scripts/enrich_incomplete_profiles.py

# For people with LinkedIn URL but no enrichment:
# Option 1: Use People Data Labs API
# Option 2: Prompt founder to manually add data
# Option 3: Mark as "needs enrichment" in queue

async def enrich_incomplete():
    """Enrich profiles with completeness < 0.5"""

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get incomplete profiles
    response = supabase.table('unified_candidates')\
        .select('*')\
        .lt('data_completeness', 0.5)\
        .execute()

    print(f"Found {len(response.data)} incomplete profiles")

    for candidate in response.data:
        linkedin_url = candidate['linkedin_url']

        if linkedin_url:
            # Add to enrichment queue
            supabase.table('enrichment_queue').insert({
                'person_id': candidate['person_id'],
                'priority': 1,  # Higher priority for existing connections
                'status': 'pending'
            }).execute()

            print(f"Queued: {candidate['full_name']}")
```

---

### Phase 5: API Layer (Week 3)

**Goal**: All code accesses candidates through unified API

#### 5.1 Unified API Endpoint

```python
# app/api/routes/candidates.py

from fastapi import APIRouter
from app.models.candidate import CandidateBuilder, UnifiedCandidate

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])

@router.get("/{person_id}")
async def get_candidate(person_id: str) -> UnifiedCandidate:
    """
    Get unified candidate profile.

    This is the ONLY way to access candidate data.
    Returns consistent structure regardless of source.
    """
    builder = CandidateBuilder(get_supabase())
    return await builder.build(person_id)

@router.get("/")
async def list_candidates(
    min_completeness: float = 0.0,
    has_github: bool = None,
    limit: int = 50
):
    """List candidates with filters."""

    # Query unified_candidates view
    query = supabase.rpc('get_unified_candidates', {
        'min_completeness': min_completeness,
        'limit': limit
    }).execute()

    return {'candidates': query.data}
```

---

## Summary: Normalization Before Aggregation

### What This Achieves

1. ✅ **Consistent Base**: All candidates have same structure
2. ✅ **Known Gaps**: We know what's missing (completeness score)
3. ✅ **Prioritized Enrichment**: Focus on high-value, low-completeness profiles
4. ✅ **Clean Foundation**: Now we can layer GitHub/DevPost on top

### Then (Phase 6): Add External Sources

Only AFTER normalization:
```python
# Now we can cleanly add GitHub data
class GitHubAggregator:
    async def augment(self, unified_candidate: UnifiedCandidate) -> UnifiedCandidate:
        """Add GitHub data to already-normalized candidate."""

        if not unified_candidate.github_url:
            return unified_candidate

        # Fetch GitHub data
        github_data = await self.fetch_github(...)

        # Add to existing structure
        unified_candidate.projects.extend(github_data.projects)
        unified_candidate.skills.extend(github_data.languages)
        unified_candidate.sources_used.append('github')

        return unified_candidate
```

---

## Next Steps

1. **Run audit script** to see actual data quality
2. **Review sample profiles** to understand formats
3. **Implement CandidateBuilder** to normalize
4. **Create unified_candidates view** for queries
5. **Then** add GitHub/DevPost aggregation

Want me to start with the audit script to see what you actually have?
