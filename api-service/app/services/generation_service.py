"""
Story 2.7: Response Generation with Citations

Generates AI responses with transparent citations using GPT-4o.
"""

import logging
from typing import Dict, List, Optional
import re

from openai import OpenAI
import os

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
        # Pattern: [Book Title] by [Authors], Chapter [X]: [Title], pp. [XX-XX]
        citation_pattern = r'\[([^\]]+)\]\s+by\s+([^,]+),\s+Chapter\s+(\d+):\s+([^,]+),\s+pp\.\s+(\d+-\d+)'

        matches = re.finditer(citation_pattern, response_text)

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

    def generate(self, query: str, retrieved_chunks: List[Dict]) -> Dict:
        """Generate a response with citations.

        Args:
            query: User query
            retrieved_chunks: Retrieved chunks from Story 2.6

        Returns:
            Dictionary with response, citations, and metadata
        """
        logger.info(f"Generating response for query: {query[:100]}...")

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

            # Build prompt
            user_prompt = f"""Based on the provided sources, answer this question from a PLC educator:

Question: {query}

Sources:
{context}

Remember to:
1. Answer directly and concisely (2-3 paragraphs)
2. Include key takeaways as bullet points
3. Add a "📚 Sources:" section with properly formatted citations
4. Only cite sources that were actually provided above"""

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
