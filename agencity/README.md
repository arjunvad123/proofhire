# Agencity

**AI hiring agent that finds people you can't search for.**

A proactive end-to-end hiring agent for early-stage startups. Tell us what you need (even if vague), and we'll find candidates worth a 30-minute conversation.

## Demo

![Agencity Demo](docs/demo/screenshot.png)

**Live Demo:** Start the server and visit `http://localhost:3000/agencity`

## Features

### 1. Conversational Intake
Tell us what you need in natural language. We ask smart follow-up questions to understand what you actually mean.

```
You: "I need a prompt engineer for my AI startup"
Agent: "Got it. What does your startup do, and what will this person actually work on?"
You: "We're building an LLM writing assistant. They'll work on RAG systems and prompt optimization."
Agent: "What would success look like by day 60?"
...
```

### 2. Multi-Source Search
We search where others don't:
- **Our Network** (1,375+ candidates in Supabase)
- **GitHub** activity and repositories
- **Devpost** hackathon projects
- **Codeforces** competitive programming
- **Stack Overflow** contributions
- **HackerNews** activity

### 3. Honest Evaluation
No fake match scores. We tell you:
- **Known Facts** - Verifiable info (school, work history, public projects)
- **Observed Signals** - GitHub activity, hackathon wins, etc.
- **Unknown** - What you'll need to verify in conversation
- **Why Consider** - Connection to your specific needs
- **Next Step** - What to ask them first

### 4. Intelligent Scoring
Candidates are ranked based on:
- AI/ML skill signals (LangChain, RAG, LLMs, PyTorch, etc.)
- Production experience at AI companies
- Hackathon wins and project deployments
- Location preferences
- GitHub activity

## Quick Start

### Backend

```bash
cd agencity

# Install dependencies
pip install -e .

# Copy environment file
cp .env.example .env

# Add your API keys to .env:
# - ANTHROPIC_API_KEY (required)
# - GITHUB_TOKEN (optional)
# - SUPABASE_URL and SUPABASE_KEY (for real candidate data)

# Run the server
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd ../web

# Install dependencies
npm install

# Run the dev server
npm run dev
```

Visit `http://localhost:3000/agencity` for the polished demo.

## API Endpoints

### Conversations

```bash
# Start a conversation
POST /api/conversations
{
  "user_id": "founder123",
  "initial_message": "I need a prompt engineer for my startup"
}

# Response
{
  "id": "conv-abc123",
  "status": "in_progress",
  "message": "Got it. What does your startup do, and what will this person actually work on?",
  "blueprint": null
}

# Send a message
POST /api/conversations/{id}/message
{
  "content": "We're building an AI writing assistant with RAG"
}

# Get the extracted blueprint
GET /api/conversations/{id}/blueprint
```

### Shortlists

```bash
# Search with a blueprint
POST /api/shortlists/search
{
  "blueprint": {
    "role_title": "Prompt Engineer",
    "company_context": "AI startup building LLM applications",
    "specific_work": "Build and optimize RAG systems",
    "success_criteria": "Ship production RAG system in 60 days",
    "must_haves": ["LLM", "Python", "RAG"],
    "nice_to_haves": ["LangChain", "FastAPI"],
    "location_preferences": ["Waterloo", "Remote"]
  }
}

# Response
{
  "candidates": [
    {
      "id": "cand-123",
      "name": "Rohan Juneja",
      "tagline": "University of Waterloo · ML Engineer at Nokia",
      "known_facts": [
        "University of Waterloo student",
        "ML Engineer intern at Nokia",
        "Built production LangChain/LangGraph systems"
      ],
      "observed_signals": [
        "GitHub: Active contributor with ML projects",
        "Experience with RAG and vector databases"
      ],
      "unknown": [
        "Availability for startup pace",
        "Salary expectations"
      ],
      "why_consider": "Has exactly the production LLM/RAG experience you need, at a top CS school",
      "next_step": "Ask about his Nokia work and interest in early-stage startups"
    }
  ]
}

# Get demo candidates
GET /api/shortlists/demo/candidates
```

## Architecture

```
agencity/
├── app/
│   ├── api/routes/          # FastAPI endpoints
│   │   ├── conversations.py # Conversation management
│   │   └── shortlists.py    # Search and shortlists
│   ├── core/                # Core engines
│   │   ├── conversation_engine.py  # Intake conversation with Claude
│   │   ├── evaluation_engine.py    # Honest candidate assessment
│   │   └── search_engine.py        # Multi-source orchestration
│   ├── models/              # Pydantic models
│   │   ├── blueprint.py     # RoleBlueprint schema
│   │   └── candidate.py     # CandidateData schema
│   ├── sources/             # Data sources
│   │   ├── network.py       # Supabase candidate database
│   │   ├── github.py        # GitHub API
│   │   └── ...              # Other sources
│   ├── services/            # External services
│   │   ├── supabase.py      # Supabase REST client
│   │   └── llm.py           # Claude API wrapper
│   └── config.py            # Settings management
├── scripts/                 # Utility scripts
│   ├── demo_conversation.py # Run full demo
│   ├── debug_scoring.py     # Test scoring algorithm
│   └── ...
├── docs/
│   └── demo/
│       └── HERO_CANDIDATES.md  # Top demo candidates
└── tests/
```

## Key Design Principles

### 1. Honest by Design
We don't make claims we can't verify. Every candidate profile clearly separates:
- What we **know** (verified facts)
- What we **observed** (signals from activity)
- What's **unknown** (needs verification)

### 2. Production Experience Matters
Our scoring algorithm heavily weights actual production experience:
- Work at AI companies (Nokia, Cohere, OpenAI, etc.) → +50 points
- Production AI skills with work experience → +20 per skill
- Hackathon wins → +25 points
- Deployed projects → +15 points

### 3. Multi-Source Intelligence
We search sources others don't:
- University clubs and organizations
- Hackathon participation
- GitHub contribution patterns
- Technical community activity

### 4. Feedback Loop
Founder decisions improve future rankings (coming soon).

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...       # Claude API for conversation

# Candidate Database (Supabase)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...                 # Service role key

# Optional
GITHUB_TOKEN=ghp_...               # GitHub API for enrichment
PDL_API_KEY=...                    # People Data Labs
```

## Hero Candidates (Demo)

For demo purposes, these candidates showcase the system's capabilities:

| Name | School | Key Signals |
|------|--------|-------------|
| Rohan Juneja | Waterloo | Nokia ML intern, LangChain/LangGraph, Production RAG |
| Gbemileke Olaifa | Waterloo | LLM projects, Hackathon winner |
| Aaron Leo | UMass | Full-stack AI, Multiple projects |
| Owen Sawyer | Unknown | Senior dev, AI experience |
| Michelle Bakels | Industry | Senior AI architect |

See [docs/demo/HERO_CANDIDATES.md](docs/demo/HERO_CANDIDATES.md) for detailed profiles.

## Development

### Running Tests
```bash
pytest tests/
```

### Debugging Scoring
```bash
python scripts/debug_scoring.py
```

### Testing the Full Flow
```bash
python scripts/demo_conversation.py
```

## Tech Stack

- **Backend:** FastAPI, Python 3.11+
- **Frontend:** Next.js 14, React, Tailwind CSS, Framer Motion
- **Database:** Supabase (PostgreSQL)
- **AI:** Claude (Anthropic) for conversation and evaluation
- **APIs:** GitHub, Devpost, Codeforces, Stack Overflow

## License

Proprietary - All rights reserved.
