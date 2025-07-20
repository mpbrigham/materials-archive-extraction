# Materials Intake Pipeline - ActivePieces Implementation

## What This Pipeline Does

This pipeline provides an automated email-based service for extracting structured metadata from architectural material PDFs:

1. **Email Trigger**: Monitors inbox for emails with PDF attachments
2. **PDF Processing**: Validates and processes each PDF attachment
3. **LLM Extraction**: Uses Google Gemini AI to extract structured metadata
4. **Response Delivery**: Sends formatted results back to the sender

## Architecture

```
IMAP Trigger → Read Config → Document Validator → Loop → LLM Extraction → Result Processor → Send Email
```

### Components

- **IMAP Trigger**: Email monitoring for incoming messages
- **Read Config**: Loads prompts and schema from mounted volumes
- **Document Validator**: Filters valid PDF attachments
- **Loop**: Processes each PDF individually
- **LLM Extraction**: Gemini AI with custom prompts
- **Result Processor**: Formats extracted data
- **Send Email**: SMTP response with results

### Infrastructure

- **Single Container**: SQLite database, in-memory queue
- **Custom Image**: ActivePieces with @google/generative-ai package
- **Lightweight**: Suitable for low-volume workloads

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
- `AP_ENCRYPTION_KEY`: Auto-generated if not set
- `AP_JWT_SECRET`: Auto-generated if not set
- `AP_API_KEY`: Auto-generated if not set

Optional configuration:
- `AP_PROJECT_ID`: Project name (defaults to 'materials-archive-extraction')

### Directory Structure

```
v0_initial_flow_ap/
├── docker-compose.yml    # Container configuration
├── Dockerfile           # ActivePieces with Gemini
├── ap.json             # Workflow definition
├── prompts/            # LLM extraction prompts
├── schema/             # Material data JSON schema
├── email_templates/    # Success/failure templates
├── scripts/            # Setup automation
└── data/               # Persistent storage
```

## Setup and Usage

### Local Development

1. Configure environment variables in `.env`
2. Start the service:
   ```bash
   docker compose up -d
   ```
3. Wait for ActivePieces to initialize
4. Run setup script to create connections and import workflow:
   ```bash
   docker compose exec ap python3 /data/scripts/setup-ap.py
   ```
5. Access ActivePieces at http://localhost:5679

### Production Deployment

The pipeline deploys automatically via GitHub Actions:

1. Push changes to `v0_initial_flow` branch
2. CI/CD validates schema and workflow JSON
3. Deploys to production server with:
   - Docker container management
   - Automated connection setup
   - Workflow import and activation
   - Health checks

Required GitHub Secrets:
- `DEPLOY_HOST`: Production server address
- `DEPLOY_SSH_KEY`: SSH key for deployment
- `EMAIL_PASS`: Email password
- `LLM_API_KEY`: Gemini API key
- `AP_ENCRYPTION_KEY`: ActivePieces encryption
- `AP_JWT_SECRET`: ActivePieces JWT secret

### API Setup

The `setup-ap.py` script automatically:
1. Creates IMAP connection for email monitoring
2. Creates SMTP connection for sending responses
3. Creates Gemini AI connection for LLM processing
4. Imports and activates the workflow

## Testing

Send an email with PDF attachments to the configured inbox. The pipeline will:
1. Process each PDF attachment
2. Extract material metadata using Gemini AI
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
- ActivePieces dashboard: Flow execution history
- Health endpoint: `docker compose exec ap curl http://localhost:80/api/v1/health`

## Platform Differences

This implementation uses ActivePieces instead of n8n but provides identical functionality:
- Same email trigger mechanism
- Same LLM extraction process
- Same output schema
- Same email response templates
