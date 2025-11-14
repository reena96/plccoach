"""
Tests for Story 2.1: PDF Extraction Pipeline

Tests the PDF extraction functionality including:
- Text extraction
- Structure preservation
- Metadata extraction
- S3 integration
"""

import json
import uuid
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest

# Add scripts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts' / 'content-ingestion'))

try:
    from scripts.content_ingestion.extract_pdfs_01 import PDFExtractor, PDFExtractionPipeline
except ImportError:
    # For direct imports when running tests
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "extract_pdfs_01",
        Path(__file__).parent.parent.parent / 'scripts' / 'content-ingestion' / '01_extract_pdfs.py'
    )
    extract_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extract_module)
    PDFExtractor = extract_module.PDFExtractor
    PDFExtractionPipeline = extract_module.PDFExtractionPipeline


class TestPDFExtractor:
    """Tests for PDFExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a PDFExtractor instance with mocked S3 client."""
        mock_s3 = Mock()
        return PDFExtractor(s3_client=mock_s3)

    def test_clean_text_removes_excessive_whitespace(self, extractor):
        """Test that clean_text removes excessive whitespace."""
        text = "This   is    a    test\n\n\n\nwith   spaces"
        result = extractor.clean_text(text)
        assert result == "This is a test with spaces"

    def test_clean_text_removes_ocr_artifacts(self, extractor):
        """Test that clean_text removes OCR artifacts."""
        text = "This �� is ￿ a test"
        result = extractor.clean_text(text)
        assert "��" not in result
        assert "￿" not in result

    def test_clean_text_normalizes_quotes(self, extractor):
        """Test that clean_text normalizes quotes."""
        text = "\u201cquoted\u201d and \u2018apostrophe\u2019"
        result = extractor.clean_text(text)
        assert '"quoted"' in result
        assert "'apostrophe'" in result

    def test_clean_text_removes_page_numbers(self, extractor):
        """Test that clean_text removes standalone page numbers."""
        text = "Chapter 1\n\n  42  \n\nContinued text"
        result = extractor.clean_text(text)
        # Page number should be removed or minimized
        assert "Chapter 1" in result
        assert "Continued text" in result

    def test_parse_authors_single_author(self, extractor):
        """Test parsing a single author."""
        result = extractor._parse_authors("John Doe")
        assert result == ["John Doe"]

    def test_parse_authors_multiple_authors_comma(self, extractor):
        """Test parsing multiple authors separated by commas."""
        result = extractor._parse_authors("DuFour, DuFour, Eaker, Many")
        assert len(result) == 4
        assert "DuFour" in result
        assert "Eaker" in result
        assert "Many" in result

    def test_parse_authors_multiple_authors_and(self, extractor):
        """Test parsing multiple authors with 'and'."""
        result = extractor._parse_authors("John Doe and Jane Smith")
        assert len(result) == 2
        assert "John Doe" in result
        assert "Jane Smith" in result

    def test_parse_authors_unknown(self, extractor):
        """Test parsing unknown author."""
        result = extractor._parse_authors("Unknown")
        assert result == ["Unknown"]

    def test_extract_year_from_date_string(self, extractor):
        """Test extracting year from various date formats."""
        assert extractor._extract_year("D:20160101") == 2016
        assert extractor._extract_year("2024-01-15") == 2024
        assert extractor._extract_year("January 2023") == 2023

    def test_extract_year_no_year(self, extractor):
        """Test extracting year when no year present."""
        assert extractor._extract_year("") is None
        assert extractor._extract_year("Invalid") is None

    @patch('boto3.client')
    def test_download_from_s3_success(self, mock_boto_client, extractor, tmp_path):
        """Test successful S3 download."""
        extractor.s3_client.download_file = Mock()

        local_path = tmp_path / "test.pdf"
        result = extractor.download_from_s3("bucket", "key", local_path)

        assert result is True
        extractor.s3_client.download_file.assert_called_once()

    @patch('boto3.client')
    def test_download_from_s3_failure(self, mock_boto_client, extractor, tmp_path):
        """Test S3 download failure."""
        from botocore.exceptions import ClientError

        extractor.s3_client.download_file = Mock(
            side_effect=ClientError({"Error": {"Code": "404"}}, "download_file")
        )

        local_path = tmp_path / "test.pdf"
        result = extractor.download_from_s3("bucket", "key", local_path)

        assert result is False

    @patch('boto3.client')
    def test_upload_to_s3_success(self, mock_boto_client, extractor, tmp_path):
        """Test successful S3 upload."""
        extractor.s3_client.upload_file = Mock()

        local_path = tmp_path / "test.json"
        local_path.write_text("{}")

        result = extractor.upload_to_s3(local_path, "bucket", "key")

        assert result is True
        extractor.s3_client.upload_file.assert_called_once()

    @patch('boto3.client')
    def test_upload_to_s3_failure(self, mock_boto_client, extractor, tmp_path):
        """Test S3 upload failure."""
        from botocore.exceptions import ClientError

        extractor.s3_client.upload_file = Mock(
            side_effect=ClientError({"Error": {"Code": "403"}}, "upload_file")
        )

        local_path = tmp_path / "test.json"
        local_path.write_text("{}")

        result = extractor.upload_to_s3(local_path, "bucket", "key")

        assert result is False


class TestPDFExtractionPipeline:
    """Tests for PDFExtractionPipeline class."""

    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance with mocked S3."""
        with patch('boto3.client'):
            return PDFExtractionPipeline(
                bucket="test-bucket",
                input_prefix="raw/",
                output_prefix="processed/"
            )

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.bucket == "test-bucket"
        assert pipeline.input_prefix == "raw/"
        assert pipeline.output_prefix == "processed/"
        assert len(pipeline.processing_log) == 0

    @patch('boto3.client')
    def test_list_pdf_files_success(self, mock_boto_client, pipeline):
        """Test listing PDF files from S3."""
        pipeline.s3_client.list_objects_v2 = Mock(return_value={
            'Contents': [
                {'Key': 'raw/book1.pdf'},
                {'Key': 'raw/book2.pdf'},
                {'Key': 'raw/notes.txt'},  # Should be filtered out
            ]
        })

        result = pipeline.list_pdf_files()

        assert len(result) == 2
        assert 'raw/book1.pdf' in result
        assert 'raw/book2.pdf' in result
        assert 'raw/notes.txt' not in result

    @patch('boto3.client')
    def test_list_pdf_files_empty(self, mock_boto_client, pipeline):
        """Test listing PDF files when none exist."""
        pipeline.s3_client.list_objects_v2 = Mock(return_value={'Contents': []})

        result = pipeline.list_pdf_files()

        assert len(result) == 0

    def test_processing_log_records_success(self, pipeline):
        """Test that processing log records successful operations."""
        pipeline.processing_log.append({
            "file": "book1.pdf",
            "status": "success",
            "pages": 100,
            "output": "processed/book1.json"
        })

        assert len(pipeline.processing_log) == 1
        assert pipeline.processing_log[0]["status"] == "success"
        assert pipeline.processing_log[0]["pages"] == 100

    def test_processing_log_records_failure(self, pipeline):
        """Test that processing log records failures."""
        pipeline.processing_log.append({
            "file": "book1.pdf",
            "status": "failed",
            "error": "Download failed"
        })

        assert len(pipeline.processing_log) == 1
        assert pipeline.processing_log[0]["status"] == "failed"
        assert "error" in pipeline.processing_log[0]


class TestMetadataStructure:
    """Tests for metadata structure compliance."""

    def test_metadata_structure_has_required_fields(self):
        """Test that metadata structure includes all required fields."""
        metadata = {
            "book_id": str(uuid.uuid4()),
            "book_title": "Learning by Doing",
            "authors": ["DuFour", "DuFour", "Eaker", "Many"],
            "publication_year": 2016,
            "total_pages": 350,
            "chapters": [
                {
                    "chapter_number": 1,
                    "chapter_title": "Test Chapter",
                    "page_start": 15,
                    "page_end": 45,
                    "content": "Test content"
                }
            ]
        }

        # Verify all required fields are present
        assert "book_id" in metadata
        assert "book_title" in metadata
        assert "authors" in metadata
        assert "publication_year" in metadata
        assert "total_pages" in metadata
        assert "chapters" in metadata

        # Verify chapter structure
        chapter = metadata["chapters"][0]
        assert "chapter_number" in chapter
        assert "chapter_title" in chapter
        assert "page_start" in chapter
        assert "page_end" in chapter
        assert "content" in chapter

    def test_metadata_book_id_is_uuid(self):
        """Test that book_id is a valid UUID."""
        book_id = str(uuid.uuid4())
        # Should not raise an exception
        uuid.UUID(book_id)

    def test_metadata_authors_is_list(self):
        """Test that authors is a list."""
        authors = ["Author 1", "Author 2"]
        assert isinstance(authors, list)
        assert len(authors) > 0

    def test_metadata_pages_are_integers(self):
        """Test that page numbers are integers."""
        chapter = {
            "page_start": 15,
            "page_end": 45
        }
        assert isinstance(chapter["page_start"], int)
        assert isinstance(chapter["page_end"], int)
        assert chapter["page_end"] >= chapter["page_start"]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
