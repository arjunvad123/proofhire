"""
Context Manager - Intelligent context window management.

Learned from OpenClaw:
- Multi-stage pruning (soft trim → hard clear)
- Protected contexts (never prune critical info)
- Token budget allocation per source
"""

import json
from dataclasses import dataclass
from enum import Enum

from app.config import settings
from app.models.conversation import Conversation


class PruneAction(str, Enum):
    """What action was taken on context."""

    NONE = "none"
    SOFT_TRIM = "soft_trim"
    HARD_CLEAR = "hard_clear"


@dataclass
class ContextBudget:
    """Token budget allocation for different context sources."""

    system_prompt: int = 2_000
    blueprint: int = 3_000
    conversation: int = 15_000
    candidates: int = 50_000
    evaluation: int = 20_000
    response_headroom: int = 10_000

    @property
    def total(self) -> int:
        return (
            self.system_prompt
            + self.blueprint
            + self.conversation
            + self.candidates
            + self.evaluation
            + self.response_headroom
        )


class ContextManager:
    """
    Manages conversation context with intelligent pruning.

    Key principles (from OpenClaw):
    1. Multi-stage pruning: soft trim before hard clear
    2. Protected contexts: never prune blueprint, calibration examples
    3. Token budgets: allocate space per source type
    """

    # What we never prune
    PROTECTED_KEYS = [
        "role_blueprint",
        "company_context",
        "calibration_examples",
        "success_criteria",
    ]

    def __init__(
        self,
        max_tokens: int = settings.max_context_tokens,
        soft_trim_ratio: float = settings.soft_trim_ratio,
        hard_clear_ratio: float = settings.hard_clear_ratio,
    ):
        self.max_tokens = max_tokens
        self.soft_trim_ratio = soft_trim_ratio
        self.hard_clear_ratio = hard_clear_ratio
        self.budget = ContextBudget()

    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation.
        ~4 chars per token for English text.
        """
        return len(text) // 4

    def get_usage_ratio(self, conversation: Conversation) -> float:
        """Calculate what % of context window is used."""
        total_chars = len(conversation.get_transcript())
        if conversation.blueprint:
            total_chars += len(conversation.blueprint.model_dump_json())
        if conversation.partial_context:
            total_chars += len(json.dumps(conversation.partial_context))

        estimated_tokens = self.estimate_tokens(str(total_chars))
        return estimated_tokens / self.max_tokens

    def should_prune(self, conversation: Conversation) -> PruneAction:
        """Determine if and how to prune context."""
        ratio = self.get_usage_ratio(conversation)

        if ratio > self.hard_clear_ratio:
            return PruneAction.HARD_CLEAR
        elif ratio > self.soft_trim_ratio:
            return PruneAction.SOFT_TRIM
        return PruneAction.NONE

    def prune(self, conversation: Conversation) -> tuple[Conversation, PruneAction]:
        """
        Apply appropriate pruning strategy.

        Returns the pruned conversation and what action was taken.
        """
        action = self.should_prune(conversation)

        if action == PruneAction.HARD_CLEAR:
            return self._hard_clear(conversation), action
        elif action == PruneAction.SOFT_TRIM:
            return self._soft_trim(conversation), action
        return conversation, action

    def _soft_trim(self, conversation: Conversation) -> Conversation:
        """
        Soft trim: Compress middle, keep head and tail.

        Strategy:
        - Keep first 3 messages (initial context)
        - Keep last 5 messages (recent context)
        - Summarize middle as "[Earlier discussion about X]"
        """
        messages = conversation.messages

        if len(messages) <= 8:
            # Not enough to trim
            return conversation

        # Keep first 3 and last 5
        head = messages[:3]
        tail = messages[-5:]
        middle = messages[3:-5]

        # Create summary of middle
        if middle:
            topics = self._extract_topics(middle)
            summary_content = f"[Earlier discussion covered: {', '.join(topics)}]"
            from app.models.conversation import Message
            summary_msg = Message(
                role="system",
                content=summary_content,
                timestamp=middle[0].timestamp
            )
            conversation.messages = head + [summary_msg] + tail

        return conversation

    def _hard_clear(self, conversation: Conversation) -> Conversation:
        """
        Hard clear: Replace old content with placeholders.

        Strategy:
        - Keep only last 3 messages
        - Replace everything else with summary placeholder
        - NEVER clear the blueprint if it exists
        """
        messages = conversation.messages

        if len(messages) <= 3:
            return conversation

        # Keep only last 3 messages
        tail = messages[-3:]

        # Create placeholder for cleared content
        from app.models.conversation import Message
        placeholder = Message(
            role="system",
            content="[Previous conversation cleared - see blueprint for context]",
            timestamp=messages[0].timestamp
        )

        conversation.messages = [placeholder] + tail
        return conversation

    def _extract_topics(self, messages: list) -> list[str]:
        """Extract topic keywords from messages for summary."""
        # Simple keyword extraction - could use LLM for better results
        topics = set()
        keywords = [
            "role", "startup", "engineer", "developer", "skills",
            "experience", "location", "school", "team", "product",
            "ML", "AI", "LLM", "prompt", "backend", "frontend",
        ]

        for msg in messages:
            content_lower = msg.content.lower()
            for kw in keywords:
                if kw.lower() in content_lower:
                    topics.add(kw)

        return list(topics)[:5]  # Max 5 topics

    def build_context_for_llm(
        self,
        conversation: Conversation,
        purpose: str = "intake"
    ) -> dict[str, str]:
        """
        Build context dict for LLM call with token budgets.

        Args:
            conversation: The conversation to build context from
            purpose: "intake" | "evaluate" | "search" - affects budget allocation

        Returns:
            Dict with context sections, each within budget
        """
        context = {}

        # Always include blueprint if available (protected)
        if conversation.blueprint:
            context["blueprint"] = self._truncate_to_budget(
                conversation.blueprint.model_dump_json(indent=2),
                self.budget.blueprint
            )

        # Conversation history
        transcript = conversation.get_transcript()
        context["conversation"] = self._truncate_to_budget(
            transcript,
            self.budget.conversation
        )

        # Partial context if no blueprint yet
        if not conversation.blueprint and conversation.partial_context:
            context["partial_context"] = self._truncate_to_budget(
                json.dumps(conversation.partial_context, indent=2),
                self.budget.blueprint
            )

        return context

    def _truncate_to_budget(self, text: str, token_budget: int) -> str:
        """Truncate text to fit within token budget."""
        char_budget = token_budget * 4  # ~4 chars per token

        if len(text) <= char_budget:
            return text

        # Keep head and tail
        head_chars = char_budget // 2
        tail_chars = char_budget // 2

        return (
            text[:head_chars]
            + "\n\n[...truncated...]\n\n"
            + text[-tail_chars:]
        )
