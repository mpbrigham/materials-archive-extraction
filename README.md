# 🧠 Intelligent Materials Intake System (IMIS)

A modular, agent-based pipeline for extracting structured metadata from architectural materials PDFs using LLMs. Uses schema-first prompting and n8n for orchestration.

## 🌐 Project Vision

IMIS automates extraction, structuring, and validation of metadata from architectural material supplier PDFs. The repository presents three evolutionary approaches:
- V1: Linear logic, fast to implement
- V2: Modular expansion, highly expressive
- V3: Intent-driven minimalism, future-aligned

## 📦 Available Pipelines

| Version | Strategy | Ideal For |
|---------|----------|-----------|
| [`V1_Linear_Flow`](./V1_Linear_Flow) | Linear simplicity | Quickstart, minimal setups |
| [`V1.5_Enhanced_Verification`](./V1.5_Enhanced_Verification) | Multi-turn visual verification | High accuracy, evidence collection |
| [`V2_Modular_Expansion`](./V2_Modular_Expansion) | Modular agents with explicit flow | Complex intake, scalable deployments |
| [`V3_Intent_Driven_Minimalism`](./V3_Intent_Driven_Minimalism) | Stateless intent-based dispatch | Adaptive pipelines, future extensibility |

Each version contains:
- Prompts (`/prompts/`)
- Workflow (`/deployment/workflows/*.json`)
- Specs & contracts (`/specs/`)
- Scripts & handlers (`/scripts/`)

## 🚀 Getting Started

### Requirements
- n8n (https://n8n.io) running locally or in Docker
- Python 3.x with Flask installed
- This repository cloned locally

### Quickstart
```bash
# Install dependencies
pip install flask

# Start webhook server
cd V1_Linear_Flow/
python scripts/webhook_handler.py

# In another terminal:
cd ..
```

1. Open n8n
2. Import the workflow file from your chosen version:
   - V1: `V1_Linear_Flow/deployment/workflow_Materials_Intake_V1.json`
   - V2: `V2_Modular_Expansion/deployment/workflow_Materials_Intake_V2.json`
   - V3: `V3_Intent_Driven_Minimalism/deployment/workflow_Materials_Intake_V3.json`
3. Configure environment variables
4. Test with sample PDFs from the `samples/` directory

### Production Deployment

For detailed instructions on deploying to a production environment, see:
- [V1 Deployment Guide](./V1_Linear_Flow/deployment/DEPLOYMENT.md) - Complete setup with n8n, webhook handlers, monitoring, and scaling strategies

## 🧭 Architecture

Each pipeline follows a composable flow:
```
[Input] → [Supervisor] → [Extraction] → [Verification] → [Response]
```

The system extracts metadata according to a standardized [schema](./materials_schema.json) including:
- Basic identification (name, brand, category)
- Physical properties (dimensions, weight, texture)
- Performance characteristics (fire rating, acoustic properties)
- Sustainability information (recycled content, EPD)
- Technical resources (BIM, CAD files)

Each pipeline implements confidence policies with fallback mechanisms.

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

## 🔗 License

MIT. See [LICENSE.txt](LICENSE.txt)