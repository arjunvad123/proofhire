# ProofHire Intelligence System - Master Architecture

## Overview

ProofHire is a network-first candidate intelligence platform. Our core insight: **"Clado tells you WHO to hire. We tell you HOW TO REACH THEM."**

This document describes the unified architecture that combines:
- **V1-V5 Search Systems** - Progressive evolution of candidate search
- **4 Pillars of Intelligence** - Network activation, timing, expansion, company events
- **Kimi K2.5 Reasoning** - Advanced AI for candidate analysis
- **RL Feedback Loop** - Continuous improvement from hiring outcomes
- **Prediction Layer** - Anticipate what founders need before they ask

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MASTER ORCHESTRATOR                                  │
│                    (app/services/master_orchestrator.py)                     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      REASONING LAYER (Kimi K2.5)                       │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │   Query     │  │  Candidate  │  │   Ranking   │  │   Context   │   │ │
│  │  │  Reasoning  │  │   Analysis  │  │  Reasoning  │  │   Builder   │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      INTELLIGENCE LAYER                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │  Activation │  │   Timing    │  │  Expansion  │  │   Company   │   │ │
│  │  │   (Pillar1) │  │  (Pillar2)  │  │  (Pillar3)  │  │  (Pillar4)  │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        SEARCH LAYER                                    │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │ │
│  │  │   V1    │  │   V2    │  │   V3    │  │   V4    │  │   V5    │     │ │
│  │  │ Gateway │  │ Tiered  │  │ Hybrid  │  │Curation │  │ Unified │     │ │
│  │  │ Search  │  │ Search  │  │ Search  │  │ Engine  │  │ Search  │     │ │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        DATA LAYER                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │  Network    │  │  External   │  │   Warm      │  │   Deep      │   │ │
│  │  │  Index      │  │   APIs      │  │   Paths     │  │  Research   │   │ │
│  │  │ (Supabase)  │  │ (Clado/PDL) │  │  (Finder)   │  │ (Perplexity)│   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     FEEDBACK & LEARNING LAYER                          │ │
│  │  ┌─────────────────────────┐    ┌─────────────────────────────────┐   │ │
│  │  │    Feedback Collector   │ → │     Reward Model (GRPO)         │   │ │
│  │  │  (user actions on       │    │  (trained on hire/reject        │   │ │
│  │  │   candidates)           │    │   outcomes)                     │   │ │
│  │  └─────────────────────────┘    └─────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      PREDICTION LAYER (NEW)                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │   Query     │  │    Role     │  │  Candidate  │  │   Skill     │   │ │
│  │  │Autocomplete │  │  Suggester  │  │  Surfacer   │  │ Predictor   │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  │  ┌─────────────┐  ┌─────────────┐                                     │ │
│  │  │  Warm Path  │  │  Interview  │                                     │ │
│  │  │   Alerter   │  │  Predictor  │                                     │ │
│  │  └─────────────┘  └─────────────┘                                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Search Systems (V1-V5)

Each version adds capabilities while maintaining backward compatibility:

| Version | Name | Key Capability | Entry Point |
|---------|------|----------------|-------------|
| V1 | Gateway Search | Network-driven pathways, multi-source parallel | `app/search/engine.py` |
| V2 | Tiered Search | Network-first (Tier 1-4), readiness scoring | `app/search/engine_v2.py` |
| V3 | Hybrid Search | External APIs + warm path finding | `app/services/search_orchestrator.py` |
| V4 | Curation Engine | Progressive enrichment, deep research | `app/services/curation_engine.py` |
| V5 | Unified Search | All above + timing intelligence | `app/services/unified_search.py` |

### 2. Intelligence Pillars

Four independent intelligence modules that feed signals into search:

#### Pillar 1: Network Activation (`app/intelligence/activation/`)
- **Purpose**: Ask your network directly instead of searching
- **Key Class**: `ReverseReferenceGenerator`
- **Output**: Recommendations from trusted contacts

#### Pillar 2: Timing Intelligence (`app/intelligence/timing/`)
- **Purpose**: Predict who's ready to move before they know
- **Key Classes**: `ReadinessScorer`, `TenureTracker`, `VestingPredictor`
- **Signals**: Layoff exposure, tenure milestones, vesting cliffs, profile activity

#### Pillar 3: Expansion (`app/intelligence/expansion/`)
- **Purpose**: Find former colleagues of network members
- **Key Class**: `ColleagueExpander`
- **Output**: Candidates with warm paths through employment history

#### Pillar 4: Company Intelligence (`app/intelligence/company/`)
- **Purpose**: Monitor events at companies where network works
- **Key Classes**: `CompanyEventMonitor`, `LayoffTracker`, `AlertGenerator`
- **Output**: Alerts when network members may be ready to move

### 3. Reasoning Layer (Kimi K2.5)

New AI reasoning capabilities using Kimi K2.5:

```
app/services/reasoning/
├── kimi_engine.py          # Main Kimi K2.5 wrapper
├── query_reasoner.py       # Generate smart search queries
├── candidate_analyzer.py   # Deep analysis of candidates
├── ranking_reasoner.py     # Explain ranking decisions
└── agent_swarm.py          # Coordinate parallel analysis
```

#### Capabilities:
1. **Query Reasoning**: Generate intelligent queries based on role + network context
2. **Candidate Analysis**: Multi-agent analysis (skills, trajectory, fit, timing)
3. **Ranking Reasoning**: Explain why candidates are ranked
4. **Context Building**: Generate rich "why consider" narratives

### 4. Feedback & Learning Layer

```
app/services/feedback/
├── collector.py            # Record user actions
└── storage.py              # Persist to Supabase

app/services/rl/
├── reward_model.py         # Score reasoning quality
├── trainer.py              # GRPO training loop
└── online_learner.py       # Continuous improvement
```

#### Feedback Signals:
| Action | Reward |
|--------|--------|
| Candidate hired | +10 |
| Candidate interviewed | +5 |
| Candidate contacted | +2 |
| Candidate saved | +1 |
| Candidate ignored | -1 |
| Candidate rejected | -5 |

---

## Data Flow

### Standard Search Flow

```
1. User Request
   └─→ POST /api/search
       ├─ role_title: "ML Engineer"
       ├─ required_skills: ["Python", "PyTorch"]
       └─ company_id: "uuid"

2. Master Orchestrator
   ├─→ Build Network Index
   │   └─→ Supabase: 1000 contacts, 500 companies
   │
   ├─→ Reasoning Layer (Kimi K2.5)
   │   ├─→ Query Reasoner: Generate smart queries
   │   │   "ML engineers who worked at {network_companies} or went to {network_schools}"
   │   │
   │   └─→ Agent Swarm: Prepare analysis agents
   │
   ├─→ Search Layer (parallel)
   │   ├─→ Network Search (V5): 15 direct matches
   │   └─→ External Search (Clado): 50 external profiles
   │
   ├─→ Warm Path Finding
   │   └─→ 20 external have warm paths
   │
   ├─→ Intelligence Layer
   │   ├─→ Timing Signals: 8 high urgency
   │   ├─→ Company Events: 3 layoff exposure
   │   └─→ Vesting Cliffs: 5 approaching cliffs
   │
   ├─→ Candidate Analysis (Kimi Agent Swarm)
   │   ├─→ Skill Agent: Verify skills match
   │   ├─→ Trajectory Agent: Analyze career path
   │   ├─→ Fit Agent: Cultural/stage fit
   │   └─→ Timing Agent: Readiness signals
   │
   ├─→ Scoring & Ranking
   │   ├─→ Fit Score (50%) + Warmth (30%) + Timing (20%)
   │   └─→ Reward Model: Adjust based on learned preferences
   │
   ├─→ Deep Research (top 5)
   │   └─→ Perplexity: GitHub, articles, projects
   │
   └─→ Context Building
       └─→ "Why consider" + "Unknowns" for each

3. Response
   └─→ 20 candidates, ranked by combined score
       ├─ Tier 1 (network): 8
       ├─ Tier 2 (warm): 7
       └─ Tier 3 (cold): 5
```

### Feedback Loop

```
User Action (e.g., marks candidate as "interviewed")
  │
  ▼
Feedback Collector
  │
  ├─→ Store: {candidate_id, action, timestamp, context}
  │
  └─→ Training Pipeline (async)
      │
      ├─→ Batch feedback (nightly)
      │
      ├─→ Generate (candidate, reasoning, outcome) triplets
      │
      ├─→ GRPO Training Step
      │   └─→ Update reward model weights
      │
      └─→ Deploy updated model
          └─→ Future rankings use improved model
```

### Prediction Layer

The Prediction Layer anticipates what founders need before they ask. It combines 6 predictive components:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PREDICTION ENGINE                                   │
│                    (app/services/prediction/engine.py)                       │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │  Query Autocomplete │  │   Role Suggester    │  │ Candidate Surfacer  │ │
│  │  - Trie matching    │  │  - Stage patterns   │  │  - Layoff signals   │ │
│  │  - History learning │  │  - Team ratios      │  │  - Tenure cliffs    │ │
│  │  - Popular queries  │  │  - Gap analysis     │  │  - Open to work     │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │   Skill Predictor   │  │  Warm Path Alerter  │  │ Interview Predictor │ │
│  │  - Role templates   │  │  - Target companies │  │  - Historical fit   │ │
│  │  - Skill clustering │  │  - Network changes  │  │  - Pattern matching │ │
│  │  - Requirements     │  │  - New connections  │  │  - Reward model     │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Component | Description | Key Features |
|-----------|-------------|--------------|
| Query Autocomplete | Suggest search queries as founder types | Trie data structure, history learning, role patterns |
| Role Suggester | Predict what roles to hire next | Stage-based (seed→series A), team ratio analysis |
| Candidate Surfacer | Surface candidates who just became available | Layoff monitoring, tenure cliffs, Open to Work |
| Skill Predictor | Auto-suggest requirements for roles | Industry templates, skill clustering |
| Warm Path Alerter | Alert when network creates opportunities | Target company tracking, promotion alerts |
| Interview Predictor | Predict which candidates will be interviewed | Historical patterns, reward model integration |

---

## Scoring Formula

### Current (Deterministic)
```python
combined_score = (
    fit_score * 0.50 +      # Skills/experience match
    warmth_score * 0.30 +   # Connection strength
    timing_score * 0.20     # Readiness signals
)
```

### Future (RL-Enhanced)
```python
# Base score
base_score = fit * 0.50 + warmth * 0.30 + timing * 0.20

# Reasoning quality from Kimi
reasoning_chain = kimi.analyze(candidate, role)
reasoning_score = reward_model.score(reasoning_chain)

# Final score adjusted by learned preferences
combined_score = base_score * reasoning_score * user_preference_adjustment
```

---

## Warmth Score Calculation

| Relationship Type | Warmth Score |
|-------------------|--------------|
| Direct network connection | 100% |
| Current company overlap | 75-80% |
| Past company overlap | 60-70% |
| School overlap | 50% |
| Skill/interest overlap | 30% |
| 2nd degree connection | 20-40% |
| Cold (no connection) | 0% |

---

## File Structure

```
app/
├── api/routes/
│   ├── search.py           # V1 API
│   ├── search_v2.py        # V2 API
│   ├── search_v3.py        # V3 API
│   ├── curation.py         # V4 API
│   ├── unified.py          # V5 API
│   └── intelligence.py     # Intelligence API
│
├── search/
│   ├── engine.py           # V1 Search Engine
│   ├── engine_v2.py        # V2 Search Engine
│   ├── network_search.py   # Network-only search
│   ├── readiness.py        # Readiness scoring
│   ├── recruiters.py       # Recruiter finding
│   ├── warm_path.py        # Warm path calculation
│   ├── models.py           # Data models
│   ├── analyzers/          # Network analysis
│   ├── scoring/            # Pathway & candidate scoring
│   ├── generators/         # Query generation
│   └── sources/            # External data sources
│
├── services/
│   ├── unified_search.py   # V5 Unified Engine
│   ├── search_orchestrator.py  # V3 Orchestrator
│   ├── curation_engine.py  # V4 Curation
│   ├── network_index.py    # Network indexing
│   ├── warm_path_finder.py # Warm path finding
│   ├── company_db.py       # Company data access
│   ├── external_search/    # Clado, PDL clients
│   ├── research/           # Deep research (Perplexity)
│   ├── reasoning/          # [NEW] Kimi K2.5 reasoning
│   │   ├── kimi_engine.py
│   │   ├── query_reasoner.py
│   │   ├── candidate_analyzer.py
│   │   └── agent_swarm.py
│   ├── feedback/           # [NEW] Feedback collection
│   │   ├── collector.py
│   │   └── storage.py
│   ├── rl/                 # [NEW] Reinforcement learning
│   │   ├── reward_model.py
│   │   └── trainer.py
│   └── prediction/         # [NEW] Prediction layer
│       ├── engine.py           # Unified prediction engine
│       ├── query_autocomplete.py
│       ├── role_suggester.py
│       ├── candidate_surfacer.py
│       ├── skill_predictor.py
│       ├── warm_path_alerter.py
│       └── interview_predictor.py
│
├── intelligence/
│   ├── activation/         # Pillar 1: Network asks
│   ├── timing/             # Pillar 2: Readiness signals
│   ├── expansion/          # Pillar 3: Colleague expansion
│   └── company/            # Pillar 4: Company events
│
└── models/
    ├── curation.py         # Curation data models
    └── candidate.py        # Candidate models
```

---

## API Endpoints Summary

### Search Endpoints
| Method | Path | Description | Version |
|--------|------|-------------|---------|
| POST | `/companies/{id}/search` | Gateway search | V1 |
| POST | `/v2/search` | Tiered search | V2 |
| POST | `/v3/search/hybrid` | Hybrid search | V3 |
| POST | `/v1/curation/curate` | Curation | V4 |
| POST | `/search` | Unified search | V5 |
| POST | `/search/network-only` | Network only | V5 |
| POST | `/search/quick` | Fast search | V5 |

### Intelligence Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v3/activate/reverse-reference` | Ask network for recs |
| GET | `/v3/timing/alerts` | Timing-based alerts |
| POST | `/v3/expansion/colleagues` | Find former colleagues |
| GET | `/v3/company/events` | Company events |

### Feedback Endpoints (NEW)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/feedback/action` | Record user action |
| GET | `/feedback/stats` | Feedback statistics |

### Prediction Endpoints (NEW)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/predictions/{company_id}` | Full prediction insights |
| GET | `/predictions/{company_id}/dashboard` | Dashboard-optimized insights |
| GET | `/predictions/autocomplete` | Query autocomplete |
| GET | `/predictions/{company_id}/roles` | Suggested roles to hire |
| GET | `/predictions/{company_id}/candidates` | Surfaced candidates |
| GET | `/predictions/{company_id}/alerts` | Warm path alerts |
| GET | `/predictions/{company_id}/hiring-plan` | Suggested hiring plan |
| POST | `/predictions/role-requirements` | Auto-fill role requirements |

---

## Implementation Phases

### Phase 1: Fix Existing Systems (Current)
1. Fix V2 imports (engine_v2.py)
2. Fix V3 intelligence imports
3. Fix V4 curation initialization
4. Verify all systems work independently

### Phase 2: Create Reasoning Layer
1. Set up Kimi K2.5 API access
2. Create kimi_engine.py wrapper
3. Implement query_reasoner.py
4. Implement candidate_analyzer.py

### Phase 3: Create Feedback System
1. Create feedback collector
2. Create Supabase tables for feedback
3. Wire up API endpoints

### Phase 4: Create RL System
1. Create reward model architecture
2. Implement GRPO trainer
3. Create online learning loop

### Phase 5: Create Master Orchestrator
1. Combine all systems
2. Create single entry point
3. Add caching and optimization

### Phase 6: Create Prediction Layer ✅ COMPLETE
1. Create prediction engine (engine.py)
2. Implement query autocomplete (trie + history)
3. Implement role suggester (stage patterns + ratios)
4. Implement candidate surfacer (timing signals)
5. Implement skill predictor (role templates)
6. Implement warm path alerter (network monitoring)
7. Implement interview predictor (patterns + RL)
8. Integrate with master orchestrator

### Phase 7: Testing & Validation
1. Unit tests for each component
2. Integration tests for full flow
3. A/B testing framework

---

## Configuration

### Environment Variables
```bash
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx

# External APIs
CLADO_API_KEY=xxx
PDL_API_KEY=xxx
PERPLEXITY_API_KEY=xxx

# Reasoning (Kimi K2.5)
KIMI_API_KEY=xxx
KIMI_API_URL=https://api.moonshot.cn/v1

# Feature Flags
ENABLE_EXTERNAL_SEARCH=true
ENABLE_TIMING_INTELLIGENCE=true
ENABLE_DEEP_RESEARCH=true
ENABLE_KIMI_REASONING=true
ENABLE_RL_RANKING=false  # Enable after training
```

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Search latency (network only) | <500ms | ~700ms |
| Search latency (full unified) | <3s | ~5s |
| Network index build | <200ms | ~300ms |
| Candidates per search | 20 | 20 |
| Deep research per search | 5 | 5 |
| Warm path match rate | >30% | ~25% |

---

## Future Roadmap

1. **Self-hosted Kimi K2.5** - Reduce API costs, full control
2. **Real-time feedback** - Improve ranking in real-time
3. **Multi-role optimization** - Learn across all roles
4. **Candidate re-engagement** - Track candidates over time
5. **Automated outreach** - Generate personalized messages

---

*Last updated: 2026-02-13*
