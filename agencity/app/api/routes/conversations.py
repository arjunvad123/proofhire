"""
Conversation API routes.

Handles the intake conversation flow with founders.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.conversation_engine import ConversationEngine
from app.core.search_engine import SearchEngine
from app.models.conversation import Conversation, ConversationStatus

router = APIRouter(prefix="/conversations", tags=["conversations"])

# In-memory storage for MVP (replace with database)
conversations: dict[str, Conversation] = {}

# Engine instances
conversation_engine = ConversationEngine()
search_engine = SearchEngine()


class StartConversationRequest(BaseModel):
    """Request to start a new conversation."""

    user_id: str
    initial_message: str | None = None


class SendMessageRequest(BaseModel):
    """Request to send a message."""

    content: str


class ConversationResponse(BaseModel):
    """Response with conversation state."""

    id: str
    status: str
    message: str | None = None
    blueprint: dict | None = None


@router.post("", response_model=ConversationResponse)
async def start_conversation(request: StartConversationRequest):
    """
    Start a new intake conversation.

    If initial_message is provided, process it immediately.
    Otherwise, return a greeting.
    """
    conversation_id = str(uuid.uuid4())

    conversation = Conversation(
        id=conversation_id,
        user_id=request.user_id,
        status=ConversationStatus.IN_PROGRESS,
        created_at=datetime.utcnow(),
    )

    # Store conversation
    conversations[conversation_id] = conversation

    if request.initial_message:
        # Process the initial message
        result = await conversation_engine.process_message(
            conversation,
            request.initial_message,
        )
        return ConversationResponse(
            id=conversation_id,
            status=result.status.value,
            message=result.message,
            blueprint=result.blueprint.model_dump() if result.blueprint else None,
        )

    # Return greeting
    greeting = (
        "Hi! Tell me about the role you're looking to fill. "
        "Even if it's vague like 'I need a prompt engineer for my startup', "
        "I'll ask follow-up questions to understand what you actually need."
    )
    conversation.add_message("assistant", greeting)

    return ConversationResponse(
        id=conversation_id,
        status=conversation.status.value,
        message=greeting,
    )


@router.post("/{conversation_id}/message", response_model=ConversationResponse)
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message in an existing conversation.

    Returns the agent's response and updated status.
    """
    conversation = conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.status == ConversationStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Conversation already complete")

    # Process the message
    result = await conversation_engine.process_message(
        conversation,
        request.content,
    )

    # If we got a blueprint, trigger search in background
    if result.status == ConversationStatus.SEARCHING and result.blueprint:
        # TODO: Move to background task
        shortlist = await search_engine.search(result.blueprint, limit=5)
        shortlist.conversation_id = conversation_id
        conversation.status = ConversationStatus.COMPLETE

        # Store shortlist (would be in database)
        # For now, just log it
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Generated shortlist with {len(shortlist.candidates)} candidates")

    return ConversationResponse(
        id=conversation_id,
        status=conversation.status.value,
        message=result.message,
        blueprint=result.blueprint.model_dump() if result.blueprint else None,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get current conversation state."""
    conversation = conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    last_message = conversation.messages[-1] if conversation.messages else None

    return ConversationResponse(
        id=conversation_id,
        status=conversation.status.value,
        message=last_message.content if last_message else None,
        blueprint=conversation.blueprint.model_dump() if conversation.blueprint else None,
    )


@router.get("/{conversation_id}/blueprint")
async def get_blueprint(conversation_id: str):
    """Get the extracted blueprint from a conversation."""
    conversation = conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not conversation.blueprint:
        raise HTTPException(status_code=400, detail="Blueprint not yet extracted")

    return conversation.blueprint.model_dump()
