#!/usr/bin/env python3
"""
Story 2.4: PostgreSQL pgvector Setup & Data Upload

Uploads vector embeddings from S3 to PostgreSQL database with pgvector.

Usage:
    python 04_upload_to_db.py --bucket plccoach-content --input-prefix embeddings/
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db_config import get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embedding_upload.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EmbeddingUploader:
    """Uploads embeddings to PostgreSQL with pgvector."""

    def __init__(self, database_url: str, batch_size: int = 1000):
        """Initialize the uploader.

        Args:
            database_url: PostgreSQL connection string
            batch_size: Number of embeddings to insert per batch
        """
        self.engine = create_engine(database_url)
        self.batch_size = batch_size
        self.Session = sessionmaker(bind=self.engine)

    def verify_pgvector(self) -> bool:
        """Verify that pgvector extension is installed.

        Returns:
            True if installed, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
                ))
                count = result.scalar()
                if count > 0:
                    logger.info("pgvector extension is installed")
                    return True
                else:
                    logger.error("pgvector extension is NOT installed")
                    return False
        except Exception as e:
            logger.error(f"Failed to check pgvector: {e}")
            return False

    def verify_table_exists(self) -> bool:
        """Verify that embeddings table exists.

        Returns:
            True if exists, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_name = 'embeddings'
                """))
                count = result.scalar()
                if count > 0:
                    logger.info("embeddings table exists")
                    return True
                else:
                    logger.error("embeddings table does NOT exist")
                    return False
        except Exception as e:
            logger.error(f"Failed to check table: {e}")
            return False

    def insert_embeddings_batch(self, embeddings: List[Dict]) -> int:
        """Insert a batch of embeddings into the database.

        Args:
            embeddings: List of embedding dictionaries

        Returns:
            Number of embeddings inserted
        """
        if not embeddings:
            return 0

        try:
            with self.engine.connect() as conn:
                # Prepare batch insert
                for embedding in embeddings:
                    # Extract metadata
                    metadata = {
                        'book_id': embedding.get('book_id'),
                        'book_title': embedding.get('book_title'),
                        'authors': embedding.get('authors'),
                        'chapter_number': embedding.get('chapter_number'),
                        'chapter_title': embedding.get('chapter_title'),
                        'page_start': embedding.get('page_start'),
                        'page_end': embedding.get('page_end'),
                        'chunk_index': embedding.get('chunk_index'),
                        'primary_domain': embedding.get('primary_domain'),
                        'secondary_domains': embedding.get('secondary_domains'),
                        'token_count': embedding.get('token_count')
                    }

                    # Insert embedding
                    conn.execute(text("""
                        INSERT INTO embeddings (content, embedding, metadata)
                        VALUES (:content, :embedding::vector, :metadata::jsonb)
                    """), {
                        'content': embedding.get('content'),
                        'embedding': embedding.get('embedding'),
                        'metadata': json.dumps(metadata)
                    })

                conn.commit()
                logger.debug(f"Inserted batch of {len(embeddings)} embeddings")
                return len(embeddings)

        except Exception as e:
            logger.error(f"Failed to insert batch: {e}")
            raise

    def test_similarity_search(self, query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """Test similarity search with a query embedding.

        Args:
            query_embedding: Query vector
            limit: Number of results to return

        Returns:
            List of similar embeddings with scores
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT
                        content,
                        metadata,
                        1 - (embedding <=> :query_embedding::vector) as similarity
                    FROM embeddings
                    ORDER BY embedding <=> :query_embedding::vector
                    LIMIT :limit
                """), {
                    'query_embedding': query_embedding,
                    'limit': limit
                })

                results = []
                for row in result:
                    results.append({
                        'content': row[0],
                        'metadata': row[1],
                        'similarity': float(row[2])
                    })

                return results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise

    def get_table_count(self) -> int:
        """Get the number of embeddings in the table.

        Returns:
            Number of rows
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM embeddings"))
                return result.scalar()
        except Exception as e:
            logger.error(f"Failed to get count: {e}")
            return 0


class UploadPipeline:
    """Orchestrates the embedding upload pipeline."""

    def __init__(self, bucket: str, input_prefix: str, database_url: str, batch_size: int = 1000):
        """Initialize the pipeline.

        Args:
            bucket: S3 bucket name
            input_prefix: S3 prefix for embedding files
            database_url: PostgreSQL connection string
            batch_size: Batch size for uploads
        """
        self.bucket = bucket
        self.input_prefix = input_prefix
        self.s3_client = boto3.client('s3')
        self.uploader = EmbeddingUploader(database_url, batch_size)
        self.processing_log = []

    def list_embedding_files(self) -> List[str]:
        """List all embedding files in S3.

        Returns:
            List of S3 keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=self.input_prefix
            )

            embedding_files = [
                obj['Key'] for obj in response.get('Contents', [])
                if obj['Key'].lower().endswith('.json') and 'logs/' not in obj['Key']
            ]

            logger.info(f"Found {len(embedding_files)} embedding files in {self.bucket}/{self.input_prefix}")
            return embedding_files

        except ClientError as e:
            logger.error(f"Failed to list embedding files: {e}")
            return []

    def download_embeddings(self, s3_key: str) -> List[Dict]:
        """Download embeddings from S3.

        Args:
            s3_key: S3 key of the embedding file

        Returns:
            List of embedding dictionaries
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            data = json.loads(response['Body'].read().decode('utf-8'))

            embeddings = data.get('chunks', [])
            logger.info(f"Downloaded {len(embeddings)} embeddings from {s3_key}")
            return embeddings

        except ClientError as e:
            logger.error(f"Failed to download {s3_key}: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {s3_key}: {e}")
            return []

    def process_file(self, s3_key: str) -> bool:
        """Process a single embedding file.

        Args:
            s3_key: S3 key of the embedding file

        Returns:
            True if successful, False otherwise
        """
        file_name = Path(s3_key).name

        try:
            # Download embeddings
            embeddings = self.download_embeddings(s3_key)
            if not embeddings:
                self.processing_log.append({
                    "file": file_name,
                    "status": "failed",
                    "error": "No embeddings found"
                })
                return False

            # Upload in batches
            total_uploaded = 0
            start_time = time.time()

            for i in tqdm(range(0, len(embeddings), self.uploader.batch_size),
                         desc=f"Uploading {file_name}"):
                batch = embeddings[i:i + self.uploader.batch_size]
                uploaded = self.uploader.insert_embeddings_batch(batch)
                total_uploaded += uploaded

            elapsed_time = time.time() - start_time

            self.processing_log.append({
                "file": file_name,
                "status": "success",
                "total_embeddings": len(embeddings),
                "uploaded": total_uploaded,
                "processing_time_seconds": elapsed_time
            })

            logger.info(f"Uploaded {total_uploaded} embeddings from {file_name} in {elapsed_time:.1f}s")
            return True

        except Exception as e:
            logger.error(f"Failed to process {file_name}: {e}")
            self.processing_log.append({
                "file": file_name,
                "status": "failed",
                "error": str(e)
            })
            return False

    def run(self):
        """Run the upload pipeline."""
        logger.info("Starting embedding upload pipeline")
        start_time = time.time()

        # Verify prerequisites
        if not self.uploader.verify_pgvector():
            logger.error("pgvector extension not installed. Run migrations first.")
            return

        if not self.uploader.verify_table_exists():
            logger.error("embeddings table not found. Run migrations first.")
            return

        try:
            # Get initial count
            initial_count = self.uploader.get_table_count()
            logger.info(f"Initial embedding count: {initial_count}")

            # List all embedding files
            embedding_files = self.list_embedding_files()

            if not embedding_files:
                logger.warning("No embedding files found")
                return

            # Process each file
            successful = 0
            failed = 0

            for s3_key in embedding_files:
                if self.process_file(s3_key):
                    successful += 1
                else:
                    failed += 1

            # Get final count
            final_count = self.uploader.get_table_count()
            total_time = time.time() - start_time

            logger.info(f"Upload complete: {successful} files successful, {failed} failed")
            logger.info(f"Total embeddings: {final_count} (added {final_count - initial_count})")
            logger.info(f"Total time: {total_time:.1f}s")

            # Save processing log
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "bucket": self.bucket,
                "input_prefix": self.input_prefix,
                "total_files": len(embedding_files),
                "successful": successful,
                "failed": failed,
                "initial_count": initial_count,
                "final_count": final_count,
                "embeddings_added": final_count - initial_count,
                "total_processing_time_seconds": total_time,
                "details": self.processing_log
            }

            log_path = Path("embedding_upload_log.json")
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)

            logger.info(f"Processing log saved to {log_path}")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Upload embeddings to PostgreSQL')
    parser.add_argument('--bucket', default='plccoach-content', help='S3 bucket name')
    parser.add_argument('--input-prefix', default='embeddings/', help='S3 prefix for embedding files')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for uploads')

    args = parser.parse_args()

    # Get database URL
    database_url = get_database_url()
    logger.info(f"Connecting to database: {database_url.split('@')[1]}")  # Log without credentials

    pipeline = UploadPipeline(
        bucket=args.bucket,
        input_prefix=args.input_prefix,
        database_url=database_url,
        batch_size=args.batch_size
    )

    pipeline.run()


if __name__ == '__main__':
    main()
