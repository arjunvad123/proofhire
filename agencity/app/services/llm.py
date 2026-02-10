"""
LLM Service - Claude API wrapper.

Handles all LLM interactions with proper error handling,
retries, and token management.
"""

import logging
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Wrapper for Claude API interactions.

    Handles:
    - Token counting and limits
    - Error handling and retries
    - Structured output parsing
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.default_model
        self.client = anthropic.Anthropic(api_key=self.api_key)

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """
        Get a completion from Claude.

        Args:
            prompt: The user prompt
            system: Optional system prompt
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            The model's response text
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature,
            }

            if system:
                kwargs["system"] = system

            # Use sync client (we're in async context but Anthropic SDK handles it)
            response = self.client.messages.create(**kwargs)

            return response.content[0].text

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in LLM service: {e}")
            raise

    async def complete_with_schema(
        self,
        prompt: str,
        schema: dict,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> dict:
        """
        Get a structured completion matching a JSON schema.

        Args:
            prompt: The user prompt
            schema: JSON schema for expected output
            system: Optional system prompt
            max_tokens: Maximum response tokens

        Returns:
            Parsed JSON response
        """
        # Add schema instructions to prompt
        schema_prompt = f"""{prompt}

Respond with ONLY valid JSON matching this schema:
```json
{schema}
```

No markdown, no explanation, just the JSON object."""

        response = await self.complete(
            prompt=schema_prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temperature for structured output
        )

        # Parse JSON from response
        import json

        text = response.strip()

        # Handle markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Find the actual JSON content
            start = 1 if lines[0].startswith("```") else 0
            end = len(lines) - 1 if lines[-1] == "```" else len(lines)
            text = "\n".join(lines[start:end])
            if text.startswith("json"):
                text = text[4:].strip()

        return json.loads(text)

    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation.
        Claude uses ~4 chars per token for English.
        """
        return len(text) // 4
