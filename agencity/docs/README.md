# Agencity Documentation

## Overview

Agencity is a proactive end-to-end hiring agent that uses graph-based intelligence to find, evaluate, and recommend candidates.

**Tagline:** Find the people you can't search for.

---

## Documentation Structure

```
docs/
├── vision/                    # Product vision & strategy
│   ├── AGENCITY_OVERVIEW.md   # Problem, solution, features
│   └── AGENCITY_VISION.md     # Full vision: graph, proactive agent, marketplace
│
├── architecture/              # Technical architecture
│   ├── AGENCITY_ARCHITECTURE.md   # High-level system design
│   └── AGENCITY_BACKEND_SPEC.md   # Detailed backend specification
│
├── research/                  # Research & exploration
│   └── AGENCITY_DATA_GRAPH_RESEARCH.md  # Data collection & graph modeling
│
├── demo/                      # Demo planning & assets
│   └── DEMO_PLAN.md           # Demo strategy and script
│
└── progress/                  # Progress tracking
    └── CHANGELOG.md           # What's been built
```

---

## Quick Links

### Vision
- [Product Overview](vision/AGENCITY_OVERVIEW.md) - Problem, solution, how it works
- [Full Vision](vision/AGENCITY_VISION.md) - Graph network, proactive agent, two-way marketplace

### Architecture
- [System Architecture](architecture/AGENCITY_ARCHITECTURE.md) - High-level design
- [Backend Spec](architecture/AGENCITY_BACKEND_SPEC.md) - Detailed implementation

### Research
- [Data & Graph Research](research/AGENCITY_DATA_GRAPH_RESEARCH.md) - Data collection, graph modeling, open questions

### Demo
- [Demo Plan](demo/DEMO_PLAN.md) - Complete demo script, narrative, and requirements

### Progress
- [Changelog](progress/CHANGELOG.md) - What's been built, in progress, and planned

---

## Current Status

### Built ✅
- FastAPI backend with conversation engine
- OpenAI GPT-4o integration
- 9 data sources (GitHub, Devpost, Codeforces, Stack Overflow, HN, etc.)
- Role Blueprint extraction from conversation
- Honest candidate evaluation (Known/Observed/Unknown)
- Basic frontend for testing

### In Progress 🔄
- Graph database schema
- Real candidate database integration
- Demo preparation

### Planned 📋
- Founder network import
- Relationship inference
- Proactive suggestions
- Candidate portal

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Role Blueprint** | Structured output from intake conversation |
| **Honest Evaluation** | Known facts, observed signals, unknowns |
| **Graph Network** | Entities + relationships as connected graph |
| **Warm Path** | Connection path from founder to candidate |
| **Proactive Agent** | Clock-cycle based candidate recommendations |

---

## Contact

- Repository: `/Users/arjunvad/Desktop/proofhire` (branch: `agencity`)
- Backend: `agencity/` directory
- Frontend: `web/src/app/agencity/`
