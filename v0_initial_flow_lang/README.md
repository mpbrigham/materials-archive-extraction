# Materials Intake Pipeline - Langflow Implementation

## Pipeline Overview

Automated email-based service for extracting structured metadata from architectural material PDFs using Langflow.

## Architecture

```
Email Input → PDF Processing → Gemini AI Extraction → JSON Output → Email Response
```

### Workflow Components

The pipeline is implemented as a single Langflow workflow (`lang.json`) with these components:

1. **Email Trigger**: IMAP monitoring for incoming emails with PDF attachments
2. **PDF Extractor**: Validates and extracts text from PDF documents
3. **Prompt Loader**: Loads the LLM extraction prompt from file
4. **Schema Loader**: Loads the JSON validation schema
5. **Gemini Extractor**: Uses Google Gemini AI to extract structured metadata
6. **JSON Validator**: Validates extracted data against schema
7. **Response Formatter**: Formats results using HTML templates
8. **Email Sender**: Sends formatted results back via SMTP

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
- `VPN_IP`: IP address for Langflow UI access

Security configuration (recommended for production):
- `LANGFLOW_SECRET_KEY`: Encryption key for sensitive data (auto-generated if not set)
- `LANGFLOW_AUTO_LOGIN`: Set to `false` to require authentication (default: `true`)
- `LANGFLOW_SUPERUSER`: Admin username (required if AUTO_LOGIN is false)
- `LANGFLOW_SUPERUSER_PASSWORD`: Admin password (required if AUTO_LOGIN is false)

To generate a secure secret key:
```bash
python3 -c "from secrets import token_urlsafe; print(token_urlsafe(32))"
```

### Directory Structure

```
v0_initial_flow_lang/
├── docker-compose.yml    # Container configuration
├── Dockerfile           # Langflow with dependencies
├── lang.json           # Langflow workflow definition
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
3. Access Langflow UI at http://${VPN_IP}:7860
4. Import the workflow:
   - Click "Import" in Langflow UI
   - Select `/app/lang.json` or upload from local `lang.json`
   - Save and activate the flow

### Testing

Send an email with PDF attachments to the configured inbox. The pipeline will:
1. Detect the email and extract PDF attachments
2. Process each PDF through Gemini AI
3. Validate the extracted JSON against the schema
4. Reply with structured results or error message

## Monitoring

- Container logs: `docker compose logs -f`
- Langflow UI: View flow execution at http://${VPN_IP}:7860
- Health endpoint: http://${VPN_IP}:7860/health

## Workflow Details

The workflow processes emails in these steps:

1. **Email Detection**: Polls IMAP inbox every 60 seconds
2. **PDF Validation**: Checks attachments are valid PDFs (max 50MB)
3. **Text Extraction**: Extracts text and images from PDFs
4. **AI Processing**: Sends to Gemini with extraction prompt
5. **Validation**: Ensures output matches materials schema
6. **Response**: Formats and sends results via email

Error handling:
- Invalid PDFs: Sends failure email
- AI errors: Retries with fallback model
- Validation errors: Sends partial results
- Email errors: Logs and retries

## Production Notes

- Workflow must be manually imported on first setup (same as n8n)
- All file paths use container-internal paths (/app/*)
- Environment variables are injected at runtime
- Persistent data stored in ./data volume
- For production deployment:
  - Set `LANGFLOW_AUTO_LOGIN=false` to require authentication
  - Configure `LANGFLOW_SECRET_KEY` for consistent encryption across restarts
  - Use strong passwords for `LANGFLOW_SUPERUSER_PASSWORD`
