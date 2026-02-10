"""
Conversation models for intake flow.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from app.models.blueprint import RoleBlueprint


class ConversationStatus(str, Enum):
    """Status of an intake conversation."""

    IN_PROGRESS = "in_progress"  # Still gathering context
    BLUEPRINT_READY = "blueprint_ready"  # Have enough context
    SEARCHING = "searching"  # Search in progress
    COMPLETE = "complete"  # Shortlist ready


class Message(BaseModel):
    """A single message in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # For assistant messages with tool calls
    tool_calls: list[dict] | None = None


class Conversation(BaseModel):
    """
    An intake conversation with a founder.

    We ask smart follow-up questions until we have
    enough context to build a Role Blueprint.
    """

    id: str
    user_id: str
    messages: list[Message] = Field(default_factory=list)
    status: ConversationStatus = ConversationStatus.IN_PROGRESS
    blueprint: RoleBlueprint | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Context tracking
    partial_context: dict = Field(
        default_factory=dict,
        description="Extracted context so far (before full blueprint)"
    )

    def add_message(self, role: str, content: str) -> Message:
        """Add a message to the conversation."""
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        return msg

    def get_transcript(self) -> str:
        """Get conversation as plain text transcript."""
        lines = []
        for msg in self.messages:
            prefix = "Founder" if msg.role == "user" else "Agencity"
            lines.append(f"{prefix}: {msg.content}")
        return "\n\n".join(lines)

    def message_count(self) -> int:
        """Count total messages."""
        return len(self.messages)

    def user_message_count(self) -> int:
        """Count user messages only."""
        return len([m for m in self.messages if m.role == "user"])
