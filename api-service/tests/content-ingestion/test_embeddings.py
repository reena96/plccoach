"""
Tests for Story 2.3: Vector Embeddings Generation

Tests the embedding generation functionality including:
- OpenAI API integration
- Batch processing
- Retry logic
- Cost calculation
- Error handling
"""

import json
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest

# Add scripts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts' / 'content-ingestion'))

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "generate_embeddings_03",
        Path(__file__).parent.parent.parent / 'scripts' / 'content-ingestion' / '03_generate_embeddings.py'
    )
    embed_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(embed_module)
    EmbeddingGenerator = embed_module.EmbeddingGenerator
    EmbeddingPipeline = embed_module.EmbeddingPipeline
except Exception as e:
    pytest.skip(f"Could not import embedding module: {e}", allow_module_level=True)


class TestEmbeddingGenerator:
    """Tests for EmbeddingGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create an EmbeddingGenerator instance with mocked OpenAI client."""
        with patch('openai.OpenAI'):
            return EmbeddingGenerator(api_key="test-key", batch_size=10)

    def test_initialization(self, generator):
        """Test generator initialization."""
        assert generator.batch_size == 10
        assert generator.total_tokens == 0
        assert generator.total_cost == 0.0
        assert generator.EMBEDDING_DIMENSION == 3072
        assert generator.MODEL == "text-embedding-3-large"

    @patch('openai.OpenAI')
    def test_generate_embeddings_success(self, mock_openai, generator):
        """Test successful embedding generation."""
        # Mock the API response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 3072),
            Mock(embedding=[0.2] * 3072)
        ]
        mock_response.usage.total_tokens = 100

        generator.client.embeddings.create = Mock(return_value=mock_response)

        texts = ["Text 1", "Text 2"]
        embeddings = generator.generate_embeddings(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 3072
        assert generator.total_tokens == 100
        assert generator.total_cost > 0

    @patch('openai.OpenAI')
    def test_generate_embeddings_tracks_cost(self, mock_openai, generator):
        """Test that cost tracking works correctly."""
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 3072)]
        mock_response.usage.total_tokens = 1_000_000  # 1M tokens

        generator.client.embeddings.create = Mock(return_value=mock_response)

        generator.generate_embeddings(["text"])

        # 1M tokens at $0.13/1M = $0.13
        assert abs(generator.total_cost - 0.13) < 0.01

    @patch('openai.OpenAI')
    def test_embed_chunks_processes_in_batches(self, mock_openai, generator):
        """Test that chunks are processed in batches."""
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 3072) for _ in range(10)]
        mock_response.usage.total_tokens = 100

        generator.client.embeddings.create = Mock(return_value=mock_response)

        # Create 25 chunks (should be 3 batches with batch_size=10)
        chunks = [{"content": f"Text {i}"} for i in range(25)]

        embedded_chunks = generator.embed_chunks(chunks)

        # Should have called API 3 times (batches of 10, 10, 5)
        assert generator.client.embeddings.create.call_count == 3
        assert len(embedded_chunks) == 25

    @patch('openai.OpenAI')
    def test_embed_chunks_adds_metadata(self, mock_openai, generator):
        """Test that embedding metadata is added to chunks."""
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 3072)]
        mock_response.usage.total_tokens = 10

        generator.client.embeddings.create = Mock(return_value=mock_response)

        chunks = [{"content": "Test text", "chunk_id": "123"}]
        embedded_chunks = generator.embed_chunks(chunks)

        assert len(embedded_chunks) == 1
        chunk = embedded_chunks[0]

        # Check original fields preserved
        assert chunk["chunk_id"] == "123"
        assert chunk["content"] == "Test text"

        # Check new fields added
        assert "embedding" in chunk
        assert "embedding_model" in chunk
        assert "embedding_dimension" in chunk
        assert chunk["embedding_model"] == "text-embedding-3-large"
        assert chunk["embedding_dimension"] == 3072

    @patch('openai.OpenAI')
    def test_embed_chunks_handles_partial_failure(self, mock_openai, generator):
        """Test that partial batch failures are handled gracefully."""
        # First batch succeeds, second fails, third succeeds
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 3072) for _ in range(10)]
        mock_response.usage.total_tokens = 100

        generator.client.embeddings.create = Mock(
            side_effect=[mock_response, Exception("API Error"), mock_response]
        )

        chunks = [{"content": f"Text {i}"} for i in range(25)]
        embedded_chunks = generator.embed_chunks(chunks)

        # Should have 20 embedded chunks (first and third batches)
        assert len(embedded_chunks) == 20

    def test_validate_embedding_success(self, generator):
        """Test embedding validation with valid embedding."""
        valid_embedding = [0.1] * 3072
        assert generator.validate_embedding(valid_embedding) is True

    def test_validate_embedding_wrong_dimension(self, generator):
        """Test embedding validation fails with wrong dimensions."""
        wrong_dim = [0.1] * 1536  # Wrong dimension
        assert generator.validate_embedding(wrong_dim) is False

    def test_validate_embedding_wrong_type(self, generator):
        """Test embedding validation fails with wrong type."""
        assert generator.validate_embedding("not a list") is False
        assert generator.validate_embedding({"not": "list"}) is False

    def test_validate_embedding_invalid_values(self, generator):
        """Test embedding validation fails with invalid values."""
        invalid_values = [0.1] * 3071 + ["string"]
        assert generator.validate_embedding(invalid_values) is False


@patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
class TestEmbeddingPipeline:
    """Tests for EmbeddingPipeline class."""

    @patch('boto3.client')
    @patch('openai.OpenAI')
    def test_pipeline_initialization(self, mock_openai, mock_boto):
        """Test pipeline initialization."""
        pipeline = EmbeddingPipeline(
            bucket="test-bucket",
            input_prefix="chunked/",
            output_prefix="embeddings/"
        )

        assert pipeline.bucket == "test-bucket"
        assert pipeline.input_prefix == "chunked/"
        assert pipeline.output_prefix == "embeddings/"
        assert pipeline.generator is not None
        assert len(pipeline.processing_log) == 0

    @patch('boto3.client')
    @patch('openai.OpenAI')
    def test_list_chunked_files(self, mock_openai, mock_boto):
        """Test listing chunked files from S3."""
        pipeline = EmbeddingPipeline(
            bucket="test-bucket",
            input_prefix="chunked/",
            output_prefix="embeddings/"
        )

        pipeline.s3_client.list_objects_v2 = Mock(return_value={
            'Contents': [
                {'Key': 'chunked/book1_chunked.json'},
                {'Key': 'chunked/book2_chunked.json'},
                {'Key': 'chunked/logs/log.json'},  # Should be filtered
            ]
        })

        result = pipeline.list_chunked_files()

        assert len(result) == 2
        assert 'chunked/book1_chunked.json' in result
        assert 'chunked/book2_chunked.json' in result
        assert 'chunked/logs/log.json' not in result

    @patch('boto3.client')
    @patch('openai.OpenAI')
    def test_download_chunked_data_success(self, mock_openai, mock_boto):
        """Test successful chunked data download."""
        pipeline = EmbeddingPipeline(
            bucket="test-bucket",
            input_prefix="chunked/",
            output_prefix="embeddings/"
        )

        mock_response = {
            'Body': Mock(read=Mock(return_value=json.dumps({
                "book_title": "Test Book",
                "total_chunks": 10,
                "chunks": [{"content": "text"}]
            }).encode('utf-8')))
        }
        pipeline.s3_client.get_object = Mock(return_value=mock_response)

        result = pipeline.download_chunked_data("chunked/test.json")

        assert result is not None
        assert result["book_title"] == "Test Book"
        assert result["total_chunks"] == 10

    @patch('boto3.client')
    @patch('openai.OpenAI')
    def test_download_chunked_data_failure(self, mock_openai, mock_boto):
        """Test chunked data download failure."""
        pipeline = EmbeddingPipeline(
            bucket="test-bucket",
            input_prefix="chunked/",
            output_prefix="embeddings/"
        )

        from botocore.exceptions import ClientError

        pipeline.s3_client.get_object = Mock(
            side_effect=ClientError({"Error": {"Code": "404"}}, "get_object")
        )

        result = pipeline.download_chunked_data("chunked/test.json")

        assert result is None


class TestCostCalculation:
    """Tests for cost calculation."""

    @patch('openai.OpenAI')
    def test_cost_calculation_accuracy(self, mock_openai):
        """Test that cost calculation is accurate."""
        generator = EmbeddingGenerator(api_key="test-key")

        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 3072)]
        mock_response.usage.total_tokens = 1_000_000

        generator.client.embeddings.create = Mock(return_value=mock_response)
        generator.generate_embeddings(["text"])

        # $0.13 per 1M tokens
        expected_cost = 0.13
        assert abs(generator.total_cost - expected_cost) < 0.001

    @patch('openai.OpenAI')
    def test_cost_accumulation(self, mock_openai):
        """Test that costs accumulate over multiple calls."""
        generator = EmbeddingGenerator(api_key="test-key")

        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 3072)]
        mock_response.usage.total_tokens = 100_000

        generator.client.embeddings.create = Mock(return_value=mock_response)

        # Call 10 times
        for _ in range(10):
            generator.generate_embeddings(["text"])

        # Should have 1M total tokens, $0.13 total cost
        assert generator.total_tokens == 1_000_000
        assert abs(generator.total_cost - 0.13) < 0.001


class TestRetryLogic:
    """Tests for retry logic."""

    @patch('openai.OpenAI')
    def test_retry_on_failure(self, mock_openai):
        """Test that retries happen on failure."""
        generator = EmbeddingGenerator(api_key="test-key")

        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 3072)]
        mock_response.usage.total_tokens = 100

        # Fail twice, then succeed
        generator.client.embeddings.create = Mock(
            side_effect=[
                Exception("Rate limit"),
                Exception("Rate limit"),
                mock_response
            ]
        )

        # Should succeed after retries
        embeddings = generator.generate_embeddings(["text"])
        assert len(embeddings) == 1

        # Should have called 3 times (2 failures + 1 success)
        assert generator.client.embeddings.create.call_count == 3

    @patch('openai.OpenAI')
    def test_gives_up_after_max_retries(self, mock_openai):
        """Test that it gives up after max retries."""
        generator = EmbeddingGenerator(api_key="test-key")

        # Always fail
        generator.client.embeddings.create = Mock(
            side_effect=Exception("Persistent error")
        )

        # Should raise exception after retries
        with pytest.raises(Exception):
            generator.generate_embeddings(["text"])

        # Should have tried 3 times (tenacity default)
        assert generator.client.embeddings.create.call_count == 3


class TestBatchProcessing:
    """Tests for batch processing logic."""

    @patch('openai.OpenAI')
    def test_batch_size_respected(self, mock_openai):
        """Test that batch size is respected."""
        generator = EmbeddingGenerator(api_key="test-key", batch_size=5)

        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 3072) for _ in range(5)]
        mock_response.usage.total_tokens = 50

        generator.client.embeddings.create = Mock(return_value=mock_response)

        chunks = [{"content": f"Text {i}"} for i in range(12)]
        generator.embed_chunks(chunks)

        # Should have called 3 times: 5 + 5 + 2
        assert generator.client.embeddings.create.call_count == 3

        # Check batch sizes
        calls = generator.client.embeddings.create.call_args_list
        assert len(calls[0][1]['input']) == 5  # First batch
        assert len(calls[1][1]['input']) == 5  # Second batch
        assert len(calls[2][1]['input']) == 2  # Third batch


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
