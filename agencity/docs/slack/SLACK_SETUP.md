# Hermes Slack Bot Setup Guide

This guide walks you through setting up the @hermes Slack bot for your workspace.

## Overview

The Hermes Slack bot lets your team find candidates directly from Slack:

```
@hermes I need a prompt engineer for my AI startup
```

Hermes will:
1. Ask clarifying questions in the thread
2. Search 1,375+ candidates in your network
3. Return candidates with honest evaluations (Known Facts, Observed Signals, Unknown)

## Prerequisites

- A Slack workspace where you have admin permissions
- The Agencity backend running (locally or deployed)
- A public URL for webhooks (use ngrok for local development)

## Step 1: Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Name it **"Hermes"** (or your preferred name)
5. Select your workspace

## Step 2: Configure Bot Permissions

### OAuth & Permissions

Navigate to **OAuth & Permissions** in the sidebar.

Add these **Bot Token Scopes**:

| Scope | Purpose |
|-------|---------|
| `app_mentions:read` | Receive @hermes mentions |
| `chat:write` | Send messages |
| `commands` | Slash commands |
| `im:history` | Read DM history |
| `im:read` | Access DMs |
| `im:write` | Send DMs |
| `reactions:write` | Add emoji reactions |

### Install to Workspace

1. Click **"Install to Workspace"**
2. Authorize the permissions
3. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

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

## Step 4: Configure Slash Commands (Optional)

Navigate to **Slash Commands** in the sidebar.

Click **"Create New Command"**:

| Field | Value |
|-------|-------|
| Command | `/hermes` |
| Request URL | `https://your-domain.com/api/slack/commands` |
| Short Description | Find candidates for your role |
| Usage Hint | `[role description]` |

## Step 5: Get App Credentials

Navigate to **Basic Information** in the sidebar.

Copy these values:
- **Signing Secret** (under "App Credentials")
- **Client ID** (if using OAuth install flow)
- **Client Secret** (if using OAuth install flow)

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
```

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

## Step 8: Test the Bot

1. Go to any channel in your Slack workspace
2. Invite the bot: `/invite @Hermes`
3. Mention the bot: `@Hermes I need a prompt engineer for my AI startup`
4. The bot should:
   - Add a 🤔 reaction
   - Reply in a thread with questions or results
   - Add a ✅ reaction when done

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

### In a Thread
Start a conversation and continue in the thread:
```
You: @hermes I need a prompt engineer
Hermes: What does your startup do, and what will this person work on?
You: We're building an AI writing assistant with RAG
Hermes: What would success look like by day 60?
...
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/slack/events` | POST | Slack Events API webhook |
| `/api/slack/commands` | POST | Slash command handler |
| `/api/slack/install` | GET | Get OAuth install URL |
| `/api/slack/oauth/callback` | GET | OAuth callback |

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

### Slow responses
- Slack requires a response within 3 seconds
- The bot sends an immediate acknowledgment, then processes in the background
- Check for timeouts in external API calls

## Security Considerations

1. **Verify all requests** using the signing secret
2. **Never commit tokens** to version control
3. **Use environment variables** for all secrets
4. **Limit permissions** to only what's needed
5. **Log and monitor** for unusual activity

## Production Deployment

For production:

1. Use a proper hosting service (Railway, Render, AWS, etc.)
2. Set up SSL/HTTPS
3. Configure proper environment variables
4. Set up monitoring and logging
5. Consider using Socket Mode for private deployments

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
