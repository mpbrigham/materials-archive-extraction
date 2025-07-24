# Materials Intake Pipeline - n8n Implementation

## Pipeline Overview

This pipeline provides an automated email-based service for extracting structured metadata from architectural material PDFs:

1. **Email Trigger**: Monitors inbox for emails with PDF attachments
2. **PDF Processing**: Validates and processes each PDF attachment
3. **LLM Extraction**: Uses Google Gemini AI to extract structured metadata
4. **Response Delivery**: Sends formatted results back to the sender

## Architecture

```
Email Trigger → Document Validator → LLM Extraction → Result Processor → Send Notification
```

### Components

- **Email Trigger**: IMAP monitoring for incoming emails
- **Document Validator**: Checks for valid PDF attachments
- **LLM Extraction**: Gemini AI with custom prompts for material data extraction
- **Result Processor**: Formats extracted data into structured JSON
- **Send Notification**: SMTP email with success/failure templates

## Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.template .env
```

Required configuration:
- `IMAP_HOST`, `IMAP_PORT`: Email server for receiving
- `SMTP_HOST`, `SMTP_PORT`: Email server for sending
- `EMAIL_USER`, `EMAIL_PASS`: Email credentials
- `LLM_API_KEY`: Google Gemini API key
- `LLM_MODEL`: Model name (e.g., gemini-2.0-flash)
- `N8N_ENCRYPTION_KEY`: Auto-generated if not set

### Directory Structure

```
v0_initial_flow_n8n/
├── docker-compose.yml    # Container configuration
├── Dockerfile           # n8n with Gemini AI package
├── n8n.json            # Workflow definition
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
3. Access n8n interface at http://localhost:5678
4. Import the workflow:
   - Go to Workflows → Import from File
   - Select `/home/node/data/n8n.json` or download and upload from local `n8n.json`
   - Save and activate the workflow

### Testing

Send an email with PDF attachments to the configured inbox. The pipeline will:
1. Process each PDF attachment
2. Extract material metadata
3. Reply with structured JSON results

## Extracted Data Schema

The pipeline extracts the following material properties:

```json
{
  "manufacturer": "string",
  "productName": "string",
  "productType": "string",
  "material": "string",
  "dimensions": {},
  "weight": {},
  "color": [],
  "finish": "string",
  "fireRating": "string",
  "acousticRating": {},
  "thermalProperties": {},
  "certifications": [],
  "applications": [],
  "price": {}
}
```

See `schema/materials_schema.json` for complete schema definition.

## Monitoring

- Container logs: `docker compose logs -f`
- n8n execution history: Available in web interface
- Health endpoint: http://localhost:5678/healthz
