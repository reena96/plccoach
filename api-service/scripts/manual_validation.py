#!/usr/bin/env python3
"""
Manual Validation Script for Epic 2 - Core AI Coach

This script creates sample data and validates all Epic 2 components:
1. Intent Classification (GPT-4o)
2. Semantic Retrieval (pgvector)
3. Response Generation (GPT-4o with citations)
4. Full API endpoint

Usage:
    python manual_validation.py --setup    # Create sample data
    python manual_validation.py --test     # Run validation tests
    python manual_validation.py --cleanup  # Remove sample data
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Sample PLC content chunks (realistic excerpts)
SAMPLE_CHUNKS = [
    {
        "content": """The four critical questions that drive the work of a Professional Learning Community are:
1. What do we want our students to know and be able to do?
2. How will we know if they have learned it?
3. What will we do if they haven't learned it?
4. What will we do if they already know it?

These questions guide collaborative teams in focusing on student learning outcomes and creating systems of support.""",
        "metadata": {
            "book_id": "sample-book-1",
            "book_title": "Learning by Doing: A Handbook for Professional Learning Communities at Work",
            "authors": ["Richard DuFour", "Rebecca DuFour", "Robert Eaker", "Thomas Many"],
            "chapter_number": 1,
            "chapter_title": "The Case for Professional Learning Communities",
            "page_start": 25,
            "page_end": 26,
            "primary_domain": "school_culture",
            "secondary_domains": ["collaboration", "assessment"]
        }
    },
    {
        "content": """Common formative assessments are team-developed, collaboratively scored assessments used throughout a unit to monitor student learning. Unlike summative assessments that evaluate learning at the end, formative assessments provide ongoing feedback to teachers and students. They help teams identify students who need additional support and adjust instruction accordingly. Effective common formative assessments are aligned to agreed-upon learning targets and essential standards.""",
        "metadata": {
            "book_id": "sample-book-2",
            "book_title": "Collaborative Common Assessments",
            "authors": ["Cassandra Erkens"],
            "chapter_number": 3,
            "chapter_title": "Creating Quality Assessments",
            "page_start": 67,
            "page_end": 68,
            "primary_domain": "assessment",
            "secondary_domains": ["collaboration", "curriculum"]
        }
    },
    {
        "content": """Effective collaborative teams establish norms and protocols that guide their interactions. These norms should address how team members will communicate, make decisions, handle conflict, and hold each other accountable. Teams that establish clear norms early create a foundation of trust and mutual respect. The norms should be revisited regularly to ensure they continue to serve the team's purpose.""",
        "metadata": {
            "book_id": "sample-book-3",
            "book_title": "Collaborative Teams That Transform Schools",
            "authors": ["Cassandra Erkens", "Chris Jakicic", "Lillie G. Jessie"],
            "chapter_number": 2,
            "chapter_title": "Building Strong Teams",
            "page_start": 45,
            "page_end": 46,
            "primary_domain": "collaboration",
            "secondary_domains": ["school_culture"]
        }
    },
    {
        "content": """Response to Intervention (RTI) is a systematic approach to providing tiered support for students. Tier 1 represents core instruction for all students. Tier 2 provides targeted interventions for students who need additional support. Tier 3 offers intensive interventions for students who continue to struggle. The key to effective RTI is using data to identify students quickly and providing timely, directive interventions based on their specific needs.""",
        "metadata": {
            "book_id": "sample-book-4",
            "book_title": "Simplifying Response to Intervention",
            "authors": ["Austin Buffum", "Mike Mattos", "Chris Weber"],
            "chapter_number": 4,
            "chapter_title": "The Three Tiers of Support",
            "page_start": 89,
            "page_end": 91,
            "primary_domain": "data_analysis",
            "secondary_domains": ["student_learning"]
        }
    },
    {
        "content": """Guaranteed and viable curriculum means that all students have access to the same essential learning standards regardless of their teacher. Teams collaborate to identify the most critical standards - those that are essential for student success. They ensure that the curriculum is viable, meaning it can be taught in the time available. This requires making difficult decisions about what to prioritize and what to eliminate.""",
        "metadata": {
            "book_id": "sample-book-5",
            "book_title": "A Guaranteed and Viable Curriculum",
            "authors": ["Robert J. Marzano"],
            "chapter_number": 1,
            "chapter_title": "The Importance of a Guaranteed Curriculum",
            "page_start": 12,
            "page_end": 14,
            "primary_domain": "curriculum",
            "secondary_domains": ["collaboration"]
        }
    }
]


def get_database_url():
    """Get database URL from environment or use test database."""
    # Use localhost:5433 for local testing (not Docker's "db" hostname)
    default_url = "postgresql+psycopg2://postgres:postgres@localhost:5433/plccoach"
    env_url = os.getenv("DATABASE_URL")

    # If DATABASE_URL points to Docker's "db" hostname, use localhost instead
    if env_url and "@db:" in env_url:
        return default_url
    return env_url or default_url


def generate_mock_embedding(text: str, dimension: int = 3072) -> list:
    """Generate a deterministic mock embedding based on text content.

    In a real scenario, this would call OpenAI's API. For testing,
    we create a pseudo-random vector based on the text hash.
    """
    # Use text hash as seed for reproducibility
    seed = hash(text) % (2**32)
    np.random.seed(seed)

    # Generate random vector and normalize it
    vector = np.random.randn(dimension)
    vector = vector / np.linalg.norm(vector)

    return vector.tolist()


def setup_sample_data():
    """Insert sample chunks with embeddings into the database."""
    print("=" * 70)
    print("SETTING UP SAMPLE DATA FOR MANUAL VALIDATION")
    print("=" * 70)

    database_url = get_database_url()
    engine = create_engine(database_url)

    print(f"\n📊 Database: {database_url}")
    print(f"📦 Inserting {len(SAMPLE_CHUNKS)} sample chunks...")

    with engine.connect() as conn:
        # Clear existing sample data
        result = conn.execute(text("""
            DELETE FROM embeddings
            WHERE metadata->>'book_id' LIKE 'sample-book-%'
        """))
        conn.commit()
        print(f"   Cleared {result.rowcount} existing sample records")

        # Insert sample chunks
        for i, chunk in enumerate(SAMPLE_CHUNKS, 1):
            # Generate mock embedding
            embedding = generate_mock_embedding(chunk['content'])

            # Insert into database
            conn.execute(text("""
                INSERT INTO embeddings (content, embedding, metadata)
                VALUES (:content, :embedding, :metadata)
            """), {
                'content': chunk['content'],
                'embedding': embedding,
                'metadata': json.dumps(chunk['metadata'])
            })

            print(f"   ✅ Inserted chunk {i}: {chunk['metadata']['book_title'][:50]}...")

        conn.commit()

    print(f"\n✅ Sample data setup complete!")
    print(f"   Total chunks: {len(SAMPLE_CHUNKS)}")
    print(f"   Domains: assessment, collaboration, curriculum, data_analysis, school_culture")
    print("\n" + "=" * 70)


def test_intent_classification():
    """Test intent classification with sample queries."""
    print("\n" + "=" * 70)
    print("TEST 1: INTENT CLASSIFICATION (GPT-4o)")
    print("=" * 70)

    from app.services.intent_router import IntentRouter

    router = IntentRouter()

    test_queries = [
        "What are the four critical questions of a PLC?",
        "How do we create common formative assessments?",
        "What are effective team norms?",
        "How does RTI work?"
    ]

    for query in test_queries:
        print(f"\n📝 Query: \"{query}\"")
        result = router.classify(query)
        print(f"   ✅ Primary Domain: {result['primary_domain']}")
        print(f"   📊 Confidence: {result['confidence']:.2f}")
        print(f"   🔍 Secondary Domains: {result.get('secondary_domains', [])}")
        print(f"   ⚠️  Needs Clarification: {result.get('needs_clarification', False)}")

    print("\n" + "=" * 70)


def test_semantic_retrieval():
    """Test semantic retrieval from database."""
    print("\n" + "=" * 70)
    print("TEST 2: SEMANTIC RETRIEVAL (pgvector)")
    print("=" * 70)

    from app.services.retrieval_service import RetrievalService

    database_url = get_database_url()
    retrieval_service = RetrievalService(database_url=database_url)

    test_query = "What are the four critical questions?"

    print(f"\n📝 Query: \"{test_query}\"")
    print(f"🔍 Searching for top 3 relevant chunks...")

    result = retrieval_service.retrieve(
        query=test_query,
        final_k=3
    )

    chunks = result.get('chunks', [])
    print(f"\n✅ Found {len(chunks)} results (from {result.get('total_retrieved', 0)} initial):")
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk['metadata']
        print(f"\n   Result {i}:")
        print(f"   📚 Book: {metadata.get('book_title', 'Unknown')}")
        print(f"   👥 Authors: {', '.join(metadata.get('authors', ['Unknown']))}")
        print(f"   📖 Chapter {metadata.get('chapter_number', '?')}: {metadata.get('chapter_title', 'Unknown')}")
        print(f"   📄 Pages: {metadata.get('page_start', '?')}-{metadata.get('page_end', '?')}")
        print(f"   🎯 Domain: {metadata.get('primary_domain', 'unknown')}")
        print(f"   📏 Similarity: {chunk.get('similarity', 0):.4f}")
        print(f"   📝 Preview: {chunk['content'][:100]}...")

    print("\n" + "=" * 70)


def test_response_generation():
    """Test response generation with retrieved chunks."""
    print("\n" + "=" * 70)
    print("TEST 3: RESPONSE GENERATION (GPT-4o)")
    print("=" * 70)

    from app.services.retrieval_service import RetrievalService
    from app.services.generation_service import GenerationService

    database_url = get_database_url()
    retrieval_service = RetrievalService(database_url=database_url)
    generation_service = GenerationService()

    test_query = "What are the four critical questions of a PLC?"

    print(f"\n📝 Query: \"{test_query}\"")
    print(f"🔍 Retrieving relevant content...")

    # Retrieve relevant chunks
    result = retrieval_service.retrieve(query=test_query, final_k=3)
    chunks = result.get('chunks', [])
    print(f"   Found {len(chunks)} relevant chunks")

    print(f"\n🤖 Generating response with GPT-4o...")

    # Generate response
    response = generation_service.generate_response(
        query=test_query,
        retrieved_chunks=chunks
    )

    print(f"\n✅ Response Generated:")
    print(f"\n{response['response']}")
    print(f"\n📚 Citations ({len(response['citations'])}):")
    for i, citation in enumerate(response['citations'], 1):
        print(f"   [{i}] {citation['book_title']} by {citation['authors']}")
        print(f"       Chapter {citation['chapter']}: {citation['chapter_title']}, pp. {citation['pages']}")

    print(f"\n📊 Metadata:")
    print(f"   Tokens Used: {response['token_usage']}")
    print(f"   Cost: ${response['cost_usd']:.4f}")

    print("\n" + "=" * 70)


def test_full_api_endpoint():
    """Test the complete API endpoint."""
    print("\n" + "=" * 70)
    print("TEST 4: FULL API ENDPOINT (/api/coach/query)")
    print("=" * 70)

    import requests

    test_queries = [
        "What are the four critical questions of a PLC?",
        "How do we create effective common formative assessments?",
        "What are good team norms?"
    ]

    api_url = "http://localhost:8000/api/coach/query"

    for query in test_queries:
        print(f"\n📝 Query: \"{query}\"")
        print(f"🌐 POST {api_url}")

        try:
            response = requests.post(
                api_url,
                json={"query": query},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {response.status_code}")
                print(f"   ⏱️  Response Time: {data['response_time_ms']}ms")
                print(f"   🎯 Domains: {', '.join(data['domains'])}")
                print(f"   📚 Citations: {len(data['citations'])}")
                print(f"   💰 Cost: ${data['cost_usd']:.4f}")
                print(f"\n   Response Preview:")
                preview = data['response'][:200]
                print(f"   {preview}...")
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   Error: {response.text}")

        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error: API server not running")
            print(f"   💡 Start with: docker-compose up -d")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "=" * 70)


def cleanup_sample_data():
    """Remove sample data from database."""
    print("\n" + "=" * 70)
    print("CLEANING UP SAMPLE DATA")
    print("=" * 70)

    database_url = get_database_url()
    engine = create_engine(database_url)

    with engine.connect() as conn:
        result = conn.execute(text("""
            DELETE FROM embeddings
            WHERE metadata->>'book_id' LIKE 'sample-book-%'
        """))
        conn.commit()
        print(f"\n✅ Removed {result.rowcount} sample records")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Manual validation for Epic 2")
    parser.add_argument('--setup', action='store_true', help='Setup sample data')
    parser.add_argument('--test', action='store_true', help='Run validation tests')
    parser.add_argument('--cleanup', action='store_true', help='Remove sample data')
    parser.add_argument('--all', action='store_true', help='Setup, test, and cleanup')

    args = parser.parse_args()

    if args.all or (not args.setup and not args.test and not args.cleanup):
        # Run everything
        setup_sample_data()
        test_intent_classification()
        test_semantic_retrieval()
        test_response_generation()
        test_full_api_endpoint()
        print("\n\n💡 TIP: Sample data is still in database. Run with --cleanup to remove it.")
    else:
        if args.setup:
            setup_sample_data()
        if args.test:
            test_intent_classification()
            test_semantic_retrieval()
            test_response_generation()
            test_full_api_endpoint()
        if args.cleanup:
            cleanup_sample_data()


if __name__ == "__main__":
    main()
