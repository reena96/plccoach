#!/usr/bin/env python3
"""
Story 2.3: Vector Embeddings Generation

Generates vector embeddings for content chunks using OpenAI text-embedding-3-large API.

Usage:
    python 03_generate_embeddings.py --bucket plccoach-content --input-prefix chunked/ --output-prefix embeddings/
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import boto3
import numpy as np
from openai import OpenAI
from botocore.exceptions import ClientError
from tqdm import tqdm
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embedding_generation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates vector embeddings using OpenAI API."""

    # OpenAI pricing (as of 2024)
    COST_PER_MILLION_TOKENS = 0.13  # text-embedding-3-large
    EMBEDDING_DIMENSION = 3072
    MODEL = "text-embedding-3-large"

    def __init__(self, api_key: Optional[str] = None, batch_size: int = 100):
        """Initialize the embedding generator.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            batch_size: Number of texts to process in one API call
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.batch_size = batch_size
        self.total_tokens = 0
        self.total_cost = 0.0

    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors

        Raises:
            Exception: If API call fails after retries
        """
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.MODEL
            )

            # Extract embeddings
            embeddings = [item.embedding for item in response.data]

            # Track usage
            tokens_used = response.usage.total_tokens
            self.total_tokens += tokens_used
            cost = (tokens_used / 1_000_000) * self.COST_PER_MILLION_TOKENS
            self.total_cost += cost

            logger.debug(f"Generated {len(embeddings)} embeddings, used {tokens_used} tokens, cost ${cost:.4f}")

            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for all chunks with progress tracking.

        Args:
            chunks: List of chunk dictionaries from Story 2.2

        Returns:
            List of chunks with embeddings added
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks")

        # Process in batches
        embedded_chunks = []

        for i in tqdm(range(0, len(chunks), self.batch_size), desc="Generating embeddings"):
            batch = chunks[i:i + self.batch_size]

            # Extract texts
            texts = [chunk["content"] for chunk in batch]

            # Generate embeddings
            try:
                embeddings = self.generate_embeddings(texts)

                # Add embeddings to chunks
                for chunk, embedding in zip(batch, embeddings):
                    chunk_with_embedding = chunk.copy()
                    chunk_with_embedding["embedding"] = embedding
                    chunk_with_embedding["embedding_model"] = self.MODEL
                    chunk_with_embedding["embedding_dimension"] = self.EMBEDDING_DIMENSION
                    embedded_chunks.append(chunk_with_embedding)

            except Exception as e:
                logger.error(f"Failed to process batch {i//self.batch_size + 1}: {e}")
                # Continue with next batch
                continue

            # Rate limiting: small delay between batches
            if i + self.batch_size < len(chunks):
                time.sleep(0.1)

        logger.info(f"Completed {len(embedded_chunks)}/{len(chunks)} chunks")
        logger.info(f"Total tokens: {self.total_tokens:,}, Total cost: ${self.total_cost:.2f}")

        return embedded_chunks

    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate that an embedding has the correct dimensions.

        Args:
            embedding: Embedding vector to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(embedding, list):
            return False

        if len(embedding) != self.EMBEDDING_DIMENSION:
            return False

        # Check that all values are floats
        if not all(isinstance(x, (int, float)) for x in embedding):
            return False

        return True


class EmbeddingPipeline:
    """Orchestrates the embedding generation pipeline."""

    def __init__(self,
                 bucket: str,
                 input_prefix: str,
                 output_prefix: str,
                 batch_size: int = 100):
        """Initialize the pipeline.

        Args:
            bucket: S3 bucket name
            input_prefix: S3 prefix for chunked content (from Story 2.2)
            output_prefix: S3 prefix for embeddings output
            batch_size: Batch size for OpenAI API calls
        """
        self.bucket = bucket
        self.input_prefix = input_prefix
        self.output_prefix = output_prefix
        self.s3_client = boto3.client('s3')
        self.generator = EmbeddingGenerator(batch_size=batch_size)
        self.processing_log = []

    def list_chunked_files(self) -> List[str]:
        """List all chunked book files in S3.

        Returns:
            List of S3 keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=self.input_prefix
            )

            chunked_files = [
                obj['Key'] for obj in response.get('Contents', [])
                if obj['Key'].lower().endswith('.json') and 'logs/' not in obj['Key']
            ]

            logger.info(f"Found {len(chunked_files)} chunked files in {self.bucket}/{self.input_prefix}")
            return chunked_files

        except ClientError as e:
            logger.error(f"Failed to list chunked files: {e}")
            return []

    def download_chunked_data(self, s3_key: str) -> Optional[Dict]:
        """Download and parse chunked book data from S3.

        Args:
            s3_key: S3 key of the chunked file

        Returns:
            Chunked book data or None
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"Downloaded chunked data: {data.get('book_title')} ({data.get('total_chunks')} chunks)")
            return data

        except ClientError as e:
            logger.error(f"Failed to download {s3_key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {s3_key}: {e}")
            return None

    def process_book(self, s3_key: str) -> bool:
        """Process a single chunked book file to generate embeddings.

        Args:
            s3_key: S3 key of the chunked file

        Returns:
            True if successful, False otherwise
        """
        book_name = Path(s3_key).name

        try:
            # Download chunked data
            chunked_data = self.download_chunked_data(s3_key)
            if not chunked_data:
                self.processing_log.append({
                    "file": book_name,
                    "status": "failed",
                    "error": "Download failed"
                })
                return False

            chunks = chunked_data.get("chunks", [])
            if not chunks:
                logger.warning(f"No chunks found in {book_name}")
                return False

            # Generate embeddings
            start_time = time.time()
            embedded_chunks = self.generator.embed_chunks(chunks)
            elapsed_time = time.time() - start_time

            if len(embedded_chunks) == 0:
                logger.error(f"Failed to generate any embeddings for {book_name}")
                self.processing_log.append({
                    "file": book_name,
                    "status": "failed",
                    "error": "No embeddings generated"
                })
                return False

            # Prepare output
            output_data = {
                "book_id": chunked_data.get("book_id"),
                "book_title": chunked_data.get("book_title"),
                "total_chunks": len(embedded_chunks),
                "chunks": embedded_chunks,
                "embedding_model": self.generator.MODEL,
                "embedding_dimension": self.generator.EMBEDDING_DIMENSION,
                "embedding_date": datetime.utcnow().isoformat(),
                "source_file": book_name,
                "processing_time_seconds": elapsed_time
            }

            # Upload to S3
            output_key = f"{self.output_prefix}{Path(book_name).stem}_embeddings.json"

            # Convert numpy arrays to lists for JSON serialization
            json_str = json.dumps(output_data, indent=2, ensure_ascii=False)

            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=output_key,
                Body=json_str.encode('utf-8'),
                ContentType='application/json'
            )

            logger.info(f"Uploaded embeddings for {book_name} to {output_key}")

            self.processing_log.append({
                "file": book_name,
                "status": "success",
                "total_chunks": len(embedded_chunks),
                "successful_embeddings": len(embedded_chunks),
                "processing_time_seconds": elapsed_time,
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
        """Run the embedding generation pipeline."""
        logger.info("Starting embedding generation pipeline")
        start_time = time.time()

        try:
            # List all chunked files
            chunked_files = self.list_chunked_files()

            if not chunked_files:
                logger.warning("No chunked files found")
                return

            # Process each file
            successful = 0
            failed = 0

            for s3_key in tqdm(chunked_files, desc="Processing books"):
                if self.process_book(s3_key):
                    successful += 1
                else:
                    failed += 1

            total_time = time.time() - start_time

            # Save processing log
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "bucket": self.bucket,
                "input_prefix": self.input_prefix,
                "output_prefix": self.output_prefix,
                "total_files": len(chunked_files),
                "successful": successful,
                "failed": failed,
                "total_tokens": self.generator.total_tokens,
                "total_cost_usd": self.generator.total_cost,
                "total_processing_time_seconds": total_time,
                "model": self.generator.MODEL,
                "embedding_dimension": self.generator.EMBEDDING_DIMENSION,
                "details": self.processing_log
            }

            log_path = Path("embedding_generation_log.json")
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)

            # Upload log to S3
            log_key = f"{self.output_prefix}logs/embedding_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=log_key,
                Body=json.dumps(log_data, indent=2).encode('utf-8'),
                ContentType='application/json'
            )

            logger.info(f"Pipeline complete: {successful} successful, {failed} failed")
            logger.info(f"Total tokens: {self.generator.total_tokens:,}")
            logger.info(f"Total cost: ${self.generator.total_cost:.2f}")
            logger.info(f"Total time: {total_time:.1f}s")
            logger.info(f"Log uploaded to {log_key}")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate vector embeddings for content chunks')
    parser.add_argument('--bucket', default='plccoach-content', help='S3 bucket name')
    parser.add_argument('--input-prefix', default='chunked/', help='S3 prefix for chunked content')
    parser.add_argument('--output-prefix', default='embeddings/', help='S3 prefix for embeddings output')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for OpenAI API calls')

    args = parser.parse_args()

    # Verify OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    pipeline = EmbeddingPipeline(
        bucket=args.bucket,
        input_prefix=args.input_prefix,
        output_prefix=args.output_prefix,
        batch_size=args.batch_size
    )

    pipeline.run()


if __name__ == '__main__':
    main()
