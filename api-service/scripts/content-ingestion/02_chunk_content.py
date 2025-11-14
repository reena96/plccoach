#!/usr/bin/env python3
"""
Story 2.2: Content Chunking with Metadata Tagging

Splits processed book content into semantic chunks with rich metadata for embedding.

Usage:
    python 02_chunk_content.py --bucket plccoach-content --input-prefix processed/ --output-prefix chunked/
"""

import argparse
import json
import logging
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import boto3
import tiktoken
from botocore.exceptions import ClientError
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('content_chunking.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ContentChunker:
    """Chunks book content into semantic pieces with metadata."""

    def __init__(self,
                 min_tokens: int = 500,
                 max_tokens: int = 1000,
                 overlap_tokens: int = 100,
                 encoding_name: str = "cl100k_base"):
        """Initialize the chunker.

        Args:
            min_tokens: Minimum tokens per chunk
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap between chunks
            encoding_name: Tiktoken encoding name (cl100k_base for GPT-4/3.5)
        """
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.encoder = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.encoder.encode(text))

    def find_sentence_boundaries(self, text: str) -> List[int]:
        """Find sentence boundaries in text.

        Args:
            text: Text to analyze

        Returns:
            List of character positions where sentences end
        """
        # Simple sentence boundary detection
        # Looks for periods, question marks, exclamation points followed by space/newline
        boundaries = []
        patterns = [
            r'\. ',
            r'\.\n',
            r'\? ',
            r'\?\n',
            r'! ',
            r'!\n',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                boundaries.append(match.end())

        return sorted(set(boundaries))

    def find_paragraph_boundaries(self, text: str) -> List[int]:
        """Find paragraph boundaries in text.

        Args:
            text: Text to analyze

        Returns:
            List of character positions where paragraphs end
        """
        boundaries = []

        # Look for double newlines
        for match in re.finditer(r'\n\n+', text):
            boundaries.append(match.end())

        # Look for headings (markdown style)
        for match in re.finditer(r'\n#+ .+\n', text):
            boundaries.append(match.start())

        return sorted(set(boundaries))

    def chunk_text(self, text: str, preserve_boundaries: bool = True) -> List[str]:
        """Split text into chunks respecting semantic boundaries.

        Args:
            text: Text to chunk
            preserve_boundaries: Whether to preserve sentence/paragraph boundaries

        Returns:
            List of text chunks
        """
        total_tokens = self.count_tokens(text)

        # If text is smaller than min_tokens, return as single chunk
        if total_tokens < self.min_tokens:
            return [text]

        chunks = []
        start_pos = 0

        while start_pos < len(text):
            # Calculate target end position
            # Start with max_tokens worth of text
            current_text = text[start_pos:]
            current_tokens = self.count_tokens(current_text)

            if current_tokens <= self.max_tokens:
                # Remaining text fits in one chunk
                chunks.append(current_text)
                break

            # Find a good boundary within max_tokens
            end_pos = self._find_chunk_boundary(
                text,
                start_pos,
                preserve_boundaries
            )

            chunk = text[start_pos:end_pos].strip()
            chunks.append(chunk)

            # Move start position with overlap
            overlap_start = self._calculate_overlap_position(chunk, end_pos)
            start_pos = max(overlap_start, end_pos - (len(chunk) // 4))  # At least 25% overlap

        return chunks

    def _find_chunk_boundary(self, text: str, start_pos: int, preserve_boundaries: bool) -> int:
        """Find the best position to end a chunk.

        Args:
            text: Full text
            start_pos: Starting position
            preserve_boundaries: Whether to preserve semantic boundaries

        Returns:
            End position for chunk
        """
        # Start with max_tokens worth of text
        test_chunk = text[start_pos:]
        end_pos = start_pos + len(test_chunk)

        # Binary search for the right size
        min_pos = start_pos + 1
        max_pos = len(text)

        while min_pos < max_pos:
            mid_pos = (min_pos + max_pos) // 2
            test_text = text[start_pos:mid_pos]
            tokens = self.count_tokens(test_text)

            if tokens < self.min_tokens:
                min_pos = mid_pos + 1
            elif tokens > self.max_tokens:
                max_pos = mid_pos
            else:
                end_pos = mid_pos
                break

        if not preserve_boundaries:
            return end_pos

        # Find nearest paragraph boundary
        remaining_text = text[start_pos:end_pos + 100]  # Look ahead a bit
        paragraph_boundaries = self.find_paragraph_boundaries(remaining_text)

        if paragraph_boundaries:
            # Find closest boundary to our target
            target_rel = end_pos - start_pos
            closest = min(paragraph_boundaries, key=lambda x: abs(x - target_rel))
            if abs(closest - target_rel) < 200:  # Within 200 chars
                return start_pos + closest

        # Otherwise find sentence boundary
        sentence_boundaries = self.find_sentence_boundaries(remaining_text)
        if sentence_boundaries:
            target_rel = end_pos - start_pos
            closest = min(sentence_boundaries, key=lambda x: abs(x - target_rel))
            if abs(closest - target_rel) < 100:  # Within 100 chars
                return start_pos + closest

        return end_pos

    def _calculate_overlap_position(self, chunk: str, end_pos: int) -> int:
        """Calculate the starting position for the next chunk with overlap.

        Args:
            chunk: Current chunk text
            end_pos: End position of current chunk

        Returns:
            Starting position for next chunk
        """
        overlap_text = chunk[-500:] if len(chunk) > 500 else chunk  # Last 500 chars as candidates
        overlap_tokens = self.count_tokens(overlap_text)

        if overlap_tokens <= self.overlap_tokens:
            # Entire overlap candidate is within limit
            return end_pos - len(overlap_text)

        # Binary search for right overlap
        min_chars = 0
        max_chars = len(overlap_text)

        while min_chars < max_chars:
            mid_chars = (min_chars + max_chars + 1) // 2
            test_text = overlap_text[-mid_chars:]
            tokens = self.count_tokens(test_text)

            if tokens <= self.overlap_tokens:
                min_chars = mid_chars
            else:
                max_chars = mid_chars - 1

        return end_pos - min_chars

    def create_chunks_with_metadata(
        self,
        book_data: Dict,
        domain_classifier: Optional[callable] = None
    ) -> List[Dict]:
        """Create chunks with full metadata from book data.

        Args:
            book_data: Book data from Story 2.1
            domain_classifier: Optional function to classify domains

        Returns:
            List of chunk dictionaries with metadata
        """
        all_chunks = []

        for chapter in book_data.get("chapters", []):
            chapter_content = chapter.get("content", "")

            if not chapter_content.strip():
                continue

            # Chunk the chapter content
            text_chunks = self.chunk_text(chapter_content, preserve_boundaries=True)

            # Create metadata for each chunk
            for idx, chunk_text in enumerate(text_chunks):
                chunk_metadata = {
                    "chunk_id": str(uuid.uuid4()),
                    "book_id": book_data.get("book_id"),
                    "book_title": book_data.get("book_title"),
                    "authors": book_data.get("authors", []),
                    "chapter_number": chapter.get("chapter_number"),
                    "chapter_title": chapter.get("chapter_title"),
                    "page_start": chapter.get("page_start"),
                    "page_end": chapter.get("page_end"),
                    "chunk_index": idx,
                    "total_chunks_in_chapter": len(text_chunks),
                    "content": chunk_text,
                    "token_count": self.count_tokens(chunk_text),
                    "created_at": datetime.utcnow().isoformat()
                }

                # Add domain classification
                if domain_classifier:
                    domains = domain_classifier(chunk_text, book_data.get("book_title"))
                    chunk_metadata["primary_domain"] = domains.get("primary")
                    chunk_metadata["secondary_domains"] = domains.get("secondary", [])
                else:
                    # Manual classification will be added later
                    chunk_metadata["primary_domain"] = None
                    chunk_metadata["secondary_domains"] = []

                all_chunks.append(chunk_metadata)

        return all_chunks

    def validate_chunks(self, chunks: List[Dict]) -> Tuple[bool, List[str]]:
        """Validate chunks meet quality requirements.

        Args:
            chunks: List of chunk dictionaries

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        required_fields = [
            "chunk_id", "book_id", "book_title", "authors",
            "chapter_number", "chapter_title", "page_start", "page_end",
            "chunk_index", "total_chunks_in_chapter", "content", "token_count"
        ]

        for i, chunk in enumerate(chunks):
            # Check required fields
            for field in required_fields:
                if field not in chunk:
                    errors.append(f"Chunk {i}: Missing required field '{field}'")

            # Check token count
            token_count = chunk.get("token_count", 0)
            if token_count > self.max_tokens:
                errors.append(f"Chunk {i}: Token count {token_count} exceeds max {self.max_tokens}")

            if token_count == 0:
                errors.append(f"Chunk {i}: Token count is 0")

            # Verify token count is accurate
            actual_tokens = self.count_tokens(chunk.get("content", ""))
            if abs(actual_tokens - token_count) > 5:  # Allow small variance
                errors.append(f"Chunk {i}: Token count mismatch (reported: {token_count}, actual: {actual_tokens})")

        return len(errors) == 0, errors


class SimpleDomainClassifier:
    """Simple rule-based domain classifier for PLC content."""

    DOMAIN_KEYWORDS = {
        "assessment": ["assessment", "formative", "summative", "test", "quiz", "evaluation", "grading"],
        "collaboration": ["team", "collaborative", "meeting", "protocol", "norms", "discussion"],
        "leadership": ["principal", "leader", "administrator", "change management", "vision"],
        "curriculum": ["curriculum", "standards", "guaranteed", "viable", "scope", "sequence"],
        "data_analysis": ["data", "RTI", "intervention", "MTSS", "tier", "progress monitoring"],
        "school_culture": ["culture", "PLC", "professional learning", "community", "implementation"],
        "student_learning": ["student", "learning", "engagement", "motivation", "achievement"]
    }

    def classify(self, text: str, book_title: str = "") -> Dict[str, any]:
        """Classify text into domain categories.

        Args:
            text: Text to classify
            book_title: Book title for context

        Returns:
            Dictionary with primary and secondary domains
        """
        text_lower = text.lower()
        book_lower = book_title.lower() if book_title else ""

        # Count keyword matches for each domain
        domain_scores = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower or keyword in book_lower)
            domain_scores[domain] = score

        # Get primary domain (highest score)
        if max(domain_scores.values()) == 0:
            primary_domain = "school_culture"  # Default
        else:
            primary_domain = max(domain_scores, key=domain_scores.get)

        # Get secondary domains (any with score > 1 and not primary)
        secondary_domains = [
            domain for domain, score in domain_scores.items()
            if score > 1 and domain != primary_domain
        ]

        return {
            "primary": primary_domain,
            "secondary": secondary_domains[:2]  # Max 2 secondary
        }


class ChunkingPipeline:
    """Orchestrates the content chunking pipeline."""

    def __init__(self, bucket: str, input_prefix: str, output_prefix: str,
                 use_simple_classifier: bool = True):
        """Initialize the pipeline.

        Args:
            bucket: S3 bucket name
            input_prefix: S3 prefix for input JSON files (from Story 2.1)
            output_prefix: S3 prefix for output chunked files
            use_simple_classifier: Use simple rule-based classifier (True) or manual (False)
        """
        self.bucket = bucket
        self.input_prefix = input_prefix
        self.output_prefix = output_prefix
        self.s3_client = boto3.client('s3')
        self.chunker = ContentChunker()
        self.domain_classifier = SimpleDomainClassifier().classify if use_simple_classifier else None
        self.processing_log = []

    def list_book_files(self) -> List[str]:
        """List all processed book JSON files in S3.

        Returns:
            List of S3 keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=self.input_prefix
            )

            book_files = [
                obj['Key'] for obj in response.get('Contents', [])
                if obj['Key'].lower().endswith('.json') and 'logs/' not in obj['Key']
            ]

            logger.info(f"Found {len(book_files)} book files in {self.bucket}/{self.input_prefix}")
            return book_files

        except ClientError as e:
            logger.error(f"Failed to list book files: {e}")
            return []

    def download_book_data(self, s3_key: str) -> Optional[Dict]:
        """Download and parse book JSON from S3.

        Args:
            s3_key: S3 key of the book file

        Returns:
            Book data dictionary or None
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            book_data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"Downloaded book data: {book_data.get('book_title')}")
            return book_data

        except ClientError as e:
            logger.error(f"Failed to download {s3_key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {s3_key}: {e}")
            return None

    def process_book(self, s3_key: str) -> bool:
        """Process a single book file into chunks.

        Args:
            s3_key: S3 key of the book file

        Returns:
            True if successful, False otherwise
        """
        book_name = Path(s3_key).name

        try:
            # Download book data
            book_data = self.download_book_data(s3_key)
            if not book_data:
                self.processing_log.append({
                    "file": book_name,
                    "status": "failed",
                    "error": "Download failed"
                })
                return False

            # Create chunks with metadata
            chunks = self.chunker.create_chunks_with_metadata(
                book_data,
                domain_classifier=self.domain_classifier
            )

            # Validate chunks
            is_valid, errors = self.chunker.validate_chunks(chunks)
            if not is_valid:
                logger.error(f"Validation failed for {book_name}: {errors[:5]}")  # Show first 5 errors
                self.processing_log.append({
                    "file": book_name,
                    "status": "failed",
                    "error": f"Validation failed: {len(errors)} errors"
                })
                return False

            # Prepare output
            output_data = {
                "book_id": book_data.get("book_id"),
                "book_title": book_data.get("book_title"),
                "total_chunks": len(chunks),
                "chunks": chunks,
                "chunking_date": datetime.utcnow().isoformat(),
                "source_file": book_name
            }

            # Upload to S3
            output_key = f"{self.output_prefix}{Path(book_name).stem}_chunked.json"
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=output_key,
                Body=json.dumps(output_data, indent=2, ensure_ascii=False).encode('utf-8'),
                ContentType='application/json'
            )

            logger.info(f"Uploaded {len(chunks)} chunks for {book_name} to {output_key}")

            self.processing_log.append({
                "file": book_name,
                "status": "success",
                "total_chunks": len(chunks),
                "avg_tokens": sum(c["token_count"] for c in chunks) / len(chunks),
                "output": output_key
            })

            return True

        except Exception as e:
            logger.error(f"Failed to process {book_name}: {e}")
            self.processing_log.append({
                "file": book_name,
                "status": "failed",
                "error": str(e)
            })
            return False

    def run(self):
        """Run the chunking pipeline."""
        logger.info("Starting content chunking pipeline")

        try:
            # List all book files
            book_files = self.list_book_files()

            if not book_files:
                logger.warning("No book files found")
                return

            # Process each book
            successful = 0
            failed = 0

            for s3_key in tqdm(book_files, desc="Chunking books"):
                if self.process_book(s3_key):
                    successful += 1
                else:
                    failed += 1

            # Save processing log
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "bucket": self.bucket,
                "input_prefix": self.input_prefix,
                "output_prefix": self.output_prefix,
                "total_files": len(book_files),
                "successful": successful,
                "failed": failed,
                "details": self.processing_log
            }

            log_path = Path("chunking_log.json")
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)

            # Upload log to S3
            log_key = f"{self.output_prefix}logs/chunking_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=log_key,
                Body=json.dumps(log_data, indent=2).encode('utf-8'),
                ContentType='application/json'
            )

            logger.info(f"Pipeline complete: {successful} successful, {failed} failed")
            logger.info(f"Log uploaded to {log_key}")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Chunk book content with metadata tagging')
    parser.add_argument('--bucket', default='plccoach-content', help='S3 bucket name')
    parser.add_argument('--input-prefix', default='processed/', help='S3 prefix for input book JSON files')
    parser.add_argument('--output-prefix', default='chunked/', help='S3 prefix for output chunked files')
    parser.add_argument('--no-classifier', action='store_true', help='Skip domain classification')

    args = parser.parse_args()

    pipeline = ChunkingPipeline(
        bucket=args.bucket,
        input_prefix=args.input_prefix,
        output_prefix=args.output_prefix,
        use_simple_classifier=not args.no_classifier
    )

    pipeline.run()


if __name__ == '__main__':
    main()
