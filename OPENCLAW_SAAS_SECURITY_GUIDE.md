# OpenClaw SaaS Security & Deployment Guide

**Version**: 2.0
**Date**: February 2026
**Status**: Research & Planning

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Case Study: Tensol.ai (YC W26)](#2-case-study-tensolai-yc-w26)
3. [Security Landscape](#3-security-landscape)
4. [Architecture Options](#4-architecture-options)
5. [Multi-Tenant Isolation](#5-multi-tenant-isolation)
6. [OAuth & Credential Management](#6-oauth--credential-management)
7. [Email & Calendar Integration](#7-email--calendar-integration)
8. [Messaging Channels (Slack/WhatsApp)](#8-messaging-channels-slackwhatsapp)
9. [Electron App Considerations](#9-electron-app-considerations)
10. [Deployment Recommendations](#10-deployment-recommendations)
11. [Security Checklist](#11-security-checklist)

---

## 1. Executive Summary

### The Challenge

Running OpenClaw as a **SaaS product** presents significant security challenges because:

1. **Designed for Personal Use**: OpenClaw was built as a single-user personal assistant
2. **Full System Access**: Can execute commands, access files, send messages
3. **Persistent Credentials**: Stores OAuth tokens for email, calendar, messaging
4. **Prompt Injection Risk**: AI models can be manipulated via crafted inputs

### Key Security Concerns (February 2026)

| Issue | Severity | Status |
|-------|----------|--------|
| **CVE-2026-25253** | Critical (CVSS 8.8) | Patched in v2026.1.29 |
| **ClawHavoc Campaign** | High | 800+ malicious skills (~20% of registry) |
| **30,000+ Exposed Instances** | High | Many without authentication |
| **No Built-in Multi-Tenancy** | Medium | Requires custom implementation |

### Recommendation

**Do NOT deploy vanilla OpenClaw as a multi-tenant SaaS.** Instead:

1. Use **Composio** for credential isolation
2. Deploy **per-customer isolated containers**
3. Build a **custom orchestration layer** (your Electron app)
4. Or consider the **Tensol model** (see Case Study below)

---

## 2. Case Study: Tensol.ai (YC W26)

### 2.1 Overview

[Tensol](https://www.tensol.ai/) is a Y Combinator W26 startup that has successfully productized OpenClaw as "AI Employees for Your Business." They provide the full power of OpenClaw with enterprise-grade security.

**Founders**:
- **Oliviero Pinotti** - Repeat founder, previously built Workflows at Stacksync (YC W24), used by Fortune 500s
- **Pratik** - AI engineer from Carnegie Mellon, ex-Rivian and Magna International

**Source**: [YC Launch Post](https://www.ycombinator.com/launches/PQ9-tensol-ai-employees-for-your-company-built-on-openclaw)

### 2.2 How Tensol Productized OpenClaw

#### The Problem They Solved

> "Most agents today require you to prompt them, and have limited memory & context capabilities. OpenClaw is an autonomous agent that acts proactively, runs 24/7 and remembers everything about your organization... but **deploying it is a nightmare**: managing access to credentials, your file system, adding integrations, and time to set it all up."

#### Their Solution

| Challenge | Tensol's Approach |
|-----------|-------------------|
| Complex setup | One-click OAuth, no terminal/coding needed |
| Credential security | OAuth 2.0 + role-based access control |
| Customer isolation | Dedicated VM per customer |
| Enterprise needs | Audit logs, SSO, guardrails |
| 24/7 operation | Managed infrastructure on AWS |

### 2.3 Tensol's Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      TENSOL PLATFORM                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Orchestration & Management                  │    │
│  │  - Customer onboarding                                   │    │
│  │  - OAuth flow handling                                   │    │
│  │  - Audit logging                                         │    │
│  │  - SSO integration                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Customer A    │ │   Customer B    │ │   Customer C    │
│   ISOLATED VM   │ │   ISOLATED VM   │ │   ISOLATED VM   │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │ OpenClaw  │  │ │  │ OpenClaw  │  │ │  │ OpenClaw  │  │
│  │ Instance  │  │ │  │ Instance  │  │ │  │ Instance  │  │
│  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │ Customer  │  │ │  │ Customer  │  │ │  │ Customer  │  │
│  │ Data Only │  │ │  │ Data Only │  │ │  │ Data Only │  │
│  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
│                 │ │                 │ │                 │
│  256-bit        │ │  256-bit        │ │  256-bit        │
│  Encryption     │ │  Encryption     │ │  Encryption     │
│  Per-customer   │ │  Per-customer   │ │  Per-customer   │
│  Keys           │ │  Keys           │ │  Keys           │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 2.4 Key Security Features

From [Tensol.ai](https://www.tensol.ai/):

| Feature | Implementation |
|---------|----------------|
| **VM Isolation** | Each customer gets dedicated VM with hardware-level separation |
| **Data Encryption** | 256-bit encryption, customer-specific keys |
| **OAuth 2.0** | One-click OAuth, credentials never exposed to agent |
| **RBAC** | Role-based access control for tool authentication |
| **Audit Logging** | Full logging of all AI employee actions |
| **SSO** | Enterprise single sign-on support |
| **Guardrails** | Configurable limits on agent actions |

### 2.5 Supported Integrations

Tensol connects to 40+ tools via OAuth:

| Category | Tools |
|----------|-------|
| **Communication** | Slack, Gmail, WhatsApp, Telegram |
| **Engineering** | GitHub, Sentry, Linear |
| **Sales/CRM** | HubSpot, Salesforce |
| **Productivity** | Notion, Jira, Google Calendar |

### 2.6 Business Model Insight

From [Lago's analysis](https://getlago.substack.com/p/can-anyone-actually-monetize-openclaw):

> "Rather than selling OpenClaw directly, successful commercialization requires constraining it into specialized products... Companies like Tensol exemplify this approach—offering AI employees for specific workflows rather than universal autonomy, enabling predictable token consumption and clear business value."

**Key insight**: Monetization succeeds through **vertical specialization**, not selling raw OpenClaw access.

### 2.7 Tensol's Phased Trust Model

Tensol implements a **draft-review-autonomy** progression:

```
Phase 1: DRAFT
├── AI employee drafts actions
├── Human reviews and approves
└── Learn from feedback

Phase 2: REVIEW
├── AI executes low-risk actions
├── Human reviews high-risk actions
└── Builds trust over time

Phase 3: AUTONOMY
├── AI operates independently
├── Human reviews audit logs
└── Guardrails prevent overreach
```

### 2.8 Lessons for Your Implementation

**What to copy from Tensol**:

1. **Per-customer VMs** - Hardware-level isolation, not just container isolation
2. **One-click OAuth** - Abstract away credential complexity
3. **Customer-specific encryption keys** - Even if breached, data is isolated
4. **Full audit logging** - Every action traceable
5. **Phased autonomy** - Start with human review, build trust
6. **Vertical focus** - Don't sell "AI agent", sell "AI employee for X"

**What you might do differently**:

1. **Electron app** - Local client vs pure cloud (better for sensitive data)
2. **Composio integration** - Additional credential isolation layer
3. **Agencity backend** - Your specialized recruiting intelligence
4. Or consider **alternatives** like Secure OpenClaw or TrustClaw

---

## 3. Security Landscape

### 3.1 Known Vulnerabilities

#### CVE-2026-25253 (Critical)
> "The Control UI trusts gatewayUrl from the query string without validation and auto-connects on load, sending the stored gateway token in the WebSocket connect payload."

**Impact**: One-click RCE via malicious link, even on localhost-bound instances.

**Fix**: Upgrade to v2026.1.29+

**Source**: [The Hacker News](https://thehackernews.com/2026/02/openclaw-bug-enables-one-click-remote.html)

#### ClawHavoc Malicious Skills Campaign
- 800+ malicious skills discovered in ClawHub (~20% of registry)
- Primarily delivers Atomic macOS Stealer (AMOS)
- Skills can execute arbitrary code with user privileges

**Source**: [CrowdStrike Analysis](https://www.crowdstrike.com/en-us/blog/what-security-teams-need-to-know-about-openclaw-ai-super-agent/)

### 3.2 Fundamental Security Model

From [Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/02/19/running-openclaw-safely-identity-isolation-runtime-risk/):

> "OpenClaw should be treated as **untrusted code execution with persistent credentials**. It is not appropriate to run on a standard personal or enterprise workstation."

### 3.3 Prompt Injection Reality

From [OpenClaw Docs](https://docs.openclaw.ai/gateway/security):

> "Prompt injection is when an attacker crafts a message that manipulates the model into doing something unsafe. No system prompt fully prevents this."

**Mitigation**: Use Anthropic Opus 4.6+ (better prompt-injection resistance)

---

## 4. Architecture Options

### 4.1 Option A: Multi-Instance (Recommended for SaaS)

**Each customer gets their own isolated OpenClaw instance.**

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR SAAS PLATFORM                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              ORCHESTRATION LAYER                           │  │
│  │         (Electron App / Web Dashboard)                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Customer A    │ │   Customer B    │ │   Customer C    │
│   Container     │ │   Container     │ │   Container     │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │ OpenClaw  │  │ │  │ OpenClaw  │  │ │  │ OpenClaw  │  │
│  │ Gateway   │  │ │  │ Gateway   │  │ │  │ Gateway   │  │
│  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │ Isolated  │  │ │  │ Isolated  │  │ │  │ Isolated  │  │
│  │ Storage   │  │ │  │ Storage   │  │ │  │ Storage   │  │
│  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

**Pros**:
- Complete isolation between customers
- Security breach contained to single instance
- Easier compliance (GDPR, SOC2)
- Independent upgrades per customer

**Cons**:
- Higher infrastructure cost
- More operational complexity
- Resource overhead per instance

**When to use**: 10-100 customers, high-value enterprise clients

### 4.2 Option B: Multi-Tenant with Agent Isolation

**Single Gateway, multiple isolated agents per organization.**

```
┌─────────────────────────────────────────────────────────────────┐
│                     SHARED GATEWAY                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Agent Router                          │    │
│  └────────────┬────────────────┬────────────────┬──────────┘    │
│               ▼                ▼                ▼               │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐      │
│  │   Agent: OrgA  │ │   Agent: OrgB  │ │   Agent: OrgC  │      │
│  │  ┌──────────┐  │ │  ┌──────────┐  │ │  ┌──────────┐  │      │
│  │  │Workspace │  │ │  │Workspace │  │ │  │Workspace │  │      │
│  │  │Sessions  │  │ │  │Sessions  │  │ │  │Sessions  │  │      │
│  │  │Auth      │  │ │  │Auth      │  │ │  │Auth      │  │      │
│  │  └──────────┘  │ │  └──────────┘  │ │  └──────────┘  │      │
│  └────────────────┘ └────────────────┘ └────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

**Current Limitations** (from [GitHub Issue #10004](https://github.com/openclaw/openclaw/issues/10004)):

> "The current tool-level config (tools.allow/tools.deny) is necessary but not sufficient to enforce user-to-user isolation within a single OpenClaw instance."

**Missing Platform Primitives**:
1. Agent-scoped session visibility
2. Agent-to-channel binding
3. Agent-scoped cron ownership
4. Per-agent workspace isolation
5. Integration credential scoping

**When to use**: Only after OpenClaw adds proper multi-tenant primitives

### 4.3 Option C: Composio-Mediated Architecture

**Use Composio as credential isolation layer.**

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR ELECTRON APP                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     OPENCLAW GATEWAY                             │
│              (Per-customer or shared)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     COMPOSIO LAYER                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │            Managed OAuth & Credential Vault              │    │
│  │  - Tokens encrypted at rest                              │    │
│  │  - Agent never sees raw credentials                      │    │
│  │  - Audit logs + instant revocation                       │    │
│  │  - 500+ app integrations                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│    Gmail    │   │  Calendar   │   │    Slack    │
│     API     │   │     API     │   │     API     │
└─────────────┘   └─────────────┘   └─────────────┘
```

**Composio Benefits**:
- OAuth handshake on Composio infrastructure, not your servers
- Tokens encrypted in Composio vault
- Per-user credential isolation
- Instant revocation capability
- Full audit trail

**Source**: [Composio Blog](https://composio.dev/blog/secure-openclaw-moltbot-clawdbot-setup)

---

## 5. Multi-Tenant Isolation

### 5.1 Required Isolation Boundaries

| Layer | Isolation Requirement | Implementation |
|-------|----------------------|----------------|
| **Compute** | Separate execution environments | Docker containers per customer |
| **Storage** | No cross-customer data access | Isolated volumes/namespaces |
| **Credentials** | Separate OAuth tokens | Composio or per-agent auth-profiles |
| **Network** | No inter-customer communication | Network policies, VPCs |
| **Sessions** | Private conversation history | Agent-scoped session stores |
| **Memory** | Separate semantic indexes | Per-customer memory backends |

### 5.2 Docker Deployment Pattern

From [DigitalOcean Guide](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw):

```yaml
# docker-compose.yml (per customer)
version: '3.8'
services:
  gateway:
    image: openclaw/openclaw:latest
    environment:
      - OPENCLAW_GATEWAY_AUTH_TOKEN=${CUSTOMER_TOKEN}
      - ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
    volumes:
      - ./customer-${CUSTOMER_ID}/workspace:/workspace
      - ./customer-${CUSTOMER_ID}/state:/root/.openclaw
    networks:
      - customer-${CUSTOMER_ID}-network
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp

  sandbox:
    image: openclaw/sandbox:latest
    networks:
      - customer-${CUSTOMER_ID}-network
    security_opt:
      - no-new-privileges:true
```

### 5.3 RBAC Model

From [Enterprise Deployment Guide](https://eastondev.com/blog/en/posts/ai/20260205-openclaw-enterprise-deploy/):

| Role | Permissions |
|------|-------------|
| **Admin** | Global config, user management, all logs |
| **Developer** | OpenClaw access, personal logs only |
| **Auditor** | Read-only access to all logs |

---

## 6. OAuth & Credential Management

### 6.1 The Credential Problem

**Default OpenClaw stores credentials insecurely**:

```
~/.openclaw/agents/<agentId>/agent/auth-profiles.json
```

> "If an attacker gains access to your instance, they can reach your private chats, emails, API Keys, Password managers, home automation system or anything you've given it access to."

**Source**: [Composio Security Blog](https://composio.dev/blog/openclaw-security-and-vulnerabilities)

### 6.2 Solution: Composio Managed Auth

```bash
# Install Composio
curl -fsSL https://composio.dev/install | bash
composio login

# Connect Gmail (credential stored in Composio vault)
composio add gmail

# Connect Google Calendar
composio add google-calendar

# Connect Slack
composio add slack
```

**How it works**:
1. OAuth flow happens on Composio infrastructure
2. Tokens encrypted and stored in Composio vault
3. Agent requests action via Composio API
4. Composio executes with scoped credentials
5. Agent never sees raw tokens

### 6.3 Alternative: Dedicated Credential Service

If you can't use Composio, build your own:

```
┌─────────────────────────────────────────────────────────────────┐
│                   CREDENTIAL SERVICE                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Vault (HashiCorp/AWS)                   │    │
│  │  - AES-256 encryption at rest                            │    │
│  │  - Per-customer encryption keys                          │    │
│  │  - Short-lived token leases                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Token Proxy                           │    │
│  │  - Receives action requests from OpenClaw                │    │
│  │  - Fetches credentials from vault                        │    │
│  │  - Executes API call                                     │    │
│  │  - Returns result (no raw tokens exposed)                │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Email & Calendar Integration

### 7.1 Gmail Integration

**Setup via Google Cloud Console**:

1. Create project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable Gmail API and Calendar API
3. Configure OAuth consent screen (External or Internal)
4. Create OAuth 2.0 credentials (Desktop app)

**Security Requirements**:

| Requirement | Implementation |
|-------------|----------------|
| Dedicated account | Never use personal Google account |
| Scoped permissions | Read-only where possible |
| Token storage | Composio vault or encrypted storage |
| Refresh token handling | Automated rotation, secure storage |

**Source**: [DigitalOcean Google Integration](https://www.digitalocean.com/community/tutorials/connect-google-to-openclaw)

### 7.2 Calendar Integration

```bash
# Via Composio
composio add google-calendar

# Scopes requested:
# - calendar.readonly (read events)
# - calendar.events (create/modify events)
```

**Minimal Scope Principle**: Only request calendar scopes you need.

### 7.3 Security Best Practices

From [OpenClaw Experts Guide](https://www.openclawexperts.io/guides/custom-dev/how-to-connect-openclaw-to-gmail-and-google-calendar):

> "Treat OAuth tokens like passwords. Store them with restrictive filesystem permissions and keep them out of git, backups and screenshots."

**Recommendations**:
1. Use SSH tunneling for OAuth flow on headless servers
2. Store `google-token.json` with 600 permissions
3. Never commit tokens to version control
4. Implement token rotation
5. Log all Gmail/Calendar access for audit

---

## 8. Messaging Channels (Slack/WhatsApp)

### 8.1 Slack Integration

**Options**:
1. **Slack Bolt** (native OpenClaw integration)
2. **Composio Slack** (managed credentials)

**Security Considerations**:
- Bot token scope: Request minimal permissions
- Signing secret: Verify all incoming requests
- Channel restrictions: Limit bot to specific channels
- User allowlists: Control who can interact

### 8.2 WhatsApp Integration

OpenClaw uses **Baileys** (unofficial WhatsApp Web API).

**Risks**:
- Account ban risk (unofficial API)
- Session hijacking if QR code exposed
- No official enterprise support

**For SaaS**: Consider WhatsApp Business API instead.

### 8.3 Channel Security

From [OpenClaw Security Docs](https://docs.openclaw.ai/gateway/security):

```json5
{
  "channels": {
    "whatsapp": {
      "allowFrom": ["+1234567890"],  // Allowlist
      "dmPolicy": "pairing"           // Require pairing code
    },
    "slack": {
      "activation": "mention"         // Only respond to @mentions
    }
  }
}
```

---

## 9. Electron App Considerations

### 9.1 Architecture

Your Electron app can serve as the **orchestration layer**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      ELECTRON APP                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Main Process                           │    │
│  │  - Customer authentication                               │    │
│  │  - Container orchestration                               │    │
│  │  - Credential management (via Composio)                  │    │
│  │  - Audit logging                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Renderer Process                        │    │
│  │  - Chat interface                                        │    │
│  │  - Settings UI                                           │    │
│  │  - Integration management                                │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ IPC
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND SERVICES                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  OpenClaw   │  │  Composio   │  │   Your API              │  │
│  │  Gateway    │  │  SDK        │  │   (Agencity)            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Existing Electron Clients

**ClawUI** ([GitHub](https://github.com/Kt-L/clawUI)):
- React + Vite + Electron
- Unsigned macOS build (requires Gatekeeper bypass)
- "Vibe Coding" experience

**ClawX** ([GitHub](https://github.com/ValueCell-ai/ClawX)):
- Desktop GUI for OpenClaw
- Native OS secure storage for API keys
- No terminal required

### 9.3 Security in Electron

| Concern | Mitigation |
|---------|------------|
| **Node integration** | Disable in renderer (`nodeIntegration: false`) |
| **Context isolation** | Enable (`contextIsolation: true`) |
| **Remote module** | Disable (`enableRemoteModule: false`) |
| **Web security** | Enable (`webSecurity: true`) |
| **Credential storage** | Use OS keychain (electron-keytar) |
| **Auto-update** | Sign updates, verify signatures |
| **Code signing** | Sign app for distribution |

### 9.4 Hybrid Architecture

**Local Electron + Cloud Backend**:

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER'S MACHINE                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   ELECTRON APP                           │    │
│  │  - UI/UX                                                 │    │
│  │  - Local file access (with permission)                   │    │
│  │  - OAuth popup handling                                  │    │
│  └───────────────────────────┬─────────────────────────────┘    │
└──────────────────────────────┼──────────────────────────────────┘
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      YOUR CLOUD                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Customer Container (per-customer isolated)              │    │
│  │  - OpenClaw Gateway                                      │    │
│  │  - Agencity Backend                                      │    │
│  │  - Isolated storage                                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Shared Services                                         │    │
│  │  - Composio (credentials)                                │    │
│  │  - Audit logging                                         │    │
│  │  - Billing                                               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Deployment Recommendations

### 10.1 For Your Use Case

Given your requirements (Email + Calendar + Slack + SaaS):

| Approach | Recommendation |
|----------|----------------|
| **Architecture** | Multi-instance (container per customer) |
| **Credentials** | Composio for all OAuth |
| **Client** | Electron app as orchestration layer |
| **Backend** | Your Agencity API + per-customer OpenClaw |
| **Isolation** | Docker + network policies |

### 10.2 Minimum Security Requirements

From [DigitalOcean Hardened Deploy](https://www.digitalocean.com/blog/technical-dive-openclaw-hardened-1-click-app):

1. **Version**: v2026.1.29+ (CVE-2026-25253 patched)
2. **Binding**: Loopback only (127.0.0.1)
3. **Auth**: Token auth required
4. **Firewall**: Rate-limit OpenClaw ports
5. **User**: Non-root execution
6. **Sandbox**: Enable for exec tools
7. **Skills**: Disable ClawHub or strict allowlist

### 10.3 Production Checklist

From [SecureClaw](https://adversa.ai/blog/secureclaw-open-source-ai-agent-security-for-openclaw-aligned-with-owasp-mitre-frameworks/):

```bash
# Run security audit
openclaw security audit --deep

# Verify configuration
openclaw doctor
```

---

## 11. Security Checklist

### Pre-Deployment

- [ ] Upgrade to v2026.1.29+ (CVE patched)
- [ ] Configure token authentication
- [ ] Bind gateway to loopback only
- [ ] Enable sandbox mode for exec tools
- [ ] Disable or allowlist ClawHub skills
- [ ] Set up Composio for credentials
- [ ] Configure firewall rules
- [ ] Enable audit logging

### Per-Customer Setup

- [ ] Create isolated container
- [ ] Generate unique gateway token
- [ ] Configure customer-specific workspace
- [ ] Set up OAuth via Composio
- [ ] Configure channel allowlists
- [ ] Test isolation boundaries
- [ ] Document customer configuration

### Ongoing Operations

- [ ] Run `openclaw security audit` weekly
- [ ] Monitor for CVEs and update promptly
- [ ] Review audit logs regularly
- [ ] Rotate gateway tokens quarterly
- [ ] Test incident response procedures
- [ ] Backup customer configurations
- [ ] Monitor for unusual activity

---

## Sources

### Official Documentation
- [OpenClaw Security Docs](https://docs.openclaw.ai/gateway/security)
- [OpenClaw Multi-Agent Docs](https://docs.openclaw.ai/concepts/multi-agent)
- [OpenClaw GitHub Security](https://github.com/openclaw/openclaw/security)

### Security Analyses
- [Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/02/19/running-openclaw-safely-identity-isolation-runtime-risk/)
- [CrowdStrike Analysis](https://www.crowdstrike.com/en-us/blog/what-security-teams-need-to-know-about-openclaw-ai-super-agent/)
- [SecureClaw by Adversa AI](https://adversa.ai/blog/secureclaw-open-source-ai-agent-security-for-openclaw-aligned-with-owasp-mitre-frameworks/)

### Deployment Guides
- [DigitalOcean Hardened Deploy](https://www.digitalocean.com/blog/technical-dive-openclaw-hardened-1-click-app)
- [Enterprise Deployment Guide](https://eastondev.com/blog/en/posts/ai/20260205-openclaw-enterprise-deploy/)
- [Composio Security Guide](https://composio.dev/blog/secure-openclaw-moltbot-clawdbot-setup)

### Integration Guides
- [Google Integration](https://www.digitalocean.com/community/tutorials/connect-google-to-openclaw)
- [Gmail/Calendar Setup](https://www.openclawexperts.io/guides/custom-dev/how-to-connect-openclaw-to-gmail-and-google-calendar)

### Desktop Clients
- [ClawUI (Electron)](https://github.com/Kt-L/clawUI)
- [ClawX](https://github.com/ValueCell-ai/ClawX)
- [Secure OpenClaw](https://github.com/ComposioHQ/secure-openclaw)

### GitHub Issues
- [Multi-Agent Isolation Prerequisites](https://github.com/openclaw/openclaw/issues/10004)

---

*Document created February 2026*
