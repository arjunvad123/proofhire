"""LLM Gateway - provider abstraction with audit logging.

All LLM calls go through this gateway to ensure:
1. All inputs/outputs are logged to audit log
2. All outputs are schema-validated
3. No deterministic grading decisions are made by LLM
"""

import json
import time
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.core.audit import log_audit_event
from app.llm.schemas import (
    InterviewQuestionsOutput,
    WriteupSummaryOutput,
    WriteupTaggingOutput,
)
from app.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMGateway:
    """Gateway for all LLM interactions.

    Provides:
    - Provider abstraction (currently Anthropic Claude)
    - Automatic audit logging of all calls
    - Schema validation of outputs
    - Rate limiting and error handling
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.LLM_MODEL

    async def tag_writeup(
        self,
        writeup_text: str,
        run_id: str,
        user_id: str | None = None,
    ) -> WriteupTaggingOutput:
        """Extract tags from a candidate writeup.

        This is a BOUNDED LLM use case:
        - Only extracts factual observations (topic presence)
        - Does NOT make quality judgments
        - All tags require citations (direct quotes)
        """
        from app.llm.prompts import WRITEUP_TAGGING_PROMPT

        prompt = WRITEUP_TAGGING_PROMPT.format(writeup=writeup_text)

        result = await self._call_with_schema(
            prompt=prompt,
            output_schema=WriteupTaggingOutput,
            run_id=run_id,
            user_id=user_id,
            call_type="writeup_tagging",
        )

        return result

    async def summarize_writeup(
        self,
        writeup_text: str,
        run_id: str,
        user_id: str | None = None,
    ) -> WriteupSummaryOutput:
        """Generate a brief summary of the writeup."""
        from app.llm.prompts import WRITEUP_SUMMARY_PROMPT

        prompt = WRITEUP_SUMMARY_PROMPT.format(writeup=writeup_text)

        result = await self._call_with_schema(
            prompt=prompt,
            output_schema=WriteupSummaryOutput,
            run_id=run_id,
            user_id=user_id,
            call_type="writeup_summary",
        )

        return result

    async def generate_interview_questions(
        self,
        unproven_claims: list[dict[str, Any]],
        com: dict[str, Any],
        run_id: str,
        user_id: str | None = None,
    ) -> InterviewQuestionsOutput:
        """Generate interview questions for unproven claims."""
        from app.llm.prompts import INTERVIEW_QUESTIONS_PROMPT

        prompt = INTERVIEW_QUESTIONS_PROMPT.format(
            claims=json.dumps(unproven_claims, indent=2),
            com=json.dumps(com, indent=2),
        )

        result = await self._call_with_schema(
            prompt=prompt,
            output_schema=InterviewQuestionsOutput,
            run_id=run_id,
            user_id=user_id,
            call_type="interview_questions",
        )

        return result

    async def _call_with_schema(
        self,
        prompt: str,
        output_schema: type[T],
        run_id: str,
        user_id: str | None,
        call_type: str,
    ) -> T:
        """Make an LLM call with schema validation and audit logging."""
        start_time = time.time()

        # Log the request
        log_audit_event(
            event_type="llm_request",
            user_id=user_id,
            details={
                "run_id": run_id,
                "call_type": call_type,
                "model": self.model,
                "prompt_length": len(prompt),
            },
        )

        try:
            # Make the API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Extract response text
            response_text = response.content[0].text
            duration = time.time() - start_time

            # Parse and validate against schema
            try:
                # Try to parse as JSON
                response_data = json.loads(response_text)
                result = output_schema.model_validate(response_data)

            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(
                    "LLM response validation failed",
                    call_type=call_type,
                    error=str(e),
                )
                # Log the failure
                log_audit_event(
                    event_type="llm_validation_error",
                    user_id=user_id,
                    details={
                        "run_id": run_id,
                        "call_type": call_type,
                        "error": str(e),
                        "response_preview": response_text[:500],
                    },
                )
                raise ValueError(f"LLM response validation failed: {e}")

            # Log successful response
            log_audit_event(
                event_type="llm_response",
                user_id=user_id,
                details={
                    "run_id": run_id,
                    "call_type": call_type,
                    "duration_seconds": duration,
                    "response_length": len(response_text),
                    "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                },
            )

            logger.info(
                "LLM call completed",
                call_type=call_type,
                duration=round(duration, 2),
                tokens=response.usage.input_tokens + response.usage.output_tokens,
            )

            return result

        except anthropic.APIError as e:
            duration = time.time() - start_time
            logger.error("LLM API error", error=str(e), call_type=call_type)

            log_audit_event(
                event_type="llm_error",
                user_id=user_id,
                details={
                    "run_id": run_id,
                    "call_type": call_type,
                    "error": str(e),
                    "duration_seconds": duration,
                },
            )
            raise


# Global gateway instance
_gateway: LLMGateway | None = None


def get_llm_gateway() -> LLMGateway:
    """Get the global LLM gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway
