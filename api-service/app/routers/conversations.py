"""
Story 3.3: Conversation List Sidebar
Story 3.6: Conversation Sharing via Link
Story 3.9: Conversation Export (Markdown)

Conversation management endpoints for listing, viewing, and managing conversations.
"""

import logging
import uuid
import re
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import Response
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
    search: Optional[str] = Query(None, description="Search query for filtering conversations"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of conversations for a user with optional search filtering.

    Returns conversations ordered by most recently updated first.
    Includes first message preview (first 60 characters) and message count.

    Story 3.3 AC #1: Sidebar Display - Return conversations ordered by updated_at DESC
    Story 3.3 AC #4: Pagination - Support limit/offset pagination with metadata
    Story 3.5 AC #1: Search filtering - Filter by title or message content (case-insensitive)
    """
    try:
        # Build base query
        base_filter = [
            Conversation.user_id == user_id,
            Conversation.status == 'active'  # Only show active conversations
        ]

        # Add search filter if provided (Story 3.5)
        if search:
            search_pattern = f"%{search}%"
            # Search in title OR in message content
            # Use subquery to find conversations with matching messages
            search_filter = func.or_(
                Conversation.title.ilike(search_pattern),
                Conversation.id.in_(
                    db.query(Message.conversation_id).filter(
                        Message.content.ilike(search_pattern)
                    ).distinct()
                )
            )
            base_filter.append(search_filter)

        # Get total count for pagination metadata
        total = db.query(Conversation).filter(*base_filter).count()

        # Get paginated conversations
        conversations_query = db.query(Conversation).filter(*base_filter).order_by(desc(Conversation.updated_at)).limit(limit).offset(offset)

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


# Story 3.6: Conversation Sharing
class ShareResponse(BaseModel):
    """Response model for share link generation."""
    share_url: str
    share_token: str
    expires_at: Optional[datetime]


class SharedConversationResponse(BaseModel):
    """Response model for viewing shared conversation."""
    id: str
    title: str
    owner_name: str
    created_at: datetime
    messages: list[dict]

    model_config = {"from_attributes": True}


@router.post("/{conversation_id}/share", response_model=ShareResponse)
async def generate_share_link(
    conversation_id: str,
    expires_in_days: int = Query(30, ge=1, le=365, description="Link expiration in days (1-365)"),
    user_id: str = Query(..., description="User ID (conversation owner)"),
    db: Session = Depends(get_db)
):
    """
    Generate a shareable link for a conversation.

    AC #2: Generate unique share token, set share_enabled=true, return share URL
    """
    try:
        # Find conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id  # Verify ownership
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or you don't have permission"
            )

        # Generate share token
        share_token = str(uuid.uuid4())

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Update conversation
        conversation.share_token = share_token
        conversation.share_enabled = True
        conversation.share_expires_at = expires_at

        db.commit()

        # Build share URL (use environment-based base URL in production)
        share_url = f"https://app.plccoach.com/shared/{share_token}"

        logger.info(f"Share link generated for conversation {conversation_id} by user {user_id}")

        return ShareResponse(
            share_url=share_url,
            share_token=share_token,
            expires_at=expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating share link: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate share link: {str(e)}"
        )


@router.get("/shared/{share_token}", response_model=SharedConversationResponse)
async def get_shared_conversation(
    share_token: str,
    db: Session = Depends(get_db)
):
    """
    View a shared conversation (read-only).

    AC #3: Return conversation if share_enabled=true and not expired
    """
    try:
        # Find conversation by share token
        conversation = db.query(Conversation).filter(
            Conversation.share_token == share_token
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared conversation not found"
            )

        # Verify sharing is enabled
        if not conversation.share_enabled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This conversation is no longer shared"
            )

        # Check expiration
        if conversation.share_expires_at and conversation.share_expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This shared link has expired"
            )

        # Get messages
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at).all()

        # Format messages
        messages_data = [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "citations": msg.citations
            }
            for msg in messages
        ]

        # Get owner name
        from app.models.user import User
        owner = db.query(User).filter(User.id == conversation.user_id).first()
        owner_name = owner.name if owner else "Unknown User"

        return SharedConversationResponse(
            id=str(conversation.id),
            title=conversation.title or "Untitled Conversation",
            owner_name=owner_name,
            created_at=conversation.created_at,
            messages=messages_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching shared conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch shared conversation: {str(e)}"
        )


@router.delete("/{conversation_id}/share")
async def disable_sharing(
    conversation_id: str,
    user_id: str = Query(..., description="User ID (conversation owner)"),
    db: Session = Depends(get_db)
):
    """
    Disable sharing for a conversation.

    AC #4: Set share_enabled=false, invalidate link
    """
    try:
        # Find conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id  # Verify ownership
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or you don't have permission"
            )

        # Disable sharing
        conversation.share_enabled = False
        # Optionally clear token for security
        conversation.share_token = None
        conversation.share_expires_at = None

        db.commit()

        logger.info(f"Sharing disabled for conversation {conversation_id} by user {user_id}")

        return {"message": "Sharing disabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling sharing: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable sharing: {str(e)}"
        )


# Story 3.7: Conversation Archiving
@router.patch("/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User ID (conversation owner)"),
    db: Session = Depends(get_db)
):
    """
    Archive a conversation.

    AC #1: Update status to 'archived', remove from main list
    """
    try:
        # Find conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id  # Verify ownership
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or you don't have permission"
            )

        # Archive conversation
        conversation.status = 'archived'
        conversation.updated_at = datetime.utcnow()

        db.commit()

        logger.info(f"Conversation {conversation_id} archived by user {user_id}")

        return {"message": "Conversation archived successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving conversation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive conversation: {str(e)}"
        )


@router.patch("/{conversation_id}/unarchive")
async def unarchive_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User ID (conversation owner)"),
    db: Session = Depends(get_db)
):
    """
    Unarchive a conversation.

    AC #2: Update status to 'active', add back to main list
    """
    try:
        # Find conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id  # Verify ownership
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or you don't have permission"
            )

        # Unarchive conversation
        conversation.status = 'active'
        conversation.updated_at = datetime.utcnow()

        db.commit()

        logger.info(f"Conversation {conversation_id} unarchived by user {user_id}")

        return {"message": "Conversation unarchived successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unarchiving conversation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unarchive conversation: {str(e)}"
        )


# Story 3.8: Conversation Deletion
@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User ID (conversation owner)"),
    db: Session = Depends(get_db)
):
    """
    Permanently delete a conversation and all its messages.

    AC #1: Hard delete with CASCADE (messages deleted automatically)
    AC #3: No undo - deletion is permanent
    """
    try:
        # Find conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id  # Verify ownership
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or you don't have permission"
            )

        # Delete conversation (CASCADE deletes all messages)
        db.delete(conversation)
        db.commit()

        logger.info(f"Conversation {conversation_id} deleted by user {user_id}")

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


# Story 3.9: Conversation Export
def sanitize_filename(filename: str) -> str:
    """Sanitize filename to be safe for file systems."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(). strip('.')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename or "conversation"


@router.get("/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User ID (conversation owner)"),
    format: str = Query("markdown", description="Export format: markdown"),
    db: Session = Depends(get_db)
):
    """
    Export a conversation as markdown file.

    Story 3.9 AC #3: Export as markdown with formatting, timestamps, and citations
    Note: PDF export deferred to future enhancement

    Args:
        conversation_id: Conversation ID to export
        user_id: User ID (for ownership verification)
        format: Export format (currently only "markdown" supported)

    Returns:
        Downloadable markdown file
    """
    try:
        # Verify format
        if format not in ["markdown", "md", "text"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {format}. Only 'markdown' is supported."
            )

        # Find conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id  # Verify ownership
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or you don't have permission"
            )

        # Get all messages ordered by creation time
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

        # Generate markdown content
        markdown_lines = []

        # Header
        markdown_lines.append(f"# {conversation.title or 'Untitled Conversation'}\n")
        markdown_lines.append(f"**Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        markdown_lines.append(f"**Last Updated:** {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        markdown_lines.append(f"**Messages:** {len(messages)}\n")
        markdown_lines.append("\n---\n\n")

        # Messages
        for i, message in enumerate(messages, 1):
            role_label = "**You:**" if message.role == "user" else "**AI Coach:**"
            timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')

            markdown_lines.append(f"## Message {i} - {role_label} ({timestamp})\n\n")
            markdown_lines.append(f"{message.content}\n\n")

            # Add citations if present (from assistant messages)
            if message.role == "assistant" and message.citations:
                markdown_lines.append("### Citations\n\n")
                try:
                    import json
                    citations = json.loads(message.citations) if isinstance(message.citations, str) else message.citations
                    for cite in citations:
                        title = cite.get('book_title', 'Unknown')
                        pages = cite.get('pages', 'N/A')
                        markdown_lines.append(f"- **{title}** (Pages: {pages})\n")
                except:
                    markdown_lines.append(f"- {message.citations}\n")
                markdown_lines.append("\n")

            markdown_lines.append("---\n\n")

        # Footer
        markdown_lines.append("\n---\n\n")
        markdown_lines.append("*Exported from PLC Coach - Powered by Solution Tree*\n")
        markdown_lines.append(f"*Export Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*\n")

        # Combine into single markdown string
        markdown_content = "".join(markdown_lines)

        # Create filename
        safe_title = sanitize_filename(conversation.title or "conversation")
        date_str = conversation.created_at.strftime('%Y%m%d')
        filename = f"{safe_title}_{date_str}.md"

        logger.info(f"Exporting conversation {conversation_id} as markdown for user {user_id}")

        # Return as downloadable file
        return Response(
            content=markdown_content.encode('utf-8'),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "text/markdown; charset=utf-8"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export conversation: {str(e)}"
        )
