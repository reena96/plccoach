"""
Story 2.8: Chat API Endpoints
Story 3.1: Multi-Turn Conversation Context Management
Story 3.2: Conversation Persistence & Auto-Save

REST API endpoints for AI coach interactions with conversation history support
and automatic message persistence.
"""

import logging
import time
from typing import Optional
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.services.retrieval_service import RetrievalService
from app.services.generation_service import GenerationService
from app.services.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from db_config import get_database_url
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/coach", tags=["coach"])


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for coach query."""
    query: str = Field(..., min_length=1, max_length=1000, description="User's question")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")


class Citation(BaseModel):
    """Citation model."""
    book_title: str
    authors: str
    chapter: int
    chapter_title: str
    pages: str


class QueryResponse(BaseModel):
    """Response model for coach query."""
    response: str
    citations: list[Citation]
    domains: list[str]
    response_time_ms: int
    token_usage: int
    cost_usd: float
    conversation_id: Optional[str] = Field(None, description="Conversation ID for this exchange")


# Initialize services (singleton pattern)
_retrieval_service = None
_generation_service = None


def get_retrieval_service() -> RetrievalService:
    """Get or create retrieval service instance."""
    global _retrieval_service
    if _retrieval_service is None:
        database_url = get_database_url()
        _retrieval_service = RetrievalService(database_url=database_url)
    return _retrieval_service


def get_generation_service() -> GenerationService:
    """Get or create generation service instance."""
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query_coach(
    request: QueryRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    generation_service: GenerationService = Depends(get_generation_service),
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(None, description="User ID for conversation context (TODO: replace with proper auth)")
):
    """Query the AI coach with a question.

    This endpoint orchestrates the full RAG pipeline:
    1. Retrieves relevant content chunks (Story 2.6)
    2. Generates a response with citations (Story 2.7)
    3. Includes conversation history if conversation_id provided (Story 3.1)

    Args:
        request: Query request with user question and optional conversation_id
        retrieval_service: Injected retrieval service
        generation_service: Injected generation service
        db: Database session
        x_user_id: User ID from header (TODO: replace with proper authentication)

    Returns:
        QueryResponse with answer, citations, and metadata

    Raises:
        HTTPException: On various error conditions
    """
    start_time = time.time()

    try:
        logger.info(f"Received query: {request.query[:100]}...")
        if request.conversation_id:
            logger.info(f"Conversation ID provided: {request.conversation_id}")

        # Step 0: Create conversation if needed (Story 3.2)
        conversation_id = request.conversation_id
        if not conversation_id and x_user_id:
            try:
                # Create new conversation
                # Generate title from first 50 chars of query
                title = request.query[:50]
                if len(request.query) > 50:
                    title += "..."

                from uuid import UUID
                conversation = Conversation(
                    id=uuid4(),
                    user_id=UUID(x_user_id),  # Convert string to UUID
                    title=title,
                    status='active'
                )
                db.add(conversation)
                db.flush()  # Get ID without committing transaction yet
                conversation_id = str(conversation.id)
                logger.info(f"Created new conversation: {conversation_id}")
            except SQLAlchemyError as e:
                logger.error(f"Failed to create conversation: {e}")
                db.rollback()
                # Continue without persistence for now
                conversation_id = None

        # Step 0.5: Save user message (Story 3.2)
        user_message_id = None
        if conversation_id and x_user_id:
            try:
                from uuid import UUID
                user_message = Message(
                    id=uuid4(),
                    conversation_id=UUID(conversation_id),  # Convert string to UUID
                    role='user',
                    content=request.query
                )
                db.add(user_message)
                db.flush()  # Save but don't commit yet
                user_message_id = str(user_message.id)
                logger.info(f"Saved user message: {user_message_id}")
            except SQLAlchemyError as e:
                logger.error(f"Failed to save user message: {e}")
                db.rollback()

        # Step 1: Retrieve relevant chunks
        retrieval_result = retrieval_service.retrieve(request.query, final_k=7)

        if 'error' in retrieval_result:
            logger.error(f"Retrieval failed: {retrieval_result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve relevant content"
            )

        chunks = retrieval_result['chunks']
        classification = retrieval_result['classification']

        # Step 1.5: Load conversation context if conversation_id provided
        conversation_history = None
        if request.conversation_id and x_user_id:
            try:
                conversation_history = generation_service.get_conversation_context(
                    conversation_id=request.conversation_id,
                    user_id=x_user_id,
                    db_session=db
                )
                logger.info(f"Loaded conversation context: {len(conversation_history)} chars")
            except ValueError as e:
                # Conversation not found or unauthorized
                logger.warning(f"Conversation context load failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            except Exception as e:
                # Non-fatal: continue without conversation context
                logger.error(f"Failed to load conversation context: {e}")
                conversation_history = None

        # Step 2: Generate response
        generation_result = generation_service.generate(
            query=request.query,
            retrieved_chunks=chunks,
            conversation_history=conversation_history
        )

        if 'error' in generation_result:
            logger.error(f"Generation failed: {generation_result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response"
            )

        # Step 3: Save assistant message (Story 3.2)
        if conversation_id and x_user_id:
            try:
                from uuid import UUID
                assistant_message = Message(
                    id=uuid4(),
                    conversation_id=UUID(conversation_id),
                    role='assistant',
                    content=generation_result['response'],
                    citations=generation_result['citations'],  # Store citations as JSONB
                    input_tokens=generation_result.get('token_usage', 0),
                    cost_usd=generation_result.get('cost_usd', 0.0)
                )
                db.add(assistant_message)

                # Update conversation timestamp (onupdate will handle this automatically)
                # Commit the transaction (conversation + user message + assistant message)
                db.commit()
                logger.info(f"Saved assistant message and committed transaction")
            except SQLAlchemyError as e:
                logger.error(f"Failed to save assistant message: {e}")
                db.rollback()
                # Don't fail the request - response was generated successfully

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Prepare domains list
        domains = [classification['primary_domain']]
        if classification.get('secondary_domains'):
            domains.extend(classification['secondary_domains'])

        # Build response
        return QueryResponse(
            response=generation_result['response'],
            citations=[Citation(**c) for c in generation_result['citations']],
            domains=domains,
            response_time_ms=response_time_ms,
            token_usage=generation_result['token_usage'],
            cost_usd=generation_result['cost_usd'],
            conversation_id=conversation_id  # Return conversation_id (Story 3.2)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in query_coach: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for coach service."""
    return {
        "status": "healthy",
        "service": "coach",
        "dependencies": {
            "database": "ok",
            "openai": "ok"
        }
    }
