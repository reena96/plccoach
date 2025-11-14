"""
Story 2.7: Response Generation with Citations
Story 3.1: Multi-Turn Conversation Context Management

Generates AI responses with transparent citations using GPT-4o.
Supports conversation history for multi-turn context-aware responses.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID
import re

from openai import OpenAI
from sqlalchemy.orm import Session
import os

from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger(__name__)


class GenerationService:
    """Generates AI coach responses with citations."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the generation service.

        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
        self.temperature = 0.3
        self.max_tokens = 1000

    def _get_system_prompt(self) -> str:
        """Get the system prompt for response generation.

        Returns:
            System prompt string
        """
        return """You are an expert PLC (Professional Learning Community) coach based on Solution Tree's research and frameworks.

Your role:
- Provide accurate, practical guidance on PLC practices
- Ground ALL responses in the provided source material
- Include specific citations to books, chapters, and pages
- Be concise and actionable (2-3 paragraphs max)
- Use educator-friendly language

Citation rules:
- ALWAYS cite your sources explicitly
- Format: [Book Title] by [Authors], Chapter [X]: [Chapter Title], pp. [XX-XX]
- Include direct quotes or key concepts from the sources
- If the provided sources don't contain relevant information, say so honestly
- Never make up citations or reference materials not provided

Response structure:
1. Direct answer (2-3 paragraphs)
2. Key takeaways (2-4 bullet points)
3. Citations section with 📚 Sources header

Tone: Professional, supportive, evidence-based"""

    def _format_context(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks into context for the LLM.

        Args:
            chunks: Retrieved chunks from Story 2.6

        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant source material was found for this query."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk['metadata']
            content = chunk['content']

            # Format chunk with metadata
            chunk_text = f"""
Source {i}:
Book: {metadata.get('book_title', 'Unknown')}
Authors: {', '.join(metadata.get('authors', ['Unknown']))}
Chapter {metadata.get('chapter_number', '?')}: {metadata.get('chapter_title', 'Unknown')}
Pages: {metadata.get('page_start', '?')}-{metadata.get('page_end', '?')}

Content:
{content}

---
"""
            context_parts.append(chunk_text)

        return "\n".join(context_parts)

    def get_conversation_context(
        self,
        conversation_id: str,
        user_id: str,
        db_session: Session
    ) -> str:
        """Retrieve and format conversation history for context.

        Loads the last 10 messages from the conversation and formats them
        as User/Assistant dialog for inclusion in the LLM prompt.

        Args:
            conversation_id: UUID of the conversation
            user_id: UUID of the user (for authorization)
            db_session: SQLAlchemy database session

        Returns:
            Formatted conversation history string, or empty string if no messages

        Raises:
            ValueError: If conversation doesn't exist or doesn't belong to user
        """
        try:
            # Convert string IDs to UUID
            conv_uuid = UUID(conversation_id)
            user_uuid = UUID(user_id)

            # Validate conversation exists and belongs to user
            conversation = db_session.query(Conversation).filter(
                Conversation.id == conv_uuid,
                Conversation.user_id == user_uuid
            ).first()

            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found or access denied")

            # Load last 10 messages, ordered by created_at DESC
            messages = db_session.query(Message).filter(
                Message.conversation_id == conv_uuid
            ).order_by(Message.created_at.desc()).limit(10).all()

            if not messages:
                # Empty conversation - no context to provide
                return ""

            # Reverse to get chronological order (oldest to newest)
            messages = list(reversed(messages))

            # Format as User/Assistant dialog
            context_lines = []
            for msg in messages:
                if msg.role == "user":
                    context_lines.append(f"User: {msg.content}")
                elif msg.role == "assistant":
                    context_lines.append(f"Assistant: {msg.content}")
                # Skip 'system' role messages - not part of conversation flow

            conversation_history = "\n\n".join(context_lines)

            logger.info(f"Loaded {len(messages)} messages for conversation {conversation_id}")

            return conversation_history

        except ValueError as e:
            # Re-raise authorization/not found errors
            raise
        except Exception as e:
            logger.error(f"Failed to load conversation context: {e}")
            raise ValueError(f"Failed to load conversation context: {str(e)}")

    def _extract_citations(self, response_text: str, chunks: List[Dict]) -> List[Dict]:
        """Extract and validate citations from the response.

        Args:
            response_text: Generated response text
            chunks: Source chunks used for generation

        Returns:
            List of validated citations
        """
        citations = []

        # Look for citation patterns in the response
        # Try two patterns: with asterisks (*Book*) and without
        pattern_with_asterisks = r'[-•]\s*\*(.+)\*\s+by\s+(.+?),\s+Chapter\s+(\d+):\s+([^,]+),\s+pp\.\s+(\d+-\d+)'
        pattern_without_asterisks = r'[-•]\s*(.+)\s+by\s+([A-Z][\w\s,\.]+),\s+Chapter\s+(\d+):\s+([^,]+),\s+pp\.\s+(\d+-\d+)'

        # Try both patterns and combine matches
        matches = list(re.finditer(pattern_with_asterisks, response_text))
        if not matches:
            matches = list(re.finditer(pattern_without_asterisks, response_text))

        for match in matches:
            book_title = match.group(1)
            authors = match.group(2)
            chapter_num = int(match.group(3))
            chapter_title = match.group(4)
            pages = match.group(5)

            # Validate against source chunks
            is_valid = False
            for chunk in chunks:
                metadata = chunk['metadata']
                if (metadata.get('book_title') == book_title and
                    metadata.get('chapter_number') == chapter_num):
                    is_valid = True
                    break

            if is_valid:
                citations.append({
                    'book_title': book_title,
                    'authors': authors,
                    'chapter': chapter_num,
                    'chapter_title': chapter_title,
                    'pages': pages,
                    'is_valid': True
                })
            else:
                logger.warning(f"Invalid citation detected: {book_title}, Chapter {chapter_num}")

        return citations

    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        conversation_history: Optional[str] = None
    ) -> Dict:
        """Generate a response with citations.

        Args:
            query: User query
            retrieved_chunks: Retrieved chunks from Story 2.6
            conversation_history: Optional formatted conversation history for context

        Returns:
            Dictionary with response, citations, and metadata
        """
        logger.info(f"Generating response for query: {query[:100]}...")
        if conversation_history:
            logger.info(f"Including conversation history ({len(conversation_history)} chars)")

        try:
            # Format context from retrieved chunks
            context = self._format_context(retrieved_chunks)

            # Check if we have any sources
            if not retrieved_chunks:
                return {
                    'query': query,
                    'response': "I don't have specific information on this in the Solution Tree books I have access to. Could you rephrase your question or ask about a different aspect of Professional Learning Communities?",
                    'citations': [],
                    'token_usage': 0,
                    'cost_usd': 0.0
                }

            # Build prompt with optional conversation history
            prompt_parts = []

            # Add conversation history if provided
            if conversation_history:
                prompt_parts.append("Previous conversation:\n" + conversation_history)
                prompt_parts.append("\n---\n")

            # Add main query and sources
            prompt_parts.append(f"""Based on the provided sources, answer this question from a PLC educator:

Question: {query}

Sources:
{context}

Remember to:
1. Answer directly and concisely (2-3 paragraphs)
2. Include key takeaways as bullet points
3. Add a "📚 Sources:" section with properly formatted citations
4. Only cite sources that were actually provided above""")

            if conversation_history:
                prompt_parts.append("\n\nNote: Consider the previous conversation context when formulating your response.")

            user_prompt = "".join(prompt_parts)

            # Call GPT-4o
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ]
            )

            response_text = response.choices[0].message.content
            token_usage = response.usage.total_tokens

            # Estimate cost (GPT-4o pricing)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            input_cost = (input_tokens / 1_000_000) * 5.00  # $5/1M input tokens
            output_cost = (output_tokens / 1_000_000) * 15.00  # $15/1M output tokens
            total_cost = input_cost + output_cost

            # Extract and validate citations
            citations = self._extract_citations(response_text, retrieved_chunks)

            logger.info(f"Generated response with {len(citations)} citations, {token_usage} tokens, ${total_cost:.4f}")

            return {
                'query': query,
                'response': response_text,
                'citations': citations,
                'token_usage': token_usage,
                'cost_usd': total_cost,
                'num_sources_used': len(retrieved_chunks)
            }

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {
                'query': query,
                'response': "I encountered an error generating a response. Please try again.",
                'citations': [],
                'token_usage': 0,
                'cost_usd': 0.0,
                'error': str(e)
            }
