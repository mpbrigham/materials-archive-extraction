# IMIS V1 Production Deployment Guide - IMAP Email Ingestion

## Overview

This guide provides step-by-step instructions for deploying the Intelligent Materials Intake System (IMIS) V1 pipeline with email ingestion via IMAP. The system processes PDF attachments from emails and extracts materials metadata using multimodal LLMs.

## Architecture

The system uses n8n for workflow orchestration with direct email ingestion:
- Monitors IMAP inbox for new emails with PDF attachments
- Processes PDFs using multimodal LLM extraction
- Sends response emails with extracted metadata

## Prerequisites

- Docker and Docker Compose
- IMAP/SMTP email account for materials intake
- API keys for your chosen LLM provider (OpenAI, Gemini, or Anthropic)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd materials-library-extraction/V1_Linear_Flow
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
docker-compose logs -f n8n
```

### 4. Import and Configure n8n Workflow

1. Access n8n web interface at http://localhost:5678
2. Import the workflow:
   - Click "Import from File"
   - Select `workflow_Materials_Intake_V1.json`
3. Activate the workflow

Note: The workflow uses environment variables directly for email and LLM credentials, so you don't need to manually configure credentials in the n8n interface.

### 5. Verify Deployment

Send a test email with a PDF attachment to your configured IMAP inbox. The system should:
1. Detect the new email
2. Extract the PDF attachment
3. Process it through the LLM pipeline
4. Send a response email with extracted metadata

## Directory Structure

```
V1_Linear_Flow/
├── docker-compose.yml      # n8n deployment configuration
├── .env                    # Environment variables (created from env-template.txt)
├── data/                   # n8n data directory (auto-created by Docker)
│   └── logs/              # Activity logs (auto-created)
├── scripts/               # Core processing functions
│   ├── document_validator.js
│   ├── success_notifier.js
│   └── error_notifier.js
├── prompts/               # LLM prompt templates
│   ├── llm_extraction.txt
│   ├── llm_data_processor.txt
│   └── llm_verifier.txt
├── email_templates/       # Email templates
│   ├── success.txt
│   └── failure.txt
├── workflow_Materials_Intake_V1.json
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
   - Check n8n logs: `docker-compose logs n8n`

2. **LLM API errors**:
   - Verify API key format in .env (see env-template.txt for provider-specific formats)
   - Check API endpoint URL in .env
   - Monitor API quota/limits

3. **Functions not found**:
   - Verify volume mounts in docker-compose.yml
   - Check file permissions on mounted directories
   - Ensure NODE_FUNCTION_ALLOW_BUILTIN=* is set

### Debugging

```bash
# View n8n logs
docker-compose logs -f n8n

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
3. Save to `workflow_Materials_Intake_V1.json`
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