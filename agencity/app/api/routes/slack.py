"""
Slack API routes for webhook handling.

Handles:
- URL verification (for Slack app setup)
- Event subscriptions (mentions, messages)
- Slash commands (optional)
"""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from app.integrations.slack import slack_bot

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/events")
async def slack_events(
    request: Request,
    background_tasks: BackgroundTasks,
    x_slack_signature: str = Header(None, alias="X-Slack-Signature"),
    x_slack_request_timestamp: str = Header(None, alias="X-Slack-Request-Timestamp"),
):
    """
    Handle Slack Events API webhooks.

    This endpoint receives:
    - URL verification challenges (during app setup)
    - App mentions (@hermes)
    - Direct messages
    """
    body = await request.body()
    payload = await request.json()

    # Verify the request is from Slack (skip in dev if no secret)
    if slack_bot.signing_secret:
        if not slack_bot.verify_signature(body, x_slack_request_timestamp or "", x_slack_signature or ""):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Handle URL verification (Slack app setup)
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}

    # Handle events
    if payload.get("type") == "event_callback":
        event = payload.get("event", {})

        # Ignore bot messages to prevent loops
        if event.get("bot_id") or event.get("subtype") == "bot_message":
            return {"ok": True}

        # Handle the event in the background so we respond quickly
        background_tasks.add_task(slack_bot.handle_event, event)

    return {"ok": True}


@router.post("/commands")
async def slack_commands(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Handle Slack slash commands.

    Example: /hermes find me a prompt engineer
    """
    form_data = await request.form()

    command = form_data.get("command", "")
    text = form_data.get("text", "")
    user_id = form_data.get("user_id", "")
    channel_id = form_data.get("channel_id", "")
    response_url = form_data.get("response_url", "")

    logger.info(f"Received command: {command} {text} from {user_id}")

    # Acknowledge immediately (Slack requires response within 3 seconds)
    # Then process in background

    if command == "/hermes":
        background_tasks.add_task(
            handle_slash_command,
            text=text,
            user_id=user_id,
            channel_id=channel_id,
            response_url=response_url,
        )
        return {
            "response_type": "ephemeral",
            "text": "🔍 Searching... I'll post results in a moment."
        }

    return {
        "response_type": "ephemeral",
        "text": f"Unknown command: {command}"
    }


async def handle_slash_command(
    text: str,
    user_id: str,
    channel_id: str,
    response_url: str,
):
    """Process slash command in background and respond via response_url."""
    import httpx

    try:
        # Start conversation
        result = await slack_bot.conversation_engine.start_conversation(
            user_id=user_id,
            initial_message=text,
        )

        # If we got a blueprint, search
        if result.get("blueprint"):
            search_result = await slack_bot.search_engine.search(result["blueprint"])
            candidates = search_result.get("candidates", [])
            response_text, blocks = slack_bot.format_search_results(candidates)
        else:
            response_text = result["message"]
            blocks = None

        # Send response via response_url
        async with httpx.AsyncClient() as client:
            payload = {
                "response_type": "in_channel",
                "text": response_text,
            }
            if blocks:
                payload["blocks"] = blocks

            await client.post(response_url, json=payload)

    except Exception as e:
        logger.error(f"Error handling slash command: {e}")
        async with httpx.AsyncClient() as client:
            await client.post(response_url, json={
                "response_type": "ephemeral",
                "text": f"Sorry, I ran into an error: {str(e)}"
            })


@router.get("/install")
async def slack_install():
    """
    OAuth installation endpoint.

    Returns the Slack install URL for adding the bot to a workspace.
    """
    from app.config import settings

    if not settings.slack_client_id:
        raise HTTPException(status_code=500, detail="Slack client ID not configured")

    scopes = "app_mentions:read,chat:write,commands,im:history,im:read,im:write,reactions:write"
    install_url = (
        f"https://slack.com/oauth/v2/authorize"
        f"?client_id={settings.slack_client_id}"
        f"&scope={scopes}"
        f"&redirect_uri={settings.slack_redirect_uri or ''}"
    )

    return {"install_url": install_url}


@router.get("/oauth/callback")
async def slack_oauth_callback(code: str):
    """
    OAuth callback for Slack app installation.

    Exchanges the code for an access token.
    """
    import httpx
    from app.config import settings

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "code": code,
                "redirect_uri": settings.slack_redirect_uri or "",
            }
        )
        data = response.json()

    if not data.get("ok"):
        raise HTTPException(status_code=400, detail=data.get("error", "OAuth failed"))

    # In production, you'd save the access token to a database
    # For now, just return success
    return {
        "ok": True,
        "team": data.get("team", {}).get("name"),
        "message": "Hermes has been installed to your workspace!"
    }
