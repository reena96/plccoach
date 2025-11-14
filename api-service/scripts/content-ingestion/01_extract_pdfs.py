#!/usr/bin/env python3
"""
Story 2.1: Content Ingestion Pipeline - PDF Processing

Extracts text and metadata from Solution Tree PDF books stored in S3.
Preserves document structure and prepares content for chunking and embedding.

Usage:
    python 01_extract_pdfs.py --bucket plccoach-content --input-prefix raw/ --output-prefix processed/
"""

import argparse
import json
import logging
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import boto3
import fitz  # PyMuPDF
from botocore.exceptions import ClientError
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_extraction.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extracts text and metadata from PDF files."""

    def __init__(self, s3_client=None):
        """Initialize the PDF extractor.

        Args:
            s3_client: Optional boto3 S3 client (for testing)
        """
        self.s3_client = s3_client or boto3.client('s3')

    def download_from_s3(self, bucket: str, key: str, local_path: Path) -> bool:
        """Download a PDF file from S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key
            local_path: Local path to save the file

        Returns:
            True if successful, False otherwise
        """
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self.s3_client.download_file(bucket, key, str(local_path))
            logger.info(f"Downloaded {key} from S3 bucket {bucket}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download {key}: {e}")
            return False

    def upload_to_s3(self, local_path: Path, bucket: str, key: str) -> bool:
        """Upload a processed JSON file to S3.

        Args:
            local_path: Local path of the file
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.upload_file(str(local_path), bucket, key)
            logger.info(f"Uploaded {key} to S3 bucket {bucket}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload {key}: {e}")
            return False

    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove common OCR artifacts (including Unicode replacement characters)
        text = re.sub(r'[��\ufffd\uffff]', '', text)

        # Normalize quotes (curly to straight)
        text = text.replace('\u201c', '"').replace('\u201d', '"')  # "" -> ""
        text = text.replace('\u2018', "'").replace('\u2019', "'")  # '' -> ''

        # Remove page numbers (common patterns)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

        return text.strip()

    def detect_structure(self, page, text: str) -> str:
        """Detect and preserve document structure using markdown.

        Args:
            page: PyMuPDF page object
            text: Extracted text from page

        Returns:
            Text with markdown structure
        """
        # This is a simplified version. In production, you might use
        # more sophisticated methods to detect headings, lists, etc.
        structured_text = text

        # Try to detect headings based on font size
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    if "spans" in line:
                        for span in line["spans"]:
                            # If font size is large (>14pt), treat as heading
                            if span.get("size", 0) > 14:
                                text_content = span.get("text", "").strip()
                                if text_content:
                                    structured_text = structured_text.replace(
                                        text_content,
                                        f"# {text_content}"
                                    )

        return structured_text

    def extract_metadata_from_pdf(self, pdf_path: Path) -> Dict:
        """Extract metadata from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with metadata
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata

            return {
                "title": metadata.get("title", pdf_path.stem),
                "author": metadata.get("author", "Unknown"),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "total_pages": len(doc)
            }
        except Exception as e:
            logger.error(f"Failed to extract metadata from {pdf_path}: {e}")
            return {"total_pages": 0}

    def extract_text_from_pdf(self, pdf_path: Path) -> Dict:
        """Extract text and structure from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with extracted content and metadata
        """
        logger.info(f"Extracting text from {pdf_path}")

        try:
            doc = fitz.open(pdf_path)

            # Extract basic metadata
            metadata = self.extract_metadata_from_pdf(pdf_path)

            # Extract text from each page
            chapters = []
            current_chapter = {
                "chapter_number": 1,
                "chapter_title": "Introduction",
                "page_start": 1,
                "page_end": len(doc),
                "content": ""
            }

            for page_num, page in enumerate(doc, start=1):
                # Extract text
                text = page.get_text()

                # Clean the text
                clean_text = self.clean_text(text)

                # Try to preserve structure
                structured_text = self.detect_structure(page, clean_text)

                # Append to current chapter
                current_chapter["content"] += f"\n\n{structured_text}"

            chapters.append(current_chapter)

            # Build the final output
            result = {
                "book_id": str(uuid.uuid4()),
                "book_title": metadata.get("title", pdf_path.stem),
                "authors": self._parse_authors(metadata.get("author", "Unknown")),
                "publication_year": self._extract_year(metadata.get("creation_date", "")),
                "total_pages": metadata["total_pages"],
                "chapters": chapters,
                "extraction_date": datetime.utcnow().isoformat(),
                "source_file": pdf_path.name
            }

            doc.close()
            logger.info(f"Successfully extracted {metadata['total_pages']} pages from {pdf_path}")
            return result

        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            raise

    def _parse_authors(self, author_string: str) -> List[str]:
        """Parse author string into list of authors.

        Args:
            author_string: Author metadata string

        Returns:
            List of author names
        """
        if not author_string or author_string == "Unknown":
            return ["Unknown"]

        # Split on common separators
        authors = re.split(r'[,;&]|\band\b', author_string)
        return [author.strip() for author in authors if author.strip()]

    def _extract_year(self, date_string: str) -> Optional[int]:
        """Extract year from date string.

        Args:
            date_string: Date string from PDF metadata

        Returns:
            Year as integer or None
        """
        if not date_string:
            return None

        # Try to find a 4-digit year
        match = re.search(r'(\d{4})', date_string)
        if match:
            return int(match.group(1))

        return None


class PDFExtractionPipeline:
    """Orchestrates the PDF extraction pipeline."""

    def __init__(self, bucket: str, input_prefix: str, output_prefix: str):
        """Initialize the pipeline.

        Args:
            bucket: S3 bucket name
            input_prefix: S3 prefix for input PDFs
            output_prefix: S3 prefix for output JSON files
        """
        self.bucket = bucket
        self.input_prefix = input_prefix
        self.output_prefix = output_prefix
        self.extractor = PDFExtractor()
        self.s3_client = boto3.client('s3')
        self.processing_log = []

    def list_pdf_files(self) -> List[str]:
        """List all PDF files in the S3 input prefix.

        Returns:
            List of S3 keys for PDF files
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=self.input_prefix
            )

            pdf_files = [
                obj['Key'] for obj in response.get('Contents', [])
                if obj['Key'].lower().endswith('.pdf')
            ]

            logger.info(f"Found {len(pdf_files)} PDF files in {self.bucket}/{self.input_prefix}")
            return pdf_files

        except ClientError as e:
            logger.error(f"Failed to list PDF files: {e}")
            return []

    def process_pdf(self, s3_key: str, temp_dir: Path) -> bool:
        """Process a single PDF file.

        Args:
            s3_key: S3 key of the PDF file
            temp_dir: Temporary directory for downloads

        Returns:
            True if successful, False otherwise
        """
        pdf_name = Path(s3_key).name
        local_pdf_path = temp_dir / pdf_name

        try:
            # Download PDF from S3
            if not self.extractor.download_from_s3(self.bucket, s3_key, local_pdf_path):
                self.processing_log.append({
                    "file": pdf_name,
                    "status": "failed",
                    "error": "Download failed"
                })
                return False

            # Extract text and metadata
            result = self.extractor.extract_text_from_pdf(local_pdf_path)

            # Save to local JSON
            json_name = f"{Path(pdf_name).stem}.json"
            local_json_path = temp_dir / json_name

            with open(local_json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            # Upload to S3
            output_key = f"{self.output_prefix}{json_name}"
            if not self.extractor.upload_to_s3(local_json_path, self.bucket, output_key):
                self.processing_log.append({
                    "file": pdf_name,
                    "status": "failed",
                    "error": "Upload failed"
                })
                return False

            self.processing_log.append({
                "file": pdf_name,
                "status": "success",
                "pages": result["total_pages"],
                "output": output_key
            })

            # Clean up local files
            local_pdf_path.unlink()
            local_json_path.unlink()

            return True

        except Exception as e:
            logger.error(f"Failed to process {pdf_name}: {e}")
            self.processing_log.append({
                "file": pdf_name,
                "status": "failed",
                "error": str(e)
            })
            return False

    def run(self):
        """Run the PDF extraction pipeline."""
        logger.info("Starting PDF extraction pipeline")

        # Create temp directory
        temp_dir = Path("temp_pdfs")
        temp_dir.mkdir(exist_ok=True)

        try:
            # List all PDF files
            pdf_files = self.list_pdf_files()

            if not pdf_files:
                logger.warning("No PDF files found")
                return

            # Process each PDF
            successful = 0
            failed = 0

            for s3_key in tqdm(pdf_files, desc="Processing PDFs"):
                if self.process_pdf(s3_key, temp_dir):
                    successful += 1
                else:
                    failed += 1

            # Save processing log
            log_path = Path("pdf_extraction_log.json")
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.utcnow().isoformat(),
                    "bucket": self.bucket,
                    "input_prefix": self.input_prefix,
                    "output_prefix": self.output_prefix,
                    "total_files": len(pdf_files),
                    "successful": successful,
                    "failed": failed,
                    "details": self.processing_log
                }, f, indent=2)

            # Upload log to S3
            log_key = f"{self.output_prefix}logs/extraction_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            self.extractor.upload_to_s3(log_path, self.bucket, log_key)

            logger.info(f"Pipeline complete: {successful} successful, {failed} failed")

        finally:
            # Clean up temp directory
            if temp_dir.exists():
                for file in temp_dir.iterdir():
                    file.unlink()
                temp_dir.rmdir()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Extract text from Solution Tree PDF books')
    parser.add_argument('--bucket', default='plccoach-content', help='S3 bucket name')
    parser.add_argument('--input-prefix', default='raw/', help='S3 prefix for input PDFs')
    parser.add_argument('--output-prefix', default='processed/', help='S3 prefix for output JSON files')

    args = parser.parse_args()

    pipeline = PDFExtractionPipeline(
        bucket=args.bucket,
        input_prefix=args.input_prefix,
        output_prefix=args.output_prefix
    )

    pipeline.run()


if __name__ == '__main__':
    main()
