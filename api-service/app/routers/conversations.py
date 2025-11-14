"""
Story 3.3: Conversation List Sidebar

Conversation management endpoints for listing, viewing, and managing conversations.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.services.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# Response models
class ConversationItem(BaseModel):
    """Single conversation item in list."""
    id: str
    title: str
    first_message_preview: str
    updated_at: datetime
    message_count: int

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """Response model for conversation list."""
    conversations: list[ConversationItem]
    total: int
    limit: int
    offset: int
    has_more: bool


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    user_id: str = Query(..., description="User ID to fetch conversations for"),
    limit: int = Query(20, ge=1, le=100, description="Number of conversations to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of conversations for a user.

    Returns conversations ordered by most recently updated first.
    Includes first message preview (first 60 characters) and message count.

    AC #1: Sidebar Display - Return conversations ordered by updated_at DESC
    AC #4: Pagination - Support limit/offset pagination with metadata
    """
    try:
        # Get total count for pagination metadata
        total = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status == 'active'  # Only show active conversations
        ).count()

        # Get paginated conversations
        conversations_query = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status == 'active'
        ).order_by(desc(Conversation.updated_at)).limit(limit).offset(offset)

        conversations = conversations_query.all()

        # Build response with first message preview and message count
        conversation_items = []
        for conv in conversations:
            # Get first user message for preview
            first_message = db.query(Message).filter(
                Message.conversation_id == conv.id,
                Message.role == 'user'
            ).order_by(Message.created_at).first()

            # Get message count
            message_count = db.query(func.count(Message.id)).filter(
                Message.conversation_id == conv.id
            ).scalar()

            # Create preview (first 60 characters)
            preview = ""
            if first_message:
                content = first_message.content
                preview = content[:60]
                if len(content) > 60:
                    preview += "..."

            conversation_items.append(ConversationItem(
                id=str(conv.id),
                title=conv.title or "Untitled Conversation",
                first_message_preview=preview,
                updated_at=conv.updated_at,
                message_count=message_count or 0
            ))

        # Calculate has_more
        has_more = (offset + limit) < total

        return ConversationListResponse(
            conversations=conversation_items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more
        )

    except Exception as e:
        logger.error(f"Error fetching conversations for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}"
        )
