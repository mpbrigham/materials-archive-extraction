# Materials Intake Pipeline - Node-RED Implementation

## Pipeline Overview

This pipeline provides an automated email-based service for extracting structured metadata from architectural material PDFs:

1. **Email Trigger**: Monitors inbox for emails with PDF attachments
2. **PDF Processing**: Validates and processes each PDF attachment
3. **LLM Extraction**: Uses Google Gemini AI to extract structured metadata
4. **Response Delivery**: Sends formatted results back to the sender

## Architecture

```
Email In → Document Validator → LLM Extraction → Result Aggregator → Result Processor → Email Out
```

### Components

- **Email In**: IMAP monitoring for incoming emails
- **Document Validator**: Function node checking for valid PDF attachments
- **LLM Extraction**: Function node using Gemini AI with custom prompts
- **Result Aggregator**: Join node collecting all processing results
- **Result Processor**: Function node formatting extracted data
- **Email Out**: SMTP email with success/failure templates

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

### Directory Structure

```
v0_initial_flow_red/
├── docker-compose.yml    # Container configuration
├── Dockerfile           # Node-RED with dependencies
├── red.json            # Workflow definition
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
3. Access Node-RED interface at http://localhost:1880
4. Flow loads automatically from red.json

### Testing

Send an email with PDF attachments to the configured inbox. The pipeline will:
1. Process each PDF attachment
2. Extract material metadata
3. Reply with structured JSON results

## Migration from n8n

This is a minimal migration from the n8n implementation, maintaining:
- Identical workflow logic
- Same LLM prompts and schemas
- Same email templates
- Same environment variables

Key differences:
- Node-RED flow format instead of n8n JSON
- Message-based instead of item-based processing
- Built-in email nodes instead of n8n email nodes
- Function nodes instead of Code nodes

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
- Node-RED dashboard: http://localhost:1880
- Debug log: `data/debug.log`
- Flow execution: Visible in Node-RED debug sidebar