"""
Conversation Engine - The intake flow.

This manages the conversation with founders to understand
what they actually need, then extracts a Role Blueprint.
"""

import json
import logging
from typing import NamedTuple

from app.config import settings
from app.core.context_manager import ContextManager
from app.models.blueprint import RoleBlueprint
from app.models.conversation import Conversation, ConversationStatus
from app.services.llm import LLMService

logger = logging.getLogger(__name__)


class ConversationResponse(NamedTuple):
    """Response from processing a message."""

    message: str
    status: ConversationStatus
    blueprint: RoleBlueprint | None = None


class ConversationEngine:
    """
    Manages the intake conversation flow.

    Flow:
    1. User describes what they need (often vague)
    2. We ask smart follow-up questions
    3. We extract partial context as we go
    4. When we have enough, we generate the Role Blueprint
    5. Trigger search with the blueprint
    """

    # What we need to have a complete blueprint
    REQUIRED_FIELDS = [
        "role_title",
        "company_context",
        "specific_work",
        "success_criteria",
    ]

    # Nice to have but not required
    OPTIONAL_FIELDS = [
        "must_haves",
        "nice_to_haves",
        "avoid",
        "location_preferences",
        "calibration_examples",
    ]

    # Max questions before we just work with what we have
    MAX_QUESTIONS = 6

    def __init__(
        self,
        llm_service: LLMService | None = None,
        context_manager: ContextManager | None = None,
    ):
        self.llm = llm_service or LLMService()
        self.context_manager = context_manager or ContextManager()

    async def process_message(
        self,
        conversation: Conversation,
        user_message: str,
    ) -> ConversationResponse:
        """
        Process a user message and decide next action.

        Returns:
        - Follow-up question if we need more context
        - Blueprint confirmation if we have enough
        - Search trigger if blueprint is complete
        """
        # Add user message
        conversation.add_message("user", user_message)

        # Prune context if needed
        conversation, prune_action = self.context_manager.prune(conversation)

        # Try to extract/update partial context
        partial = await self._extract_partial_context(conversation)
        conversation.partial_context.update(partial)

        # Check if we have enough for a complete blueprint
        if self._has_enough_context(conversation):
            # Generate the final blueprint
            blueprint = await self._finalize_blueprint(conversation)
            conversation.blueprint = blueprint
            conversation.status = ConversationStatus.SEARCHING

            response_msg = self._build_search_confirmation(blueprint)
            conversation.add_message("assistant", response_msg)

            return ConversationResponse(
                message=response_msg,
                status=ConversationStatus.SEARCHING,
                blueprint=blueprint,
            )

        # Check if we've asked too many questions
        if conversation.user_message_count() >= self.MAX_QUESTIONS:
            # Work with what we have
            blueprint = await self._finalize_blueprint(conversation)
            conversation.blueprint = blueprint
            conversation.status = ConversationStatus.SEARCHING

            response_msg = (
                "I think I have enough to start searching. "
                + self._build_search_confirmation(blueprint)
            )
            conversation.add_message("assistant", response_msg)

            return ConversationResponse(
                message=response_msg,
                status=ConversationStatus.SEARCHING,
                blueprint=blueprint,
            )

        # Need more context - ask follow-up question
        next_question = await self._get_next_question(conversation)
        conversation.add_message("assistant", next_question)

        return ConversationResponse(
            message=next_question,
            status=ConversationStatus.IN_PROGRESS,
        )

    def _has_enough_context(self, conversation: Conversation) -> bool:
        """Check if we have enough context for a useful blueprint."""
        ctx = conversation.partial_context

        # Check all required fields have substance
        for field in self.REQUIRED_FIELDS:
            value = ctx.get(field, "")
            if not value or len(str(value)) < 10:
                return False

        return True

    async def _extract_partial_context(
        self,
        conversation: Conversation,
    ) -> dict:
        """
        Extract structured context from conversation so far.
        Uses LLM to understand what information we have.
        """
        prompt = f"""Analyze this conversation and extract any information relevant to a hiring search.

Conversation:
{conversation.get_transcript()}

Extract what you can for these fields (leave empty if not mentioned):
- role_title: What role are they hiring for?
- company_context: What does their startup do? Stage? Team size?
- specific_work: What will this person actually build/do?
- success_criteria: What does success look like?
- must_haves: Non-negotiable requirements
- nice_to_haves: Preferences
- avoid: Red flags or anti-patterns
- location_preferences: Schools, cities, remote preferences
- calibration_examples: Past hire patterns that worked/didn't

Respond with ONLY valid JSON, no markdown:
{{"role_title": "...", "company_context": "...", ...}}
"""

        response = await self.llm.complete(prompt)

        try:
            # Parse JSON from response
            # Handle potential markdown code blocks
            text = response.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse context extraction: {response[:200]}")
            return {}

    async def _get_next_question(self, conversation: Conversation) -> str:
        """
        Generate the next follow-up question based on what we're missing.
        """
        ctx = conversation.partial_context
        missing = []

        for field in self.REQUIRED_FIELDS:
            if not ctx.get(field):
                missing.append(field)

        prompt = f"""You are helping a founder describe what they're looking for in a hire.

Here's what you know so far:
{json.dumps(ctx, indent=2)}

Missing information: {missing}

Conversation so far:
{conversation.get_transcript()}

Ask 1-2 focused follow-up questions to understand what they need.
Be conversational, not robotic. Don't ask about everything at once.

Focus on understanding:
- What will this person actually DO day-to-day?
- What does success look like by day 60?
- Any specific skills or background they need?
- Location/school preferences?

Keep it brief and natural. Just respond with your question(s), nothing else."""

        return await self.llm.complete(prompt)

    async def _finalize_blueprint(self, conversation: Conversation) -> RoleBlueprint:
        """
        Generate the final Role Blueprint from conversation.
        """
        prompt = f"""Based on this conversation, create a structured Role Blueprint.

Conversation:
{conversation.get_transcript()}

Partial context extracted:
{json.dumps(conversation.partial_context, indent=2)}

Create a complete blueprint. For any missing information, make reasonable inferences
based on the context (but keep them conservative).

Respond with ONLY valid JSON matching this schema:
{{
    "role_title": "string",
    "company_context": "string",
    "specific_work": "string",
    "success_criteria": "string",
    "must_haves": ["string"],
    "nice_to_haves": ["string"],
    "avoid": ["string"],
    "location_preferences": ["string"],
    "calibration_examples": ["string"]
}}"""

        response = await self.llm.complete(prompt)

        try:
            text = response.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            return RoleBlueprint(**data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse blueprint: {e}")
            # Return a minimal blueprint from partial context
            ctx = conversation.partial_context
            return RoleBlueprint(
                role_title=ctx.get("role_title", "Unknown Role"),
                company_context=ctx.get("company_context", "Early stage startup"),
                specific_work=ctx.get("specific_work", "To be determined"),
                success_criteria=ctx.get("success_criteria", "Shipping quality work"),
                must_haves=ctx.get("must_haves", []),
                nice_to_haves=ctx.get("nice_to_haves", []),
                avoid=ctx.get("avoid", []),
                location_preferences=ctx.get("location_preferences", []),
                calibration_examples=ctx.get("calibration_examples", []),
            )

    def _build_search_confirmation(self, blueprint: RoleBlueprint) -> str:
        """Build a confirmation message showing what we understood."""
        return f"""Got it! Here's what I understood:

**Looking for:** {blueprint.role_title}
**Company:** {blueprint.company_context}
**The work:** {blueprint.specific_work}
**Success looks like:** {blueprint.success_criteria}

{"**Must have:** " + ", ".join(blueprint.must_haves) if blueprint.must_haves else ""}
{"**Nice to have:** " + ", ".join(blueprint.nice_to_haves) if blueprint.nice_to_haves else ""}
{"**Prefer:** " + ", ".join(blueprint.location_preferences) if blueprint.location_preferences else ""}

Searching our network, GitHub, and hackathon projects now..."""
