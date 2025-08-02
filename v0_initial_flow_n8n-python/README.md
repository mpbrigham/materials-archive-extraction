# Materials Intake Pipeline - n8n Implementation with Python Microservices

## Pipeline Overview

This pipeline provides an automated email-based service for extracting structured metadata from architectural material PDFs using Python microservices:

1. **Email Trigger**: Monitors inbox for emails with PDF attachments
2. **PDF Processing**: Validates and processes each PDF attachment via HTTP API
3. **LLM Extraction**: Uses Google Gemini AI to extract structured metadata
4. **Response Delivery**: Sends formatted results back to the sender

## Architecture

```
Email Trigger → Write Files → Document Validator (HTTP) → LLM Extraction (HTTP) → Result Processor (HTTP) → Send Notification
```

### Components

- **Email Trigger**: IMAP monitoring for incoming emails
- **Write Files**: Saves PDF attachments to `/tmp/n8n/attachments/`
- **Document Validator**: HTTP endpoint to check valid PDF attachments
- **LLM Extraction**: HTTP endpoint using Gemini AI for material data extraction
- **Result Processor**: HTTP endpoint to format extracted data into structured JSON
- **Send Notification**: SMTP email with success/failure templates
- **FastAPI Service**: Python microservices exposed on port 8000

## Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.template .env
```

Required configuration:
- `VPN_IP`: IP address to bind services (use 0.0.0.0 for all interfaces)
- `IMAP_HOST`, `IMAP_port`: Email server for receiving
- `SMTP_HOST`, `SMTP_port`: Email server for sending
- `EMAIL_USER`, `EMAIL_PASS`: Email credentials
- `LLM_API_KEY`: Google Gemini API key
- `LLM_MODEL`: Model name (e.g., gemini-2.0-flash)
- `N8N_ENCRYPTION_KEY`: Auto-generated if not set

### Directory Structure

```
v0_initial_flow_n8n-python/
├── docker-compose.yml    # Container configuration
├── Dockerfile           # n8n with Python and FastAPI
├── n8n-python.json      # Workflow definition
├── python/              # Python microservices
│   ├── app.py          # FastAPI application
│   ├── common.py       # Shared utilities
│   ├── document_validator.py
│   ├── llm_extraction.py
│   ├── result_processor.py
│   └── requirements.txt
├── prompts/            # LLM extraction prompts
├── schema/             # Material data JSON schema
├── email_templates/    # Success/failure templates
└── data/               # Persistent storage
```

## Setup and Usage

### Deployment

1. Configure environment variables in `.env`
2. Start the service:
   ```bash
   docker compose up -d
   ```
3. Access n8n interface at http://<your-VPN_IP>:5679
4. Import the workflow:
   - Go to Workflows → Import from File
   - Select `/home/node/data/n8n-python.json` or upload from local `n8n-python.json`
   - Save and activate the workflow

### Quick Start Checklist

1. **Copy and configure `.env` file**:
   ```bash
   cp .env.template .env
   # Edit .env and fill in ALL required values
   ```

2. **Start the services**:
   ```bash
   docker compose up -d
   ```

3. **Import and activate the workflow**:
   - Open http://<your-VPN_IP>:5679 in your browser
   - Go to Workflows → Import from File → Choose `n8n-python.json`
   - Click "Save" and then "Active" toggle to enable

That's it! Send an email with PDF attachments to test.

### Testing

Send an email with PDF attachments to the configured inbox. The pipeline will:
1. Process each PDF attachment
2. Extract material metadata
3. Reply with structured JSON results

## Microservices API

The FastAPI service exposes the following endpoints on port 8000:

- `POST /validate` - Validates PDF files from a list of file paths.
- `POST /extract` - Extract material data using LLM
- `POST /process` - Format results into email response
- `GET /health` - Health check endpoint

## API Implementation

Each HTTP endpoint is backed by a Python module:
- `document_validator.py`: Validates PDF files from file paths and creates the initial state object.
- `llm_extraction.py`: Extracts material data from PDF files using Gemini AI.
- `result_processor.py`: Formats and validates the output
- `common.py`: Shared utilities and logging functions

## Extracted Data Schema

The pipeline extracts material properties with confidence scores for each field. Each field includes:
- `value`: The extracted data
- `confidence`: A confidence score (0-1) indicating extraction reliability

See `schema/materials_schema.json` for the complete schema definition with all fields and enum constraints.

## Monitoring

- Container logs: `docker compose logs -f`
- n8n execution history: Available in web interface
- FastAPI docs: http://<your-VPN_IP>:8000/docs (when container is running)
- Health endpoints:
  - n8n: http://<your-VPN_IP>:5679/healthz
  - FastAPI: http://<your-VPN_IP>:8000/health

## PROJECT_SPEC
```spec
NAME: Materials Intake Pipeline
DOMAIN: AI-Powered Data Extraction
PRIMARY_TOOLS: n8n, Python, FastAPI, Docker, Google Gemini
PIPELINE_STAGES:
  1. Email Ingestion
  2. PDF Validation
  3. AI-Powered Metadata Extraction
  4. Results Formatting
  5. Email Notification
KEY_COMPONENTS:
- `n8n-python.json`: The n8n workflow that orchestrates the pipeline.
- `python/app.py`: The FastAPI microservice that handles the core logic.
- `docker-compose.yml`: Defines the services, networks, and volumes for deployment.
- `prompts/llm_extraction.txt`: The prompt used to instruct the Gemini AI.
- `schema/materials_schema.json`: The JSON schema for the extracted data.
DESIGN_CONSTRAINTS:
- The core processing logic must be implemented as a stateless microservice.
- The n8n workflow should only be used for orchestration and not for core logic.
- The system must be deployable as a single unit using Docker Compose.
```
