# Proof-Directed Search: Implementation Guide

## Integration with Existing Agencity System

This guide shows how to implement proof-directed search on top of your existing Supabase database with LinkedIn connections and candidates.

---

## 1. Database Migration

### 1.1 Extend Existing Schema

Your current schema has:
- `companies` table
- `roles` table
- `people` table (your candidates/connections)

We'll add proof-directed tables alongside:

```sql
-- ============================================
-- PROOF-DIRECTED SEARCH TABLES
-- ============================================

-- Artifacts: Raw evidence collected from sources
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    type TEXT NOT NULL,  -- 'github_repo', 'linkedin_profile', 'resume', etc.
    source_url TEXT,
    raw_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_artifact_type CHECK (
        type IN (
            'github_repo', 'github_commit', 'github_pr',
            'linkedin_profile', 'linkedin_experience',
            'resume', 'portfolio_project', 'hackathon_project',
            'interview_transcript', 'code_sample'
        )
    )
);

CREATE INDEX idx_artifacts_person ON artifacts(person_id);
CREATE INDEX idx_artifacts_type ON artifacts(type);
CREATE INDEX idx_artifacts_collected ON artifacts(collected_at DESC);

-- Evidence: Structured facts extracted from artifacts
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    fact TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    structured_data JSONB NOT NULL DEFAULT '{}'::jsonb,

    CONSTRAINT valid_evidence_type CHECK (
        type IN (
            'commit_pattern', 'code_review_activity', 'language_usage',
            'test_coverage', 'open_source_contribution',
            'job_tenure', 'title_progression', 'company_history',
            'skill_endorsements', 'recommendations',
            'education', 'certification', 'project_description',
            'project_complexity', 'documentation_quality',
            'communication_clarity', 'technical_depth', 'problem_solving'
        )
    )
);

CREATE INDEX idx_evidence_person ON evidence(person_id);
CREATE INDEX idx_evidence_artifact ON evidence(artifact_id);
CREATE INDEX idx_evidence_type ON evidence(type);
CREATE INDEX idx_evidence_extracted ON evidence(extracted_at DESC);

-- Enable pgvector for semantic search (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column for evidence
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS fact_embedding VECTOR(1536);
CREATE INDEX IF NOT EXISTS idx_evidence_embedding
    ON evidence USING ivfflat (fact_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Claims: Hypotheses about candidate capabilities
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    statement TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unproved',
    confidence_score FLOAT NOT NULL DEFAULT 0.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    relevance_to_role FLOAT NOT NULL DEFAULT 0.5 CHECK (relevance_to_role >= 0 AND relevance_to_role <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- For proved claims
    proof_summary TEXT,

    -- For unproved claims
    follow_up_questions JSONB DEFAULT '[]'::jsonb,

    CONSTRAINT valid_claim_type CHECK (
        type IN (
            'technical_skill', 'framework_experience', 'system_design', 'code_quality',
            'role_experience', 'industry_knowledge', 'team_collaboration', 'leadership',
            'formal_education', 'self_directed_learning',
            'communication', 'problem_solving', 'shipping_speed'
        )
    ),
    CONSTRAINT valid_claim_status CHECK (
        status IN ('proved', 'unproved', 'contradicted', 'partial')
    )
);

CREATE INDEX idx_claims_person ON claims(person_id);
CREATE INDEX idx_claims_role ON claims(role_id);
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_type ON claims(type);
CREATE INDEX idx_claims_updated ON claims(updated_at DESC);

-- Claim-Evidence junction: Links claims to supporting evidence
CREATE TABLE claim_evidence (
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    weight FLOAT NOT NULL DEFAULT 1.0,  -- How strongly this evidence supports the claim
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (claim_id, evidence_id)
);

CREATE INDEX idx_claim_evidence_claim ON claim_evidence(claim_id);
CREATE INDEX idx_claim_evidence_evidence ON claim_evidence(evidence_id);

-- Proof profiles: Cached evaluation results
CREATE TABLE proof_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,

    -- Summary statistics
    total_artifacts INT NOT NULL DEFAULT 0,
    total_evidence INT NOT NULL DEFAULT 0,
    total_claims INT NOT NULL DEFAULT 0,
    proved_claims INT NOT NULL DEFAULT 0,
    unproved_claims INT NOT NULL DEFAULT 0,

    -- Scores
    proof_strength FLOAT NOT NULL DEFAULT 0.0,
    role_fit_score FLOAT NOT NULL DEFAULT 0.0,

    -- Cached data
    critical_unknowns JSONB NOT NULL DEFAULT '[]'::jsonb,
    interview_questions JSONB NOT NULL DEFAULT '[]'::jsonb,
    top_strengths JSONB NOT NULL DEFAULT '[]'::jsonb,

    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- Cache expiration

    UNIQUE(person_id, role_id)
);

CREATE INDEX idx_proof_profiles_person ON proof_profiles(person_id);
CREATE INDEX idx_proof_profiles_role ON proof_profiles(role_id);
CREATE INDEX idx_proof_profiles_scores ON proof_profiles(proof_strength DESC, role_fit_score DESC);
CREATE INDEX idx_proof_profiles_generated ON proof_profiles(generated_at DESC);

-- Function to update claim updated_at
CREATE OR REPLACE FUNCTION update_claim_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_claims_updated_at
    BEFORE UPDATE ON claims
    FOR EACH ROW
    EXECUTE FUNCTION update_claim_updated_at();

-- ============================================
-- VIEWS FOR EASY QUERYING
-- ============================================

-- View: Complete candidate proof profile
CREATE OR REPLACE VIEW candidate_proof_summary AS
SELECT
    p.id as person_id,
    p.full_name,
    p.current_title,
    p.current_company,
    pp.role_id,
    r.title as role_title,
    pp.proof_strength,
    pp.role_fit_score,
    pp.proved_claims,
    pp.unproved_claims,
    pp.total_claims,
    pp.generated_at,
    COUNT(DISTINCT a.id) as artifact_count,
    COUNT(DISTINCT e.id) as evidence_count
FROM people p
LEFT JOIN proof_profiles pp ON p.id = pp.person_id
LEFT JOIN roles r ON pp.role_id = r.id
LEFT JOIN artifacts a ON p.id = a.person_id
LEFT JOIN evidence e ON p.id = e.person_id
GROUP BY p.id, p.full_name, p.current_title, p.current_company,
         pp.role_id, r.title, pp.proof_strength, pp.role_fit_score,
         pp.proved_claims, pp.unproved_claims, pp.total_claims, pp.generated_at;

-- View: Evidence by candidate
CREATE OR REPLACE VIEW evidence_by_candidate AS
SELECT
    e.person_id,
    p.full_name,
    e.type as evidence_type,
    COUNT(*) as evidence_count,
    AVG(e.confidence) as avg_confidence,
    jsonb_agg(
        jsonb_build_object(
            'id', e.id,
            'fact', e.fact,
            'confidence', e.confidence,
            'artifact_type', a.type
        )
    ) as evidence_items
FROM evidence e
JOIN people p ON e.person_id = p.id
JOIN artifacts a ON e.artifact_id = a.id
GROUP BY e.person_id, p.full_name, e.type;

-- View: Claims by candidate and role
CREATE OR REPLACE VIEW claims_by_candidate_role AS
SELECT
    c.person_id,
    p.full_name,
    c.role_id,
    r.title as role_title,
    c.type as claim_type,
    c.status,
    COUNT(*) as claim_count,
    AVG(c.confidence_score) as avg_confidence,
    AVG(c.relevance_to_role) as avg_relevance
FROM claims c
JOIN people p ON c.person_id = p.id
JOIN roles r ON c.role_id = r.id
GROUP BY c.person_id, p.full_name, c.role_id, r.title, c.type, c.status;
```

### 1.2 Migration Script

```bash
# Save the above SQL to a file
# Then run via Supabase CLI or dashboard

supabase db push

# Or via psql
psql $DATABASE_URL < migrations/add_proof_tables.sql
```

---

## 2. Seed Initial Artifacts from Existing Data

Your existing `people` table already has LinkedIn data. Let's create initial artifacts from it:

```python
# scripts/seed_initial_artifacts.py

import asyncio
from datetime import datetime
from app.core.database import get_supabase_client
from app.models.proof import Artifact, ArtifactType

async def seed_linkedin_artifacts():
    """
    Create LinkedIn profile artifacts for all existing people
    who have LinkedIn data.
    """

    supabase = get_supabase_client()

    # Get all people with LinkedIn URLs or data
    response = supabase.table('people').select('*').execute()
    people = response.data

    print(f"Found {len(people)} people in database")

    created_count = 0

    for person in people:
        # Check if we already have a LinkedIn artifact for this person
        existing = supabase.table('artifacts')\
            .select('id')\
            .eq('person_id', person['id'])\
            .eq('type', 'linkedin_profile')\
            .execute()

        if existing.data:
            print(f"  Skipping {person['full_name']} - artifact exists")
            continue

        # Build artifact from existing people data
        raw_data = {
            'full_name': person.get('full_name'),
            'headline': person.get('headline'),
            'location': person.get('location'),
            'current_company': person.get('current_company'),
            'current_title': person.get('current_title'),
            'linkedin_url': person.get('linkedin_url'),
            'skills': person.get('skills', []),
            'experience': person.get('experience', []),
            'education': person.get('education', []),
            'enrichment_data': person.get('enrichment_data', {})
        }

        # Create artifact
        artifact = {
            'person_id': person['id'],
            'type': 'linkedin_profile',
            'source_url': person.get('linkedin_url'),
            'raw_data': raw_data,
            'collected_at': person.get('created_at', datetime.now().isoformat()),
            'metadata': {
                'source': 'existing_people_table',
                'is_from_network': person.get('is_from_network', False)
            }
        }

        supabase.table('artifacts').insert(artifact).execute()
        created_count += 1
        print(f"  ✓ Created artifact for {person['full_name']}")

    print(f"\n✅ Created {created_count} LinkedIn artifacts")

if __name__ == "__main__":
    asyncio.run(seed_linkedin_artifacts())
```

Run this script to create initial artifacts:

```bash
python scripts/seed_initial_artifacts.py
```

---

## 3. Evidence Extraction Service

### 3.1 LinkedIn Evidence Extractor

```python
# app/services/evidence/linkedin_extractor.py

from typing import List
from datetime import datetime
from dateutil.relativedelta import relativedelta
from app.models.proof import Artifact, Evidence, EvidenceType
import uuid

class LinkedInEvidenceExtractor:
    """Extract evidence from LinkedIn profile artifacts."""

    async def extract(self, artifact: Artifact) -> List[Evidence]:
        """Extract all evidence from LinkedIn artifact."""

        if artifact.type != 'linkedin_profile':
            return []

        evidence = []
        profile_data = artifact.raw_data

        # Extract education evidence
        evidence.extend(self._extract_education(artifact, profile_data))

        # Extract experience evidence
        evidence.extend(self._extract_experience(artifact, profile_data))

        # Extract skills evidence (with caution - self-reported)
        evidence.extend(self._extract_skills(artifact, profile_data))

        return evidence

    def _extract_education(self, artifact: Artifact, profile: dict) -> List[Evidence]:
        """Extract education evidence."""
        evidence = []

        for edu in profile.get('education', []):
            if not edu:
                continue

            # Build fact statement
            school = edu.get('school', {})
            school_name = school.get('name') if isinstance(school, dict) else school
            degree = edu.get('degree')
            field = edu.get('field_of_study')
            end_year = edu.get('end_date', {}).get('year') if isinstance(edu.get('end_date'), dict) else edu.get('end_date')

            if school_name:
                fact_parts = []
                if degree:
                    fact_parts.append(degree)
                if field:
                    fact_parts.append(f"in {field}")
                fact_parts.append(f"from {school_name}")
                if end_year:
                    fact_parts.append(f"({end_year})")

                fact = " ".join(fact_parts)

                evidence.append(Evidence(
                    id=str(uuid.uuid4()),
                    person_id=artifact.person_id,
                    artifact_id=artifact.id,
                    type=EvidenceType.EDUCATION,
                    fact=fact,
                    confidence=0.9,  # LinkedIn is fairly reliable
                    extracted_at=datetime.now(),
                    structured_data={
                        'school': school_name,
                        'degree': degree,
                        'field': field,
                        'end_year': end_year,
                        'grade': edu.get('grade'),
                        'activities': edu.get('activities')
                    }
                ))

        return evidence

    def _extract_experience(self, artifact: Artifact, profile: dict) -> List[Evidence]:
        """Extract work experience evidence."""
        evidence = []

        experiences = profile.get('experience', [])
        if not experiences:
            return evidence

        # Job tenure for each position
        for exp in experiences:
            if not exp:
                continue

            company = exp.get('company', '')
            title = exp.get('title', '')
            start_date = exp.get('start_date')
            end_date = exp.get('end_date')

            if not (company and title):
                continue

            # Calculate tenure
            tenure_months = self._calculate_tenure_months(start_date, end_date)
            is_current = end_date is None or end_date == 'Present'

            # Build fact
            date_range = self._format_date_range(start_date, end_date)
            fact = f"{title} at {company}"
            if tenure_months:
                fact += f" for {tenure_months} months"
            if date_range:
                fact += f" ({date_range})"

            evidence.append(Evidence(
                id=str(uuid.uuid4()),
                person_id=artifact.person_id,
                artifact_id=artifact.id,
                type=EvidenceType.JOB_TENURE,
                fact=fact,
                confidence=0.9,
                extracted_at=datetime.now(),
                structured_data={
                    'company': company,
                    'title': title,
                    'start_date': start_date,
                    'end_date': end_date,
                    'tenure_months': tenure_months,
                    'is_current': is_current,
                    'description': exp.get('description'),
                    'location': exp.get('location')
                }
            ))

        # Title progression (if multiple roles)
        if len(experiences) > 1:
            titles = [exp.get('title', '') for exp in experiences if exp.get('title')]
            companies = [exp.get('company', '') for exp in experiences if exp.get('company')]

            progression_fact = f"Career progression: {' → '.join(titles[:5])}"  # First 5

            evidence.append(Evidence(
                id=str(uuid.uuid4()),
                person_id=artifact.person_id,
                artifact_id=artifact.id,
                type=EvidenceType.TITLE_PROGRESSION,
                fact=progression_fact,
                confidence=0.9,
                extracted_at=datetime.now(),
                structured_data={
                    'titles': titles,
                    'companies': companies,
                    'total_positions': len(experiences),
                    'shows_growth': self._analyze_progression(titles)
                }
            ))

        return evidence

    def _extract_skills(self, artifact: Artifact, profile: dict) -> List[Evidence]:
        """Extract skills evidence (low confidence - self-reported)."""
        evidence = []

        skills = profile.get('skills', [])
        if not skills:
            return evidence

        # If skills is a list of dicts
        if skills and isinstance(skills[0], dict):
            for skill in skills[:20]:  # Top 20
                skill_name = skill.get('name')
                endorsements = skill.get('endorsements', 0)

                if skill_name:
                    fact = f"Lists '{skill_name}' as skill"
                    if endorsements:
                        fact += f" ({endorsements} endorsements)"

                    # Higher confidence if endorsed by others
                    confidence = 0.4 if endorsements == 0 else min(0.7, 0.4 + (endorsements * 0.02))

                    evidence.append(Evidence(
                        id=str(uuid.uuid4()),
                        person_id=artifact.person_id,
                        artifact_id=artifact.id,
                        type=EvidenceType.SKILL_ENDORSEMENTS,
                        fact=fact,
                        confidence=confidence,
                        extracted_at=datetime.now(),
                        structured_data={
                            'skill': skill_name,
                            'endorsements': endorsements,
                            'needs_verification': True,
                            'category': skill.get('category')
                        }
                    ))

        # If skills is a simple list
        elif skills and isinstance(skills[0], str):
            for skill_name in skills[:20]:
                evidence.append(Evidence(
                    id=str(uuid.uuid4()),
                    person_id=artifact.person_id,
                    artifact_id=artifact.id,
                    type=EvidenceType.SKILL_ENDORSEMENTS,
                    fact=f"Lists '{skill_name}' as skill",
                    confidence=0.3,  # Low - no endorsement info
                    extracted_at=datetime.now(),
                    structured_data={
                        'skill': skill_name,
                        'endorsements': 0,
                        'needs_verification': True
                    }
                ))

        return evidence

    def _calculate_tenure_months(self, start_date, end_date) -> int:
        """Calculate tenure in months."""
        try:
            if not start_date:
                return 0

            # Parse start date
            if isinstance(start_date, dict):
                start_year = start_date.get('year')
                start_month = start_date.get('month', 1)
            elif isinstance(start_date, str):
                parts = start_date.split('-')
                start_year = int(parts[0]) if parts else None
                start_month = int(parts[1]) if len(parts) > 1 else 1
            else:
                return 0

            if not start_year:
                return 0

            start = datetime(start_year, start_month, 1)

            # Parse end date
            if end_date is None or end_date == 'Present':
                end = datetime.now()
            elif isinstance(end_date, dict):
                end_year = end_date.get('year')
                end_month = end_date.get('month', 12)
                if not end_year:
                    end = datetime.now()
                else:
                    end = datetime(end_year, end_month, 1)
            elif isinstance(end_date, str):
                parts = end_date.split('-')
                end_year = int(parts[0]) if parts else None
                end_month = int(parts[1]) if len(parts) > 1 else 12
                if not end_year:
                    end = datetime.now()
                else:
                    end = datetime(end_year, end_month, 1)
            else:
                end = datetime.now()

            delta = relativedelta(end, start)
            return delta.years * 12 + delta.months

        except Exception as e:
            print(f"Error calculating tenure: {e}")
            return 0

    def _format_date_range(self, start_date, end_date) -> str:
        """Format date range for display."""
        try:
            # Format start
            if isinstance(start_date, dict):
                start_str = f"{start_date.get('month', '')}/{start_date.get('year', '')}"
            elif isinstance(start_date, str):
                start_str = start_date
            else:
                start_str = ""

            # Format end
            if end_date is None or end_date == 'Present':
                end_str = "Present"
            elif isinstance(end_date, dict):
                end_str = f"{end_date.get('month', '')}/{end_date.get('year', '')}"
            elif isinstance(end_date, str):
                end_str = end_date
            else:
                end_str = "Present"

            return f"{start_str} - {end_str}" if start_str else ""

        except Exception:
            return ""

    def _analyze_progression(self, titles: List[str]) -> bool:
        """Analyze if titles show career growth."""
        # Simple heuristic: look for seniority keywords
        seniority_keywords = ['senior', 'lead', 'principal', 'staff', 'head', 'director', 'vp', 'chief']

        # Check if later titles have more seniority keywords
        early_titles = ' '.join(titles[:len(titles)//2]).lower()
        later_titles = ' '.join(titles[len(titles)//2:]).lower()

        early_seniority = sum(1 for kw in seniority_keywords if kw in early_titles)
        later_seniority = sum(1 for kw in seniority_keywords if kw in later_titles)

        return later_seniority > early_seniority
```

### 3.2 Extract Evidence from All Existing Artifacts

```python
# scripts/extract_all_evidence.py

import asyncio
from app.core.database import get_supabase_client
from app.services.evidence.linkedin_extractor import LinkedInEvidenceExtractor

async def extract_evidence_from_artifacts():
    """Extract evidence from all existing artifacts."""

    supabase = get_supabase_client()
    extractor = LinkedInEvidenceExtractor()

    # Get all artifacts
    response = supabase.table('artifacts').select('*').execute()
    artifacts = response.data

    print(f"Found {len(artifacts)} artifacts")

    total_evidence = 0

    for artifact_data in artifacts:
        print(f"\nProcessing artifact {artifact_data['id']} for person {artifact_data['person_id']}")

        # Check if evidence already extracted
        existing = supabase.table('evidence')\
            .select('id')\
            .eq('artifact_id', artifact_data['id'])\
            .execute()

        if existing.data:
            print(f"  Skipping - {len(existing.data)} evidence items already exist")
            continue

        # Convert to Artifact model
        artifact = Artifact(**artifact_data)

        # Extract evidence
        evidence_list = await extractor.extract(artifact)

        print(f"  Extracted {len(evidence_list)} evidence items")

        # Insert evidence
        for evidence in evidence_list:
            evidence_dict = evidence.dict()
            supabase.table('evidence').insert(evidence_dict).execute()
            total_evidence += 1

        print(f"  ✓ Inserted {len(evidence_list)} evidence items")

    print(f"\n✅ Total evidence extracted: {total_evidence}")

if __name__ == "__main__":
    asyncio.run(extract_evidence_from_artifacts())
```

Run to extract evidence:

```bash
python scripts/extract_all_evidence.py
```

---

## 4. API Endpoints

### 4.1 FastAPI Routes

```python
# app/api/routes/proof.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.database import get_supabase_client
from app.models.proof import (
    CandidateProofProfile,
    Artifact,
    Evidence,
    Claim
)
from app.services.proof_engine import ProofEngine

router = APIRouter(prefix="/api/v1/proof", tags=["proof-search"])

@router.post("/search")
async def proof_directed_search(
    role_id: str,
    limit: int = 20,
    min_proof_strength: float = 0.3
):
    """
    Search for candidates with proof-directed evaluation.

    This runs proof evaluation for all candidates in the network
    and returns those with sufficient proof strength.
    """

    supabase = get_supabase_client()

    # Get role details
    role_response = supabase.table('roles').select('*').eq('id', role_id).single().execute()
    if not role_response.data:
        raise HTTPException(status_code=404, detail="Role not found")

    role = role_response.data
    company_id = role['company_id']

    # Get all people in the network for this company
    people_response = supabase.table('people')\
        .select('*')\
        .eq('company_id', company_id)\
        .execute()

    people = people_response.data

    # Get or generate proof profiles
    proof_engine = ProofEngine(supabase)
    proof_profiles = []

    for person in people:
        # Check if proof profile exists and is fresh
        profile = await proof_engine.get_or_generate_proof_profile(
            person_id=person['id'],
            role_id=role_id
        )

        if profile and profile['proof_strength'] >= min_proof_strength:
            proof_profiles.append(profile)

    # Sort by role fit score
    proof_profiles.sort(
        key=lambda p: (
            0.5 * p['role_fit_score'] +
            0.3 * p['proof_strength'] +
            0.2 * (p['proved_claims'] / max(p['total_claims'], 1))
        ),
        reverse=True
    )

    return {
        'candidates': proof_profiles[:limit],
        'total_evaluated': len(people),
        'passed_threshold': len(proof_profiles),
        'avg_proof_strength': sum(p['proof_strength'] for p in proof_profiles) / len(proof_profiles) if proof_profiles else 0
    }

@router.get("/candidate/{person_id}/proof")
async def get_candidate_proof(
    person_id: str,
    role_id: str
):
    """Get detailed proof profile for a candidate."""

    supabase = get_supabase_client()
    proof_engine = ProofEngine(supabase)

    profile = await proof_engine.get_or_generate_proof_profile(
        person_id=person_id,
        role_id=role_id
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Proof profile not found")

    return profile

@router.get("/candidate/{person_id}/evidence")
async def get_candidate_evidence(person_id: str):
    """Get all evidence for a candidate."""

    supabase = get_supabase_client()

    response = supabase.table('evidence')\
        .select('*, artifacts(type, source_url)')\
        .eq('person_id', person_id)\
        .order('confidence', desc=True)\
        .execute()

    return {'evidence': response.data}

@router.get("/candidate/{person_id}/claims")
async def get_candidate_claims(
    person_id: str,
    role_id: str,
    status: str = None
):
    """Get all claims for a candidate for a specific role."""

    supabase = get_supabase_client()

    query = supabase.table('claims')\
        .select('*')\
        .eq('person_id', person_id)\
        .eq('role_id', role_id)

    if status:
        query = query.eq('status', status)

    response = query.order('relevance_to_role', desc=True).execute()

    return {'claims': response.data}

@router.post("/candidate/{person_id}/refresh-proof")
async def refresh_proof_profile(
    person_id: str,
    role_id: str
):
    """
    Force refresh of proof profile.
    Re-extracts evidence and regenerates claims.
    """

    supabase = get_supabase_client()
    proof_engine = ProofEngine(supabase)

    # Delete existing proof profile
    supabase.table('proof_profiles')\
        .delete()\
        .eq('person_id', person_id)\
        .eq('role_id', role_id)\
        .execute()

    # Regenerate
    profile = await proof_engine.generate_proof_profile(
        person_id=person_id,
        role_id=role_id
    )

    return profile
```

---

## 5. Proof Engine Implementation

```python
# app/services/proof_engine.py

from typing import Optional, Dict, List
from datetime import datetime, timedelta
from app.services.evidence.linkedin_extractor import LinkedInEvidenceExtractor
from app.services.claim_generator import ClaimGenerator

class ProofEngine:
    """Core engine for proof-directed evaluation."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.linkedin_extractor = LinkedInEvidenceExtractor()
        self.claim_generator = ClaimGenerator()

    async def get_or_generate_proof_profile(
        self,
        person_id: str,
        role_id: str,
        cache_ttl_hours: int = 24
    ) -> Optional[Dict]:
        """
        Get existing proof profile or generate new one.
        Uses caching to avoid expensive regeneration.
        """

        # Check for existing profile
        response = self.supabase.table('proof_profiles')\
            .select('*')\
            .eq('person_id', person_id)\
            .eq('role_id', role_id)\
            .single()\
            .execute()

        if response.data:
            profile = response.data
            generated_at = datetime.fromisoformat(profile['generated_at'])

            # Check if cache is still fresh
            if datetime.now() - generated_at < timedelta(hours=cache_ttl_hours):
                return profile

        # Generate new profile
        return await self.generate_proof_profile(person_id, role_id)

    async def generate_proof_profile(
        self,
        person_id: str,
        role_id: str
    ) -> Dict:
        """
        Generate complete proof profile for a candidate.

        Steps:
        1. Get artifacts
        2. Get/extract evidence
        3. Generate claims
        4. Compute statistics
        5. Cache result
        """

        # Step 1: Get artifacts
        artifacts_response = self.supabase.table('artifacts')\
            .select('*')\
            .eq('person_id', person_id)\
            .execute()

        artifacts = artifacts_response.data

        # Step 2: Get evidence (or extract if missing)
        evidence_response = self.supabase.table('evidence')\
            .select('*')\
            .eq('person_id', person_id)\
            .execute()

        evidence = evidence_response.data

        # If no evidence but we have artifacts, extract it
        if not evidence and artifacts:
            for artifact_data in artifacts:
                if artifact_data['type'] == 'linkedin_profile':
                    from app.models.proof import Artifact
                    artifact = Artifact(**artifact_data)
                    extracted = await self.linkedin_extractor.extract(artifact)

                    # Insert evidence
                    for ev in extracted:
                        self.supabase.table('evidence').insert(ev.dict()).execute()

                    evidence.extend([ev.dict() for ev in extracted])

        # Step 3: Generate claims
        role_response = self.supabase.table('roles')\
            .select('*')\
            .eq('id', role_id)\
            .single()\
            .execute()

        role = role_response.data

        claims = await self.claim_generator.generate_claims(
            person_id=person_id,
            role_id=role_id,
            role=role,
            evidence=evidence
        )

        # Insert claims
        for claim in claims:
            self.supabase.table('claims').insert(claim).execute()

        # Step 4: Compute statistics
        proved_claims = [c for c in claims if c['status'] == 'proved']
        unproved_claims = [c for c in claims if c['status'] == 'unproved']

        proof_strength = len(proved_claims) / len(claims) if claims else 0.0

        # Role fit = weighted average of proved claim relevance
        if proved_claims:
            role_fit_score = sum(
                c['confidence_score'] * c['relevance_to_role']
                for c in proved_claims
            ) / sum(c['relevance_to_role'] for c in proved_claims)
        else:
            role_fit_score = 0.0

        # Get person details
        person_response = self.supabase.table('people')\
            .select('*')\
            .eq('id', person_id)\
            .single()\
            .execute()

        person = person_response.data

        # Build top strengths
        top_strengths = []
        for claim in sorted(proved_claims, key=lambda c: c['confidence_score'] * c['relevance_to_role'], reverse=True)[:5]:
            # Get evidence for this claim
            claim_evidence = self.supabase.table('claim_evidence')\
                .select('evidence_id')\
                .eq('claim_id', claim['id'])\
                .execute()

            evidence_ids = [ce['evidence_id'] for ce in claim_evidence.data]

            top_strengths.append({
                'claim': claim['statement'],
                'proof': claim['proof_summary'],
                'confidence': claim['confidence_score'],
                'evidence_count': len(evidence_ids)
            })

        # Critical unknowns
        critical_unknowns = [
            c['statement']
            for c in unproved_claims
            if c['relevance_to_role'] > 0.7
        ][:5]

        # Interview questions
        interview_questions = []
        for claim in unproved_claims:
            if claim['relevance_to_role'] > 0.7:
                interview_questions.extend(claim.get('follow_up_questions', []))
        interview_questions = interview_questions[:10]

        # Step 5: Cache result
        profile = {
            'person_id': person_id,
            'role_id': role_id,
            'total_artifacts': len(artifacts),
            'total_evidence': len(evidence),
            'total_claims': len(claims),
            'proved_claims': len(proved_claims),
            'unproved_claims': len(unproved_claims),
            'proof_strength': proof_strength,
            'role_fit_score': role_fit_score,
            'critical_unknowns': critical_unknowns,
            'interview_questions': interview_questions,
            'top_strengths': top_strengths,
            'generated_at': datetime.now().isoformat()
        }

        # Upsert proof profile
        self.supabase.table('proof_profiles')\
            .upsert(profile, on_conflict='person_id,role_id')\
            .execute()

        # Add person details
        profile['person_name'] = person['full_name']
        profile['current_title'] = person.get('current_title')
        profile['current_company'] = person.get('current_company')

        return profile
```

---

## 6. Quick Start

### Step 1: Run Migrations

```bash
# Apply database migrations
python scripts/run_migrations.py
```

### Step 2: Seed Artifacts

```bash
# Create LinkedIn artifacts from existing people data
python scripts/seed_initial_artifacts.py
```

### Step 3: Extract Evidence

```bash
# Extract evidence from all artifacts
python scripts/extract_all_evidence.py
```

### Step 4: Test API

```bash
# Start FastAPI server
uvicorn app.main:app --reload --port 8001

# Test proof search endpoint
curl -X POST "http://localhost:8001/api/v1/proof/search" \
  -H "Content-Type: application/json" \
  -d '{
    "role_id": "YOUR_ROLE_ID",
    "limit": 10,
    "min_proof_strength": 0.3
  }'
```

---

## 7. Integration with Existing Search

Update your existing search endpoint to include proof profiles:

```python
# app/api/routes/search.py

@router.post("/v2/search")
async def tiered_search(request: SearchRequest):
    """Enhanced search with proof profiles."""

    # Run existing tiered search
    candidates = await run_tiered_search(request)

    # Enrich with proof profiles
    proof_engine = ProofEngine(get_supabase_client())

    for candidate in candidates:
        proof_profile = await proof_engine.get_or_generate_proof_profile(
            person_id=candidate['id'],
            role_id=request.role_id
        )

        candidate['proof_profile'] = proof_profile

    return candidates
```

---

## 8. Next Steps

1. **Add GitHub Integration**: Implement GitHubExtractor to pull repo data
2. **Add Resume Parsing**: Extract evidence from uploaded resumes
3. **Claim Generation with LLM**: Use Claude to generate smarter claims
4. **Frontend Components**: Build UI to display proof chains
5. **Interview Mode**: Add ability to manually verify claims post-interview

---

This implementation works with your existing Supabase database and LinkedIn connections data, progressively enhancing candidates with proof-directed evaluation.
