"""
LLM Service - OpenAI API wrapper.

Handles all LLM interactions with proper error handling,
retries, and token management.
"""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Wrapper for OpenAI API interactions.

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
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.default_model
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """
        Get a completion from OpenAI.

        Args:
            prompt: The user prompt
            system: Optional system prompt
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            The model's response text
        """
        try:
            messages = []

            if system:
                messages.append({"role": "system", "content": system})

            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
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
{json.dumps(schema, indent=2)}
```

No markdown, no explanation, just the JSON object."""

        response = await self.complete(
            prompt=schema_prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temperature for structured output
        )

        # Parse JSON from response
        text = response.strip()

        # Handle markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            start = 1 if lines[0].startswith("```") else 0
            end = len(lines) - 1 if lines[-1] == "```" else len(lines)
            text = "\n".join(lines[start:end])
            if text.startswith("json"):
                text = text[4:].strip()

        return json.loads(text)

    async def embed(self, text: str) -> list[float]:
        """
        Generate embeddings for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation.
        GPT uses ~4 chars per token for English.
        """
        return len(text) // 4
