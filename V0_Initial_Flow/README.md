# Materials Intake Pipeline

Email → PDF extraction → LLM metadata → Send results

## Core Workflow

**Request-response email service:**
1. User sends email with PDF attachments to bot@brigham.be
2. Bot extracts materials metadata from PDFs using Gemini AI
3. Bot emails results back to the original sender

## Architecture

Email Trigger → Document Validator → LLM Extraction → Result Processor → Send Notification

## Quick Start

1. Copy `.env.template` to `.env` and add credentials
2. `docker compose up -d`
3. Open http://localhost:5678
4. Import `materials_archive_extraction.json`
5. Configure IMAP/SMTP credentials
6. Activate workflow

## Files

```
.
├── materials_archive_extraction.json        # n8n workflow
├── docker-compose.yml                       # Docker setup
├── DEPLOYMENT.md                            # Setup guide
├── prompts/llm_extraction.txt               # LLM prompt
├── email_templates/
│   ├── success.html                         # Success template
│   └── failure.html                         # Error template
└── tests/                                   # Test scripts
    ├── test-extraction.js
    ├── test-email.js
    └── check-latest-email.js
```

## Test

```bash
cd tests
node test-extraction.js      # Direct LLM test
node test-email.js          # Full pipeline test
node check-latest-email.js  # Check latest email
```

## PROJECT_SPEC
```spec
NAME: Materials Library Extraction Pipeline
DOMAIN: Document Processing Automation
PRIMARY_TOOLS: n8n, Gemini AI, Node.js, IMAP/SMTP, Docker
PIPELINE_STAGES:
  1. Email trigger receives PDF attachments
  2. Document validator creates email context + clean PDF items
  3. LLM extraction processes PDFs, passes through email context
  4. Result processor combines context + results, generates HTML
  5. Send notification emails results back to sender
KEY_COMPONENTS:
- `materials_archive_extraction.json`: n8n workflow definition
- `email_templates/success.html`: HTML results template
- `prompts/llm_extraction.txt`: LLM extraction prompt
- `tests/test-extraction.js`: Direct API testing
- `tests/test-email.js`: End-to-end pipeline testing
DATA_STRUCTURE:
- Email context: single item with email metadata
- PDF items: clean processing items without duplication
- Results: structured HTML tables with metadata
DESIGN_CONSTRAINTS:
- Results sent back to original email sender only
- Header table: supplier, product_name, sku_number, source_file
- Data table: all other extracted fields
- Must handle multiple PDFs per email
- Must gracefully handle extraction failures
- Symmetric structure: email context separate from PDF processing
```
