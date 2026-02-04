# ProofHire: Technical Architecture Document

**Version**: 1.0
**Date**: February 3, 2026
**Author**: Arjun Vad
**Status**: Production Ready (MVP)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture](#3-architecture)
4. [Backend Architecture](#4-backend-architecture)
5. [Proof Engine](#5-proof-engine)
6. [Evidence Extraction](#6-evidence-extraction)
7. [LLM Integration](#7-llm-integration)
8. [Company Operating Model](#8-company-operating-model)
9. [Simulation System](#9-simulation-system)
10. [Candidate Briefs](#10-candidate-briefs)
11. [Runner Architecture](#11-runner-architecture)
12. [Frontend Architecture](#12-frontend-architecture)
13. [Database Schema](#13-database-schema)
14. [API Reference](#14-api-reference)
15. [Security & Audit](#15-security--audit)
16. [Deployment Guide](#16-deployment-guide)
17. [Testing Strategy](#17-testing-strategy)

---

## 1. Executive Summary

**ProofHire** is a B2B SaaS platform that revolutionizes engineering hiring by replacing resume screening with evidence-backed candidate evaluation briefs. The system operates on three core principles:

1. **Evidence-First**: All claims about candidates must be backed by artifacts
2. **Fail-Closed**: Unproven claims become interview questions, not hidden gaps
3. **Decision Support**: No automated hire/no-hire decisions

### Key Innovation: Proof-Gated Evaluation

Instead of relying on resumes and subjective interviews, ProofHire:
- Has candidates complete standardized work simulations
- Extracts objective evidence from artifacts (code diffs, test logs, coverage reports)
- Applies deterministic proof rules to generate proven/unproven claims
- Generates structured briefs for founders to make informed decisions

### System Statistics

| Metric | Value |
|--------|-------|
| Backend Modules | 12 |
| API Endpoints | 25+ |
| Proof Rules | 6 |
| Simulation Types | 2 |
| Test Coverage | 85%+ |

---

## 2. System Overview

### 2.1 Vision

ProofHire addresses the fundamental problem in startup hiring: founders waste time on candidates who look good on paper but can't actually do the job. By requiring candidates to complete standardized work simulations and evaluating them against objective criteria, ProofHire provides:

- **For Founders**: Confidence that candidates can actually do the work
- **For Candidates**: Fair evaluation based on demonstrated skills, not resume keywords
- **For Both**: Faster, more transparent hiring process

### 2.2 Core Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    FOUNDER WORKFLOW                              │
│  1. Answer interview questions about company + role             │
│  2. System generates Company Operating Model (COM)              │
│  3. System builds evaluation rubric from COM                    │
│  4. Founder activates role to accept applications               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CANDIDATE WORKFLOW                             │
│  1. Apply to role (name, email, GitHub, consent)                │
│  2. Complete standardized simulation (bugfix, feature, etc.)    │
│  3. Submit code + writeup                                       │
│  4. View results and feedback                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROOF WORKFLOW                                │
│  1. Runner executes simulation in Docker sandbox                │
│  2. Evidence extractors parse artifacts                         │
│  3. Proof engine evaluates claims against rules                 │
│  4. Brief builder generates proven/unproven claims              │
│  5. LLM generates interview questions for gaps                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   REVIEW WORKFLOW                                │
│  Founder reviews brief with:                                    │
│  - Proven claims (with evidence links)                          │
│  - Unproven claims (with suggested questions)                   │
│  - Risk flags                                                   │
│  - Direct artifact access                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Key Differentiators

| Traditional Hiring | ProofHire |
|-------------------|-----------|
| Resume screening | Work simulation |
| Subjective interviews | Evidence-based claims |
| Hidden biases | Deterministic rules |
| "Culture fit" guessing | Objective metrics |
| Black box decisions | Full audit trail |

---

## 3. Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Founder   │  │  Candidate  │  │      Public Pages       │ │
│  │  Dashboard  │  │   Portal    │  │  (Home, Login, Signup)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                         Next.js (React/TypeScript)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API LAYER                               │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────────┐│
│  │ Auth │ │ Orgs │ │Roles │ │ Apps │ │ Runs │ │Briefs/Artifacts││
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────────────┘│
│                         FastAPI (Python)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐  ┌─────────────────────┐  ┌───────────────────┐
│   PROOF       │  │    LLM GATEWAY      │  │     EVIDENCE      │
│   ENGINE      │  │                     │  │      STORE        │
│  ┌─────────┐  │  │  Anthropic Claude   │  │  ┌─────────────┐  │
│  │ Rules   │  │  │  Schema Validation  │  │  │ S3/MinIO    │  │
│  │ Claims  │  │  │  Audit Logging      │  │  │ Extractors  │  │
│  │ Results │  │  └─────────────────────┘  │  │ Parsers     │  │
│  └─────────┘  │                           │  └─────────────┘  │
└───────────────┘                           └───────────────────┘
        │                                           │
        └───────────────────┬───────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATABASE                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐ │
│  │  Users  │ │  Roles  │ │  Runs   │ │ Claims  │ │ AuditLog  │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └───────────┘ │
│                       PostgreSQL                                │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                          RUNNER                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐│
│  │  Job Polling    │  │  Docker Sandbox │  │ Artifact Upload  ││
│  │  (Redis Queue)  │  │    Execution    │  │    (S3)          ││
│  └─────────────────┘  └─────────────────┘  └──────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| API | FastAPI, Python 3.11+, Pydantic |
| Database | PostgreSQL (asyncpg) |
| Cache/Queue | Redis |
| Storage | S3/MinIO |
| LLM | Anthropic Claude API |
| Runner | Docker (sandboxed execution) |
| Deployment | Docker Compose |

### 3.3 Module Structure

```
proofhire/
├── backend/
│   └── app/
│       ├── api/           # FastAPI routes
│       ├── core/          # Utilities (security, time, ids)
│       ├── db/            # SQLAlchemy models, migrations
│       ├── proof/         # Proof engine + rules
│       ├── evidence/      # Artifact storage + extractors
│       ├── llm/           # LLM gateway + schemas
│       ├── company_model/ # COM + rubric building
│       ├── simulations/   # Simulation catalog
│       ├── hypothesis/    # Claim generation
│       ├── briefs/        # Brief building
│       └── tests/         # Backend tests
├── runner/
│   ├── runner.py          # Main worker loop
│   ├── sandbox.py         # Docker execution
│   └── job_handlers.py    # Job processing
└── web/
    └── src/
        ├── app/           # Next.js pages
        ├── components/    # React components
        └── lib/           # API client, types
```

---

## 4. Backend Architecture

### 4.1 Application Entry Point

**File**: `/backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connections
    await init_db()
    await init_redis()
    yield
    # Shutdown: Close connections
    await close_connections()

app = FastAPI(
    title="ProofHire API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
```

### 4.2 Configuration

**File**: `/backend/app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str
    database_url_test: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379"

    # S3/MinIO
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = "proofhire"
    s3_region: str = "us-east-1"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # LLM
    anthropic_api_key: str

    # Runner
    runner_timeout_seconds: int = 600
    runner_memory_limit_mb: int = 512
    runner_cpu_limit: float = 1.0

    # App
    app_env: str = "development"
    debug: bool = False

    class Config:
        env_file = ".env"
```

### 4.3 Dependency Injection

**File**: `/backend/app/deps.py`

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def get_current_user(
    token: str = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_token(token.credentials)
    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(401, "Invalid or inactive user")
    return user

async def require_org_membership(
    org_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Membership:
    membership = await get_membership(db, user.id, org_id)
    if not membership:
        raise HTTPException(403, "Not a member of this organization")
    return membership
```

### 4.4 Core Utilities

**File**: `/backend/app/core/`

| File | Purpose |
|------|---------|
| `ids.py` | ID generation (prefixed UUIDs) |
| `time.py` | Timezone-aware datetime utilities |
| `hashing.py` | Password hashing (bcrypt) |
| `security.py` | JWT encoding/decoding |
| `audit.py` | Audit log helpers |
| `errors.py` | Custom exception classes |

---

## 5. Proof Engine

### 5.1 Architecture

**File**: `/backend/app/proof/engine.py`

The proof engine is the core of ProofHire's "fail-closed guarantee". It evaluates claims against registered rules using extracted metrics and artifacts.

```python
class ProofEngine:
    def __init__(self):
        self.rules: Dict[str, List[ProofRule]] = {}

    def register_rule(self, claim_type: str, rule: ProofRule):
        """Register a rule for a claim type."""
        if claim_type not in self.rules:
            self.rules[claim_type] = []
        self.rules[claim_type].append(rule)

    def evaluate(
        self,
        claim: Claim,
        metrics: MetricsBundle,
        artifacts: Dict[str, Artifact],
        llm_tags: Dict[str, Any],
        com: CompanyOperatingModel
    ) -> ProofResult:
        """
        Evaluate a claim against all applicable rules.
        Returns PROVED if ANY rule proves the claim.
        """
        applicable_rules = self.rules.get(claim.claim_type, [])

        for rule in applicable_rules:
            result = rule.evaluate(claim, metrics, artifacts, llm_tags, com)
            if result.verdict == ProofVerdict.PROVED:
                return result

        return ProofResult(
            verdict=ProofVerdict.UNPROVED,
            rule_id=None,
            reason="No rule could prove this claim",
            evidence_refs=[]
        )
```

### 5.2 Proof Rules

**File**: `/backend/app/proof/rules/backend_engineer_v1.py`

```python
class AddedRegressionTestRule(ProofRule):
    """Verifies candidate added a regression test for the bug fix."""

    rule_id = "added_regression_test_v1"
    claim_type = "added_regression_test"

    def evaluate(
        self,
        claim: Claim,
        metrics: MetricsBundle,
        artifacts: Dict[str, Artifact],
        llm_tags: Dict[str, Any],
        com: CompanyOperatingModel
    ) -> ProofResult:
        # Check tests passed
        if not metrics.tests_passed:
            return self.unproved("Tests did not pass")

        # Check test was added
        test_added = metrics.test_added or (
            metrics.test_files_changed > 0 and
            metrics.test_count_delta > 0
        )

        if not test_added:
            return self.unproved("No regression test was added")

        return self.proved(
            "Candidate added regression test that passes",
            evidence_refs=[
                EvidenceRef(type="metric", key="tests_passed"),
                EvidenceRef(type="metric", key="test_files_changed"),
                EvidenceRef(type="artifact", key="test_log")
            ]
        )


class DebuggingEffectiveRule(ProofRule):
    """Verifies candidate effectively diagnosed and fixed the bug."""

    rule_id = "debugging_effective_v1"
    claim_type = "debugging_effective"

    def evaluate(self, claim, metrics, artifacts, llm_tags, com) -> ProofResult:
        # Check tests pass
        if not metrics.tests_passed:
            return self.unproved("Tests did not pass")

        # Check time efficiency
        pace_threshold = com.get_pace_threshold()
        if metrics.time_to_green and metrics.time_to_green > pace_threshold:
            return self.unproved(f"Time to green ({metrics.time_to_green}m) exceeded threshold ({pace_threshold}m)")

        # Check LLM identified root cause
        if not llm_tags.get("root_cause_identified"):
            return self.unproved("Root cause not clearly identified in writeup")

        return self.proved(
            "Candidate effectively debugged the issue",
            evidence_refs=[
                EvidenceRef(type="metric", key="tests_passed"),
                EvidenceRef(type="metric", key="time_to_green"),
                EvidenceRef(type="llm_tag", key="root_cause_identified")
            ]
        )
```

### 5.3 Registered Rules

| Rule | Claim Type | What It Proves |
|------|------------|----------------|
| `AddedRegressionTestRule` | `added_regression_test` | Candidate added a passing regression test |
| `DebuggingEffectiveRule` | `debugging_effective` | Candidate diagnosed and fixed bug efficiently |
| `TestingDisciplineRule` | `testing_discipline` | Candidate demonstrates good testing practices |
| `TimeEfficientRule` | `time_efficient` | Candidate completed task within expected time |
| `HandlesEdgeCasesRule` | `handles_edge_cases` | Candidate properly handles edge cases |
| `CommunicationClearRule` | `communication_clear` | Candidate communicates clearly in writeup |

### 5.4 Proof Result Structure

```python
@dataclass
class ProofResult:
    verdict: ProofVerdict  # PROVED or UNPROVED
    rule_id: Optional[str]
    reason: str
    evidence_refs: List[EvidenceRef]
    confidence: float = 1.0

@dataclass
class EvidenceRef:
    type: str  # "metric", "artifact", "llm_tag"
    key: str
    value: Optional[Any] = None
```

---

## 6. Evidence Extraction

### 6.1 Evidence Store

**File**: `/backend/app/evidence/store.py`

```python
class EvidenceStore:
    """S3-backed artifact storage with integrity verification."""

    def __init__(self, s3_client, bucket: str):
        self.s3 = s3_client
        self.bucket = bucket

    async def upload(
        self,
        run_id: str,
        artifact_type: ArtifactType,
        content: bytes,
        metadata: Dict[str, Any]
    ) -> Artifact:
        """Upload artifact with SHA256 hash."""
        sha256 = hashlib.sha256(content).hexdigest()
        key = f"runs/{run_id}/{artifact_type.value}/{sha256}"

        await self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            Metadata=metadata
        )

        return Artifact(
            artifact_id=generate_id("art"),
            run_id=run_id,
            artifact_type=artifact_type,
            s3_key=key,
            sha256=sha256,
            size_bytes=len(content),
            metadata=metadata
        )

    async def download(self, artifact: Artifact) -> bytes:
        """Download artifact with integrity check."""
        response = await self.s3.get_object(
            Bucket=self.bucket,
            Key=artifact.s3_key
        )
        content = await response["Body"].read()

        # Verify integrity
        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != artifact.sha256:
            raise IntegrityError(f"Hash mismatch: {actual_hash} != {artifact.sha256}")

        return content
```

### 6.2 Extractors

**File**: `/backend/app/evidence/extractors/`

#### Diff Extractor
```python
def extract_diff_metrics(diff_content: str) -> DiffMetrics:
    """Parse unified diff to extract code change metrics."""
    files_changed = 0
    lines_added = 0
    lines_removed = 0
    test_files_changed = 0

    for line in diff_content.split("\n"):
        if line.startswith("+++"):
            files_changed += 1
            if "test" in line.lower():
                test_files_changed += 1
        elif line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            lines_removed += 1

    return DiffMetrics(
        files_changed=files_changed,
        lines_added=lines_added,
        lines_removed=lines_removed,
        test_files_changed=test_files_changed
    )
```

#### Test Log Parser
```python
def parse_test_log(log_content: str) -> TestLogMetrics:
    """Parse test output (JSON or text format)."""
    try:
        # Try JSON format first
        data = json.loads(log_content)
        return TestLogMetrics(
            tests_passed=data.get("passed", 0) == data.get("total", 0),
            test_count=data.get("total", 0),
            failed_count=data.get("failed", 0),
            duration_seconds=data.get("duration", 0),
            failed_tests=data.get("failed_tests", [])
        )
    except json.JSONDecodeError:
        # Fall back to text parsing
        return parse_text_test_log(log_content)
```

#### Coverage Parser
```python
def parse_coverage_report(xml_content: str) -> CoverageMetrics:
    """Parse Cobertura XML coverage report."""
    root = ET.fromstring(xml_content)

    line_rate = float(root.get("line-rate", 0))
    branch_rate = float(root.get("branch-rate", 0))

    return CoverageMetrics(
        line_coverage=line_rate * 100,
        branch_coverage=branch_rate * 100
    )
```

#### Writeup Extractor
```python
def extract_writeup_metrics(writeup_content: str) -> WriteupMetrics:
    """Extract metrics from candidate writeup."""
    words = len(writeup_content.split())

    # Check for required sections
    sections = []
    for section in REQUIRED_SECTIONS:
        if section.lower() in writeup_content.lower():
            sections.append(section)

    return WriteupMetrics(
        word_count=words,
        prompts_answered=len(sections),
        sections_found=sections
    )
```

### 6.3 Metrics Bundle

```python
@dataclass
class MetricsBundle:
    # Test results
    tests_passed: bool
    test_count: int
    failed_count: int
    duration_seconds: float

    # Code changes
    files_changed: int
    lines_added: int
    lines_removed: int
    test_files_changed: int

    # Coverage
    line_coverage: float
    branch_coverage: float
    coverage_delta: float

    # Timing
    time_to_green: Optional[int]  # minutes
    submission_time: datetime

    # Writeup
    word_count: int
    prompts_answered: int
```

---

## 7. LLM Integration

### 7.1 LLM Gateway

**File**: `/backend/app/llm/gateway.py`

```python
class LLMGateway:
    """
    Bounded LLM integration with audit logging.

    Principles:
    1. Provider abstraction (currently Anthropic)
    2. All inputs/outputs logged
    3. Schema validation of outputs
    4. No deterministic grading decisions
    """

    def __init__(self, api_key: str, audit_logger: AuditLogger):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.audit = audit_logger

    async def tag_writeup(
        self,
        writeup: str,
        simulation_context: str
    ) -> WriteupTags:
        """
        Extract factual tags from writeup.
        NOT quality judgments - just observations.
        """
        prompt = WRITEUP_TAGGING_PROMPT.format(
            writeup=writeup,
            context=simulation_context
        )

        response = await self._call(prompt, WriteupTags)

        self.audit.log("llm_tag_writeup", {
            "input_length": len(writeup),
            "tags_found": len(response.tags)
        })

        return response

    async def summarize_writeup(
        self,
        writeup: str
    ) -> WriteupSummary:
        """Generate brief summary of writeup."""
        prompt = WRITEUP_SUMMARY_PROMPT.format(writeup=writeup)
        return await self._call(prompt, WriteupSummary)

    async def generate_interview_questions(
        self,
        unproven_claims: List[Claim],
        com: CompanyOperatingModel
    ) -> List[InterviewQuestion]:
        """Generate targeted questions for unproven claims."""
        prompt = INTERVIEW_QUESTIONS_PROMPT.format(
            claims=json.dumps([c.dict() for c in unproven_claims]),
            com=com.to_context()
        )

        return await self._call(prompt, InterviewQuestionList)

    async def _call(self, prompt: str, schema: Type[T]) -> T:
        """Make LLM call with schema validation."""
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse and validate
        try:
            data = json.loads(response.content[0].text)
            return schema(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            self.audit.log("llm_validation_error", {"error": str(e)})
            raise LLMValidationError(str(e))
```

### 7.2 Bounded Use Cases

| Use Case | Input | Output | NOT Allowed |
|----------|-------|--------|-------------|
| Writeup Tagging | Writeup text | Factual tags | Quality judgments |
| Writeup Summary | Writeup text | Brief summary | Recommendations |
| Interview Questions | Unproven claims | Questions | Hire/no-hire decisions |

### 7.3 Output Schemas

**File**: `/backend/app/llm/schemas.py`

```python
class WriteupTag(BaseModel):
    tag: str
    confidence: float
    evidence_quote: str
    char_start: int
    char_end: int

class WriteupTags(BaseModel):
    tags: List[WriteupTag]

class WriteupSummary(BaseModel):
    summary: str  # max 500 chars
    key_points: List[str]  # max 5
    technical_depth: str  # "shallow", "medium", "deep"

class InterviewQuestion(BaseModel):
    question: str
    dimension: str
    rationale: str
    claim_ref: str
```

---

## 8. Company Operating Model

### 8.1 COM Building

**File**: `/backend/app/company_model/com_builder.py`

The Company Operating Model (COM) captures how a company operates and what they value, derived from founder interview answers.

```python
def build_com(interview_answers: Dict[str, Any]) -> CompanyOperatingModel:
    """Build COM from founder interview answers."""

    # Determine pace
    pace = determine_pace(
        answers.get("shipping_cadence"),
        answers.get("tech_debt_tolerance"),
        answers.get("deadline_flexibility")
    )

    # Determine quality bar
    quality_bar = determine_quality(
        answers.get("ci_infrastructure"),
        answers.get("code_review_rigor"),
        answers.get("test_coverage_expectation")
    )

    # Determine priorities
    priorities = extract_priorities(
        answers.get("current_phase"),
        answers.get("main_challenges")
    )

    return CompanyOperatingModel(
        pace=pace,                    # "high", "medium", "low"
        quality_bar=quality_bar,      # "high", "medium", "low"
        ambiguity=answers.get("ambiguity", "high"),
        priorities=priorities,         # ["ship_v1", "stabilize", ...]
        risk_intolerance=answers.get("risks", [])
    )


def determine_pace(cadence, debt_tolerance, flexibility) -> str:
    """Determine company pace from answers."""
    score = 0

    if cadence == "weekly_or_faster":
        score += 2
    elif cadence == "biweekly":
        score += 1

    if debt_tolerance == "high":
        score += 2
    elif debt_tolerance == "medium":
        score += 1

    if flexibility == "tight":
        score += 1

    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"
```

### 8.2 Rubric Building

**File**: `/backend/app/company_model/rubric.py`

```python
def build_rubric(com: CompanyOperatingModel) -> RoleRubric:
    """Build evaluation rubric from COM."""

    # Default weights
    weights = {
        "shipping_speed": 0.25,
        "correctness": 0.25,
        "testing_discipline": 0.20,
        "debugging_method": 0.20,
        "communication": 0.10
    }

    # Adjust for pace
    if com.pace == "high":
        weights["shipping_speed"] = 0.30
        weights["correctness"] = 0.20
    elif com.pace == "low":
        weights["shipping_speed"] = 0.15
        weights["correctness"] = 0.30

    # Adjust for quality bar
    if com.quality_bar == "high":
        weights["testing_discipline"] = 0.25
        # Rebalance others
        _normalize(weights)

    # Adjust for priorities
    if "stabilize_uptime" in com.priorities:
        weights["debugging_method"] = 0.25
        _normalize(weights)

    # Build thresholds
    thresholds = {
        "must_pass_tests": True,
        "min_coverage_delta": 0 if com.quality_bar == "low" else 5
    }

    return RoleRubric(
        dimensions=weights,
        thresholds=thresholds,
        pace_threshold=_get_pace_threshold(com.pace)
    )


def _get_pace_threshold(pace: str) -> int:
    """Get time threshold in minutes based on pace."""
    return {
        "high": 45,
        "medium": 60,
        "low": 90
    }.get(pace, 60)
```

---

## 9. Simulation System

### 9.1 Simulation Catalog

**File**: `/backend/app/simulations/catalog.py`

```python
SIMULATIONS = {
    "bugfix_v1": SimulationDefinition(
        simulation_id="bugfix_v1",
        name="Bug Fix Challenge",
        type="bugfix",
        difficulty="medium",
        time_limit_minutes=60,
        dimensions=["debugging_method", "testing_discipline", "communication"],
        instructions="""
        You will be fixing a bug in a Python web application.

        The bug causes incorrect calculation of order totals when
        discounts are applied. Your task is to:

        1. Identify the root cause of the bug
        2. Fix the bug
        3. Add a regression test
        4. Write up your approach

        The test suite must pass when you're done.
        """,
        writeup_prompts=[
            "What was the root cause of the bug?",
            "How did you identify it?",
            "What testing approach did you take?",
            "Were there any tradeoffs in your fix?"
        ]
    ),

    "feature_migration_v1": SimulationDefinition(
        simulation_id="feature_migration_v1",
        name="Feature + Migration",
        type="feature",
        difficulty="medium",
        time_limit_minutes=90,
        dimensions=["shipping_speed", "correctness", "testing_discipline", "communication"],
        instructions="""
        You will be adding a new feature that requires a database migration.

        Task: Add a "favorites" feature that allows users to mark items.

        Requirements:
        1. Create the database migration
        2. Implement the API endpoints
        3. Write tests
        4. Document rollback procedure
        """,
        writeup_prompts=[
            "Describe your migration strategy",
            "What's the rollback procedure?",
            "How did you handle backwards compatibility?",
            "What testing did you do?"
        ]
    )
}
```

### 9.2 Simulation Definitions (YAML)

**File**: `/backend/app/simulations/definitions/bugfix_v1.yaml`

```yaml
id: bugfix_v1
name: Bug Fix Challenge
type: bugfix
difficulty: medium
time_limit_minutes: 60

dimensions:
  - debugging_method
  - testing_discipline
  - communication

repo:
  url: https://github.com/proofhire/sim-bugfix-v1
  branch: main
  commit: abc123

setup:
  - pip install -r requirements.txt
  - python -m pytest --collect-only

grading:
  tests_command: python -m pytest --json-report
  coverage_command: python -m pytest --cov --cov-report=xml

instructions: |
  You will be fixing a bug in a Python web application...

writeup_prompts:
  - What was the root cause?
  - How did you identify it?
  - What testing approach did you take?
```

---

## 10. Candidate Briefs

### 10.1 Claim Schema

**File**: `/backend/app/hypothesis/claim_schema.py`

```python
CLAIM_TYPES = {
    "added_regression_test": ClaimType(
        type="added_regression_test",
        statement="Candidate added a regression test for the bug fix",
        dimensions=["testing_discipline"],
        evidence_required=["diff", "test_log", "metrics"]
    ),
    "debugging_effective": ClaimType(
        type="debugging_effective",
        statement="Candidate effectively diagnosed and fixed the bug",
        dimensions=["debugging_method"],
        evidence_required=["diff", "test_log", "writeup", "metrics"]
    ),
    "testing_discipline": ClaimType(
        type="testing_discipline",
        statement="Candidate demonstrates good testing practices",
        dimensions=["testing_discipline"],
        evidence_required=["diff", "test_log", "coverage"]
    ),
    "communication_clear": ClaimType(
        type="communication_clear",
        statement="Candidate communicates clearly in writeup",
        dimensions=["communication"],
        evidence_required=["writeup"]
    ),
    "time_efficient": ClaimType(
        type="time_efficient",
        statement="Candidate completed task within expected time",
        dimensions=["shipping_speed"],
        evidence_required=["metrics"]
    ),
    "handles_edge_cases": ClaimType(
        type="handles_edge_cases",
        statement="Candidate properly handles edge cases",
        dimensions=["correctness"],
        evidence_required=["diff", "test_log"]
    )
}
```

### 10.2 Brief Builder

**File**: `/backend/app/briefs/brief_builder.py`

```python
async def build_brief(
    application: Application,
    runs: List[SimulationRun],
    proof_results: Dict[str, ProofResult],
    llm_gateway: LLMGateway
) -> CandidateBrief:
    """Build candidate evaluation brief from proof results."""

    # Separate proven and unproven claims
    proven_claims = []
    unproven_claims = []

    for claim_type, result in proof_results.items():
        claim = Claim(
            claim_type=claim_type,
            statement=CLAIM_TYPES[claim_type].statement,
            dimensions=CLAIM_TYPES[claim_type].dimensions
        )

        if result.verdict == ProofVerdict.PROVED:
            proven_claims.append(ProvenClaim(
                claim=claim,
                proof_result=result,
                confidence=result.confidence
            ))
        else:
            unproven_claims.append(UnprovenClaim(
                claim=claim,
                reason=result.reason
            ))

    # Generate interview questions for unproven claims
    interview_questions = []
    if unproven_claims:
        questions = await llm_gateway.generate_interview_questions(
            [uc.claim for uc in unproven_claims],
            application.role.com
        )
        interview_questions = questions

    # Compute dimensions coverage
    dimensions_coverage = compute_coverage(proven_claims, application.role.rubric)

    # Identify risk flags
    risk_flags = identify_risks(runs, proof_results)

    # Compute proof rate
    total_claims = len(proven_claims) + len(unproven_claims)
    proof_rate = len(proven_claims) / total_claims if total_claims > 0 else 0

    return CandidateBrief(
        brief_id=generate_id("brief"),
        application_id=application.id,
        candidate_name=application.candidate.name,
        role_title=application.role.title,
        simulation_info=SimulationInfo(
            simulation_id=runs[0].simulation_id,
            completed_at=runs[0].completed_at,
            duration_minutes=runs[0].duration_minutes
        ),
        proven_claims=proven_claims,
        unproven_claims=unproven_claims,
        interview_questions=interview_questions,
        dimensions_coverage=dimensions_coverage,
        risk_flags=risk_flags,
        proof_rate=proof_rate,
        generated_at=datetime.utcnow()
    )
```

### 10.3 Brief Structure

```python
@dataclass
class CandidateBrief:
    brief_id: str
    application_id: str
    candidate_name: str
    role_title: str

    simulation_info: SimulationInfo
    # simulation_id, completed_at, duration_minutes

    proven_claims: List[ProvenClaim]
    # claim, proof_result, confidence, evidence_refs

    unproven_claims: List[UnprovenClaim]
    # claim, reason

    interview_questions: List[InterviewQuestion]
    # question, dimension, rationale, claim_ref

    dimensions_coverage: Dict[str, CoverageStatus]
    # dimension -> "covered" | "partial" | "uncovered"

    risk_flags: List[RiskFlag]
    # severity, description, evidence

    proof_rate: float
    # percentage of claims proven (0-1)

    generated_at: datetime
```

---

## 11. Runner Architecture

### 11.1 Runner Main Loop

**File**: `/runner/runner.py`

```python
class Runner:
    """Background worker that executes simulation jobs."""

    def __init__(self, config: RunnerConfig):
        self.redis = redis.Redis.from_url(config.redis_url)
        self.sandbox = SandboxManager(config)
        self.store = EvidenceStore(config.s3_config)

    async def run(self):
        """Main job processing loop."""
        logger.info("Runner started, polling for jobs...")

        while True:
            # Poll for job
            job_data = await self.redis.brpop("proofhire:jobs", timeout=5)
            if not job_data:
                continue

            job = Job.parse_raw(job_data[1])
            logger.info(f"Processing job: {job.run_id}")

            try:
                await self.process_job(job)
            except Exception as e:
                logger.error(f"Job failed: {e}")
                await self.notify_failure(job, str(e))

    async def process_job(self, job: Job):
        """Process a single job."""

        # Update status
        await self.set_status(job.run_id, "running")

        if job.type == "simulation":
            await self.run_simulation(job)
        elif job.type == "grade":
            await self.grade_submission(job)

    async def run_simulation(self, job: Job):
        """Execute simulation in sandbox."""

        # Get simulation definition
        simulation = get_simulation(job.simulation_id)

        # Create sandbox
        result = await self.sandbox.execute(
            image=simulation.docker_image,
            commands=simulation.setup_commands,
            timeout=simulation.time_limit_minutes * 60,
            memory_limit=self.config.memory_limit_mb,
            cpu_limit=self.config.cpu_limit
        )

        if not result.success:
            await self.set_status(job.run_id, "failed", result.error)
            return

        # Upload artifacts
        await self.upload_artifacts(job.run_id, result.artifacts)

        await self.set_status(job.run_id, "waiting_submission")
```

### 11.2 Sandbox Manager

**File**: `/runner/sandbox.py`

```python
class SandboxManager:
    """Docker-based isolated execution environment."""

    def __init__(self, config: SandboxConfig):
        self.docker = docker.from_env()
        self.config = config

    async def execute(
        self,
        image: str,
        commands: List[str],
        timeout: int,
        memory_limit: int,
        cpu_limit: float
    ) -> SandboxResult:
        """Execute commands in isolated container."""

        container = None
        try:
            # Create container with limits
            container = self.docker.containers.create(
                image=image,
                command="/bin/bash",
                stdin_open=True,
                tty=True,
                mem_limit=f"{memory_limit}m",
                cpu_period=100000,
                cpu_quota=int(cpu_limit * 100000),
                network_mode="none",  # No network access
                read_only=False,
                tmpfs={"/tmp": "size=100m"}
            )

            container.start()

            # Execute commands
            outputs = []
            for cmd in commands:
                exit_code, output = container.exec_run(
                    cmd,
                    timeout=timeout
                )
                outputs.append({
                    "command": cmd,
                    "exit_code": exit_code,
                    "output": output.decode()
                })

                if exit_code != 0:
                    break

            # Collect artifacts
            artifacts = await self.collect_artifacts(container)

            return SandboxResult(
                success=all(o["exit_code"] == 0 for o in outputs),
                outputs=outputs,
                artifacts=artifacts
            )

        finally:
            if container:
                container.stop(timeout=5)
                container.remove()

    async def collect_artifacts(self, container) -> Dict[str, bytes]:
        """Collect result artifacts from container."""
        artifacts = {}

        artifact_paths = {
            "test_log": "/app/test-results.json",
            "coverage": "/app/coverage.xml",
            "diff": "/app/changes.diff"
        }

        for name, path in artifact_paths.items():
            try:
                bits, _ = container.get_archive(path)
                artifacts[name] = b"".join(bits)
            except Exception:
                pass

        return artifacts
```

### 11.3 Job Handlers

**File**: `/runner/job_handlers.py`

```python
async def handle_grade_job(
    job: Job,
    sandbox: SandboxManager,
    store: EvidenceStore
) -> GradeResult:
    """Handle grading a submitted solution."""

    # Get simulation
    simulation = get_simulation(job.simulation_id)

    # Run tests
    test_result = await sandbox.execute(
        image=simulation.docker_image,
        commands=[simulation.grading.tests_command],
        timeout=300
    )

    # Run coverage
    coverage_result = await sandbox.execute(
        image=simulation.docker_image,
        commands=[simulation.grading.coverage_command],
        timeout=300
    )

    # Upload artifacts
    await store.upload(job.run_id, ArtifactType.TEST_LOG, test_result.artifacts.get("test_log", b""))
    await store.upload(job.run_id, ArtifactType.COVERAGE, coverage_result.artifacts.get("coverage", b""))

    # Parse metrics
    metrics = parse_all_metrics(
        test_result.artifacts,
        coverage_result.artifacts
    )

    return GradeResult(
        success=test_result.success,
        metrics=metrics
    )
```

---

## 12. Frontend Architecture

### 12.1 Page Structure

**Directory**: `/web/src/app/`

```
app/
├── layout.tsx           # Root layout with providers
├── page.tsx             # Home page (marketing)
├── login/page.tsx       # Login form
├── signup/page.tsx      # Registration form
├── (founder)/
│   ├── dashboard/page.tsx      # Founder dashboard
│   ├── roles/new/page.tsx      # Role creation wizard
│   └── candidates/
│       └── [applicationId]/page.tsx  # View candidate brief
└── (candidate)/
    ├── apply/[roleId]/page.tsx       # Apply to role
    ├── simulation/[applicationId]/page.tsx  # Run simulation
    └── status/[applicationId]/page.tsx      # View status
```

### 12.2 Key Components

**File**: `/web/src/components/ui/button.tsx`

```tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'rounded-lg font-medium transition-colors',
        variants[variant],
        sizes[size],
        loading && 'opacity-50 cursor-not-allowed'
      )}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? <Spinner /> : children}
    </button>
  );
}
```

### 12.3 API Client

**File**: `/web/src/lib/api.ts`

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('token');

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new APIError(response.status, await response.text());
  }

  return response.json();
}

// Auth
export const auth = {
  login: (email: string, password: string) =>
    fetchAPI<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (data: RegisterData) =>
    fetchAPI<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  me: () => fetchAPI<User>('/auth/me'),
};

// Roles
export const roles = {
  create: (data: CreateRoleData) =>
    fetchAPI<Role>('/roles', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  get: (roleId: string) =>
    fetchAPI<Role>(`/roles/${roleId}`),

  activate: (roleId: string) =>
    fetchAPI<Role>(`/roles/${roleId}/activate`, { method: 'POST' }),
};

// Applications
export const applications = {
  apply: (roleId: string, data: ApplyData) =>
    fetchAPI<Application>(`/applications/roles/${roleId}/apply`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  get: (applicationId: string) =>
    fetchAPI<Application>(`/applications/${applicationId}`),

  getBrief: (applicationId: string) =>
    fetchAPI<CandidateBrief>(`/applications/${applicationId}/brief`),
};

// Simulations
export const simulations = {
  start: (applicationId: string, simulationId: string) =>
    fetchAPI<SimulationRun>(`/runs/applications/${applicationId}/runs`, {
      method: 'POST',
      body: JSON.stringify({ simulation_id: simulationId }),
    }),

  submit: (runId: string, code: File, writeup: string) => {
    const formData = new FormData();
    formData.append('code', code);
    formData.append('writeup', writeup);

    return fetch(`${API_URL}/runs/${runId}/submit`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      body: formData,
    });
  },

  getStatus: (runId: string) =>
    fetchAPI<RunStatus>(`/runs/${runId}/status`),
};
```

### 12.4 TypeScript Types

**File**: `/web/src/lib/types.ts`

```typescript
export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Org {
  id: string;
  name: string;
  created_at: string;
}

export interface Role {
  id: string;
  org_id: string;
  title: string;
  status: 'DRAFT' | 'ACTIVE' | 'CLOSED';
  com: CompanyOperatingModel;
  rubric: RoleRubric;
  created_at: string;
}

export interface CompanyOperatingModel {
  pace: 'high' | 'medium' | 'low';
  quality_bar: 'high' | 'medium' | 'low';
  ambiguity: 'high' | 'medium' | 'low';
  priorities: string[];
  risk_intolerance: string[];
}

export interface RoleRubric {
  dimensions: Record<string, number>;
  thresholds: Record<string, any>;
  pace_threshold: number;
}

export interface Application {
  id: string;
  role_id: string;
  candidate_id: string;
  status: ApplicationStatus;
  created_at: string;
}

export type ApplicationStatus =
  | 'APPLIED'
  | 'PRESCREENED'
  | 'IN_SIMULATION'
  | 'GRADING'
  | 'COMPLETE'
  | 'REJECTED'
  | 'WITHDRAWN';

export interface CandidateBrief {
  brief_id: string;
  application_id: string;
  candidate_name: string;
  role_title: string;
  simulation_info: SimulationInfo;
  proven_claims: ProvenClaim[];
  unproven_claims: UnprovenClaim[];
  interview_questions: InterviewQuestion[];
  dimensions_coverage: Record<string, string>;
  risk_flags: RiskFlag[];
  proof_rate: number;
  generated_at: string;
}

export interface ProvenClaim {
  claim_type: string;
  statement: string;
  confidence: number;
  evidence_refs: EvidenceRef[];
}

export interface UnprovenClaim {
  claim_type: string;
  statement: string;
  reason: string;
}

export interface InterviewQuestion {
  question: string;
  dimension: string;
  rationale: string;
  claim_ref: string;
}
```

---

## 13. Database Schema

### 13.1 Migrations

**File**: `/backend/app/db/migrations/versions/c1821620b598_initial.py`

```python
def upgrade():
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Organizations
    op.create_table(
        'orgs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Memberships
    op.create_table(
        'memberships',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('orgs.id')),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Candidates
    op.create_table(
        'candidates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('github_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Roles
    op.create_table(
        'roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('orgs.id')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), default='DRAFT'),
        sa.Column('com', sa.JSON()),
        sa.Column('rubric', sa.JSON()),
        sa.Column('evaluation_pack', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Applications
    op.create_table(
        'applications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('role_id', sa.String(36), sa.ForeignKey('roles.id')),
        sa.Column('candidate_id', sa.String(36), sa.ForeignKey('candidates.id')),
        sa.Column('status', sa.String(50), default='APPLIED'),
        sa.Column('prescreen_answers', sa.JSON()),
        sa.Column('consent_version', sa.String(50)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Simulation Runs
    op.create_table(
        'simulation_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id')),
        sa.Column('simulation_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), default='QUEUED'),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('duration_minutes', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Artifacts
    op.create_table(
        'artifacts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(36), sa.ForeignKey('simulation_runs.id')),
        sa.Column('artifact_type', sa.String(50), nullable=False),
        sa.Column('s3_key', sa.String(500), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('size_bytes', sa.Integer()),
        sa.Column('metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Metrics
    op.create_table(
        'metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(36), sa.ForeignKey('simulation_runs.id')),
        sa.Column('metric_type', sa.String(100), nullable=False),
        sa.Column('value', sa.Float()),
        sa.Column('metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Claims
    op.create_table(
        'claims',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id')),
        sa.Column('claim_type', sa.String(100), nullable=False),
        sa.Column('verdict', sa.String(50)),
        sa.Column('rule_id', sa.String(100)),
        sa.Column('reason', sa.Text()),
        sa.Column('evidence_refs', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Briefs
    op.create_table(
        'briefs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id')),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Audit Log
    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(36)),
        sa.Column('resource_type', sa.String(100)),
        sa.Column('resource_id', sa.String(36)),
        sa.Column('data', sa.JSON()),
        sa.Column('prev_hash', sa.String(64)),
        sa.Column('hash', sa.String(64)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
```

### 13.2 Entity Relationship Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Users     │────<│ Memberships  │>────│    Orgs      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                                │
                                          ┌─────┴─────┐
                                          │   Roles   │
                                          └─────┬─────┘
                                                │
┌──────────────┐                          ┌─────┴─────┐
│  Candidates  │──────────────────────────│Applications│
└──────────────┘                          └─────┬─────┘
                                                │
                           ┌────────────────────┼────────────────────┐
                           │                    │                    │
                     ┌─────┴─────┐        ┌─────┴─────┐        ┌─────┴─────┐
                     │  Briefs   │        │   Runs    │        │  Claims   │
                     └───────────┘        └─────┬─────┘        └───────────┘
                                                │
                                          ┌─────┴─────┐
                                          │ Artifacts │
                                          │  Metrics  │
                                          └───────────┘
```

---

## 14. API Reference

### 14.1 Authentication Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login, returns JWT | No |
| GET | `/api/auth/me` | Get current user | Yes |
| POST | `/api/auth/logout` | Logout (client-side) | Yes |

### 14.2 Organization Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/orgs` | Create organization | Yes |
| GET | `/api/orgs` | List user's orgs | Yes |
| GET | `/api/orgs/{org_id}` | Get org details | Yes |

### 14.3 Role Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/roles` | Create role from interview | Yes |
| GET | `/api/roles/{role_id}` | Get role details | Yes |
| PATCH | `/api/roles/{role_id}` | Update role | Yes |
| POST | `/api/roles/{role_id}/activate` | Activate role | Yes |
| GET | `/api/roles/{role_id}/applications` | List applications | Yes |

### 14.4 Application Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/applications/roles/{role_id}/apply` | Apply to role | Yes |
| GET | `/api/applications/{app_id}` | Get application | Yes |
| POST | `/api/applications/{app_id}/prescreen` | Submit prescreen | Yes |
| GET | `/api/applications/{app_id}/brief` | Get brief (founder) | Yes |

### 14.5 Simulation Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/simulations` | List simulations | Yes |
| GET | `/api/simulations/{sim_id}` | Get simulation | Yes |

### 14.6 Run Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/runs/applications/{app_id}/runs` | Start run | Yes |
| GET | `/api/runs/{run_id}` | Get run | Yes |
| GET | `/api/runs/{run_id}/status` | Get status | Yes |
| POST | `/api/runs/{run_id}/submit` | Submit code | Yes |
| GET | `/api/runs/{run_id}/artifacts` | Get artifacts | Yes |

### 14.7 Artifact Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/artifacts/{art_id}/download` | Download artifact | Yes |
| GET | `/api/artifacts/{art_id}/metadata` | Get metadata | Yes |

---

## 15. Security & Audit

### 15.1 Authentication

- **JWT-based**: HS256 algorithm
- **Access tokens**: 30 minute expiry
- **Refresh tokens**: 7 day expiry
- **Password hashing**: bcrypt

### 15.2 Authorization

```python
# Role-based access control
class MembershipRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

# Permission checks
def can_view_brief(user: User, application: Application) -> bool:
    membership = get_membership(user.id, application.role.org_id)
    return membership is not None

def can_manage_role(user: User, role: Role) -> bool:
    membership = get_membership(user.id, role.org_id)
    return membership and membership.role in [MembershipRole.OWNER, MembershipRole.ADMIN]
```

### 15.3 Audit Logging

**File**: `/backend/app/core/audit.py`

```python
class AuditLogger:
    """Append-only audit log with hash chain."""

    async def log(
        self,
        event_type: str,
        user_id: Optional[str],
        resource_type: str,
        resource_id: str,
        data: Dict[str, Any]
    ):
        # Get previous hash
        prev = await self.get_latest()
        prev_hash = prev.hash if prev else "0" * 64

        # Compute hash
        content = f"{event_type}{user_id}{resource_id}{json.dumps(data)}{prev_hash}"
        new_hash = hashlib.sha256(content.encode()).hexdigest()

        # Insert log entry
        entry = AuditLogEntry(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            data=data,
            prev_hash=prev_hash,
            hash=new_hash
        )

        await self.db.add(entry)
```

### 15.4 Data Isolation

- Organization-scoped roles and applications
- Candidates only see their own applications
- Founders only see their organization's data
- Artifacts access-controlled by org membership

---

## 16. Deployment Guide

### 16.1 Docker Compose

**File**: `/docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: proofhire
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: proofhire
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U proofhire"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio
    environment:
      MINIO_ROOT_USER: ${S3_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${S3_SECRET_KEY}
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://proofhire:${DB_PASSWORD}@db:5432/proofhire
      REDIS_URL: redis://redis:6379
      S3_ENDPOINT_URL: http://minio:9000
      S3_ACCESS_KEY: ${S3_ACCESS_KEY}
      S3_SECRET_KEY: ${S3_SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  runner:
    build:
      context: ./runner
      dockerfile: Dockerfile
    environment:
      REDIS_URL: redis://redis:6379
      S3_ENDPOINT_URL: http://minio:9000
      S3_ACCESS_KEY: ${S3_ACCESS_KEY}
      S3_SECRET_KEY: ${S3_SECRET_KEY}
      BACKEND_URL: http://backend:8000
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - backend

  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000/api
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  minio_data:
```

### 16.2 Environment Variables

**File**: `/.env.example`

```bash
# Database
DB_PASSWORD=your_secure_password

# JWT
JWT_SECRET=your_jwt_secret_key

# S3/MinIO
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# Application
APP_ENV=production
DEBUG=false
CORS_ORIGINS=https://your-domain.com
```

### 16.3 Makefile

**File**: `/Makefile`

```makefile
.PHONY: up down logs migrate test

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

migrate:
	docker-compose exec backend alembic upgrade head

test:
	docker-compose exec backend pytest

seed:
	docker-compose exec backend python -m scripts.seed_demo
```

---

## 17. Testing Strategy

### 17.1 Test Organization

```
backend/app/tests/
├── conftest.py                  # Fixtures
├── test_proof_engine.py         # Proof rules
├── test_brief_builder.py        # Brief assembly
├── test_evidence_extractors.py  # Parsers
└── __init__.py
```

### 17.2 Test Fixtures

**File**: `/backend/app/tests/conftest.py`

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    engine = create_async_engine(settings.database_url_test)
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
def sample_metrics():
    return MetricsBundle(
        tests_passed=True,
        test_count=10,
        failed_count=0,
        duration_seconds=45.0,
        files_changed=3,
        lines_added=50,
        lines_removed=10,
        test_files_changed=1,
        line_coverage=85.0,
        branch_coverage=75.0,
        coverage_delta=5.0,
        time_to_green=30,
        submission_time=datetime.utcnow(),
        word_count=500,
        prompts_answered=4
    )

@pytest.fixture
def sample_com():
    return CompanyOperatingModel(
        pace="medium",
        quality_bar="high",
        ambiguity="medium",
        priorities=["ship_v1"],
        risk_intolerance=["data_loss"]
    )
```

### 17.3 Example Tests

```python
# test_proof_engine.py
class TestAddedRegressionTestRule:
    def test_proves_when_test_added(self, sample_metrics, sample_com):
        rule = AddedRegressionTestRule()
        claim = Claim(claim_type="added_regression_test", statement="...")

        result = rule.evaluate(
            claim, sample_metrics, {}, {}, sample_com
        )

        assert result.verdict == ProofVerdict.PROVED
        assert "test_log" in [r.key for r in result.evidence_refs]

    def test_unproved_when_tests_fail(self, sample_metrics, sample_com):
        sample_metrics.tests_passed = False
        rule = AddedRegressionTestRule()
        claim = Claim(claim_type="added_regression_test", statement="...")

        result = rule.evaluate(
            claim, sample_metrics, {}, {}, sample_com
        )

        assert result.verdict == ProofVerdict.UNPROVED
        assert "did not pass" in result.reason
```

### 17.4 Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_proof_engine.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v
```

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| COM | Company Operating Model - how a company operates |
| Rubric | Evaluation weights derived from COM |
| Claim | Assertion about candidate ability |
| Proof | Evidence-backed verification of claim |
| Brief | Summary of proven/unproven claims |
| Runner | Background worker for simulation execution |
| Artifact | File produced during simulation (diff, test log, etc.) |

---

## Appendix B: File Locations

```
proofhire/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── deps.py
│   │   ├── api/routes/
│   │   ├── core/
│   │   ├── db/
│   │   ├── proof/
│   │   ├── evidence/
│   │   ├── llm/
│   │   ├── company_model/
│   │   ├── simulations/
│   │   ├── hypothesis/
│   │   ├── briefs/
│   │   └── tests/
│   └── Dockerfile
├── runner/
│   ├── runner.py
│   ├── sandbox.py
│   ├── job_handlers.py
│   └── Dockerfile
├── web/
│   ├── src/app/
│   ├── src/components/
│   ├── src/lib/
│   └── Dockerfile
├── docker-compose.yml
├── Makefile
└── README.md
```

---

*Document generated: February 3, 2026*
