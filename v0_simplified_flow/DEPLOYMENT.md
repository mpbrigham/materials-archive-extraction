# IMIS V0 Production Deployment Guide - IMAP Email Ingestion

## Overview

This guide provides step-by-step instructions for deploying the Intelligent Materials Intake System (IMIS) V0 pipeline with email ingestion via IMAP. The system processes PDF attachments from emails and extracts materials metadata using multimodal LLMs.

## Architecture

The system uses n8n for workflow orchestration with direct email ingestion:
- Monitors IMAP inbox for new emails with PDF attachments
- Processes PDFs using multimodal LLM extraction with integrated confidence-based processing
- Sends response emails with extracted metadata

## Prerequisites

- Docker and Docker Compose
- IMAP/SMTP email account for materials intake
- API keys for your chosen LLM provider (OpenAI, Gemini, or Anthropic)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd materials-library-extraction/V0_Simplified_Flow
```

### 2. Configure Environment Variables

Copy the provided environment template and update with your values:

```bash
cp env-template.txt .env
nano .env  # or use any text editor
```

Required environment variables:
- Email: `IMAP_HOST`, `IMAP_PORT`, `SMTP_HOST`, `SMTP_PORT`, `EMAIL_USER`, `EMAIL_PASS`
- LLM: `LLM_API_KEY` and `LLM_API_ENDPOINT` (Gemini 2.0 Flash for both text and vision)

### 3. Deploy with Docker Compose

```bash
# Start n8n (this automatically creates the data directory)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Import and Configure n8n Workflow

1. Access n8n web interface at http://localhost:5678
2. Import the workflow:
   - Click "Import from File"
   - Select `workflow_Materials_Intake_V0.json`
3. Configure Email credentials:
   - Click on the Email Trigger node
   - Create new IMAP Email credentials with your .env values
   - Enter these manually (not as expressions for the first setup)
4. Activate the workflow

### 5. Verify Deployment

Send a test email with a PDF attachment to your configured IMAP inbox. The system should:
1. Detect the new email
2. Extract the PDF attachment
3. Process it through the streamlined LLM pipeline
4. Send a response email with extracted metadata

## Directory Structure

```
V0_Simplified_Flow/
├── docker-compose.yml      # n8n deployment configuration
├── .env                    # Environment variables (created from env-template.txt)
├── data/                   # n8n data directory (auto-created by Docker)
│   └── logs/              # Activity logs (auto-created)
├── scripts/               # Core processing functions
│   ├── document_validator.js
│   └── result_processor.js
├── prompts/               # LLM prompt templates
│   └── llm_extraction.txt     # Integrated extraction and processing prompt
├── email_templates/       # Email templates
│   ├── success.txt
│   └── failure.txt
├── workflow_Materials_Intake_V0.json
├── DEPLOYMENT.md
└── env-template.txt
```

Note: The `data/` directory and its subdirectories are automatically created by Docker when the container starts. You don't need to create them manually.

## Volume Mounts

The Docker Compose configuration mounts these directories:
- `./data:/home/node/data` - n8n data persistence (directory auto-created)
- `./scripts:/home/node/scripts:ro` - Processing functions (read-only)
- `./prompts:/home/node/prompts:ro` - LLM prompts (read-only)
- `./email_templates:/home/node/email_templates:ro` - Email templates (read-only)

## Workflow Implementation Details

### Node Types

The streamlined workflow uses Code nodes for better reliability and performance:

1. **Document Validator** (Code Node):
   - Processes incoming emails
   - Validates PDF attachments
   - Builds structured metadata for extraction

2. **LLM Extraction** (HTTP Request Node):
   - Calls the LLM API with the PDF document
   - Processes multimodal extraction with integrated confidence-based processing
   - Standardizes output format for single/multiple products

3. **Result Processor** (Code Node):
   - Consolidates validation routing and email formatting
   - Handles both success and error scenarios
   - Groups multi-attachment results for unified notification

4. **Activity Logger** (Code Node):
   - Logs document lifecycle events to persistent storage
   - Creates structured audit trail of all processing

### Processing Improvements

The streamlined workflow provides these advantages:
- Single LLM API call with integrated processing for efficiency
- Consolidated success/error routing in Result Processor
- Better error handling with try/catch blocks
- Consistent handling of input/output formats
- Template-based email formatting

## Monitoring and Maintenance

### Activity Logs

Document lifecycle logs are stored in `./data/logs/document_lifecycle.json` (directory auto-created by Docker on first run)

### n8n Monitoring

- Access execution history in n8n UI
- Monitor workflow status and errors
- Check email trigger for connection issues

### Backup Strategy

Regular backups recommended for:
- `./data/` directory (n8n credentials and executions)
- `.env` file (configuration)
- Any workflow modifications exported from n8n

## Troubleshooting

### Common Issues

1. **Email trigger not working**:
   - Check IMAP credentials (EMAIL_USER/EMAIL_PASS)
   - Verify firewall allows IMAP connections
   - Check n8n logs: `docker-compose logs -f`

2. **LLM API errors**:
   - Verify API key format in .env (see env-template.txt for provider-specific formats)
   - Check API endpoint URL in .env
   - Monitor API quota/limits

3. **"Cannot read properties of undefined" errors**:
   - These typically occur during testing when data is missing
   - Use actual email inputs rather than manual testing

4. **Docker-compose configuration issues**:
   - If you encounter Redis connection errors with the default docker-compose.yml
   - Create a simplified configuration in docker-compose-simple.yml without Redis:
     ```yaml
     version: '3'
     services:
       n8n:
         image: n8nio/n8n
         ports:
           - "5678:5678"
         environment:
           - N8N_BASIC_AUTH_ACTIVE=false
           - N8N_HOST=0.0.0.0
           - N8N_PORT=5678
           - DB_TYPE=sqlite
           - DB_SQLITE_DATABASE=/home/node/data/database.sqlite
         volumes:
           - ./data:/home/node/data
           - ./scripts:/home/node/scripts:ro
           - ./prompts:/home/node/prompts:ro
           - ./email_templates:/home/node/email_templates:ro
         env_file:
           - .env
     ```
     Then run:
     ```
     docker-compose -f docker-compose-simple.yml up -d
     ```

### Debugging

```bash
# View n8n logs
docker-compose logs -f

# Access n8n container
docker-compose exec n8n sh

# Check mounted files
docker-compose exec n8n ls -la /home/node/scripts
docker-compose exec n8n ls -la /home/node/prompts
```

## Maintenance

### Updating Functions or Prompts

1. Edit files in `scripts/` or `prompts/` directories
2. Changes take effect immediately (read on each execution)
3. No need to restart n8n or modify workflow

### Updating Email Templates

1. Edit files in `email_templates/` directory:
   - `success.txt`: Template for successful extraction emails
   - `failure.txt`: Template for error notification emails
2. Changes take effect immediately (templates loaded on each execution)
3. Use placeholders like `{{sender}}`, `{{productCount}}` in templates

### Updating the Workflow

1. Make changes in n8n UI
2. Export the workflow
3. Save to `workflow_Materials_Intake_V0.json`
4. Commit to version control

## Security Considerations

1. Use strong passwords for email accounts
2. Rotate API keys regularly
3. Keep credentials in .env file (not in version control)
4. Use read-only mounts for code directories
5. Regular security updates for Docker images

## Support

- Check logs in `./data/logs/` for activity history
- Review n8n execution history for detailed error messages
- Refer to prompt files for LLM interaction details