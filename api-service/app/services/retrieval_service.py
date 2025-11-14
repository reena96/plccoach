"""
Story 2.6: Semantic Retrieval Service

Retrieves relevant content chunks based on user queries using pgvector similarity search.
"""

import logging
from typing import Dict, List, Optional
import json

from openai import OpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

from app.services.intent_router import IntentRouter

logger = logging.getLogger(__name__)


class RetrievalService:
    """Semantic retrieval using pgvector similarity search."""

    def __init__(self, database_url: str, api_key: Optional[str] = None, top_k: int = 10):
        """Initialize the retrieval service.

        Args:
            database_url: PostgreSQL connection string
            api_key: OpenAI API key for embeddings
            top_k: Number of chunks to retrieve initially (before deduplication)
        """
        self.engine = create_engine(database_url)
        self.openai_client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.intent_router = IntentRouter(api_key=api_key)
        self.top_k = top_k
        self.embedding_model = "text-embedding-3-large"

    def _embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query.

        Args:
            query: User query text

        Returns:
            Query embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                input=query,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise

    def _retrieve_similar_chunks(
        self,
        query_embedding: List[float],
        primary_domain: Optional[str] = None,
        secondary_domains: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Retrieve similar chunks from the database.

        Args:
            query_embedding: Query vector
            primary_domain: Primary domain to filter by
            secondary_domains: Secondary domains to include
            limit: Number of results to return

        Returns:
            List of similar chunks with metadata and scores
        """
        try:
            with self.engine.connect() as conn:
                # Build domain filter
                domain_filter = ""
                if primary_domain:
                    domains_to_search = [primary_domain]
                    if secondary_domains:
                        domains_to_search.extend(secondary_domains)

                    domain_list = ", ".join([f"'{d}'" for d in domains_to_search])
                    domain_filter = f"AND (metadata->>'primary_domain') IN ({domain_list})"

                query = text(f"""
                    SELECT
                        content,
                        metadata,
                        1 - (embedding <=> :query_embedding::vector) as similarity
                    FROM embeddings
                    WHERE 1=1 {domain_filter}
                    ORDER BY embedding <=> :query_embedding::vector
                    LIMIT :limit
                """)

                result = conn.execute(query, {
                    'query_embedding': query_embedding,
                    'limit': limit
                })

                chunks = []
                for row in result:
                    chunks.append({
                        'content': row[0],
                        'metadata': row[1],
                        'similarity': float(row[2])
                    })

                return chunks

        except Exception as e:
            logger.error(f"Retrieval query failed: {e}")
            raise

    def _deduplicate_chunks(self, chunks: List[Dict], final_k: int = 7) -> List[Dict]:
        """Deduplicate overlapping chunks based on page ranges.

        Args:
            chunks: List of retrieved chunks
            final_k: Final number of chunks to return

        Returns:
            Deduplicated list of chunks
        """
        if not chunks:
            return []

        deduplicated = []
        seen_ranges = set()

        for chunk in chunks:
            metadata = chunk['metadata']
            page_start = metadata.get('page_start')
            page_end = metadata.get('page_end')
            book_id = metadata.get('book_id')

            # Create a unique key for this page range
            range_key = (book_id, page_start, page_end)

            # Skip if we've already seen this exact range
            if range_key in seen_ranges:
                continue

            # Check for overlapping ranges
            has_overlap = False
            for seen_book, seen_start, seen_end in seen_ranges:
                if seen_book == book_id:
                    # Check if ranges overlap
                    if (page_start <= seen_end and page_end >= seen_start):
                        has_overlap = True
                        break

            if not has_overlap:
                deduplicated.append(chunk)
                seen_ranges.add(range_key)

            # Stop when we have enough
            if len(deduplicated) >= final_k:
                break

        return deduplicated

    def retrieve(self, query: str, final_k: int = 7) -> Dict:
        """Retrieve relevant content chunks for a user query.

        This is the main entry point for retrieval:
        1. Classify query into domains (Story 2.5)
        2. Embed the query
        3. Perform vector similarity search with domain filtering
        4. Deduplicate overlapping chunks
        5. Return top-k most relevant chunks

        Args:
            query: User query text
            final_k: Number of final chunks to return (after deduplication)

        Returns:
            Dictionary with retrieved chunks and metadata
        """
        logger.info(f"Retrieving chunks for query: {query[:100]}...")

        try:
            # Step 1: Classify query into domains
            classification = self.intent_router.classify(query)
            primary_domain = classification.get('primary_domain')
            secondary_domains = classification.get('secondary_domains', [])

            logger.info(f"Classified as primary={primary_domain}, secondary={secondary_domains}")

            # Step 2: Embed the query
            query_embedding = self._embed_query(query)

            # Step 3: Retrieve similar chunks (get more than final_k for deduplication)
            initial_k = self.top_k
            chunks = self._retrieve_similar_chunks(
                query_embedding=query_embedding,
                primary_domain=primary_domain,
                secondary_domains=secondary_domains,
                limit=initial_k
            )

            logger.info(f"Retrieved {len(chunks)} initial chunks")

            # Step 4: Deduplicate
            deduplicated_chunks = self._deduplicate_chunks(chunks, final_k=final_k)

            logger.info(f"After deduplication: {len(deduplicated_chunks)} chunks")

            # Step 5: Prepare result
            return {
                'query': query,
                'classification': classification,
                'chunks': deduplicated_chunks,
                'total_retrieved': len(chunks),
                'total_after_dedup': len(deduplicated_chunks)
            }

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return {
                'query': query,
                'classification': {'primary_domain': 'school_culture', 'secondary_domains': []},
                'chunks': [],
                'total_retrieved': 0,
                'total_after_dedup': 0,
                'error': str(e)
            }

    def test_retrieval(self, test_queries: List[str]) -> List[Dict]:
        """Test retrieval with a list of queries.

        Args:
            test_queries: List of test queries

        Returns:
            List of retrieval results
        """
        results = []
        for query in test_queries:
            result = self.retrieve(query)
            results.append({
                'query': query,
                'primary_domain': result['classification']['primary_domain'],
                'num_chunks': len(result['chunks']),
                'avg_similarity': sum(c['similarity'] for c in result['chunks']) / len(result['chunks']) if result['chunks'] else 0
            })
        return results
