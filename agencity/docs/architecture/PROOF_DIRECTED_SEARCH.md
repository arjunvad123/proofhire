# Candidate Data Aggregation System

## Overview

A simple data aggregation system that pulls together all available information about candidates from multiple sources (LinkedIn, GitHub, DevPost, etc.) into a unified profile. Founders can quickly see the complete picture of who this person is without jumping between platforms.

**Core Principle:** Aggregate, normalize, and present. No complex scoring or evaluation - just give founders all the data in one place.

---

## 1. Simple Architecture

### 1.1 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                             │
│  LinkedIn | GitHub | DevPost | Portfolio | Resume           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├─> Fetch & Store
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    RAW DATA STORE                           │
│  Store original API responses/scraped data                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├─> Normalize & Merge
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                 UNIFIED PROFILE                             │
│  Single view with all candidate data                        │
│  Education | Experience | Projects | Activity               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Data Models

```python
# Core Models
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any

class DataSourceType(str, Enum):
    LINKEDIN = "linkedin"
    GITHUB = "github"
    DEVPOST = "devpost"
    PORTFOLIO = "portfolio"
    RESUME = "resume"
    TWITTER = "twitter"
    PERSONAL_SITE = "personal_site"

class DataSource(BaseModel):
    """A candidate's profile on a specific platform."""
    id: str
    person_id: str
    source_type: DataSourceType
    profile_url: str
    username: Optional[str]
    raw_data: dict  # Original API response or scraped data
    last_fetched: datetime
    is_verified: bool = False  # Did we successfully fetch data?
    fetch_error: Optional[str] = None

class EvidenceType(str, Enum):
    # GitHub Evidence
    COMMIT_PATTERN = "commit_pattern"
    CODE_REVIEW_ACTIVITY = "code_review_activity"
    LANGUAGE_USAGE = "language_usage"
    TEST_COVERAGE = "test_coverage"
    OPEN_SOURCE_CONTRIBUTION = "open_source_contribution"

    # LinkedIn Evidence
    JOB_TENURE = "job_tenure"
    TITLE_PROGRESSION = "title_progression"
    COMPANY_HISTORY = "company_history"
    SKILL_ENDORSEMENTS = "skill_endorsements"
    RECOMMENDATIONS = "recommendations"

    # Resume Evidence
    EDUCATION = "education"
    CERTIFICATION = "certification"
    PROJECT_DESCRIPTION = "project_description"

    # Portfolio Evidence
    PROJECT_COMPLEXITY = "project_complexity"
    DOCUMENTATION_QUALITY = "documentation_quality"
    DEPLOYMENT_STATUS = "deployment_status"

    # Interview Evidence
    COMMUNICATION_CLARITY = "communication_clarity"
    TECHNICAL_DEPTH = "technical_depth"
    PROBLEM_SOLVING = "problem_solving"

class Evidence(BaseModel):
    """Structured fact extracted from artifact."""
    id: str
    candidate_id: str
    artifact_id: str  # Links back to source
    type: EvidenceType
    fact: str  # Human-readable statement
    confidence: float  # 0.0-1.0, how certain we are this is true
    extracted_at: datetime
    structured_data: dict  # Machine-readable version

    # Examples:
    # fact = "15 commits to llm-router repo between Oct 1-31, 2024"
    # structured_data = {
    #     "repo": "llm-router",
    #     "commit_count": 15,
    #     "date_range": ["2024-10-01", "2024-10-31"],
    #     "languages": ["python", "typescript"]
    # }

class ClaimType(str, Enum):
    # Technical Skills
    TECHNICAL_SKILL = "technical_skill"
    FRAMEWORK_EXPERIENCE = "framework_experience"
    SYSTEM_DESIGN = "system_design"
    CODE_QUALITY = "code_quality"

    # Work Experience
    ROLE_EXPERIENCE = "role_experience"
    INDUSTRY_KNOWLEDGE = "industry_knowledge"
    TEAM_COLLABORATION = "team_collaboration"
    LEADERSHIP = "leadership"

    # Education & Learning
    FORMAL_EDUCATION = "formal_education"
    SELF_DIRECTED_LEARNING = "self_directed_learning"

    # Soft Skills
    COMMUNICATION = "communication"
    PROBLEM_SOLVING = "problem_solving"
    SHIPPING_SPEED = "shipping_speed"

class ProofStatus(str, Enum):
    PROVED = "proved"              # Strong evidence supports this
    UNPROVED = "unproved"          # No evidence found
    CONTRADICTED = "contradicted"  # Evidence contradicts this
    PARTIAL = "partial"            # Some evidence, but incomplete

class Claim(BaseModel):
    """Hypothesis about candidate capability."""
    id: str
    candidate_id: str
    type: ClaimType
    statement: str  # Human-readable claim
    status: ProofStatus
    evidence_ids: list[str]  # Supporting evidence
    confidence_score: float  # 0.0-1.0, based on evidence strength
    relevance_to_role: float  # 0.0-1.0, how relevant to current search
    created_at: datetime

    # For UNPROVED claims
    follow_up_questions: list[str] = []

    # For PROVED claims
    proof_summary: str | None = None  # Brief explanation of proof

    # Example:
    # statement = "Has experience building production LLM API integrations"
    # status = PROVED
    # evidence_ids = ["ev_123", "ev_456"]
    # proof_summary = "Built llm-router (500+ commits), deployed to prod, handles 10k+ daily requests"
    # confidence_score = 0.85

class CandidateProofProfile(BaseModel):
    """Complete proof-based profile for a candidate."""
    candidate_id: str

    # Core identity (always proved from artifacts)
    name: str
    current_title: str | None
    current_company: str | None
    location: str | None

    # Proof summary
    total_artifacts: int
    total_evidence: int
    total_claims: int
    proved_claims: int
    unproved_claims: int

    # Organized by category
    claims_by_type: dict[ClaimType, list[Claim]]

    # What we need to verify
    critical_unknowns: list[str]  # High-priority unproved claims
    interview_questions: list[str]  # Generated from unproved claims

    # Overall assessment
    proof_strength: float  # 0.0-1.0, % of relevant claims that are proved
    role_fit_score: float  # 0.0-1.0, based on proved claims vs. blueprint

    generated_at: datetime
```

---

## 2. Evidence Extraction Pipeline

### 2.1 Source-Specific Extractors

```python
class EvidenceExtractor(ABC):
    """Base class for source-specific extractors."""

    @abstractmethod
    async def extract(self, artifact: Artifact) -> list[Evidence]:
        """Extract evidence from artifact."""
        pass

class GitHubExtractor(EvidenceExtractor):
    """Extract evidence from GitHub artifacts."""

    async def extract(self, artifact: Artifact) -> list[Evidence]:
        evidence = []

        if artifact.type == ArtifactType.GITHUB_REPO:
            evidence.extend(await self._extract_repo_evidence(artifact))
        elif artifact.type == ArtifactType.GITHUB_COMMIT:
            evidence.extend(await self._extract_commit_evidence(artifact))
        elif artifact.type == ArtifactType.GITHUB_PR:
            evidence.extend(await self._extract_pr_evidence(artifact))

        return evidence

    async def _extract_repo_evidence(self, artifact: Artifact) -> list[Evidence]:
        """Extract evidence from repository data."""
        repo_data = artifact.raw_data
        evidence = []

        # Language distribution
        if "languages" in repo_data:
            for lang, bytes_count in repo_data["languages"].items():
                evidence.append(Evidence(
                    id=generate_id(),
                    candidate_id=artifact.candidate_id,
                    artifact_id=artifact.id,
                    type=EvidenceType.LANGUAGE_USAGE,
                    fact=f"Wrote {bytes_count:,} bytes of {lang} in {repo_data['name']}",
                    confidence=1.0,  # Direct from GitHub
                    extracted_at=datetime.now(),
                    structured_data={
                        "language": lang,
                        "bytes": bytes_count,
                        "repo": repo_data["name"],
                        "repo_url": repo_data["html_url"]
                    }
                ))

        # Commit activity
        if "commit_count" in repo_data:
            evidence.append(Evidence(
                id=generate_id(),
                candidate_id=artifact.candidate_id,
                artifact_id=artifact.id,
                type=EvidenceType.COMMIT_PATTERN,
                fact=f"{repo_data['commit_count']} commits to {repo_data['name']} over {repo_data['active_months']} months",
                confidence=1.0,
                extracted_at=datetime.now(),
                structured_data={
                    "commit_count": repo_data["commit_count"],
                    "active_months": repo_data["active_months"],
                    "repo": repo_data["name"],
                    "date_range": [repo_data["first_commit"], repo_data["last_commit"]]
                }
            ))

        # Test coverage (if available)
        if "has_tests" in repo_data and repo_data["has_tests"]:
            test_dirs = repo_data.get("test_directories", [])
            evidence.append(Evidence(
                id=generate_id(),
                candidate_id=artifact.candidate_id,
                artifact_id=artifact.id,
                type=EvidenceType.TEST_COVERAGE,
                fact=f"Repository {repo_data['name']} includes test directories: {', '.join(test_dirs)}",
                confidence=0.9,  # Can see test dirs, but not coverage %
                extracted_at=datetime.now(),
                structured_data={
                    "repo": repo_data["name"],
                    "test_directories": test_dirs,
                    "has_ci": repo_data.get("has_ci", False)
                }
            ))

        # Code review activity
        if "pull_requests_reviewed" in repo_data:
            evidence.append(Evidence(
                id=generate_id(),
                candidate_id=artifact.candidate_id,
                artifact_id=artifact.id,
                type=EvidenceType.CODE_REVIEW_ACTIVITY,
                fact=f"Reviewed {repo_data['pull_requests_reviewed']} pull requests in {repo_data['name']}",
                confidence=1.0,
                extracted_at=datetime.now(),
                structured_data={
                    "pr_count": repo_data["pull_requests_reviewed"],
                    "repo": repo_data["name"],
                    "review_quality_indicators": repo_data.get("review_comments", 0)
                }
            ))

        return evidence

    async def _extract_commit_evidence(self, artifact: Artifact) -> list[Evidence]:
        """Extract evidence from commit history."""
        # Pattern analysis: consistency, time of day, commit messages
        pass

    async def _extract_pr_evidence(self, artifact: Artifact) -> list[Evidence]:
        """Extract evidence from PR activity."""
        # Review quality, discussion depth, merge rate
        pass

class LinkedInExtractor(EvidenceExtractor):
    """Extract evidence from LinkedIn artifacts."""

    async def extract(self, artifact: Artifact) -> list[Evidence]:
        evidence = []

        if artifact.type == ArtifactType.LINKEDIN_PROFILE:
            profile_data = artifact.raw_data

            # Job tenure
            if "experience" in profile_data:
                for exp in profile_data["experience"]:
                    tenure_months = self._calculate_tenure(
                        exp["start_date"],
                        exp.get("end_date")
                    )

                    evidence.append(Evidence(
                        id=generate_id(),
                        candidate_id=artifact.candidate_id,
                        artifact_id=artifact.id,
                        type=EvidenceType.JOB_TENURE,
                        fact=f"{exp['title']} at {exp['company']} for {tenure_months} months ({exp['start_date']} - {exp.get('end_date', 'Present')})",
                        confidence=1.0,
                        extracted_at=datetime.now(),
                        structured_data={
                            "title": exp["title"],
                            "company": exp["company"],
                            "tenure_months": tenure_months,
                            "is_current": exp.get("end_date") is None,
                            "description": exp.get("description")
                        }
                    ))

            # Title progression
            if len(profile_data.get("experience", [])) > 1:
                titles = [exp["title"] for exp in profile_data["experience"]]
                evidence.append(Evidence(
                    id=generate_id(),
                    candidate_id=artifact.candidate_id,
                    artifact_id=artifact.id,
                    type=EvidenceType.TITLE_PROGRESSION,
                    fact=f"Career progression: {' → '.join(titles)}",
                    confidence=1.0,
                    extracted_at=datetime.now(),
                    structured_data={
                        "titles": titles,
                        "total_roles": len(titles),
                        "shows_growth": self._analyze_progression(titles)
                    }
                ))

            # Skills (treat with lower confidence - self-reported)
            if "skills" in profile_data:
                for skill in profile_data["skills"]:
                    evidence.append(Evidence(
                        id=generate_id(),
                        candidate_id=artifact.candidate_id,
                        artifact_id=artifact.id,
                        type=EvidenceType.SKILL_ENDORSEMENTS,
                        fact=f"Lists '{skill['name']}' as skill ({skill.get('endorsements', 0)} endorsements)",
                        confidence=0.5,  # Self-reported, needs verification
                        extracted_at=datetime.now(),
                        structured_data={
                            "skill": skill["name"],
                            "endorsements": skill.get("endorsements", 0),
                            "needs_verification": True
                        }
                    ))

        return evidence

class ResumeExtractor(EvidenceExtractor):
    """Extract evidence from resume/CV."""

    async def extract(self, artifact: Artifact) -> list[Evidence]:
        evidence = []
        resume_data = artifact.raw_data

        # Education (high confidence if from verified source)
        if "education" in resume_data:
            for edu in resume_data["education"]:
                evidence.append(Evidence(
                    id=generate_id(),
                    candidate_id=artifact.candidate_id,
                    artifact_id=artifact.id,
                    type=EvidenceType.EDUCATION,
                    fact=f"{edu['degree']} in {edu['field']} from {edu['school']} ({edu['year']})",
                    confidence=0.7,  # Self-reported, should verify with LinkedIn
                    extracted_at=datetime.now(),
                    structured_data=edu
                ))

        # Certifications
        if "certifications" in resume_data:
            for cert in resume_data["certifications"]:
                evidence.append(Evidence(
                    id=generate_id(),
                    candidate_id=artifact.candidate_id,
                    artifact_id=artifact.id,
                    type=EvidenceType.CERTIFICATION,
                    fact=f"Certified: {cert['name']} from {cert['issuer']} ({cert.get('date')})",
                    confidence=0.8 if cert.get("verification_url") else 0.5,
                    extracted_at=datetime.now(),
                    structured_data=cert
                ))

        # Projects (needs GitHub verification)
        if "projects" in resume_data:
            for project in resume_data["projects"]:
                evidence.append(Evidence(
                    id=generate_id(),
                    candidate_id=artifact.candidate_id,
                    artifact_id=artifact.id,
                    type=EvidenceType.PROJECT_DESCRIPTION,
                    fact=f"Claims project: {project['name']} - {project['description']}",
                    confidence=0.3,  # Low until we verify with GitHub
                    extracted_at=datetime.now(),
                    structured_data={
                        **project,
                        "needs_github_verification": True
                    }
                ))

        return evidence

class PortfolioExtractor(EvidenceExtractor):
    """Extract evidence from portfolio websites."""

    async def extract(self, artifact: Artifact) -> list[Evidence]:
        evidence = []
        portfolio_data = artifact.raw_data

        # Project complexity analysis
        for project in portfolio_data.get("projects", []):
            complexity_score = await self._analyze_complexity(project)

            evidence.append(Evidence(
                id=generate_id(),
                candidate_id=artifact.candidate_id,
                artifact_id=artifact.id,
                type=EvidenceType.PROJECT_COMPLEXITY,
                fact=f"Portfolio project '{project['name']}' shows {complexity_score['description']}",
                confidence=0.6,  # Visual analysis, not code inspection
                extracted_at=datetime.now(),
                structured_data={
                    "project_name": project["name"],
                    "complexity_factors": complexity_score["factors"],
                    "tech_stack": project.get("tech_stack", []),
                    "live_url": project.get("url")
                }
            ))

            # Documentation quality
            if "documentation_score" in project:
                evidence.append(Evidence(
                    id=generate_id(),
                    candidate_id=artifact.candidate_id,
                    artifact_id=artifact.id,
                    type=EvidenceType.DOCUMENTATION_QUALITY,
                    fact=f"Project '{project['name']}' has {project['documentation_score']}/10 documentation quality",
                    confidence=0.7,
                    extracted_at=datetime.now(),
                    structured_data={
                        "project": project["name"],
                        "has_readme": project.get("has_readme", False),
                        "has_comments": project.get("has_comments", False),
                        "has_api_docs": project.get("has_api_docs", False)
                    }
                ))

        return evidence

    async def _analyze_complexity(self, project: dict) -> dict:
        """Analyze project complexity from portfolio data."""
        # Use LLM to assess based on description, screenshots, tech stack
        pass
```

### 2.2 Evidence Aggregation & Deduplication

```python
class EvidenceAggregator:
    """Aggregate and deduplicate evidence from multiple sources."""

    async def aggregate(
        self,
        candidate_id: str,
        new_evidence: list[Evidence]
    ) -> list[Evidence]:
        """
        Combine new evidence with existing, handling:
        1. Cross-source verification (LinkedIn + GitHub agree)
        2. Contradiction detection (Resume says X, GitHub shows Y)
        3. Confidence boosting (same fact from multiple sources)
        """

        existing = await self.get_existing_evidence(candidate_id)

        # Group by evidence type
        evidence_map: dict[EvidenceType, list[Evidence]] = defaultdict(list)
        for ev in existing + new_evidence:
            evidence_map[ev.type].append(ev)

        aggregated = []

        for ev_type, evidence_list in evidence_map.items():
            if len(evidence_list) == 1:
                # Single source, keep as-is
                aggregated.append(evidence_list[0])
            else:
                # Multiple sources, verify or merge
                merged = await self._merge_evidence(evidence_list)
                aggregated.extend(merged)

        return aggregated

    async def _merge_evidence(self, evidence_list: list[Evidence]) -> list[Evidence]:
        """
        Merge evidence from multiple sources.

        Example:
        - Resume says: "Python expert"
        - GitHub shows: 50,000 lines of Python across 10 repos
        → Boost confidence, link both artifacts
        """

        # Check for agreement vs. contradiction
        if self._sources_agree(evidence_list):
            # Boost confidence, create merged evidence
            return [self._create_verified_evidence(evidence_list)]
        else:
            # Flag contradiction, keep all for review
            for ev in evidence_list:
                ev.metadata["contradiction_detected"] = True
            return evidence_list

    def _sources_agree(self, evidence_list: list[Evidence]) -> bool:
        """Check if evidence from different sources agrees."""
        # Use semantic similarity on facts
        # Use structured_data comparison
        pass

    def _create_verified_evidence(self, evidence_list: list[Evidence]) -> Evidence:
        """Create new evidence with boosted confidence from multiple sources."""
        primary = evidence_list[0]

        # Calculate boosted confidence
        # confidence = 1 - (1 - c1) * (1 - c2) * ... for independent sources
        confidence = 1.0
        for ev in evidence_list:
            confidence *= (1 - ev.confidence)
        confidence = 1 - confidence

        return Evidence(
            id=generate_id(),
            candidate_id=primary.candidate_id,
            artifact_id=f"merged_{len(evidence_list)}",
            type=primary.type,
            fact=f"{primary.fact} [verified across {len(evidence_list)} sources]",
            confidence=confidence,
            extracted_at=datetime.now(),
            structured_data={
                **primary.structured_data,
                "verified_by": [ev.artifact_id for ev in evidence_list],
                "source_count": len(evidence_list)
            }
        )
```

---

## 3. Claim Generation & Proof Engine

### 3.1 Claim Generator

```python
class ClaimGenerator:
    """Generate claims from evidence, aligned with role blueprint."""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def generate_claims(
        self,
        candidate_id: str,
        evidence: list[Evidence],
        blueprint: RoleBlueprint
    ) -> list[Claim]:
        """
        Generate claims relevant to the role blueprint.
        Focus on what the blueprint requires.
        """

        # Group evidence by type
        evidence_by_type = self._group_evidence(evidence)

        # Extract blueprint requirements
        requirements = self._extract_requirements(blueprint)

        claims = []

        for requirement in requirements:
            # Find relevant evidence
            relevant_evidence = self._find_relevant_evidence(
                requirement,
                evidence_by_type
            )

            if relevant_evidence:
                # Generate claim with proof
                claim = await self._generate_proved_claim(
                    candidate_id,
                    requirement,
                    relevant_evidence
                )
            else:
                # Generate unproved claim
                claim = await self._generate_unproved_claim(
                    candidate_id,
                    requirement
                )

            claims.append(claim)

        return claims

    def _extract_requirements(self, blueprint: RoleBlueprint) -> list[dict]:
        """
        Extract specific requirements from blueprint.

        Example:
        blueprint.must_haves = ["Python", "LLM APIs", "production experience"]

        →
        [
            {"category": "technical_skill", "skill": "Python", "level": "proficient"},
            {"category": "technical_skill", "skill": "LLM API integration", "level": "experienced"},
            {"category": "work_experience", "type": "production systems", "level": "required"}
        ]
        """
        pass

    def _find_relevant_evidence(
        self,
        requirement: dict,
        evidence_by_type: dict[EvidenceType, list[Evidence]]
    ) -> list[Evidence]:
        """Find evidence that speaks to this requirement."""

        # Use semantic similarity + structured matching
        relevant = []

        if requirement["category"] == "technical_skill":
            # Look for: LANGUAGE_USAGE, COMMIT_PATTERN, PROJECT_DESCRIPTION
            for ev_type in [EvidenceType.LANGUAGE_USAGE, EvidenceType.COMMIT_PATTERN]:
                for evidence in evidence_by_type.get(ev_type, []):
                    if self._evidence_matches_skill(evidence, requirement["skill"]):
                        relevant.append(evidence)

        elif requirement["category"] == "work_experience":
            # Look for: JOB_TENURE, TITLE_PROGRESSION
            for ev_type in [EvidenceType.JOB_TENURE, EvidenceType.TITLE_PROGRESSION]:
                for evidence in evidence_by_type.get(ev_type, []):
                    if self._evidence_matches_experience(evidence, requirement["type"]):
                        relevant.append(evidence)

        return relevant

    async def _generate_proved_claim(
        self,
        candidate_id: str,
        requirement: dict,
        evidence: list[Evidence]
    ) -> Claim:
        """Generate a claim with supporting evidence."""

        # Use LLM to synthesize evidence into claim
        prompt = f"""
        Based on this evidence, generate a claim about the candidate's capability.

        Requirement: {json.dumps(requirement)}

        Evidence:
        {self._format_evidence(evidence)}

        Generate:
        1. claim_statement: Clear statement of what candidate can do
        2. proof_summary: Brief explanation of how evidence proves this
        3. confidence_score: 0.0-1.0 based on evidence strength

        Be specific. Reference concrete artifacts.
        """

        response = await self.llm.generate(prompt)

        return Claim(
            id=generate_id(),
            candidate_id=candidate_id,
            type=self._map_to_claim_type(requirement),
            statement=response["claim_statement"],
            status=ProofStatus.PROVED,
            evidence_ids=[ev.id for ev in evidence],
            confidence_score=response["confidence_score"],
            relevance_to_role=self._calculate_relevance(requirement),
            created_at=datetime.now(),
            proof_summary=response["proof_summary"]
        )

    async def _generate_unproved_claim(
        self,
        candidate_id: str,
        requirement: dict
    ) -> Claim:
        """Generate an unproved claim with follow-up questions."""

        # Use LLM to generate interview questions
        prompt = f"""
        We need to verify this requirement but have no evidence:
        {json.dumps(requirement)}

        Generate:
        1. claim_statement: What we need to verify
        2. follow_up_questions: 2-3 specific questions to ask in interview

        Questions should be:
        - Specific and concrete
        - Designed to reveal actual depth
        - Not yes/no questions
        """

        response = await self.llm.generate(prompt)

        return Claim(
            id=generate_id(),
            candidate_id=candidate_id,
            type=self._map_to_claim_type(requirement),
            statement=response["claim_statement"],
            status=ProofStatus.UNPROVED,
            evidence_ids=[],
            confidence_score=0.0,
            relevance_to_role=self._calculate_relevance(requirement),
            created_at=datetime.now(),
            follow_up_questions=response["follow_up_questions"]
        )
```

### 3.2 Proof Engine

```python
class ProofEngine:
    """Core engine for proof-directed evaluation."""

    def __init__(
        self,
        extractors: list[EvidenceExtractor],
        aggregator: EvidenceAggregator,
        claim_generator: ClaimGenerator
    ):
        self.extractors = extractors
        self.aggregator = aggregator
        self.claim_generator = claim_generator

    async def build_proof_profile(
        self,
        candidate: CandidateData,
        blueprint: RoleBlueprint
    ) -> CandidateProofProfile:
        """
        Complete proof-directed evaluation pipeline.

        Steps:
        1. Collect artifacts from all sources
        2. Extract evidence from artifacts
        3. Aggregate and verify evidence
        4. Generate claims aligned with blueprint
        5. Compute proof statistics
        6. Generate interview questions
        """

        # Step 1: Collect artifacts
        artifacts = await self._collect_artifacts(candidate)

        # Step 2: Extract evidence
        all_evidence = []
        for artifact in artifacts:
            for extractor in self.extractors:
                if extractor.can_handle(artifact.type):
                    evidence = await extractor.extract(artifact)
                    all_evidence.extend(evidence)

        # Step 3: Aggregate
        aggregated_evidence = await self.aggregator.aggregate(
            candidate.id,
            all_evidence
        )

        # Step 4: Generate claims
        claims = await self.claim_generator.generate_claims(
            candidate.id,
            aggregated_evidence,
            blueprint
        )

        # Step 5: Organize and compute stats
        claims_by_type = self._organize_claims(claims)

        proved_claims = [c for c in claims if c.status == ProofStatus.PROVED]
        unproved_claims = [c for c in claims if c.status == ProofStatus.UNPROVED]

        # Step 6: Generate interview questions from unproved claims
        interview_questions = []
        critical_unknowns = []

        for claim in unproved_claims:
            if claim.relevance_to_role > 0.7:  # High priority
                critical_unknowns.append(claim.statement)
                interview_questions.extend(claim.follow_up_questions)

        # Calculate proof strength
        if claims:
            proof_strength = len(proved_claims) / len(claims)
        else:
            proof_strength = 0.0

        # Calculate role fit (weighted by relevance)
        role_fit = self._calculate_role_fit(proved_claims)

        return CandidateProofProfile(
            candidate_id=candidate.id,
            name=candidate.full_name,
            current_title=candidate.current_title,
            current_company=candidate.current_company,
            location=candidate.location,
            total_artifacts=len(artifacts),
            total_evidence=len(aggregated_evidence),
            total_claims=len(claims),
            proved_claims=len(proved_claims),
            unproved_claims=len(unproved_claims),
            claims_by_type=claims_by_type,
            critical_unknowns=critical_unknowns,
            interview_questions=interview_questions[:10],  # Top 10
            proof_strength=proof_strength,
            role_fit_score=role_fit,
            generated_at=datetime.now()
        )

    async def _collect_artifacts(self, candidate: CandidateData) -> list[Artifact]:
        """Collect artifacts from all available sources."""
        artifacts = []

        # GitHub
        if candidate.github_username:
            artifacts.extend(await self._fetch_github_artifacts(candidate.github_username))

        # LinkedIn
        if candidate.linkedin_url:
            artifacts.extend(await self._fetch_linkedin_artifacts(candidate.linkedin_url))

        # Resume (if available)
        if candidate.resume_url:
            artifacts.append(await self._fetch_resume_artifact(candidate.resume_url))

        # Portfolio
        if candidate.portfolio_url:
            artifacts.append(await self._fetch_portfolio_artifact(candidate.portfolio_url))

        return artifacts

    def _calculate_role_fit(self, proved_claims: list[Claim]) -> float:
        """
        Calculate role fit based on proved claims.
        Weighted by relevance_to_role.
        """
        if not proved_claims:
            return 0.0

        weighted_sum = sum(
            claim.confidence_score * claim.relevance_to_role
            for claim in proved_claims
        )

        weight_total = sum(claim.relevance_to_role for claim in proved_claims)

        return weighted_sum / weight_total if weight_total > 0 else 0.0
```

---

## 4. Integration with Search Pipeline

### 4.1 Enhanced Search with Proof

```python
class ProofDirectedSearch:
    """Search engine that builds proof profiles for candidates."""

    def __init__(
        self,
        hybrid_rag: HybridRAG,
        proof_engine: ProofEngine
    ):
        self.rag = hybrid_rag
        self.proof_engine = proof_engine

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 50
    ) -> list[CandidateProofProfile]:
        """
        Search and evaluate with proof.

        Pipeline:
        1. RAG search for candidate matches
        2. Build proof profiles in parallel
        3. Rank by proof_strength + role_fit
        4. Return top-K with full proof chains
        """

        # Step 1: Initial RAG search
        candidates = await self.rag.search(
            query=blueprint.role_title,
            blueprint=blueprint,
            limit=limit * 2  # Get more for filtering
        )

        # Step 2: Build proof profiles (parallel)
        proof_profiles = await asyncio.gather(*[
            self.proof_engine.build_proof_profile(candidate, blueprint)
            for candidate in candidates
        ])

        # Step 3: Filter and rank
        # Only return candidates with decent proof strength
        MIN_PROOF_STRENGTH = 0.3  # At least 30% of claims proved

        filtered = [
            profile for profile in proof_profiles
            if profile.proof_strength >= MIN_PROOF_STRENGTH
        ]

        # Rank by combined score
        ranked = sorted(
            filtered,
            key=lambda p: (
                0.5 * p.role_fit_score +
                0.3 * p.proof_strength +
                0.2 * (1 - len(p.critical_unknowns) / 10)  # Fewer unknowns is better
            ),
            reverse=True
        )

        return ranked[:limit]
```

### 4.2 API Endpoints

```python
# FastAPI routes
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/proof", tags=["proof-search"])

@router.post("/search")
async def proof_directed_search(
    request: SearchRequest,
    proof_search: ProofDirectedSearch = Depends()
) -> SearchResponse:
    """
    Search with proof-directed evaluation.

    Request:
    {
        "company_id": "...",
        "role_title": "Software Engineer",
        "blueprint": {...},
        "limit": 20
    }

    Response:
    {
        "candidates": [
            {
                "candidate_id": "...",
                "name": "Maya Patel",
                "proof_summary": {
                    "proof_strength": 0.78,
                    "role_fit_score": 0.85,
                    "proved_claims": 12,
                    "unproved_claims": 3
                },
                "top_strengths": [
                    {
                        "claim": "Strong Python programming experience",
                        "proof": "15,000+ lines of Python across 8 repos, 300+ commits over 18 months",
                        "evidence_links": ["github.com/maya/..."]
                    }
                ],
                "critical_unknowns": [
                    "Production system experience",
                    "Team collaboration in professional setting"
                ],
                "interview_questions": [
                    "Walk me through a time you deployed code to production...",
                    "How do you approach code reviews with teammates?"
                ]
            }
        ],
        "search_metadata": {
            "total_candidates_evaluated": 47,
            "passed_proof_threshold": 23,
            "avg_proof_strength": 0.65
        }
    }
    """

    blueprint = request.blueprint
    proof_profiles = await proof_search.search(blueprint, request.limit)

    return SearchResponse(
        candidates=[
            format_candidate_response(profile)
            for profile in proof_profiles
        ],
        search_metadata={
            "total_candidates_evaluated": len(candidates),
            "passed_proof_threshold": len(proof_profiles),
            "avg_proof_strength": sum(p.proof_strength for p in proof_profiles) / len(proof_profiles)
        }
    )

@router.get("/candidate/{candidate_id}/proof")
async def get_proof_profile(
    candidate_id: str,
    blueprint_id: str,
    proof_engine: ProofEngine = Depends()
) -> CandidateProofProfile:
    """
    Get detailed proof profile for a candidate.

    Returns full proof chain:
    - All artifacts
    - All evidence
    - All claims (proved + unproved)
    - Interview questions
    """

    candidate = await get_candidate(candidate_id)
    blueprint = await get_blueprint(blueprint_id)

    profile = await proof_engine.build_proof_profile(candidate, blueprint)

    return profile

@router.get("/candidate/{candidate_id}/artifacts")
async def get_candidate_artifacts(
    candidate_id: str
) -> list[Artifact]:
    """Get all artifacts for a candidate."""
    return await get_artifacts(candidate_id)

@router.get("/evidence/{evidence_id}")
async def get_evidence_detail(
    evidence_id: str
) -> EvidenceDetail:
    """
    Get evidence with full context.

    Returns:
    - Evidence record
    - Source artifact
    - Related claims
    - Verification status
    """
    pass

@router.post("/candidate/{candidate_id}/verify-claim")
async def verify_claim_manually(
    candidate_id: str,
    request: VerifyClaimRequest
) -> Claim:
    """
    Manually verify an unproved claim.
    Used after interview or additional verification.

    Request:
    {
        "claim_id": "...",
        "status": "proved" | "contradicted",
        "evidence": "Verified in interview: candidate deployed to AWS prod...",
        "confidence": 0.9
    }
    """
    pass
```

---

## 5. UI/UX Considerations

### 5.1 Candidate Card with Proof

```typescript
interface CandidateProofCard {
  candidate: {
    id: string;
    name: string;
    title: string;
    location: string;
  };

  proofSummary: {
    proofStrength: number;      // 0-1, shown as progress bar
    roleFitScore: number;        // 0-1, shown as match %
    provedClaims: number;
    unprovedClaims: number;
  };

  // Top 3-5 strongest proved claims
  topStrengths: Array<{
    claim: string;
    proof: string;              // One-liner proof summary
    evidenceLinks: string[];    // Links to artifacts
    confidence: number;
  }>;

  // What we don't know
  criticalUnknowns: string[];

  // Next steps
  interviewQuestions: string[];
}

// Visual hierarchy:
// 1. Name, title (always visible)
// 2. Proof strength + role fit (visual indicators)
// 3. Expandable sections:
//    - "Why consider" (top strengths with proof)
//    - "What to verify" (unknowns + questions)
//    - "Full proof chain" (all claims + evidence)
```

### 5.2 Proof Chain Visualization

```
Maya Patel
Software Engineer Candidate
Proof Strength: ████████░░ 78%  |  Role Fit: ████████░░ 85%

━━━ PROVED STRENGTHS (12 claims) ━━━

✓ Strong Python programming (conf: 0.92)
  └─ Evidence:
     • 15,234 lines of Python across 8 repos [GitHub ↗]
     • 327 commits over 18 months (consistent activity)
     • Used in: ML pipeline, API backend, data processing
  └─ Proof: Extensive Python codebase demonstrates hands-on experience

✓ Experience with LLM APIs (conf: 0.85)
  └─ Evidence:
     • Built 'llm-router' project - 500+ commits [GitHub ↗]
     • OpenAI API integration in 3 projects
     • Won "Best AI Hack" at SD Hacks 2024 [Devpost ↗]
  └─ Proof: Multiple projects show practical LLM integration skills

✓ Active open-source contributor (conf: 0.88)
  └─ Evidence:
     • 12 merged PRs to external repos (FastAPI, LangChain)
     • Code review activity on 47 PRs
     • Maintains 2 public libraries (40+ stars combined)
  └─ Proof: Demonstrates collaboration and code quality standards

[Show 9 more proved claims...]

━━━ NEEDS VERIFICATION (3 claims) ━━━

? Production system experience
  └─ Why unknown: No evidence of deployed production systems
  └─ Ask: "Walk me through deploying your project to production.
            What monitoring/logging did you set up?"

? Team collaboration in professional setting
  └─ Why unknown: Only student projects visible, no job history
  └─ Ask: "Tell me about a time you had to coordinate with
            a teammate to ship a feature."

? System design for scale
  └─ Why unknown: Projects are small-scale (< 1k users)
  └─ Ask: "How would you design your llm-router to handle
            10k requests/second?"

━━━ FULL AUDIT TRAIL ━━━
📦 12 artifacts collected
   • 5 GitHub repos
   • 3 Devpost projects
   • 2 LinkedIn experiences
   • 1 Portfolio site
   • 1 Resume

🔍 43 pieces of evidence extracted
   • 28 from GitHub (code, commits, reviews)
   • 8 from Devpost (hackathons, awards)
   • 4 from LinkedIn (education, clubs)
   • 3 from Portfolio (projects)

📊 15 claims generated (12 proved, 3 unproved)
   • Technical skills: 8 proved, 1 unproved
   • Work experience: 2 proved, 2 unproved
   • Soft skills: 2 proved, 0 unproved
```

---

## 6. Database Schema

```sql
-- Artifacts table
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    type TEXT NOT NULL,  -- github_repo, linkedin_profile, etc.
    source_url TEXT,
    raw_data JSONB NOT NULL,
    collected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_artifacts_candidate ON artifacts(candidate_id);
CREATE INDEX idx_artifacts_type ON artifacts(type);

-- Evidence table
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    artifact_id UUID NOT NULL REFERENCES artifacts(id),
    type TEXT NOT NULL,  -- commit_pattern, job_tenure, etc.
    fact TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    extracted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    structured_data JSONB NOT NULL,

    -- For search
    fact_embedding VECTOR(1536)  -- pgvector for semantic search
);

CREATE INDEX idx_evidence_candidate ON evidence(candidate_id);
CREATE INDEX idx_evidence_artifact ON evidence(artifact_id);
CREATE INDEX idx_evidence_type ON evidence(type);
CREATE INDEX idx_evidence_embedding ON evidence USING ivfflat (fact_embedding vector_cosine_ops);

-- Claims table
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    blueprint_id UUID NOT NULL REFERENCES role_blueprints(id),
    type TEXT NOT NULL,  -- technical_skill, work_experience, etc.
    statement TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('proved', 'unproved', 'contradicted', 'partial')),
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    relevance_to_role FLOAT NOT NULL CHECK (relevance_to_role >= 0 AND relevance_to_role <= 1),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- For proved claims
    proof_summary TEXT,

    -- For unproved claims
    follow_up_questions JSONB DEFAULT '[]'::jsonb
);

CREATE INDEX idx_claims_candidate ON claims(candidate_id);
CREATE INDEX idx_claims_blueprint ON claims(blueprint_id);
CREATE INDEX idx_claims_status ON claims(status);

-- Claim-Evidence junction table
CREATE TABLE claim_evidence (
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    PRIMARY KEY (claim_id, evidence_id)
);

CREATE INDEX idx_claim_evidence_claim ON claim_evidence(claim_id);
CREATE INDEX idx_claim_evidence_evidence ON claim_evidence(evidence_id);

-- Proof profiles (cached results)
CREATE TABLE proof_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    blueprint_id UUID NOT NULL REFERENCES role_blueprints(id),

    -- Summary stats
    total_artifacts INT NOT NULL,
    total_evidence INT NOT NULL,
    total_claims INT NOT NULL,
    proved_claims INT NOT NULL,
    unproved_claims INT NOT NULL,

    -- Scores
    proof_strength FLOAT NOT NULL,
    role_fit_score FLOAT NOT NULL,

    -- Cached data
    critical_unknowns JSONB NOT NULL,
    interview_questions JSONB NOT NULL,

    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(candidate_id, blueprint_id)
);

CREATE INDEX idx_proof_profiles_candidate ON proof_profiles(candidate_id);
CREATE INDEX idx_proof_profiles_blueprint ON proof_profiles(blueprint_id);
CREATE INDEX idx_proof_profiles_scores ON proof_profiles(proof_strength DESC, role_fit_score DESC);
```

---

## 7. Cost Management

### 7.1 Budget Allocation

```python
class ProofBudgetManager:
    """Manage costs for proof-directed search."""

    # Cost estimates (USD)
    COSTS = {
        "github_api_call": 0.0,       # Free (rate limited)
        "pdl_enrichment": 0.05,       # $0.03-0.10 per person
        "llm_evidence_extraction": 0.002,  # ~1k tokens
        "llm_claim_generation": 0.01,      # ~5k tokens
        "embedding_generation": 0.0001,    # Very cheap
    }

    DAILY_BUDGET = 50.0  # $50/day

    async def should_extract_evidence(
        self,
        artifact: Artifact,
        candidate: CandidateData
    ) -> bool:
        """Decide if we should extract evidence from this artifact."""

        # Always extract from free sources
        if artifact.type in [ArtifactType.GITHUB_REPO, ArtifactType.GITHUB_COMMIT]:
            return True

        # For paid sources, check budget
        cost = self._estimate_cost(artifact)
        if not await self.has_budget(cost):
            return False

        # Only extract if candidate looks promising
        if candidate.initial_score < 0.5:
            return False

        return True

    async def batch_extract(
        self,
        artifacts: list[Artifact],
        max_budget: float
    ) -> list[Artifact]:
        """
        Select which artifacts to extract from, staying within budget.
        Prioritize by potential value.
        """

        # Score each artifact by potential value
        scored = [
            (artifact, self._score_artifact_value(artifact))
            for artifact in artifacts
        ]

        # Sort by value, select greedily within budget
        scored.sort(key=lambda x: x[1], reverse=True)

        selected = []
        budget_used = 0.0

        for artifact, value in scored:
            cost = self._estimate_cost(artifact)
            if budget_used + cost <= max_budget:
                selected.append(artifact)
                budget_used += cost

        return selected
```

---

## 8. Example: Complete Flow

```python
# User searches for "Software Engineer who can ship LLM features fast"

# Step 1: Build blueprint from conversation
blueprint = RoleBlueprint(
    role_title="Software Engineer",
    company_context="Early-stage AI startup, need to move fast",
    specific_work="Build LLM-powered features, integrate APIs, ship to production",
    success_criteria="Ships complete feature in first 60 days",
    must_haves=["Python", "LLM APIs", "can work independently"],
    nice_to_haves=["FastAPI", "React", "production experience"],
    avoid=["needs lots of hand-holding", "pure research focus"]
)

# Step 2: Search finds Maya Patel
candidate = CandidateData(
    id="cand_123",
    full_name="Maya Patel",
    school="UC San Diego",
    major="Computer Science",
    graduation_year=2026,
    github_username="maya-codes",
    linkedin_url="linkedin.com/in/maya-patel",
    portfolio_url="mayapatel.dev"
)

# Step 3: Build proof profile
proof_engine = ProofEngine(...)
profile = await proof_engine.build_proof_profile(candidate, blueprint)

# Step 4: Profile generated
"""
CandidateProofProfile(
    candidate_id="cand_123",
    name="Maya Patel",

    # Stats
    total_artifacts=12,
    total_evidence=43,
    total_claims=15,
    proved_claims=12,
    unproved_claims=3,

    # Scores
    proof_strength=0.78,  # 78% of claims proved
    role_fit_score=0.85,  # Strong match to blueprint

    # Top proved claims
    claims_by_type={
        ClaimType.TECHNICAL_SKILL: [
            Claim(
                statement="Strong Python programming skills",
                status=ProofStatus.PROVED,
                confidence_score=0.92,
                evidence_ids=["ev_1", "ev_2", "ev_3"],
                proof_summary="15k+ lines of Python across 8 repos, 300+ commits over 18 months"
            ),
            Claim(
                statement="Experienced with LLM API integration",
                status=ProofStatus.PROVED,
                confidence_score=0.85,
                evidence_ids=["ev_4", "ev_5", "ev_6"],
                proof_summary="Built llm-router (500+ commits), OpenAI integration in 3 projects, won AI hackathon"
            )
        ],
        ClaimType.SHIPPING_SPEED: [
            Claim(
                statement="Can ship features quickly",
                status=ProofStatus.PROVED,
                confidence_score=0.75,
                evidence_ids=["ev_10", "ev_11"],
                proof_summary="Built and deployed 3 projects in 6 months, hackathon winner (ships under time pressure)"
            )
        ]
    },

    # What we don't know
    critical_unknowns=[
        "Production system experience at scale",
        "Team collaboration in professional setting",
        "Debugging/maintaining existing codebases"
    ],

    # Interview questions
    interview_questions=[
        "Walk me through how you deployed llm-router to production. What monitoring did you set up?",
        "Tell me about a time you had to debug a production issue. What was your process?",
        "Describe how you work with teammates on shared code. How do you handle code reviews?"
    ]
)
"""

# Step 5: UI displays proof-based profile
# User sees:
# - Top strengths with proof links
# - What needs verification
# - Specific interview questions
# - Full audit trail available on click
```

---

## 9. Key Advantages

### 9.1 vs. Traditional ATS

| Traditional ATS | Proof-Directed Search |
|----------------|---------------------|
| Resume keyword matching | Multi-source evidence extraction |
| Binary "qualified/not qualified" | Transparent proof chain |
| Hidden scoring algorithms | Every claim links to artifacts |
| No verification | Explicit UNPROVED tracking |
| Generic interview questions | Targeted questions for gaps |

### 9.2 Intellectual Honesty

- **No hallucinations**: We never claim what we can't prove
- **Explicit unknowns**: We highlight what we don't know
- **Audit trail**: Every claim traceable to source
- **Interview efficiency**: Focus on verifying unknowns, not rehashing proved facts

### 9.3 Legal Defensibility

- **Reproducible**: Same evidence → same claims
- **Documented**: Full audit trail for compliance
- **Bias detection**: Can analyze if certain groups get fewer "proved" claims
- **Right to explanation**: Can show exactly why we recommended someone

---

## 10. Future Enhancements

### 10.1 Contradiction Detection & Resolution

```python
class ContradictionDetector:
    """Detect when evidence contradicts claims."""

    async def detect(self, evidence: list[Evidence]) -> list[Contradiction]:
        """
        Find contradictions like:
        - Resume says "Expert in X" but GitHub shows no X usage
        - LinkedIn says "3 years at Company" but company acquired after 2 years
        - Claims production experience but all projects are localhost
        """
        pass
```

### 10.2 Evidence Quality Scoring

```python
class EvidenceQualityScorer:
    """Score evidence by reliability."""

    QUALITY_WEIGHTS = {
        # High reliability
        "github_verified": 1.0,
        "linkedin_verified": 0.9,

        # Medium reliability
        "portfolio_claimed": 0.6,
        "resume_stated": 0.5,

        # Low reliability
        "self_reported_skill": 0.3,
    }
```

### 10.3 Temporal Proof Chains

```python
# Track how proof evolves over time
# Example: "Was skilled in React 2 years ago, but no recent usage"

class TemporalProof:
    evidence_timeline: list[tuple[datetime, Evidence]]
    recency_weight: float  # Decay factor for old evidence
```

### 10.4 Peer Comparison

```python
# Compare proof profiles across candidates
# "This candidate has 2x more proved claims than average"

class ProofBenchmark:
    async def compare(
        self,
        candidate: CandidateProofProfile,
        peer_group: list[CandidateProofProfile]
    ) -> ComparisonReport:
        pass
```

---

## 11. Implementation Checklist

### Week 1: Foundation
- [ ] Define data models (Artifact, Evidence, Claim)
- [ ] Set up database schema with pgvector
- [ ] Implement base EvidenceExtractor interface
- [ ] Build GitHubExtractor

### Week 2: Evidence Layer
- [ ] LinkedInExtractor
- [ ] ResumeExtractor
- [ ] PortfolioExtractor
- [ ] EvidenceAggregator (dedup, cross-verification)

### Week 3: Claim Layer
- [ ] ClaimGenerator (LLM-based)
- [ ] ProofEngine (full pipeline)
- [ ] Interview question generation

### Week 4: Integration
- [ ] ProofDirectedSearch (integrate with existing RAG)
- [ ] API endpoints
- [ ] Frontend components for proof display
- [ ] Cost management

### Week 5: Polish
- [ ] Contradiction detection
- [ ] Evidence quality scoring
- [ ] Audit trail UI
- [ ] Testing and launch
