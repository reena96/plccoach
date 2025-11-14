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

### Stage 3: Embedding Generation (Story 2.3)
_Coming next_

### Stage 4: Database Upload (Story 2.4)
_Coming next_

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
