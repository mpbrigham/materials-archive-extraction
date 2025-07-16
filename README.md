# 🧠 Intelligent Materials Intake System (IMIS) 

A modular, agent-based pipeline for extracting structured metadata from architectural materials PDFs using LLMs. Available in both n8n and ActivePieces implementations.

## 🌐 Project Vision

IMIS automates extraction, structuring, and validation of metadata from architectural material supplier PDFs. The repository presents evolutionary approaches from initial implementation to advanced modular systems.

## 📦 Available Pipelines

| Version | Implementation | Strategy | Ideal For |
|---------|---------------|----------|-----------|
| [`v0_initial_flow`](./v0_initial_flow) | n8n | Email-to-extraction pipeline | Email-based intake, production ready |
| [`v0_initial_flow_ap`](./v0_initial_flow_ap) | ActivePieces | Email-to-extraction pipeline | Alternative to n8n, same functionality |
| [`v1_linear_flow`](./v1_linear_flow) | n8n | Linear simplicity | Quickstart, minimal setups |
| [`v1.5_enhanced_verification`](./v1.5_enhanced_verification) | n8n | Multi-turn visual verification | High accuracy, evidence collection |
| [`v2_modular_expansion`](./v2_modular_expansion) | n8n | Modular agents with explicit flow | Complex intake, scalable deployments |
| [`v3_intent_driven_minimalism`](./v3_intent_driven_minimalism) | n8n | Stateless intent-based dispatch | Adaptive pipelines, future extensibility |

Each version contains:
- Prompts (`/prompts/`)
- Workflow definitions (`*.json`)
- Schema contracts (`/schema/`)
- Email templates (`/email_templates/`)
- Deployment configuration

## 🚀 Getting Started

### V0 Initial Flow - Choose Your Platform

We offer the same email-based extraction pipeline in two workflow automation platforms:

#### n8n Implementation (Original)

```bash
# Navigate to n8n version
cd v0_initial_flow

# Configure environment
cp .env.template .env
# Edit .env with your credentials

# Launch locally
docker compose up -d

# Open n8n at http://localhost:5678
```

#### ActivePieces Implementation (Alternative)

```bash
# Navigate to ActivePieces version
cd v0_initial_flow_ap

# Configure environment
cp .env.template .env
# Edit .env with your credentials

# Launch locally
docker compose up -d

# Open ActivePieces at http://localhost:5679
```

Both implementations provide the same functionality:
- Email trigger with PDF attachments
- Gemini AI extraction
- Structured results emailed back

### Production Deployment

**Automated CI/CD with Path-Based Triggers:**
- Changes to `v0_initial_flow/` → Deploy n8n version
- Changes to `v0_initial_flow_ap/` → Deploy ActivePieces version
- Single GitHub Actions workflow handles both

```bash
# Deploy n8n version
git add v0_initial_flow/
git commit -m "Update n8n workflow"
git push origin v0_initial_flow

# Deploy ActivePieces version
git add v0_initial_flow_ap/
git commit -m "Update ActivePieces workflow"
git push origin v0_initial_flow
```

See deployment guides:
- [n8n Deployment](./v0_initial_flow/DEPLOYMENT.md)
- [ActivePieces Deployment](./v0_initial_flow_ap/DEPLOYMENT.md)

### Other Versions

For webhook-based or modular approaches:

```bash
# V1 Linear Flow
cd v1_linear_flow/
python scripts/webhook_handler.py

# V2+ workflows available in respective directories
```

## 🧭 Architecture

### V0 Initial Flow (Both Implementations)
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

### Unified Deployment Strategy
- **Single workflow** handles both n8n and ActivePieces deployments
- **Path-based triggers** detect which implementation changed
- **Independent deployments** - each platform deploys separately
- **Shared resources** - prompts and schemas can be symlinked

### GitHub Actions Workflow
```yaml
on:
  push:
    branches: [v0_initial_flow]
    paths:
      - 'v0_initial_flow/**'      # Triggers n8n deployment
      - 'v0_initial_flow_ap/**'   # Triggers ActivePieces deployment
```

### Required GitHub Secrets
- `DEPLOY_HOST` - Production server IP
- `DEPLOY_SSH_KEY` - SSH deployment key
- `EMAIL_USER`, `EMAIL_PASS` - Email credentials
- `LLM_API_KEY`, `LLM_MODEL` - Gemini configuration
- `N8N_ENCRYPTION_KEY` - n8n specific

## 🛠 Contributing

We welcome thoughtful contributions that follow these principles:

1. **Design with Intent**
   - Match the clarity and minimalism of existing prompts and workflows
   - Include purpose and expected behavior in any new agent or prompt

2. **Structure Prompts Consistently**
   - Follow the [Prompt Design](./guidelines/prompt_design_guidelines.txt) and [Style Guidelines](./guidelines/prompt_style_guidelines.txt)

3. **Validate Before Committing**
   - Test workflows with placeholder data
   - Validate all JSON outputs against the schema
   - Test both n8n and ActivePieces implementations if relevant

4. **Platform Parity**
   - When updating v0, consider updating both implementations
   - Document any platform-specific differences

## 🔗 License

MIT. See [LICENSE.txt](LICENSE.txt)
