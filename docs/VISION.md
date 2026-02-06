# ProofHire: Evidence-Based Technical Hiring

## Executive Summary

ProofHire replaces resume-based hiring with **evidence-based evaluation** — candidates complete company-calibrated work samples, and founders receive a shareable Proof Brief showing what's proven, what isn't, and what to ask next.

**Core value proposition:**
- **For startups:** Move fast without lowering the bar. Get consistent, defensible hiring decisions.
- **For candidates:** Get hired for what you can do, not what you claim.

---

## The Problem

### Current State of Technical Hiring

1. **Resumes are narrative** — They capture credentials, not capabilities. "5 years of Python" says nothing about debugging intuition or code quality.

2. **Interviews are noisy** — Different interviewers evaluate differently. Same candidate, different outcomes.

3. **Take-homes are painful** — Hard to compare, hard to justify, hard to scale.

4. **A bad hire is existential** — When your team is 6 people, one weak hire creates drag everywhere: code quality, velocity, on-call, morale.

### The Fundamental Mismatch

Companies describe what they want in natural language (job descriptions).
Candidates describe what they offer in natural language (resumes).
Humans match these through conversation (interviews).

Every step loses information. Every step introduces bias.

---

## Our Solution: Evidence-First Hiring

### Core Concept

Replace narrative screening with **work evidence** you can trust:

1. **Candidates complete a realistic work sample** (bugfix, feature slice, refactor)
2. **System captures artifacts** (diffs, tests, logs, coverage, writeups)
3. **Proof engine evaluates claims** against evidence
4. **Founder receives a Proof Brief** with proven/unproven claims and interview prompts

### The Proof Brief

```
┌─────────────────────────────────────────────────────────────────┐
│  CANDIDATE PROOF BRIEF                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Correctness        [PROVED]     Tests + logs verify behavior   │
│  Testing habits     [PARTIAL]    Coverage good, edge cases weak │
│  Code quality       [PROVED]     Diff review + complexity ok    │
│  Communication      [UNPROVED]   → Interview prompts generated  │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  SUGGESTED INTERVIEW (30 min):                                  │
│  1. Walk through one design decision and alternatives           │
│  2. Ask for edge cases and failure modes they'd monitor         │
│  3. Have them improve one test for better coverage              │
│                                                                 │
│  Evidence links: [diff] [test-log] [coverage] [writeup]         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Properties

- **Fail-closed** — We don't guess. Claims are PROVED or UNPROVED with artifact links.
- **Company-calibrated** — You set what matters (speed vs rigor, testing bar, autonomy).
- **Defensible** — Every result traces to evidence. No mystery scoring.
- **Fast to review** — Typical founder review time: 5–8 minutes per brief.

---

## Technical Architecture

### Current Implementation (v1.0)

```
┌─────────────────────────────────────────────────────────────────┐
│                        PROOFHIRE v1.0                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   FOUNDER    │    │  SIMULATION  │    │    PROOF     │      │
│  │  CALIBRATION │───▶│   SANDBOX    │───▶│   ENGINE     │      │
│  │              │    │              │    │              │      │
│  │ Set rubric   │    │ Docker       │    │ Rule-based   │      │
│  │ weights for  │    │ isolated     │    │ claim        │      │
│  │ your startup │    │ execution    │    │ evaluation   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │     COM      │    │  ARTIFACTS   │    │ PROOF BRIEF  │      │
│  │              │    │              │    │              │      │
│  │ Company      │    │ • Diffs      │    │ • Proved     │      │
│  │ Operating    │    │ • Test logs  │    │ • Unproved   │      │
│  │ Model        │    │ • Coverage   │    │ • Interview  │      │
│  │              │    │ • Writeups   │    │   prompts    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### What We've Built

| Component | Description | Status |
|-----------|-------------|--------|
| **Simulation Sandbox** | Docker-based isolated execution with resource limits and deterministic grading | ✅ Complete |
| **Artifact Pipeline** | Collection of all candidate outputs (diffs, test logs, coverage, writeups) | ✅ Complete |
| **Evidence Extractors** | Parsers for artifact types to extract structured data | ✅ Complete |
| **Proof Engine** | Rule-based evaluation marking claims as PROVED or UNPROVED | ✅ Complete |
| **Brief Generator** | Shareable output with evidence links and interview prompts | ✅ Complete |
| **Company Operating Model** | Calibration from founder interview | ✅ Complete |
| **Rubric System** | Weighted dimensions (correctness, testing, code quality, communication) | ✅ Complete |

---

## What's Genuinely Strong

### 1. Fail-Closed Evidence Orientation

Most assessment vendors produce a score that pretends to be ground truth. Our "proved/unproved with artifact links" is:
- What buyers trust
- What legal teams tolerate
- What candidates accept

**Key advantage:** We sell "decision support + structured interview focus," not "AI decides."

### 2. Systems Layer First

Deterministic sandboxing, artifact capture, reproducibility, and audit trails are the hard parts. With this foundation, we can iterate on scoring/ML later.

### 3. Company Operating Model (COM)

A structured "how we build software here" profile useful for:
- Rubric calibration
- Interview planning
- Aligning hiring managers internally
- Consistent evaluation across interviewers

---

## Critical Gaps & Risks (Honest Assessment)

### A. "Success Profile" Learning Requires Scale

To learn "engineers who thrive here," you need:
- Enough hires per company
- Clean outcome labels (performance, retention)
- Stable team/context
- Feedback loops that aren't biased

**Reality:** Most startups hire 5–30 engineers/year. Not enough to train on.

**Implication:** System must work without outcome-trained models.

### B. "Bias-Resistant" Claims Need Careful Framing

Even hiding names/schools, we risk learning proxies:
- Writing style, time-of-day patterns
- Keystroke rhythms (can correlate with disability)
- Native language effects

**Implication:**
- Frame as "evidence-based, consistently applied rubric with audit logs"
- Don't claim "bias-resistant" — claim "job-relevant signals from work samples"
- Plan for subgroup performance measurement

### C. Telemetry is a Product-Market Hazard

Behavioral telemetry sounds high-signal but is:
- Creepy to candidates
- A compliance magnet (GDPR purpose limitation)
- A proxy-risk generator
- Easy to misinterpret (fast ≠ good)

**Safer alternative:** Capture artifact-level workflow evidence:
- Sequence of commits/diffs
- Test iterations (red/green cycles)
- Structured reflection prompts

### D. Codebase Ingestion Requires Trust

Companies worry about:
- IP leakage
- Security posture
- Training on proprietary code

**Implication:**
- Start with standardized simulations, not private repos
- Offer "no training retention" mode
- Clear contractual terms

### E. AI Assistance Will Dominate

Candidates will use AI tools. System must:
- Explicitly define what's allowed per company
- Evaluate outcomes and engineering judgment
- Require reasoning artifacts, tests, tradeoff notes

---

## Positioning (Sharpened)

### Don't Sell "Culture Fit"

Sell **working-style requirements tied to job outcomes**:
- "Writes high-coverage code under ambiguity"
- "Strong PR communication"
- Not "culture fit" (red-flag term legally)

### Don't Lead with "Model-to-Model Matching"

That sounds like "AI decides hiring" → triggers resistance.

**Lead with:** "Company-calibrated work sample + proof packet + interview plan"

### Don't Claim "Bias-Resistant"

**Claim:** "Evidence-based, consistently applied rubric with audit logs"

---

## The Wedge Product

**"Company-calibrated work sample + proof packet + interview plan"**

### Inputs
- 10–15 min hiring manager calibration (COM)
- Role expectations + sample PRs or style guide (optional)
- Choose from library of job-realistic tasks

### Outputs
- **Proof packet** (what's proven, with links)
- **Structured interview guide** (what to verify live)
- **Risk flags** grounded in evidence

### Why This Sells
- Immediate ROI
- Minimal trust barriers (no codebase ingest required)
- Works with low data
- Aligns with compliance ("here's the evidence")

---

## Competitive Landscape

| Company | Approach | Limitation |
|---------|----------|------------|
| **HackerRank/LeetCode** | Algorithmic puzzles | Tests puzzle-solving, not real work |
| **Triplebyte** (defunct) | Standardized quiz | One-size-fits-all, no company calibration |
| **Karat** | Human interviewers | Expensive, inconsistent, not scalable |
| **Vervoe** | Job simulations | No fail-closed evaluation, rule-based scoring |
| **Pymetrics** | Behavioral games | No technical assessment, games ≠ work |
| **Eightfold.ai** | Resume parsing + ML | Still based on resume claims, not demonstrated work |

### ProofHire's Differentiation
- Only platform with fail-closed, legally defensible evaluation
- Only platform producing shareable Proof Briefs with artifact links
- Only platform generating interview prompts from unproved claims
- Built for early startups, not enterprise process

---

## Roadmap

### Phase 1: Foundation ✅
- Rule-based evaluation infrastructure
- Simulation sandbox
- Artifact collection
- Basic COM from calibration
- Proof Brief generation

### Phase 2: Signal Expansion
- Add more simulation types (bugfix, feature, refactor)
- Seeded-bug variant tasks (high signal, job-like)
- Structured reflection prompts
- Improved rubric taxonomy

### Phase 3: Scale Features
- ATS integration (Ashby, Lever, Greenhouse)
- Candidate reusable profiles
- Outcome feedback loop (where data exists)
- Dynamic task variations (prevent cheating)

### Phase 4: Advanced (If/When Data Supports)
- Company embedding from calibration + outcomes
- Similarity-based matching
- Continuous model improvement

---

## Target Market

**Primary:** Seed to Series A startups hiring first 5–50 engineers

**Buyer:** Founder / Head of Engineering / First EM

**Why startups:**
- Feel the pain most acutely (one bad hire is existential)
- Move fast, willing to try new tools
- Less procurement friction than enterprise
- Value speed + signal over process

---

## Success Metrics (What We'll Measure)

1. **Engineer interview hours saved** per hire
2. **On-site-to-offer conversion** improvement
3. **Hiring manager satisfaction** (NPS)
4. **Candidate drop-off rate** (must stay low)
5. **False negative audits** (strong candidates we rejected)

---

## Technical Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS |
| **Backend** | FastAPI, Python 3.11, Async SQLAlchemy |
| **Database** | PostgreSQL 15 |
| **Cache/Queue** | Redis 7 |
| **Object Storage** | S3-compatible (MinIO in dev) |
| **Sandbox** | Docker with resource limits, network isolation |
| **Infrastructure** | Docker Compose (dev), Kubernetes (planned prod) |

---

## Conclusion

ProofHire is building evidence-first hiring for early startups. The current system delivers:
- Secure execution and artifact capture
- Fail-closed evaluation with Proof Briefs
- Company-calibrated rubrics
- Interview prompts from unproved claims

The result is hiring that is:
- **Faster** — Review a brief in minutes, not an hour-long debrief
- **More consistent** — Same rubric, same evidence standard
- **More defensible** — Every decision traces to artifacts
- **More focused** — Interviews target what's actually unproven

---

*Document Version: 2.0*
*Last Updated: February 2026*
*Status: Internal*
