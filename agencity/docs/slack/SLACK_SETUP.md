# Hermes Slack Bot Setup Guide

## Unified Agent: Dual-Source Candidate Discovery

**Version 3.0** | Updated: February 12, 2026

---

## Overview

The Hermes Slack bot searches **~5,000 candidates** across two sources and delivers shortlists with **Proof Briefs** - structured reasoning showing evidence and confidence for each recommendation.

```
@hermes I need a prompt engineer for my AI startup
```

Hermes will:
1. Ask clarifying questions in the thread
2. Search across **both** data sources:
   - **Hermes Database**: 1,375+ opted-in candidates with verified GitHub repos
   - **LinkedIn Network**: 3,637 connections with warm introduction paths
3. Deduplicate and merge candidates found in both sources
4. Generate **Proof Briefs** with honest evaluations (Known Facts, Signals, Unknowns)
5. Deliver a **10-15 candidate shortlist** directly in Slack

---

## Data Sources

| Source | Size | Quality | Strengths |
|--------|------|---------|-----------|
| **Hermes** | 1,375+ | High (verified) | Opted-in, GitHub repos, verified skills |
| **Network** | 3,637 | Medium (30% complete) | Warm paths, current employment, network proximity |

**Combined Pool**: ~5,000 unique candidates (with ~120 appearing in both)

---

## How the Agent Reasons

### Proof Brief Structure

For each candidate, Hermes generates a **Proof Brief**:

```
#1 - Sarah Chen
ML Engineer @ OpenAI
Score: 87/100 (85% confidence)
Sources: Hermes | Network | Multi-source

KNOWN FACTS:
  • 3 years prompt engineering at OpenAI (Hermes - verified)
  • Published papers on LLM optimization (GitHub - verified)
  • MIT CS grad, focus on NLP (Hermes - opted-in data)

KEY SIGNALS:
  • Recently updated LinkedIn (may be exploring)
  • GitHub active with prompt engineering repos

UNKNOWN:
  • Current compensation expectations
  • Interest in early-stage startups

WARM PATH: Connected via John (worked together at Google)

NEXT STEP: Ask John for intro, mention RAG project
```

### Scoring Algorithm

```
Final Score = (
    30% Skills Match +
    25% Experience Match +
    15% Source Quality +
    15% Network Proximity +
    10% Readiness Signals +
    5%  Culture Signals
)
```

### Confidence Levels

| Indicator | Confidence | Meaning |
|-----------|------------|---------|
| Green | >70% | High-quality data, multiple sources |
| Yellow | 40-70% | Some data gaps, may need enrichment |
| Red | <40% | Limited data, conservative estimate |

---

## Prerequisites

- A Slack workspace where you have admin permissions
- The Agencity backend running (locally or deployed)
- A public URL for webhooks (use ngrok for local development)
- Supabase database configured (contains both `candidates` and `people` tables)

---

## Step 1: Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Name it **"Hermes"** (or your preferred name)
5. Select your workspace

---

## Step 2: Configure Bot Permissions

### OAuth & Permissions

Navigate to **OAuth & Permissions** in the sidebar.

Add these **Bot Token Scopes**:

| Scope | Purpose |
|-------|---------|
| `app_mentions:read` | Receive @hermes mentions |
| `chat:write` | Send messages and shortlists |
| `commands` | Slash commands |
| `im:history` | Read DM history for context |
| `im:read` | Access DMs |
| `im:write` | Send DMs |
| `reactions:write` | Add status reactions |

### Install to Workspace

1. Click **"Install to Workspace"**
2. Authorize the permissions
3. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

---

## Step 3: Enable Event Subscriptions

Navigate to **Event Subscriptions** in the sidebar.

1. Toggle **"Enable Events"** to ON
2. Set the **Request URL** to: `https://your-domain.com/api/slack/events`
   - For local dev: Use ngrok (see below)
3. Wait for the URL to be verified

### Subscribe to Bot Events

Add these events:

| Event | Purpose |
|-------|---------|
| `app_mention` | When someone @mentions the bot |
| `message.im` | Direct messages to the bot |

---

## Step 4: Configure Slash Commands (Optional)

Navigate to **Slash Commands** in the sidebar.

Click **"Create New Command"**:

| Field | Value |
|-------|-------|
| Command | `/hermes` |
| Request URL | `https://your-domain.com/api/slack/commands` |
| Short Description | Search ~5,000 candidates for your role |
| Usage Hint | `[role description]` |

---

## Step 5: Get App Credentials

Navigate to **Basic Information** in the sidebar.

Copy these values:
- **Signing Secret** (under "App Credentials")
- **Client ID** (if using OAuth install flow)
- **Client Secret** (if using OAuth install flow)

---

## Step 6: Configure Environment Variables

Add these to your `.env` file:

```bash
# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# Optional: For OAuth install flow
SLACK_CLIENT_ID=your-client-id
SLACK_CLIENT_SECRET=your-client-secret
SLACK_REDIRECT_URI=https://your-domain.com/api/slack/oauth/callback

# Supabase (single database for both sources)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx

# Enrichment APIs
OPENAI_API_KEY=xxx
PERPLEXITY_API_KEY=xxx

# Agent Tuning (optional - defaults shown)
SEARCH_HERMES_WEIGHT=0.95
SEARCH_NETWORK_WEIGHT=0.70
ENRICHMENT_TOP_N=30
DEEP_RESEARCH_TOP_N=5
SHORTLIST_SIZE=12
```

---

## Step 7: Local Development with ngrok

For local development, you need a public URL. Use ngrok:

```bash
# Install ngrok
brew install ngrok

# Start your backend
uvicorn app.main:app --reload --port 8001

# In another terminal, start ngrok
ngrok http 8001
```

Copy the ngrok URL (e.g., `https://abc123.ngrok.io`) and use it for:
- Event Subscriptions Request URL: `https://abc123.ngrok.io/api/slack/events`
- Slash Command Request URL: `https://abc123.ngrok.io/api/slack/commands`

**Note:** ngrok URLs change each time you restart. Update Slack settings accordingly.

---

## Step 8: Test the Bot

1. Go to any channel in your Slack workspace
2. Invite the bot: `/invite @Hermes`
3. Mention the bot: `@Hermes I need a prompt engineer for my AI startup`
4. The bot should:
   - Add a reaction (thinking, then check or X)
   - Ask clarifying questions
   - Search ~5,000 candidates
   - Return a shortlist with Proof Briefs

---

## Usage Examples

### Basic Search
```
@hermes I need a prompt engineer for my AI startup
```

### With Details
```
@hermes Looking for a backend engineer who knows Python and FastAPI,
preferably from Waterloo or willing to work remote
```

### In a Thread (Recommended)
```
You: @hermes I need a prompt engineer

Hermes: I'll help you find prompt engineers. A few quick questions:
        1. What does your startup do specifically?
        2. What will this person work on day-to-day?
        3. Any must-have skills or background?

You: We're building a RAG-based writing assistant. They'll design
     prompts and improve output quality. Need someone with LLM experience.

Hermes: Got it. Searching ~5,000 candidates (Hermes + Network) for:
        *Prompt Engineer*...

        [Delivers shortlist with Proof Briefs]
```

### Follow-up Questions
```
You: Tell me more about candidate #3

Hermes: [Provides deep dive on specific candidate]

You: Can you find someone more senior?

Hermes: [Adjusts search and returns updated shortlist]
```

---

## Understanding the Shortlist

### Candidate Card

```
#1 - Sarah Chen
ML Engineer @ OpenAI
Score: 87/100 (85% confidence)
Sources: Hermes | Network | Multi-source

KNOWN FACTS:
  • 3 years prompt engineering at OpenAI
  • Published papers on LLM optimization
  • MIT CS grad, focus on NLP

KEY SIGNALS:
  • Recently updated LinkedIn (may be exploring)
  • GitHub active with prompt engineering repos

UNKNOWN:
  • Current compensation expectations

WARM PATH: Connected via John (worked together at Google)

NEXT STEP: Ask John for intro, mention RAG project
```

### Source Badges

| Badge | Meaning |
|-------|---------|
| Hermes | Found in opted-in Hermes database |
| Network | Found in LinkedIn connections |
| Multi-source | Found in both (higher confidence) |

### Tier Priority

| Tier | Description | Action |
|------|-------------|--------|
| Tier 1 | Warm + Ready | Reach out directly |
| Tier 2 | Warm Intro | Ask connection for intro |
| Tier 3 | Hermes Cold | Cold outreach (but opted-in) |
| Tier 4 | Network Cold | Needs enrichment/verification |

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/slack/events` | POST | Slack Events API webhook |
| `/api/slack/commands` | POST | Slash command handler |
| `/api/slack/install` | GET | Get OAuth install URL |
| `/api/slack/oauth/callback` | GET | OAuth callback |
| `/api/v1/unified/search` | POST | Unified search (internal) |
| `/api/v1/unified/shortlist` | POST | Generate shortlist (internal) |

---

## Troubleshooting

### "URL verification failed"
- Make sure your server is running and publicly accessible
- Check that the endpoint returns the challenge parameter

### "Invalid signature"
- Verify `SLACK_SIGNING_SECRET` is correct
- Check that timestamps aren't too old (Slack rejects requests older than 5 minutes)

### Bot doesn't respond
- Check the bot is in the channel (`/invite @Hermes`)
- Check server logs for errors
- Verify `SLACK_BOT_TOKEN` is correct
- Verify both database connections are working

### Slow responses
- Slack requires a response within 3 seconds
- The bot sends an immediate acknowledgment, then processes in the background
- Full search + enrichment takes ~45-60 seconds
- Check for timeouts in external API calls (Perplexity, OpenAI)

### Low confidence scores
- This is expected for network-only candidates (30% data completeness)
- Top 30 candidates are enriched automatically
- Top 5 get deep research via Perplexity
- Confidence improves after enrichment

### Missing warm paths
- Only available for Network source candidates
- Hermes candidates may not have network connections
- Check that LinkedIn import is complete

---

## Security Considerations

1. **Verify all requests** using the signing secret
2. **Never commit tokens** to version control
3. **Use environment variables** for all secrets
4. **Limit permissions** to only what's needed
5. **Log and monitor** for unusual activity
6. **Candidate data** is only shown to authorized users

---

## Production Deployment

For production:

1. Use a proper hosting service (Railway, Render, AWS, etc.)
2. Set up SSL/HTTPS
3. Configure proper environment variables
4. Set up monitoring and logging
5. Configure rate limits for API calls
6. Set up database connection pooling
7. Consider using Socket Mode for private deployments

---

## Socket Mode (Alternative)

For private deployments without a public URL, use Socket Mode:

1. Go to **Socket Mode** in the Slack app settings
2. Enable Socket Mode
3. Generate an App-Level Token with `connections:write` scope
4. Use the Slack SDK's socket mode client

This is useful for:
- Development without ngrok
- Private networks
- Enterprise deployments

---

## Agent Configuration

### Scoring Weights

Adjust in `.env` or config:

```python
AGENT_CONFIG = {
    "scoring": {
        "skills_match": 0.30,       # Technical fit
        "experience_match": 0.25,   # Seniority & relevance
        "source_quality": 0.15,     # Data trustworthiness
        "network_proximity": 0.15,  # Warm path availability
        "readiness_signals": 0.10,  # Likely to be interested
        "culture_signals": 0.05,    # Startup fit indicators
    }
}
```

### Shortlist Composition

```python
SHORTLIST_CONFIG = {
    "target_size": 12,
    "tier_1_pct": 0.50,    # Warm + Ready (50%)
    "tier_2_pct": 0.30,    # Warm Intro (30%)
    "tier_3_pct": 0.15,    # Hermes Cold (15%)
    "tier_4_pct": 0.05,    # Network Cold (5%)
}
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [UNIFIED_AGENT_ARCHITECTURE.md](../architecture/UNIFIED_AGENT_ARCHITECTURE.md) | System architecture & data models |
| [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) | End-to-end implementation with code |
| [AGENCITY_ARCHITECTURE.md](../architecture/AGENCITY_ARCHITECTURE.md) | Original architecture (V1-V2) |

## Key Components
- **Unified Search Orchestrator**: Parallel search across both sources
- **Deduplication Engine**: Merges candidates found in both
- **Reasoning Engine**: Generates Proof Briefs with evidence chains
- **Shortlist Builder**: Creates tiered recommendations
- **Slack Delivery**: Formats and delivers results

---

## Version History

- **v3.0** (Feb 12, 2026): Unified dual-source architecture
  - Search across Hermes + Network (~5,000 candidates)
  - Proof Brief reasoning system
  - Confidence-based shortlists
  - Progressive enrichment pipeline

- **v2.0** (Feb 11, 2026): Network-only search (3,637 candidates)

- **v1.0** (Initial): Hermes-only search (1,375 candidates)

---

*Hermes Agent v3.0 | ~5,000 candidates | Dual-source | Proof Brief reasoning*
