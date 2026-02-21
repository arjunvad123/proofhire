# OpenClaw + Agencity SaaS Implementation Guide

**Version**: 4.1
**Date**: February 2026
**Status**: Phase 1 Complete — Plugin loads cleanly (1 loaded, 0 errors)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Implementation Phases](#2-implementation-phases)
3. [Phase 1: Local Development Setup](#3-phase-1-local-development-setup)
4. [Phase 2: VM Image & Provisioning](#4-phase-2-vm-image--provisioning)
5. [Phase 3: Web Orchestration Layer](#5-phase-3-web-orchestration-layer)
6. [Phase 4: Multi-Channel & Credentials](#6-phase-4-multi-channel--credentials)
7. [Phase 5: Production Hardening](#7-phase-5-production-hardening)
8. [OpenClaw Core Capabilities](#8-openclaw-core-capabilities)
9. [Agencity Tools Reference](#9-agencity-tools-reference)
10. [Security Checklist](#10-security-checklist)
11. [Cost Analysis](#11-cost-analysis)

---

## 1. Architecture Overview

### 1.1 The Model: Tensol-Style Per-Company VMs

Each customer gets their own isolated VM running the full OpenClaw + Agencity stack. This provides:

- **Complete isolation** - No cross-customer data leakage
- **Full OpenClaw capabilities** - Always-on orchestration, context management, token budgeting
- **Security** - Per-customer encryption keys, isolated credentials
- **Compliance** - Easy GDPR/SOC2 compliance with data isolation

```
1─────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Company A VM  │ │   Company B VM  │ │   Company C VM  │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │ OpenClaw  │  │ │  │ OpenClaw  │  │ │  │ OpenClaw  │  │
│  │ Gateway   │  │ │  │ Gateway   │  │ │  │ Gateway   │  │
│  │ - Always-on│  │ │  │ - Always-on│  │ │  │ - Always-on│  │
│  │ - Context │  │ │  │ - Context │  │ │  │ - Context │  │
│  │ - Memory  │  │ │  │ - Memory  │  │ │  │ - Memory  │  │
│  ├───────────┤  │ │  ├───────────┤  │ │  ├───────────┤  │
│  │ Agencity  │  │ │  │ Agencity  │  │ │  │ Agencity  │  │
│  │ Backend   │  │ │  │ Backend   │  │ │  │ Backend   │  │
│  ├───────────┤  │ │  ├───────────┤  │ │  ├───────────┤  │
│  │ Customer  │  │ │  │ Customer  │  │ │  │ Customer  │  │
│  │ Data/Creds│  │ │  │ Data/Creds│  │ │  │ Data/Creds│  │
│  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
│  256-bit keys   │ │  256-bit keys   │ │  256-bit keys   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 1.2 Why OpenClaw is the Orchestrator

OpenClaw provides capabilities that are hard to build from scratch:

| Capability | What It Does | Why It Matters |
|------------|--------------|----------------|
| **Always-on daemon** | Runs 24/7, proactively acts on triggers | Can monitor for candidate signals, schedule outreach |
| **Context management** | Multi-stage pruning, protected contexts | Long recruiting conversations without token explosion |
| **Token budgeting** | Intelligent allocation across sessions | Predictable costs, no surprise bills |
| **Semantic memory** | Indexes and searches past conversations | "Remember that ML engineer we discussed last week?" |
| **Multi-channel routing** | Same agent across Slack/WhatsApp/Email | Recruiter can talk to agent anywhere |
| **Cron/Webhooks** | Scheduled tasks, event-driven actions | Daily candidate digests, interview reminders |

### 1.3 Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Web Dashboard** | Customer auth, billing, VM lifecycle, OAuth flows |
| **OpenClaw (per VM)** | Orchestration, context, memory, multi-channel |
| **Agencity (per VM)** | Recruiting intelligence, search, scoring, enrichment |
| **Composio** | Credential isolation for Gmail/Calendar/Slack |
| **Supabase** | Shared database for customer metadata, audit logs |

---

## 2. Implementation Phases

### Phase Summary

| Phase | Focus | Deliverable | Prerequisites |
|-------|-------|-------------|---------------|
| **1** | Local Development | OpenClaw + Agencity running locally | None |
| **2** | VM Image | Docker/AMI with full stack | Phase 1 |
| **3** | Web Orchestration | Dashboard for provisioning VMs | Phase 2 |
| **4** | Multi-Channel | Slack, Gmail, Calendar via Composio | Phase 3 |
| **5** | Production | Security hardening, monitoring, scaling | Phase 4 |

### Milestone Checklist

```
Phase 1: Local Development
├── [x] Install OpenClaw locally (embedded at agencity/vendor/openclaw)
├── [x] Verify gateway starts (port 18789, token auth)
├── [x] Run Agencity backend (port 8001)
├── [x] OpenClaw can call Agencity tools (plugin loads: 1 loaded, 0 errors)
├── [ ] Test context management
└── [ ] Test semantic memory

Phase 2: VM Image
├── [ ] Create Dockerfile with OpenClaw + Agencity
├── [ ] Configure systemd services
├── [ ] Build and test image locally
├── [ ] Push to container registry
├── [ ] Create cloud VM from image
└── [ ] Test remote access

Phase 3: Web Orchestration
├── [ ] Set up web dashboard (Next.js)
├── [ ] Customer authentication
├── [ ] VM provisioning API
├── [ ] WebSocket proxy to customer VMs
├── [ ] Basic billing integration
└── [ ] Customer onboarding flow

Phase 4: Multi-Channel & Credentials
├── [ ] Composio integration
├── [ ] Gmail OAuth flow
├── [ ] Google Calendar OAuth
├── [ ] Slack workspace connection
├── [ ] Credential storage per VM
└── [ ] Channel routing in OpenClaw

Phase 5: Production
├── [ ] Security audit
├── [ ] Rate limiting
├── [ ] Monitoring/alerting
├── [ ] Backup strategy
├── [ ] Incident response
└── [ ] SOC2 compliance prep
```

---

## 2.5 Completed Work Log

### Plugin Implementation (Feb 2026)

The Agencity OpenClaw plugin lives at `agencity/extensions/agencity/` and is
loaded via the config at `agencity/openclaw.config.json`.

**Plugin structure**:
```
agencity/extensions/agencity/
├── index.ts                  # Plugin entry — registers all tools
├── package.json              # name: @agencity/agencity (matches plugin id)
└── src/
    ├── api-client.ts         # agencityGet / agencityPatch helpers
    ├── search-tool.ts        # candidate_search → POST /api/search
    ├── curation-tool.ts      # curate_candidates → POST /api/v1/curation/curate
    ├── pipeline-tool.ts      # pipeline_status → GET/PATCH
    └── network-intel-tool.ts # network_intel → warm-path lookup
```

**API path fixes applied** (plugin was previously 404-ing silently):

| Tool | Old (broken) path | Correct path |
|------|-------------------|--------------|
| `curate_candidates` | `POST /api/curate` | `POST /api/v1/curation/curate` |
| `pipeline_status` (view) | `GET /api/integration/pipeline?company_id=…` | `GET /api/pipeline/{company_id}` |
| `pipeline_status` (update) | `POST /api/integration/pipeline/{id}/status` | `PATCH /api/candidates/{id}/status` |
| `pipeline_status` & `network_intel` | missing `company_id` path param check | explicit error thrown before request |

**Package name fix**: renamed from `@agencity/openclaw-plugin` → `@agencity/agencity`
so the package `name` matches the plugin `id` field and OpenClaw's ID-hint
matching works without warnings.

**Result**: plugin loads cleanly — `1 loaded, 0 errors` — with:
```bash
OPENCLAW_CONFIG_PATH=agencity/openclaw.config.json openclaw gateway --port 18789
```

**Gateway integration test suite** added at:
`agencity/vendor/openclaw/test/agencity-gateway.test.ts`

Run with: `make test-gateway`

---

## 3. Phase 1: Local Development Setup

**Goal**: Get OpenClaw + Agencity running locally, with OpenClaw calling Agencity tools.

### 3.1 Prerequisites

```bash
# Required
node --version  # v22+
python --version  # 3.11+
docker --version  # For later phases

# Recommended
pnpm --version  # Faster than npm
```

### 3.2 Install OpenClaw

```bash
# Option A: npm global install
npm install -g openclaw@latest
openclaw onboard --install-daemon
openclaw doctor

# Option B: From source (for modifications)
git clone https://github.com/openclaw/openclaw.git ~/openclaw
cd ~/openclaw
pnpm install
pnpm build
pnpm openclaw onboard --install-daemon
```

### 3.3 Start Agencity Backend

```bash
cd proofhire/agencity

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Start
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Verify
curl http://localhost:8001/health
```

### 3.4 Configure OpenClaw to Use Agencity

OpenClaw needs to know about Agencity tools. Create/update the agent configuration:

```bash
# Create workspace for Agencity agent
mkdir -p ~/.openclaw/agents/agencity
```

**Agent System Prompt** (`~/.openclaw/agents/agencity/system.md`):
```markdown
You are an AI recruiting assistant powered by Agencity.

You have access to powerful recruiting tools:
- **search**: Find candidates using natural language queries
- **enrich**: Get detailed profiles for candidates
- **score**: Evaluate candidate fit for a role
- **network**: Find warm paths to candidates

When users ask about hiring or candidates, use these tools proactively.

Always:
- Explain your reasoning
- Show confidence scores
- Highlight warm paths when available
```

**Agent Config** (`~/.openclaw/agents/agencity/agent.json`):
```json
{
  "name": "agencity",
  "model": "anthropic/claude-sonnet-4-20250514",
  "systemPromptPath": "./system.md",
  "tools": {
    "http": {
      "enabled": true,
      "endpoints": [
        {
          "name": "agencity_search",
          "description": "Search for candidates using natural language",
          "method": "POST",
          "url": "http://localhost:8001/api/search",
          "headers": {
            "Content-Type": "application/json"
          },
          "bodyTemplate": {
            "query": "{{query}}",
            "limit": "{{limit | default: 20}}",
            "include_external": true
          }
        },
        {
          "name": "agencity_enrich",
          "description": "Get detailed profile for a candidate",
          "method": "POST",
          "url": "http://localhost:8001/api/enrich",
          "headers": {
            "Content-Type": "application/json"
          },
          "bodyTemplate": {
            "linkedin_url": "{{linkedin_url}}"
          }
        },
        {
          "name": "agencity_score",
          "description": "Score a candidate against role requirements",
          "method": "POST",
          "url": "http://localhost:8001/api/score",
          "headers": {
            "Content-Type": "application/json"
          },
          "bodyTemplate": {
            "candidate_id": "{{candidate_id}}",
            "role_requirements": "{{requirements}}"
          }
        }
      ]
    }
  }
}
```

### 3.5 Test the Integration

```bash
# Start OpenClaw gateway
openclaw gateway --port 18789

# In another terminal, start a chat session
openclaw chat --agent agencity

# Test queries:
> Find me senior ML engineers who worked at Stripe
> What's the warm path to this candidate?
> Score this candidate for our Staff Engineer role
```

### 3.6 Verify Core Capabilities

**Context Management Test**:
```bash
# Have a long conversation, then check memory usage
openclaw memory status

# Search past conversations
openclaw memory search "ML engineer"
```

**Token Budgeting Test**:
```bash
# Check token usage
openclaw usage --agent agencity

# Should show budget allocation and actual usage
```

### 3.7 Phase 1 Completion Criteria

- [ ] `openclaw doctor` passes all checks
- [ ] Agencity health endpoint returns healthy
- [ ] OpenClaw can call `agencity_search` tool
- [ ] Search results display in chat
- [ ] Memory persists across sessions
- [ ] Token usage is tracked

---

## 4. Phase 2: VM Image & Provisioning

**Goal**: Create a deployable VM image with OpenClaw + Agencity that can be spun up per customer.

### 4.1 Dockerfile

```dockerfile
# Dockerfile.agencity-vm
FROM ubuntu:22.04

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3.11 \
    python3-pip \
    nodejs \
    npm \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm and OpenClaw
RUN npm install -g pnpm openclaw@latest

# Create app user
RUN useradd -m -s /bin/bash agencity
WORKDIR /home/agencity

# Copy Agencity backend
COPY --chown=agencity:agencity agencity/ ./agencity/
RUN cd agencity && pip install -r requirements.txt

# Copy OpenClaw config
COPY --chown=agencity:agencity openclaw-config/ ./.openclaw/

# Supervisor config for running both services
COPY supervisor.conf /etc/supervisor/conf.d/agencity.conf

# Expose ports
EXPOSE 8001 18789

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8001/health && curl -f http://localhost:18789/health

USER agencity
CMD ["/usr/bin/supervisord", "-n"]
```

**Supervisor Config** (`supervisor.conf`):
```ini
[supervisord]
nodaemon=true

[program:agencity-api]
command=python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
directory=/home/agencity/agencity
user=agencity
autostart=true
autorestart=true
stdout_logfile=/var/log/agencity-api.log
stderr_logfile=/var/log/agencity-api-error.log

[program:openclaw-gateway]
command=openclaw gateway --port 18789
directory=/home/agencity
user=agencity
autostart=true
autorestart=true
stdout_logfile=/var/log/openclaw-gateway.log
stderr_logfile=/var/log/openclaw-gateway-error.log
environment=HOME="/home/agencity",OPENCLAW_STATE_DIR="/home/agencity/.openclaw"
```

### 4.2 Build and Test Locally

```bash
# Build image
docker build -t agencity-vm:latest -f Dockerfile.agencity-vm .

# Run locally
docker run -d \
    --name agencity-test \
    -p 8001:8001 \
    -p 18789:18789 \
    -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
    -e SUPABASE_URL=$SUPABASE_URL \
    -e SUPABASE_KEY=$SUPABASE_KEY \
    agencity-vm:latest

# Test
curl http://localhost:8001/health
curl http://localhost:18789/health
```

### 4.3 Cloud Deployment Options

**Option A: AWS EC2 with AMI**
```bash
# Create AMI from running instance
aws ec2 create-image \
    --instance-id i-xxx \
    --name "agencity-vm-v1" \
    --description "OpenClaw + Agencity SaaS VM"

# Launch new instance from AMI
aws ec2 run-instances \
    --image-id ami-xxx \
    --instance-type t3.medium \
    --key-name your-key \
    --security-groups agencity-sg
```

**Option B: GCP Compute Engine**
```bash
# Create instance from container
gcloud compute instances create-with-container agencity-vm-1 \
    --container-image=gcr.io/your-project/agencity-vm:latest \
    --machine-type=e2-medium \
    --zone=us-central1-a
```

**Option C: Fly.io (Simpler)**
```bash
# fly.toml
flyctl deploy --config fly.toml
```

### 4.4 Per-Customer Configuration

Each VM needs customer-specific config injected at boot:

```bash
# Environment variables per customer
CUSTOMER_ID=uuid
CUSTOMER_NAME="Acme Corp"
ENCRYPTION_KEY=per-customer-256-bit-key
SUPABASE_SCHEMA=customer_uuid  # Isolated schema per customer
COMPOSIO_USER_ID=customer-composio-id
```

### 4.5 Phase 2 Completion Criteria

- [ ] Docker image builds successfully
- [ ] Container runs with both services healthy
- [ ] Can deploy to cloud provider
- [ ] Customer config injection works
- [ ] Persistent storage configured
- [ ] Logs accessible

---

## 5. Phase 3: Web Orchestration Layer

**Goal**: Web dashboard that provisions VMs, handles auth, and proxies to customer instances.

### 5.1 Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Framework** | Next.js 14 | App router, server components |
| **Auth** | Clerk or Auth0 | Enterprise SSO support |
| **Database** | Supabase | Already using, RLS for isolation |
| **Payments** | Stripe | Usage-based billing |
| **Infra API** | AWS SDK / GCP SDK | VM provisioning |

### 5.2 Dashboard Structure

```
web/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/
│   │   ├── layout.tsx          # Sidebar, nav
│   │   ├── page.tsx            # Dashboard home
│   │   ├── chat/
│   │   │   └── page.tsx        # WebSocket to customer VM
│   │   ├── candidates/
│   │   │   └── page.tsx        # Search results
│   │   ├── settings/
│   │   │   ├── integrations/   # Composio OAuth
│   │   │   ├── team/           # Team management
│   │   │   └── billing/        # Stripe portal
│   │   └── admin/              # Super admin only
│   │       └── vms/            # VM management
│   └── api/
│       ├── vm/
│       │   ├── provision/      # Create customer VM
│       │   ├── [id]/status/    # VM health
│       │   └── [id]/destroy/   # Teardown
│       ├── proxy/
│       │   └── [...path]/      # Proxy to customer VM
│       └── webhooks/
│           ├── stripe/
│           └── composio/
├── lib/
│   ├── vm-manager.ts           # AWS/GCP SDK wrapper
│   ├── supabase.ts
│   └── composio.ts
└── components/
    ├── chat/
    │   └── ChatInterface.tsx   # WebSocket chat UI
    └── ...
```

### 5.3 VM Provisioning API

```typescript
// app/api/vm/provision/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs';
import { VMManager } from '@/lib/vm-manager';
import { supabase } from '@/lib/supabase';

export async function POST(req: NextRequest) {
  const { userId, orgId } = auth();
  if (!userId || !orgId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Check if org already has a VM
  const { data: existing } = await supabase
    .from('customer_vms')
    .select('*')
    .eq('org_id', orgId)
    .single();

  if (existing) {
    return NextResponse.json({ error: 'VM already exists' }, { status: 400 });
  }

  // Provision new VM
  const vmManager = new VMManager();
  const vm = await vmManager.provision({
    orgId,
    region: 'us-east-1',
    size: 't3.medium',
    config: {
      CUSTOMER_ID: orgId,
      ENCRYPTION_KEY: generateEncryptionKey(),
    },
  });

  // Store VM metadata
  await supabase.from('customer_vms').insert({
    org_id: orgId,
    vm_id: vm.id,
    ip_address: vm.publicIp,
    status: 'provisioning',
    created_at: new Date().toISOString(),
  });

  return NextResponse.json({ vm });
}
```

### 5.4 WebSocket Proxy to Customer VM

```typescript
// app/api/proxy/ws/route.ts
// Proxies WebSocket connections to customer's OpenClaw gateway

import { auth } from '@clerk/nextjs';
import { supabase } from '@/lib/supabase';

export async function GET(req: NextRequest) {
  const { orgId } = auth();

  // Get customer's VM
  const { data: vm } = await supabase
    .from('customer_vms')
    .select('ip_address')
    .eq('org_id', orgId)
    .single();

  if (!vm) {
    return new Response('VM not found', { status: 404 });
  }

  // Upgrade to WebSocket and proxy to customer VM
  const targetUrl = `ws://${vm.ip_address}:18789`;

  // Use edge runtime for WebSocket support
  // Implementation depends on deployment platform
}
```

### 5.5 Chat Interface

```typescript
// components/chat/ChatInterface.tsx
'use client';

import { useEffect, useRef, useState } from 'react';

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to proxy WebSocket
    const ws = new WebSocket('/api/proxy/ws');
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, data]);
    };

    return () => ws.close();
  }, []);

  const sendMessage = () => {
    if (wsRef.current && input.trim()) {
      wsRef.current.send(JSON.stringify({
        type: 'message',
        content: input,
      }));
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
      </div>
      <div className="border-t p-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about candidates..."
          className="w-full p-2 border rounded"
        />
      </div>
    </div>
  );
}
```

### 5.6 Phase 3 Completion Criteria

- [ ] User can sign up and create org
- [ ] VM provisioned on signup
- [ ] Chat interface connects to customer VM
- [ ] Settings page works
- [ ] Basic billing in place
- [ ] Admin can view all VMs

---

## 6. Phase 4: Multi-Channel & Credentials

**Goal**: Connect customer Gmail, Calendar, Slack via Composio with isolated credentials.

### 6.1 Composio Integration

Composio handles OAuth flows and stores credentials securely, so credentials never touch your servers.

```bash
# Install Composio
curl -fsSL https://composio.dev/install | bash
composio login
```

### 6.2 OAuth Flow Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Customer   │────▶│  Your Web    │────▶│   Composio   │
│   Browser    │     │  Dashboard   │     │   OAuth      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │   Google/    │
                                          │   Slack      │
                                          └──────────────┘
                                                  │
                                                  ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  Customer    │◀────│   Composio   │
                     │  VM          │     │   Vault      │
                     │  (OpenClaw)  │     │  (Encrypted) │
                     └──────────────┘     └──────────────┘
```

### 6.3 Composio Setup in Web Dashboard

```typescript
// lib/composio.ts
import { Composio } from 'composio-core';

const composio = new Composio({ apiKey: process.env.COMPOSIO_API_KEY });

export async function initiateGmailOAuth(orgId: string) {
  // Create entity for this customer
  const entity = await composio.getEntity(orgId);

  // Get OAuth URL
  const connection = await entity.initiateConnection('gmail', {
    redirectUrl: `${process.env.NEXT_PUBLIC_URL}/settings/integrations/callback`,
  });

  return connection.redirectUrl;
}

export async function getCustomerConnections(orgId: string) {
  const entity = await composio.getEntity(orgId);
  return entity.getConnections();
}
```

### 6.4 OpenClaw Channel Configuration

Once credentials are in Composio, configure OpenClaw to use them:

```json
// Per-customer OpenClaw config
{
  "channels": {
    "gmail": {
      "enabled": true,
      "composioEntityId": "{{CUSTOMER_ID}}",
      "watchLabels": ["INBOX"],
      "replyPrefix": "[Agencity] "
    },
    "slack": {
      "enabled": true,
      "composioEntityId": "{{CUSTOMER_ID}}",
      "defaultChannel": "#recruiting"
    },
    "calendar": {
      "enabled": true,
      "composioEntityId": "{{CUSTOMER_ID}}",
      "syncDirection": "bidirectional"
    }
  }
}
```

### 6.5 Phase 4 Completion Criteria

- [ ] Gmail OAuth flow works
- [ ] Calendar OAuth flow works
- [ ] Slack workspace connection works
- [ ] Credentials stored in Composio (not your DB)
- [ ] OpenClaw can send/receive via Gmail
- [ ] OpenClaw can post to Slack
- [ ] Calendar events sync

---

## 7. Phase 5: Production Hardening

**Goal**: Security, monitoring, scaling, compliance.

### 7.1 Security Checklist

**VM Security**:
- [ ] OpenClaw v2026.1.29+ (CVE patched)
- [ ] Gateway bound to loopback only (proxied via web)
- [ ] Token authentication required
- [ ] Sandbox mode for exec tools
- [ ] ClawHub skills disabled/allowlisted
- [ ] Non-root execution
- [ ] Read-only filesystem where possible

**Network Security**:
- [ ] VMs in private subnet
- [ ] Only web dashboard has public IP
- [ ] TLS everywhere
- [ ] VPN for admin access
- [ ] DDoS protection

**Credential Security**:
- [ ] All OAuth via Composio
- [ ] Per-customer encryption keys
- [ ] Key rotation policy
- [ ] No credentials in logs

### 7.2 Monitoring

```yaml
# Docker Compose addition for monitoring
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"

  loki:
    image: grafana/loki
```

**Key Metrics**:
- VM health (CPU, memory, disk)
- OpenClaw gateway response times
- Agencity API latency
- Token usage per customer
- Error rates
- Active sessions

### 7.3 Scaling Strategy

| Customers | Architecture |
|-----------|--------------|
| 1-10 | Single region, manual provisioning |
| 10-50 | Auto-scaling group, multiple regions |
| 50+ | Kubernetes, global load balancing |

### 7.4 Backup Strategy

```bash
# Per-VM backup script
#!/bin/bash
CUSTOMER_ID=$1
BACKUP_DATE=$(date +%Y%m%d)

# Backup OpenClaw state
tar -czf /backups/${CUSTOMER_ID}/${BACKUP_DATE}-openclaw.tar.gz \
    /home/agencity/.openclaw/

# Backup Agencity data
pg_dump -h localhost agencity > /backups/${CUSTOMER_ID}/${BACKUP_DATE}-agencity.sql

# Upload to S3 with customer-specific key
aws s3 cp /backups/${CUSTOMER_ID}/ s3://agencity-backups/${CUSTOMER_ID}/ \
    --recursive --sse aws:kms --sse-kms-key-id ${CUSTOMER_KMS_KEY}
```

### 7.5 Phase 5 Completion Criteria

- [ ] Security audit passed
- [ ] Penetration test passed
- [ ] Monitoring dashboards live
- [ ] Alerting configured
- [ ] Backup/restore tested
- [ ] Incident response documented
- [ ] SOC2 Type 1 prep complete

---

## 8. OpenClaw Core Capabilities

### 8.1 Why We Use OpenClaw

| Capability | What It Provides | Alternative Effort |
|------------|------------------|-------------------|
| **Always-on orchestration** | Daemon that runs 24/7, handles triggers | 2-3 months to build |
| **Context management** | Multi-stage pruning, protected contexts | 1-2 months to build |
| **Token budgeting** | Per-session and global budget allocation | 2-4 weeks to build |
| **Semantic memory** | Vector indexing, search, persistence | 1 month to build |
| **Multi-channel** | Unified agent across Slack/Email/etc | 1-2 months to build |
| **Tool calling** | Robust tool execution with retries | 2-3 weeks to build |

**Total: 6-10 months of engineering vs. using OpenClaw**

### 8.2 Context Management Details

OpenClaw's context manager (which we leverage, not rebuild):

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXT BUDGET                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Total: 128,000 tokens                               │    │
│  │  ├── System prompt: 2,000 (protected)               │    │
│  │  ├── Agent instructions: 3,000 (protected)          │    │
│  │  ├── Recent conversation: 20,000 (soft limit)       │    │
│  │  ├── Memory retrieval: 10,000                       │    │
│  │  ├── Tool results: 30,000                           │    │
│  │  └── Response buffer: 8,000                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  PRUNING STRATEGY:                                          │
│  1. At 70% usage: Summarize old messages (soft trim)        │
│  2. At 85% usage: Remove tool results (hard trim)           │
│  3. At 95% usage: Keep only last 5 messages + summary       │
│  4. Protected contexts NEVER pruned                         │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Token Budgeting

```json
// OpenClaw token budget config
{
  "tokenBudget": {
    "daily": 1000000,
    "perSession": 50000,
    "perMessage": 8000,
    "alertAt": 0.8,
    "hardCapAt": 0.95
  }
}
```

---

## 9. Agencity Tools Reference

### 9.1 Tools Exposed to OpenClaw

| Tool | Endpoint | Description |
|------|----------|-------------|
| `agencity_search` | `POST /api/search` | Natural language candidate search |
| `agencity_enrich` | `POST /api/enrich` | Get detailed candidate profile |
| `agencity_score` | `POST /api/score` | Score candidate against requirements |
| `agencity_warm_path` | `POST /api/warm-path` | Find connection paths |
| `agencity_outreach` | `POST /api/outreach` | Generate personalized message |

### 9.2 Search Tool

```typescript
// What OpenClaw sends
{
  "tool": "agencity_search",
  "params": {
    "query": "Senior ML engineers who worked at Stripe, now at startups",
    "limit": 20,
    "filters": {
      "location": "San Francisco Bay Area",
      "yearsExperience": { "min": 5 }
    }
  }
}

// What Agencity returns
{
  "candidates": [
    {
      "id": "uuid",
      "name": "Jane Doe",
      "headline": "Staff ML Engineer at Stealth Startup",
      "score": 92,
      "warmPath": {
        "exists": true,
        "hops": 1,
        "via": "John Smith (your network)"
      }
    }
  ],
  "totalResults": 47,
  "searchCost": "$0.12"
}
```

### 9.3 Cost Per Tool Call

| Tool | Typical Cost | Notes |
|------|--------------|-------|
| `agencity_search` | $0.05-0.20 | Depends on cache hit rate |
| `agencity_enrich` | $0.02-0.10 | Clado cache vs live scrape |
| `agencity_score` | $0.001 | Claude API call |
| `agencity_warm_path` | $0.01 | Graph traversal |
| `agencity_outreach` | $0.002 | Claude API call |

---

## 10. Security Checklist

### Pre-Deployment

- [ ] OpenClaw v2026.1.29+ (CVE-2026-25253 patched)
- [ ] Gateway token authentication configured
- [ ] Gateway bound to loopback (accessed via proxy)
- [ ] Sandbox mode enabled for exec tools
- [ ] ClawHub skills disabled or strict allowlist
- [ ] Composio configured for all OAuth
- [ ] Per-customer encryption keys generated
- [ ] Firewall rules configured

### Per-Customer Setup

- [ ] Isolated VM provisioned
- [ ] Unique gateway token generated
- [ ] Customer-specific encryption key
- [ ] Composio entity created
- [ ] Audit logging enabled
- [ ] Backup schedule configured

### Ongoing Operations

- [ ] Weekly `openclaw doctor` runs
- [ ] Monthly security updates
- [ ] Quarterly penetration testing
- [ ] Audit log review
- [ ] Token rotation
- [ ] Backup restoration tests

---

## 11. Cost Analysis

### 11.1 Per-Customer VM Costs

| Provider | Instance | Monthly Cost |
|----------|----------|--------------|
| AWS | t3.medium | ~$30 |
| GCP | e2-medium | ~$25 |
| Fly.io | shared-cpu-2x | ~$15 |

### 11.2 Per-Search Costs

```
TYPICAL SEARCH (with 50% cache hit):
├── Clado search: $0.02
├── PDL enrichment (5 candidates): $0.50
├── Claude scoring: $0.005
├── OpenClaw overhead: $0.001
└── Total: ~$0.53

WITH HIGH CACHE HIT (80%):
└── Total: ~$0.15
```

### 11.3 Pricing Model Suggestion

| Tier | Monthly | Includes | Overage |
|------|---------|----------|---------|
| Starter | $99 | 100 searches, 1 user | $1/search |
| Growth | $299 | 500 searches, 5 users | $0.75/search |
| Enterprise | Custom | Unlimited, SSO, SLA | - |

---

## Appendix: File Locations

| Component | Path |
|-----------|------|
| Agencity Backend | `proofhire/agencity/` |
| OpenClaw Config Template | `proofhire/agencity/openclaw.config.json` |
| CLI Wrapper | `proofhire/agencity/bin/agencity` |
| VM Dockerfile | `proofhire/infra/Dockerfile.agencity-vm` |
| Web Dashboard | `proofhire/web/` |

---

*Document updated February 2026*
