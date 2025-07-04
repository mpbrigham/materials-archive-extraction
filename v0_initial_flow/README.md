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

### Development
1. Copy `.env.template` to `.env` and add credentials
2. `docker compose up -d`
3. Open http://localhost:5678
4. Import workflow and configure credentials manually (one-time setup)
5. Test with sample email + PDFs
6. Export everything: `docker exec v0_initial_flow-n8n-1 n8n export:credentials --all --output=/home/node/import/credentials.json`
7. Export workflow: `docker exec v0_initial_flow-n8n-1 n8n export:workflow --id=WORKFLOW_ID --output=/home/node/import/workflows.json`

### Production Deployment via CI/CD

The project uses GitHub Actions with an **export/import pattern** for automated deployment:

**Deployment Strategy:**
- Export credentials and workflows from working development environment
- Store exported files in `import/` folder in Git
- CI/CD imports both credentials and workflows to production
- Preserves UUIDs and credential relationships automatically

**Required GitHub Secrets:**
- `DEPLOY_HOST` - Production server address
- `DEPLOY_SSH_KEY` - SSH private key for deployment user
- `EMAIL_USER` - Email account for IMAP/SMTP
- `EMAIL_PASS` - Email password/app password  
- `LLM_API_KEY` - Gemini AI API key

**Deployment Process:**
1. Push to `v0_initial_flow` branch triggers deployment
2. Server pulls latest code including updated `import/` files
3. Deploys Docker containers with environment variables
4. Imports credentials: `n8n import:credentials --input=/home/node/import/credentials.json`
5. Imports workflows: `n8n import:workflow --input=/home/node/import/workflows.json`
6. Workflow ready to process emails

## Files

```
.
├── import/
│   ├── credentials.json                     # Exported n8n credentials
│   └── workflows.json                       # Exported n8n workflow
├── docker-compose.yml                       # Development/Production setup
├── DEPLOYMENT.md                            # Setup guide
├── prompts/llm_extraction.txt               # LLM prompt
├── schema/materials_schema.json             # Data structure definition
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

## CI/CD Monitoring

**GitHub Actions Dashboard:** Check workflow status in repository's Actions tab

**Health Checks:**
- Production: `curl -f http://localhost:5678/healthz`
- Logs: `docker compose logs -f`

**Updating Workflows:**
1. Make changes in local n8n development environment
2. Test thoroughly with sample emails
3. Export updated files:
   ```bash
   docker exec v0_initial_flow-n8n-1 n8n export:credentials --all --output=/home/node/import/credentials.json
   docker exec v0_initial_flow-n8n-1 n8n export:workflow --id=WORKFLOW_ID --output=/home/node/import/workflows.json
   ```
4. Commit and push to `v0_initial_flow` branch
5. Deployment automatically imports updated workflow

## PROJECT_SPEC
```spec
NAME: Materials Library Extraction Pipeline
DOMAIN: Document Processing Automation
PRIMARY_TOOLS: n8n, Gemini AI, Node.js, IMAP/SMTP, Docker, GitHub Actions
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
- `.github/workflows/v0-ci-cd.yml`: CI/CD pipeline
- `docker-compose.prod.yml`: Production deployment
DATA_STRUCTURE:
- Email context: single item with email metadata
- PDF items: clean processing items without duplication
- Results: structured HTML tables with metadata
DESIGN_CONSTRAINTS:
- Export/import deployment pattern for credentials and workflows
- Results sent back to original email sender only
- Header table: supplier, product_name, sku_number, source_file
- Data table: all other extracted fields
- Must handle multiple PDFs per email
- Must gracefully handle extraction failures
- Preserves UUID relationships via n8n export/import
- Automated CI/CD deployment via GitHub Actions
- Container-based production deployment
```
