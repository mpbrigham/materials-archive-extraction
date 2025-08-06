# Materials Intake Pipeline - n8n Implementation with Python Microservices

## Pipeline Overview

This pipeline provides an automated email-based service for extracting structured metadata from architectural material PDFs using Python microservices:

1. **Email Trigger**: Monitors inbox for emails with PDF attachments
2. **PDF Processing**: Validates and processes each PDF attachment via HTTP API
3. **LLM Extraction**: Uses Google Gemini AI to extract structured metadata
4. **Response Delivery**: Sends formatted results back to the sender

## Architecture

```
Email Trigger → Convert Binary → Split Attachments → Document Validator (HTTP) → LLM Extraction (HTTP) → Aggregate → Result Processor (HTTP) → Send Notification
```

### Components

- **Email Trigger**: IMAP monitoring for incoming emails with PDF attachments
- **Convert Binary to JSON**: Transforms email attachments into processable JSON format
- **Split Out Attachments**: Processes each attachment individually for scalability
- **Document Validator**: HTTP endpoint validating PDF files (type, size, encoding)
- **LLM Extraction**: HTTP endpoint using Gemini AI for material data extraction
- **Aggregate Processed Attachments**: Collects all processed attachments back together
- **Result Processor**: HTTP endpoint formatting extracted data and errors into email response
- **Send Notification**: SMTP email with success/failure templates
- **FastAPI Service**: Python microservices exposed on port 8000

## Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.template .env
```

Required configuration:
- `IP`: IP address to bind services (use 0.0.0.0 for all interfaces)
- `PORT`: Port for n8n web interface (e.g., 5678)
- `IMAP_HOST`, `IMAP_PORT`: Email server for receiving
- `SMTP_HOST`, `SMTP_PORT`: Email server for sending
- `EMAIL_USER`, `EMAIL_PASS`: Email credentials for the service
- `EMAIL_USER_TEST`, `EMAIL_USER_TEST_PASS`: Test email credentials (optional, for testing)
- `LLM_API_KEY`: Google Gemini API key
- `LLM_MODEL`: Model name (e.g., gemini-2.0-flash)
- `N8N_ENCRYPTION_KEY`: Auto-generated if not set

### Directory Structure

```
v1_standard_flow/
├── docker-compose.yml    # Container configuration
├── docker/              # Docker build files
│   ├── Dockerfile.n8n   # n8n container configuration
│   ├── Dockerfile.python # Python FastAPI container
│   └── requirements-python.txt # Python dependencies
├── n8n-python.json      # Workflow definition
├── python/              # Python microservices
│   ├── app.py          # FastAPI application
│   ├── common.py       # Shared utilities
│   ├── document_validation.py
│   ├── llm_extraction.py
│   └── email_formatting.py
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
3. Access n8n interface at http://<your-IP>:${PORT}
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
   - Open http://<your-IP>:${PORT} in your browser (where IP and PORT are from your .env file)
   - Go to Workflows → Import from File → Choose `n8n-python.json`
   - Click "Save" and then "Active" toggle to enable

That's it! Send an email with PDF attachments to test.

### Testing

Send an email with PDF attachments to the configured inbox. The pipeline will:
1. Process each PDF attachment individually
2. Extract material metadata using AI
3. Reply with structured JSON results or detailed error information

## Error Handling

The pipeline implements robust error handling at multiple levels:

### Per-Attachment Processing
- Each PDF attachment is processed independently
- Failed attachments don't block processing of valid ones
- Errors are tracked per attachment with clear descriptions

### Error Feedback
Email responses include:
- **Success emails**: List any attachments that failed with specific reasons
- **Failure emails**: Detailed error messages for debugging
- **Error format**: `[Service Name] Attachment filename.pdf: specific error description`

### Common Error Scenarios
- **Invalid file type**: Non-PDF attachments are rejected with clear message
- **File size limits**: PDFs over 4MB are rejected to prevent timeouts
- **LLM extraction failures**: API errors or timeouts are captured and reported
- **Base64 encoding issues**: Corrupted attachments are identified

### Monitoring
- **Execution History**: View all workflow executions in n8n UI at http://<your-IP>:${PORT}
- **Execution Details**: Click any execution to see detailed error messages per node
- **Container Logs**: Use `docker compose logs -f` for system-level debugging

## Microservices API

The FastAPI service exposes the following endpoints on port 8000:

- `POST /validate` - Validates individual PDF attachment (MIME type, size, encoding)
- `POST /extract` - Extracts material data using LLM from single attachment
- `POST /email-format` - Formats aggregated results into email response
- `GET /health` - Health check endpoint

## API Implementation

Each HTTP endpoint is backed by a Python module:
- `document_validation.py`: Validates single PDF attachment and updates status
- `llm_extraction.py`: Extracts material data from PDF using Gemini AI (removes base64 data after processing for memory optimization)
- `email_formatting.py`: Formats aggregated results into email response
- `common.py`: Shared utilities for HTML table generation

Note: Python dependencies are defined in `docker/requirements-python.txt`


## Extracted Data Schema

The pipeline extracts material properties with confidence scores for each field. Each field includes:
- `value`: The extracted data
- `confidence`: A confidence score (0-1) indicating extraction reliability

See `schema/materials_schema.json` for the complete schema definition with all fields and enum constraints.

## Monitoring

- Container logs: `docker compose logs -f`
- n8n execution history: Available in web interface
- FastAPI docs: http://<your-IP>:8000/docs (when container is running)
- Health endpoints:
  - n8n: http://<your-IP>:${PORT}/healthz
  - FastAPI: http://<your-IP>:8000/health

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
