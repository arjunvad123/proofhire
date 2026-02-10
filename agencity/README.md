# Agencity

AI hiring agent that finds people you can't search for.

## Overview

Agencity helps early-stage founders find hidden talent through:

1. **Conversational Intake** - Tell us what you need (even if vague), we ask smart follow-up questions
2. **Multi-Source Search** - We search our network, GitHub, hackathons, and more
3. **Honest Evaluation** - We tell you what we know (facts), what we observed (signals), and what you'll need to verify (unknowns)
4. **Shortlist Generation** - Candidates worth a 30-minute conversation

## Quick Start

```bash
# Install dependencies
pip install -e .

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn app.main:app --reload --port 8001
```

## API Endpoints

### Conversations

```bash
# Start a conversation
POST /api/conversations
{
  "user_id": "founder123",
  "initial_message": "I need a prompt engineer for my startup"
}

# Send a message
POST /api/conversations/{id}/message
{
  "content": "We're building an AI writing assistant..."
}

# Get blueprint
GET /api/conversations/{id}/blueprint
```

### Shortlists

```bash
# Search with a blueprint
POST /api/shortlists/search
{
  "blueprint": {
    "role_title": "Prompt Engineer",
    "company_context": "...",
    ...
  }
}

# Get shortlist
GET /api/shortlists/{id}

# Submit feedback
POST /api/shortlists/{id}/feedback
{
  "candidate_id": "...",
  "decision": "interested",
  "reason": "Great GitHub activity"
}
```

## Architecture

```
agencity/
├── app/
│   ├── api/              # FastAPI routes
│   ├── core/             # Core engines
│   │   ├── context_manager.py    # OpenClaw-inspired context pruning
│   │   ├── conversation_engine.py # Intake conversation
│   │   ├── evaluation_engine.py   # Honest candidate assessment
│   │   └── search_engine.py       # Multi-source search
│   ├── models/           # Pydantic models
│   ├── sources/          # Data sources (GitHub, Network, etc.)
│   ├── services/         # LLM, enrichment services
│   └── rag/              # Hybrid search (to be implemented)
├── tests/
└── scripts/
```

## Key Design Principles

1. **Honest by Design** - No fake match scores. Known facts, observed signals, unknowns.
2. **Context Management** - Multi-stage pruning, protected contexts (from OpenClaw)
3. **Multi-Source** - Search where others don't (GitHub, hackathons, clubs)
4. **Feedback Loop** - Learn from founder decisions to improve ranking

## Environment Variables

See `.env.example` for all configuration options.

Required:
- `ANTHROPIC_API_KEY` - Claude API for conversation and evaluation
- `GITHUB_TOKEN` - GitHub API for developer search

Optional:
- `PDL_API_KEY` - People Data Labs for enrichment
- `DATABASE_URL` - PostgreSQL (for persistence, currently in-memory)
