# 🧠 Intelligent Materials Intake System (IMIS)
```
Thousands of prompts, one breath.  
One prompt, a thousand shapes.
```
IMIS is a standardized, agent-based PDF intake pipeline for extracting structured metadata from architectural materials.  
It uses schema-first prompting, modular LLM agents, and n8n for orchestration.

---

## 🌐 Core Concepts

- **Schema-first prompting**: Metadata fields defined before prompt logic  
- **Composable agent flow**: Supervisor → Metadata Extractor → Verifier  
- **Modular design**: Each version represents a unique orchestration strategy  
- **CI-friendly layout**: Prompt files, specs, workflows, and scripts are isolated and versioned  

---

## 📦 Available Pipelines

| Version | Strategy                  | Ideal For                            |
|---------|---------------------------|--------------------------------------|
| [`V1_Linear_Flow`](./V1_Linear_Flow) | Linear simplicity           | Quickstart, minimal setups           |
| [`V1.5_Enhanced_Verification`](./V1.5_Enhanced_Verification) | Multi-turn visual verification | High accuracy, evidence collection    |
| [`V2_Modular_Expansion`](./V2_Modular_Expansion) | Modular agents with explicit flow | Complex intake, scalable deployments |
| [`V3_Intent_Driven_Minimalism`](./V3_Intent_Driven_Minimalism) | Stateless intent-based dispatch | Adaptive pipelines, future extensibility |

Each version contains:
- 🧠 Prompts (`/prompts/`)
- ⚙️ Workflow (`/deployment/workflows/*.json`)
- 📜 Specs & contracts (`/specs/`)
- 🧪 Scripts & handlers (`/scripts/`)

---

## 🚀 Quickstart

```bash
git clone https://github.com/mpbrigham/materials-archive-extraction.git
cd materials-archive-extraction
cp .env.example .env
```

1. Launch your self-hosted n8n instance  
2. Import the corresponding `.json` workflow file  
3. Configure environment variables in `.env`  
4. Start your email intake, webhook, or test PDF trigger  

---

## 📥 n8n Workflow Imports

| Version | Import File |
|---------|-------------|
| V1 | `V1_Linear_Flow/deployment/IMIS_V1_Linear_Flow.n8n.json` |
| V2 | `V2_Modular_Expansion/deployment/workflows/workflow_Materials_Intake_FullFlow.json` |
| V3 | `V3_Intent_Driven_Minimalism/deployment/workflows/n8n_workflow.json` |

---

## 🧭 Architecture Overview

Each pipeline follows a composable flow:

```plaintext
[IMAP/Email/Webhook Input]
        ↓
[Supervisor Agent] — validates & routes
        ↓
[Metadata Extraction Agent] — runs schema-aligned LLM prompt
        ↓
[Verifier Agent] — checks schema integrity
        ↓
[Notification or Response Agent]
```

## 📊 Materials Schema

The system extracts metadata according to a standardized [materials schema](./materials_schema.json) that includes:

- Basic identification (name, brand, category)
- Physical properties (dimensions, weight, texture)
- Performance characteristics (fire rating, acoustic properties)
- Sustainability information (recycled content, EPD)
- Technical resources (BIM, CAD files)
- Application details (indoor/outdoor, project types)

Each pipeline implements confidence policies that may fall back to reduced schema sets when full extraction isn't possible.

---

## 🌬️ Design Zen koan
```
In a whisper, the scroll arrives.
The apprentice reads it with eyes.
The master reads it with silence.

The apprentice asks, “Which field is required?”
The master replies, “The one that is present.”

“How shall I validate truth?”
“Do not chase it. Let structure reveal it.”

“And if it fails?”
The master smiles. “All systems do.
The wise one builds with grace in failure."
```
---

## 🛠 Contributing

- Use `V3_Intent_Driven_Minimalism` as your starting point for new versions  
- Follow the repo's [Prompt Design Guidelines](PROMPT_DESIGN_GUIDELINES.txt) and [Prompt Style Guide](PROMPT_STYLE_GUIDELINES.txt)  
- For questions, file an issue or start a discussion  

---

## 🔗 License

MIT. See [LICENSE.txt](LICENSE.txt)
