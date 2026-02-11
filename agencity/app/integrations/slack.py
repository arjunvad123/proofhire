"""
Slack integration for Hermes agent.

Allows users to interact with Agencity via @hermes mentions in Slack.
"""

import asyncio
import hashlib
import hmac
import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.core.conversation_engine import ConversationEngine
from app.core.search_engine import SearchEngine

logger = logging.getLogger(__name__)


class SlackBot:
    """
    Slack bot that responds to @hermes mentions.

    Usage in Slack:
        @hermes I need a prompt engineer for my AI startup
        @hermes Looking for a backend engineer who knows Python
    """

    def __init__(self):
        self.bot_token = settings.slack_bot_token
        self.signing_secret = settings.slack_signing_secret
        self.conversation_engine = ConversationEngine()
        self.search_engine = SearchEngine()

        # Track active conversations per channel/thread
        self.conversations: dict[str, str] = {}  # thread_ts -> conversation_id

    def verify_signature(self, body: bytes, timestamp: str, signature: str) -> bool:
        """Verify that the request came from Slack."""
        if not self.signing_secret:
            logger.warning("No Slack signing secret configured")
            return False

        # Check timestamp to prevent replay attacks
        if abs(time.time() - int(timestamp)) > 60 * 5:
            return False

        sig_basestring = f"v0:{timestamp}:{body.decode()}"
        my_signature = "v0=" + hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(my_signature, signature)

    async def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: str | None = None,
        blocks: list[dict] | None = None,
    ) -> dict:
        """Send a message to Slack."""
        async with httpx.AsyncClient() as client:
            payload = {
                "channel": channel,
                "text": text,
            }
            if thread_ts:
                payload["thread_ts"] = thread_ts
            if blocks:
                payload["blocks"] = blocks

            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            return response.json()

    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: list[dict] | None = None,
    ) -> dict:
        """Update an existing Slack message."""
        async with httpx.AsyncClient() as client:
            payload = {
                "channel": channel,
                "ts": ts,
                "text": text,
            }
            if blocks:
                payload["blocks"] = blocks

            response = await client.post(
                "https://slack.com/api/chat.update",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            return response.json()

    async def add_reaction(self, channel: str, timestamp: str, emoji: str) -> dict:
        """Add a reaction to a message."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/reactions.add",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "channel": channel,
                    "timestamp": timestamp,
                    "name": emoji,
                },
            )
            return response.json()

    def format_candidate_blocks(self, candidate: dict) -> list[dict]:
        """Format a candidate as Slack blocks."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{candidate['name']}*\n_{candidate.get('tagline', 'Candidate')}_"
                }
            }
        ]

        # Known Facts
        if candidate.get("known_facts"):
            facts = "\n".join([f"• {f}" for f in candidate["known_facts"][:3]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Known Facts*\n{facts}"
                }
            })

        # Observed Signals
        if candidate.get("observed_signals"):
            signals = "\n".join([f"• {s}" for s in candidate["observed_signals"][:3]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Observed Signals*\n{signals}"
                }
            })

        # Unknown
        if candidate.get("unknown"):
            unknown = "\n".join([f"• {u}" for u in candidate["unknown"][:2]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Unknown (verify in conversation)*\n{unknown}"
                }
            })

        # Why Consider
        if candidate.get("why_consider"):
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"💡 *Why consider:* {candidate['why_consider']}"
                    }
                ]
            })

        # Next Step
        if candidate.get("next_step"):
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"👉 *Next step:* {candidate['next_step']}"
                    }
                ]
            })

        blocks.append({"type": "divider"})

        return blocks

    def format_search_results(self, candidates: list[dict]) -> tuple[str, list[dict]]:
        """Format search results as Slack message with blocks."""
        if not candidates:
            return "No candidates found matching your criteria.", []

        text = f"Found {len(candidates)} candidates worth talking to:"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎯 Found {len(candidates)} candidates",
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "People worth a 30-minute conversation"
                    }
                ]
            },
            {"type": "divider"}
        ]

        # Add each candidate
        for candidate in candidates[:5]:  # Limit to 5 in Slack
            blocks.extend(self.format_candidate_blocks(candidate))

        if len(candidates) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_...and {len(candidates) - 5} more candidates_"
                    }
                ]
            })

        return text, blocks

    async def handle_mention(
        self,
        channel: str,
        user: str,
        text: str,
        thread_ts: str | None = None,
        message_ts: str | None = None,
    ) -> None:
        """
        Handle an @hermes mention.

        This runs the full conversation flow:
        1. Acknowledge the message
        2. Process through conversation engine
        3. If blueprint is ready, search for candidates
        4. Send results back to thread
        """
        # Use thread_ts if in thread, otherwise use message_ts to start a thread
        reply_thread = thread_ts or message_ts

        # Remove the bot mention from the text
        clean_text = text.replace("<@", "").split(">", 1)[-1].strip()

        if not clean_text:
            await self.send_message(
                channel,
                "Hey! Tell me what role you're hiring for and I'll find candidates worth talking to.\n\nExample: `@hermes I need a prompt engineer for my AI startup`",
                thread_ts=reply_thread,
            )
            return

        # Add thinking reaction
        if message_ts:
            await self.add_reaction(channel, message_ts, "thinking_face")

        try:
            # Get or create conversation for this thread
            conv_key = f"{channel}:{reply_thread}"

            if conv_key in self.conversations:
                # Continue existing conversation
                conv_id = self.conversations[conv_key]
                result = await self.conversation_engine.send_message(conv_id, clean_text)
            else:
                # Start new conversation
                result = await self.conversation_engine.start_conversation(
                    user_id=user,
                    initial_message=clean_text,
                )
                self.conversations[conv_key] = result["id"]

            # Send the agent's response
            await self.send_message(
                channel,
                result["message"],
                thread_ts=reply_thread,
            )

            # If we have a blueprint, search for candidates
            if result.get("blueprint"):
                # Send searching message
                searching_msg = await self.send_message(
                    channel,
                    "🔍 Searching our network of 1,375+ candidates...",
                    thread_ts=reply_thread,
                )

                # Run the search
                search_result = await self.search_engine.search(result["blueprint"])
                candidates = search_result.get("candidates", [])

                # Format and send results
                text, blocks = self.format_search_results(candidates)
                await self.send_message(
                    channel,
                    text,
                    thread_ts=reply_thread,
                    blocks=blocks if blocks else None,
                )

            # Add success reaction
            if message_ts:
                await self.add_reaction(channel, message_ts, "white_check_mark")

        except Exception as e:
            logger.error(f"Error handling mention: {e}")
            await self.send_message(
                channel,
                f"Sorry, I ran into an error: {str(e)}",
                thread_ts=reply_thread,
            )
            if message_ts:
                await self.add_reaction(channel, message_ts, "x")

    async def handle_event(self, event: dict) -> None:
        """Handle a Slack event."""
        event_type = event.get("type")

        if event_type == "app_mention":
            await self.handle_mention(
                channel=event["channel"],
                user=event["user"],
                text=event.get("text", ""),
                thread_ts=event.get("thread_ts"),
                message_ts=event.get("ts"),
            )
        elif event_type == "message":
            # Handle direct messages to the bot
            if event.get("channel_type") == "im":
                await self.handle_mention(
                    channel=event["channel"],
                    user=event["user"],
                    text=event.get("text", ""),
                    thread_ts=event.get("thread_ts"),
                    message_ts=event.get("ts"),
                )


# Global instance
slack_bot = SlackBot()
