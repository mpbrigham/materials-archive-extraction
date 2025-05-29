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
4. Import `materials_archive_extraction.json`
5. Configure IMAP/SMTP credentials
6. Activate workflow

### Production Deployment via CI/CD

The project uses GitHub Actions for automated CI/CD deployment:

**Branches:**
- `develop` → Deploys to staging environment
- `main` → Deploys to production environment

**CI/CD Pipeline:**
1. **Test Phase**: Validates JSON files, prompt templates, and test scripts
2. **Build Phase**: Creates Docker image and pushes to GitHub Container Registry
3. **Deploy Phase**: Automatically deploys to production server

**Required GitHub Secrets:**
- `DEPLOY_HOST` - Production server address
- `DEPLOY_SSH_KEY` - SSH private key for deployment user
- `DEPLOY_SSH_USER` - SSH username (default: deploy)

**Production Server Setup:**
```bash
# Create deployment directory
sudo mkdir -p /opt/materials-extraction/V0_Initial_Flow
sudo chown deploy:deploy /opt/materials-extraction/V0_Initial_Flow

# Clone repository
cd /opt/materials-extraction
git clone <repository-url> .

# Setup environment
cd V0_Initial_Flow
cp .env.template .env
# Edit .env with production credentials

# Create data directory
mkdir -p data
```

**Manual Production Deployment:**
```bash
# On production server
cd /opt/materials-extraction/V0_Initial_Flow
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## Files

```
.
├── materials_archive_extraction.json        # n8n workflow
├── docker-compose.yml                       # Development setup
├── docker-compose.prod.yml                  # Production setup
├── Dockerfile                               # Custom n8n image
├── DEPLOYMENT.md                            # Setup guide
├── prompts/llm_extraction.txt               # LLM prompt
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
- Logs: `docker compose -f docker-compose.prod.yml logs -f`

**Rollback:**
```bash
# On production server - rollback to previous image
docker compose -f docker-compose.prod.yml down
docker image rm ghcr.io/materiatek/materials-library-extraction/v0-initial-flow:latest
docker compose -f docker-compose.prod.yml up -d
```

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
- Results sent back to original email sender only
- Header table: supplier, product_name, sku_number, source_file
- Data table: all other extracted fields
- Must handle multiple PDFs per email
- Must gracefully handle extraction failures
- Symmetric structure: email context separate from PDF processing
- Automated CI/CD deployment via GitHub Actions
- Container-based production deployment
```
