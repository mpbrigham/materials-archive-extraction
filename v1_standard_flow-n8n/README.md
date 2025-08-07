# Materials Intake Pipeline - Pure n8n Implementation

## Pipeline Overview

This pipeline provides an automated email-based service for extracting structured metadata from architectural material PDFs using a pure n8n workflow implementation:

1. **Email Trigger**: Monitors inbox for emails with PDF attachments
2. **PDF Processing**: Validates and processes each PDF attachment
3. **LLM Extraction**: Uses Google Gemini AI to extract structured metadata
4. **Response Delivery**: Sends formatted results back to the sender

## Architecture

```
Email Trigger → Convert Binary → Split Attachments → Document Validator → Route Valid/Invalid → Extract PDF → AI Agent → Process Results → Aggregate → Result Processor → Send Email
```

### Components

- **Email Trigger**: IMAP monitoring for incoming emails with PDF attachments
- **Convert Binary to JSON**: Transforms email attachments into processable JSON format
- **Split Out Attachments**: Processes each attachment individually for scalability
- **Document Validator**: JavaScript code node validating PDF files (type, size, encoding)
- **Route Valid/Invalid**: IF node routing based on validation results
- **Extract PDF Content**: Extracts text from valid PDFs using n8n's built-in node
- **AI Agent Extraction**: Orchestrates LLM extraction with structured output parsing
  - **Google Gemini Chat Model**: Provides AI capabilities with temperature control
  - **Structured Output Parser**: Enforces schema compliance with auto-fix
- **Process Extraction Results**: Post-processes AI output and handles errors
- **Aggregate Attachments**: Collects all processed attachments back together
- **Result Processor**: JavaScript code node formatting extracted data and errors into email response
- **Send Email**: SMTP email with success/failure templates

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
v1_standard_flow-n8n/
├── docker-compose.yml    # Container configuration
├── docker/              # Docker build files
│   └── Dockerfile.n8n   # n8n container configuration with LangChain nodes
├── n8n-python.json      # Workflow definition
├── prompts/            # LLM extraction prompts and JSON schemas
│   ├── llm_extraction.txt    # System prompt for AI extraction
│   └── materials_schema.json # JSON schema for structured output
├── email_templates/    # Success/failure templates
│   ├── success.html    # Template for successful extractions
│   └── failure.html    # Template for failed extractions
└── data/               # Persistent storage for n8n
```

### Workflow Variables Required

The workflow requires these variables to be configured in n8n:
- `materials_extraction_prompt`: Content from `prompts/llm_extraction.txt`
- `materials_schema`: JSON schema from `prompts/materials_schema.json`
- `email_success_template`: HTML from `email_templates/success.html`
- `email_failure_template`: HTML from `email_templates/failure.html`

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

## Extracted Data Schema

The pipeline extracts material properties with confidence scores for each field. Each field includes:
- `value`: The extracted data
- `confidence`: A confidence score (0-1) indicating extraction reliability

See `prompts/materials_schema.json` for the complete schema definition with all fields and enum constraints.

## Monitoring

- Container logs: `docker compose logs -f`
- n8n execution history: Available in web interface
- Health endpoints:
  - n8n: http://<your-IP>:${PORT}/healthz

## PROJECT_SPEC
```spec
NAME: Materials Intake Pipeline
DOMAIN: AI-Powered Data Extraction
PRIMARY_TOOLS: n8n, Docker, Google Gemini, LangChain
PIPELINE_STAGES:
  1. Email Ingestion
  2. PDF Validation
  3. AI-Powered Metadata Extraction
  4. Results Formatting
  5. Email Notification
KEY_COMPONENTS:
- `n8n-python.json`: The n8n workflow that implements the entire pipeline.
- `docker-compose.yml`: Defines the n8n service and volumes for deployment.
- `prompts/llm_extraction.txt`: The prompt used to instruct the Gemini AI.
- `prompts/materials_schema.json`: The JSON schema for the extracted data.
- `email_templates/`: HTML templates for success and failure responses.
DESIGN_CONSTRAINTS:
- The entire pipeline is implemented as a pure n8n workflow.
- AI extraction uses n8n's LangChain nodes for structured output.
- The system must be deployable as a single container using Docker Compose.
```