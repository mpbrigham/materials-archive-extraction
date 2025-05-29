# 🧠 Intelligent Materials Intake System (IMIS) 

A modular, agent-based pipeline for extracting structured metadata from architectural materials PDFs using LLMs. Uses schema-first prompting and n8n for orchestration.

## 🌐 Project Vision

IMIS automates extraction, structuring, and validation of metadata from architectural material supplier PDFs. The repository presents evolutionary approaches from initial implementation to advanced modular systems.

## 📦 Available Pipelines

| Version | Strategy | Ideal For |
|---------|----------|-----------|
| [`v0_initial_flow`](./v0_initial_flow) | Email-to-extraction pipeline | Email-based intake, production ready |
| [`v1_linear_flow`](./v1_linear_flow) | Linear simplicity | Quickstart, minimal setups |
| [`v1.5_enhanced_verification`](./v1.5_enhanced_verification) | Multi-turn visual verification | High accuracy, evidence collection |
| [`v2_modular_expansion`](./v2_modular_expansion) | Modular agents with explicit flow | Complex intake, scalable deployments |
| [`v3_intent_driven_minimalism`](./v3_intent_driven_minimalism) | Stateless intent-based dispatch | Adaptive pipelines, future extensibility |

Each version contains:
- Prompts (`/prompts/`)
- Workflow definitions (`*.json`)
- Schema contracts (`/schema/`)
- Email templates (`/email_templates/`)
- Deployment configuration

## 🚀 Getting Started

### V0 Initial Flow (Recommended)

**Email-based materials extraction pipeline with automated CI/CD deployment.**

#### Requirements
- Docker & Docker Compose
- Email provider (Gmail/IMAP/SMTP)
- Google Gemini API key
- Git repository with GitHub Actions enabled

#### Quick Setup
```bash
# Clone and navigate
git clone https://github.com/mpbrigham/materials-archive-extraction.git
cd materials-archive-extraction/v0_initial_flow

# Configure environment
cp .env.template .env
# Edit .env with your credentials

# Launch locally
docker compose up -d

# Open n8n at http://localhost:5678
# Import materials_archive_extraction.json
# Configure IMAP/SMTP credentials
# Activate workflow
```

#### Production Deployment
- **Automatic**: Push to `v0_initial_flow` branch triggers CI/CD deployment
- **Manual**: See [V0 Deployment Guide](./v0_initial_flow/DEPLOYMENT.md)

### Other Versions

For webhook-based or modular approaches:

```bash
# V1 Linear Flow
cd v1_linear_flow/
python scripts/webhook_handler.py

# V2+ workflows available in respective directories
```

## 🧭 Architecture

### V0 Initial Flow
```
Email Trigger → Document Validator → LLM Extraction → Result Processor → Send Notification
```

### Other Pipelines
```
[Input] → [Supervisor] → [Extraction] → [Verification] → [Response]
```

The system extracts metadata according to a standardized [schema](./specs/MATERIALS_SCHEMA.json) including:
- Basic identification (name, brand, category)
- Physical properties (dimensions, weight, texture)
- Performance characteristics (fire rating, acoustic properties)
- Sustainability information (recycled content, EPD)
- Technical resources (BIM, CAD files)

Each pipeline implements confidence policies with fallback mechanisms.

## 🔄 CI/CD Integration

### Branch-Specific Deployment
- **`v0_initial_flow`** → Automatic deployment to production
- Other branches can have their own CI/CD workflows added

### Workflow Features
- Schema validation on every commit
- Automated deployment with environment variable injection
- Single Docker Compose file approach
- Health checks and rollback capabilities

## 🛠 Contributing

We welcome thoughtful contributions that follow these principles:

1. **Design with Intent**
   - Match the clarity and minimalism of existing prompts and workflows
   - Include purpose and expected behavior in any new agent or prompt

2. **Structure Prompts Consistently**
   - Follow the [Prompt Design](./guidelines/prompt_design_guidelines.txt) and [Style Guidelines](./guidelines/prompt_style_guidelines.txt)

3. **Validate Before Committing**
   - Test workflows in n8n with placeholder data
   - Validate all JSON outputs against the schema
   - Branch-specific testing ensures isolation

## 🔗 License

MIT. See [LICENSE.txt](LICENSE.txt)
