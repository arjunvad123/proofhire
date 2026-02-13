"""
Slack Client - API wrapper with signature verification
"""

import hashlib
import hmac
import time
from typing import Optional, List
import httpx
import os


class SlackClient:
    """
    Slack API client with signature verification and messaging.
    """

    def __init__(self):
        self.token = os.getenv("SLACK_BOT_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        self.base_url = "https://slack.com/api"

        if not self.token or not self.signing_secret:
            raise ValueError("SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET must be set")

    def verify_signature(
        self,
        timestamp: str,
        body: bytes,
        signature: str
    ) -> bool:
        """
        Verify Slack request signature.

        Prevents replay attacks and unauthorized requests.
        """

        # Check timestamp is recent (within 5 minutes)
        if abs(time.time() - int(timestamp)) > 60 * 5:
            print("Slack signature verification failed: timestamp too old")
            return False

        # Compute signature
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        computed = 'v0=' + hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        if not hmac.compare_digest(computed, signature):
            print("Slack signature verification failed: signature mismatch")
            return False

        return True

    async def post_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[dict]] = None
    ) -> dict:
        """Post a message to a channel."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat.postMessage",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "channel": channel,
                    "text": text,
                    "thread_ts": thread_ts,
                    "blocks": blocks
                }
            )
            return response.json()

    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        name: str
    ) -> dict:
        """Add an emoji reaction to a message."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/reactions.add",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "channel": channel,
                    "timestamp": timestamp,
                    "name": name
                }
            )
            return response.json()

    async def remove_reaction(
        self,
        channel: str,
        timestamp: str,
        name: str
    ) -> dict:
        """Remove an emoji reaction from a message."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/reactions.remove",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "channel": channel,
                    "timestamp": timestamp,
                    "name": name
                }
            )
            return response.json()
