"""
Slack integration for Hermes agent - UNIFIED SEARCH VERSION

Allows users to interact with Agencity via @hermes mentions in Slack.
Searches across BOTH Hermes (1,378 opted-in) + Network (7,274 LinkedIn) = ~9,000 total.
"""

import hashlib
import hmac
import logging
import time
from datetime import datetime

import httpx

from app.config import settings
from app.services.conversation_engine import ConversationEngine
from app.services.unified_search import UnifiedSearchOrchestrator
from app.services.shortlist_builder import ShortlistBuilder
from app.services.slack_workspace_mapper import SlackWorkspaceMapper

logger = logging.getLogger(__name__)


class SlackBot:
    """
    Slack bot that responds to @hermes mentions.

    NEW: Uses unified search across Hermes + Network sources.

    Usage in Slack:
        @hermes I need a prompt engineer for my AI startup
        @hermes Looking for a backend engineer who knows Python
    """

    def __init__(self):
        self.bot_token = settings.slack_bot_token
        self.signing_secret = settings.slack_signing_secret

        # NEW: Unified search services
        self.conversation_engine = ConversationEngine()
        self.search_orchestrator = UnifiedSearchOrchestrator()
        self.shortlist_builder = ShortlistBuilder()
        self.workspace_mapper = SlackWorkspaceMapper()

    def verify_signature(self, body: bytes, timestamp: str, signature: str) -> bool:
        """Verify that the request came from Slack."""
        if not self.signing_secret:
            logger.warning("No Slack signing secret configured")
            return False

        # Check timestamp to prevent replay attacks
        try:
            if abs(time.time() - int(timestamp)) > 60 * 5:
                logger.warning("Slack request timestamp too old")
                return False
        except (ValueError, TypeError):
            logger.warning("Invalid Slack timestamp")
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
            result = response.json()
            if not result.get("ok"):
                logger.error(f"Slack API error: {result.get('error')}")
            return result

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
            result = response.json()
            if not result.get("ok") and result.get("error") != "already_reacted":
                logger.warning(f"Failed to add reaction: {result.get('error')}")
            return result

    async def remove_reaction(self, channel: str, timestamp: str, emoji: str) -> dict:
        """Remove a reaction from a message."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/reactions.remove",
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
            result = response.json()
            if not result.get("ok") and result.get("error") != "no_reaction":
                logger.warning(f"Failed to remove reaction: {result.get('error')}")
            return result

    async def handle_mention(
        self,
        channel: str,
        user: str,
        text: str,
        thread_ts: str | None = None,
        message_ts: str | None = None,
        team_id: str | None = None,
    ) -> None:
        """
        Handle an @hermes mention - UNIFIED SEARCH VERSION

        Flow:
        1. Extract role requirements from message
        2. If clear -> run unified search across Hermes + Network
        3. If unclear -> ask clarifying question
        4. Deliver shortlist to Slack
        """
        # Use thread_ts if in thread, otherwise use message_ts to start a thread
        reply_thread = thread_ts or message_ts

        # Remove the bot mention from the text
        clean_text = text
        if "<@" in text:
            parts = text.split(">", 1)
            if len(parts) > 1:
                clean_text = parts[1].strip()

        if not clean_text:
            await self.send_message(
                channel,
                "Hey! Tell me what role you're hiring for and I'll search ~9,000 candidates (Hermes + Network).\n\nExample: `@hermes I need a prompt engineer for my AI startup`",
                thread_ts=reply_thread,
            )
            return

        # Add thinking reaction
        if message_ts:
            await self.add_reaction(channel, message_ts, "thinking_face")

        try:
            # Extract role requirements using conversation engine
            role = await self.conversation_engine.extract_role(clean_text)

            if role:
                # Clear requirements -> run unified search
                await self._run_unified_search(
                    channel=channel,
                    reply_thread=reply_thread,
                    role=role,
                    team_id=team_id
                )

                # Success reaction
                if message_ts:
                    await self.remove_reaction(channel, message_ts, "thinking_face")
                    await self.add_reaction(channel, message_ts, "white_check_mark")

            else:
                # Unclear requirements -> ask clarifying question
                question = await self.conversation_engine.generate_clarifying_question(clean_text)

                await self.send_message(
                    channel,
                    question,
                    thread_ts=reply_thread,
                )

                # Keep thinking reaction (waiting for answer)

        except Exception as e:
            logger.error(f"Error handling mention: {e}", exc_info=True)

            # Error reaction
            if message_ts:
                await self.remove_reaction(channel, message_ts, "thinking_face")
                await self.add_reaction(channel, message_ts, "x")

            await self.send_message(
                channel,
                f"Sorry, I ran into an error: {str(e)}",
                thread_ts=reply_thread,
            )

    async def _run_unified_search(
        self,
        channel: str,
        reply_thread: str,
        role: 'RoleBlueprint',
        team_id: str | None = None
    ):
        """Run unified search and deliver shortlist to Slack."""

        # Get company_id from Slack workspace
        try:
            if team_id:
                company_id = await self.workspace_mapper.get_company_id(team_id)
            else:
                # Fallback to default company (Confido from docs)
                company_id = "100b5ac1-1912-4970-a378-04d0169fd597"
                logger.warning(f"No team_id provided, using default company: {company_id}")
        except ValueError as e:
            logger.error(f"Failed to get company_id: {e}")
            await self.send_message(
                channel,
                "⚠️ Your Slack workspace hasn't been connected to Agencity yet. Please complete onboarding first.",
                thread_ts=reply_thread,
            )
            return

        # Status update
        await self.send_message(
            channel,
            f"🔍 Searching ~9,000 candidates (Hermes + Network) for: *{role.title}*...",
            thread_ts=reply_thread,
        )

        # Run unified search
        search_results = await self.search_orchestrator.search(
            company_id=company_id,
            role=role,
            limit=100
        )

        # Build shortlist (12 candidates)
        shortlist = self.shortlist_builder.build_shortlist(
            search_results=search_results,
            target_size=12
        )

        # Format for Slack
        blocks = self.shortlist_builder.format_for_slack(
            shortlist=shortlist,
            stats=search_results["stats"]
        )

        # Deliver shortlist
        await self.send_message(
            channel,
            f"Found {len(shortlist)} candidates worth talking to",  # Fallback text
            thread_ts=reply_thread,
            blocks=blocks
        )

        # Send stats summary
        stats = search_results["stats"]
        stats_text = (
            f"_Search complete:_\n"
            f"• Hermes candidates: {stats['hermes_searched']:,}\n"
            f"• Network candidates: {stats['network_searched']:,}\n"
            f"• Duplicates merged: {stats['duplicates_merged']}\n"
            f"• Total unique: {stats['total_unique']:,}\n"
            f"• Time: {search_results['duration_seconds']:.1f}s"
        )

        await self.send_message(
            channel,
            stats_text,
            thread_ts=reply_thread,
        )

    async def handle_event(self, event: dict) -> None:
        """Handle a Slack event."""
        event_type = event.get("type")

        # Extract team_id for workspace mapping
        # Note: team_id is in the outer event payload, not in event itself
        # The route will need to pass this in
        team_id = event.get("team")

        if event_type == "app_mention":
            await self.handle_mention(
                channel=event["channel"],
                user=event["user"],
                text=event.get("text", ""),
                thread_ts=event.get("thread_ts"),
                message_ts=event.get("ts"),
                team_id=team_id,
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
                    team_id=team_id,
                )


# Global instance
slack_bot = SlackBot()
