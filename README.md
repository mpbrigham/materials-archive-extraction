# Intelligent Materials Intake System (IMIS)

> “Thousands of prompts, one breath.  
> One prompt, a thousand shapes.”

IMIS is a standardized LLM-powered PDF intake pipeline for architectural materials.  
It transforms unstructured supplier documents into structured metadata using schema-first prompts, modular LLM agents, and orchestrated workflows built in n8n.

---

## 🧭 Pipeline Versions

| Version | Design Philosophy         | Ideal For                    |
|---------|---------------------------|------------------------------|
| V1      | Linear simplicity          | Quickstart, minimal flows    |
| V2      | Modular orchestration      | Scalable workflows, separation of concerns |
| V3      | Intent-driven minimalism   | AGI-aligned, adaptive agents |

Each version includes:
- 🧠 Agent prompt (`AGENT_PROMPT.txt`)
- ⚙️  n8n workflow (`n8n_workflow.json`)
- 🌐 Webhook scaffold (`webhook_handler.py`)
- 📖 Version-specific `README.md`

---

## 🚀 Getting Started

1. Clone the repository  
2. Read [`GETTING_STARTED.txt`](GETTING_STARTED.txt) for install and usage  
3. Import workflows into n8n and run Python webhook handlers  
4. Feed PDF/OCR samples and inspect structured JSON results

Each pipeline version includes a ready-to-run n8n workflow as a `.json` file. To import and run one:

1. Open your n8n instance (self-hosted or cloud).
2. Click the **menu icon** → `Import workflow`.
3. Upload the corresponding JSON file from the table below.
4. Ensure `.env.example` is copied to `.env`, and all environment variables are configured.
5. Deploy and test with a sample PDF email.

| Pipeline Version              | Workflow Import File Path                                      |
|------------------------------|----------------------------------------------------------------|
| `V1_Linear_Flow`             | `V1_Linear_Flow/deployment/IMIS_V1_Linear_Flow.n8n.json`       |
| `V2_Modular_Expansion`       | `V2_Modular_Expansion/deployment/workflows/workflow_Materials_Intake_FullFlow.json` |
| `V3_Intent_Driven_Minimalism`| `V3_Intent_Driven_Minimalism/deployment/workflows/n8n_workflow.json` |

💡 Each version includes its own `deployment/DEPLOYMENT.md` file with additional guidance.


---

## 🧘 Philosophy

This is not just a repo. It is a lineage of intelligent, modular pipelines—  
structured to scale, teach, and breathe clarity into the flow of information.

Designed with:
- Schema-first prompts
- Layout-aware extraction
- Clear agent responsibilities
- Resilience through graceful fallback
- Traceability, observability, elegance

---

## 🛠 Built With

- [n8n](https://n8n.io) – Open-source workflow automation
- Python (Flask) – Lightweight webhook interface
- LLMs (OpenAI, Gemini, Claude-compatible) – Schema-bound JSON extraction

---

---

## 🧘 Guiding Koan

> A supplier sends a PDF.  
> The apprentice reads it with eyes.  
> The master reads it with silence.  
>
> The apprentice asks, “Which field is required?”  
> The master replies, “The one that is present.”  
>
> “How shall I validate truth?”  
> “Do not chase it. Let structure reveal it.”  
>
> “And if it fails?”  
> The master smiles. “All systems do.  
> The wise one builds with grace in failure.”

## 📦 Release v1.0.0

Production-ready.  
Includes all documentation, prompts, guidelines, and validation logic.

See [`RELEASE_NOTES.txt`](RELEASE_NOTES.txt)

---

## 🤝 Contributing

See [`CONTRIBUTING.txt`](CONTRIBUTING.txt)  
All contributions should honor the clarity, conciseness, and tone of the existing lineage.

---

## 📜 License

MIT License — see [`LICENSE.txt`](LICENSE.txt)---

## 🖼 Vision Pipeline Integration

This system supports automated ingestion of real-world PDFs using the Gemini Vision API.

See `pdf_ingest/process_pdf.py` for a command-line tool that:
1. Encodes a supplier PDF
2. Calls Gemini Vision
3. Extracts layout-aware text for downstream processing

Use the text output as input to any of the `AGENT_PROMPT.txt` extraction workflows in V1–V3.

---

## 🧪 Samples

See [`samples/`](samples/) for example PDF files and expected structured output.
