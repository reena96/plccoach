"""
Story 2.8: Chat API Endpoints

REST API endpoints for AI coach interactions.
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from app.services.retrieval_service import RetrievalService
from app.services.generation_service import GenerationService
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
    generation_service: GenerationService = Depends(get_generation_service)
):
    """Query the AI coach with a question.

    This endpoint orchestrates the full RAG pipeline:
    1. Retrieves relevant content chunks (Story 2.6)
    2. Generates a response with citations (Story 2.7)

    Args:
        request: Query request with user question
        retrieval_service: Injected retrieval service
        generation_service: Injected generation service

    Returns:
        QueryResponse with answer, citations, and metadata

    Raises:
        HTTPException: On various error conditions
    """
    start_time = time.time()

    try:
        logger.info(f"Received query: {request.query[:100]}...")

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

        # Step 2: Generate response
        generation_result = generation_service.generate(
            query=request.query,
            retrieved_chunks=chunks
        )

        if 'error' in generation_result:
            logger.error(f"Generation failed: {generation_result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response"
            )

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
            cost_usd=generation_result['cost_usd']
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
