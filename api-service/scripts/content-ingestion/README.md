# Content Ingestion Pipeline

This directory contains scripts for processing Solution Tree PDF books into embeddings for semantic search.

## Pipeline Stages

### Stage 1: PDF Extraction (`01_extract_pdfs.py`)
Extracts text and metadata from PDF files stored in S3.

**Input:** PDF files in S3 (`raw/` prefix)
**Output:** JSON files with extracted text and metadata (`processed/` prefix)

**Usage:**
```bash
python 01_extract_pdfs.py --bucket plccoach-content --input-prefix raw/ --output-prefix processed/
```

**Features:**
- Text extraction with structure preservation
- Metadata extraction (title, authors, pages)
- OCR error cleanup
- Header/footer removal
- S3 integration
- Processing logs

### Stage 2: Content Chunking (`02_chunk_content.py`)
Splits book content into semantic chunks with metadata tagging.

**Input:** JSON files with extracted book content (`processed/` prefix)
**Output:** JSON files with chunked content and metadata (`chunked/` prefix)

**Usage:**
```bash
python 02_chunk_content.py --bucket plccoach-content --input-prefix processed/ --output-prefix chunked/
```

**Features:**
- Intelligent chunking (500-1000 tokens per chunk)
- 100-token overlap between chunks
- Semantic boundary detection
- Rich metadata tagging
- Domain classification (rule-based)
- Quality validation

### Stage 3: Embedding Generation (`03_generate_embeddings.py`)
Generates vector embeddings for content chunks using OpenAI API.

**Input:** JSON files with chunked content (`chunked/` prefix)
**Output:** JSON files with chunks + embeddings (`embeddings/` prefix)

**Usage:**
```bash
export OPENAI_API_KEY="your-api-key"
python 03_generate_embeddings.py --bucket plccoach-content --input-prefix chunked/ --output-prefix embeddings/
```

**Features:**
- 3072-dimensional embeddings (text-embedding-3-large)
- Batch processing (100 chunks per API call)
- Exponential backoff retry logic
- Real-time cost tracking
- Progress logging

### Stage 4: Database Upload (`04_upload_to_db.py`)
Uploads vector embeddings to PostgreSQL with pgvector extension.

**Input:** JSON files with embeddings (`embeddings/` prefix in S3)
**Output:** PostgreSQL embeddings table with pgvector index

**Prerequisites:**
```bash
# Run database migration first
alembic upgrade head
```

**Usage:**
```bash
python 04_upload_to_db.py --bucket plccoach-content --input-prefix embeddings/
```

**Features:**
- pgvector extension setup
- ivfflat index for fast similarity search
- Batch upload (1000 embeddings per batch)
- Metadata indexing for filtering
- Similarity search testing

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure AWS credentials:
```bash
aws configure
```

3. Ensure S3 bucket exists:
```bash
aws s3 ls s3://plccoach-content/
```

## Testing

Run tests:
```bash
cd ../../
pytest tests/content-ingestion/ -v
```

## Logging

All scripts log to:
- `pdf_extraction.log` (file)
- stdout (console)
- S3 (`processed/logs/` prefix)

## Monitoring

Processing logs include:
- Total files processed
- Success/failure counts
- Page counts
- Error details
- Timestamps
