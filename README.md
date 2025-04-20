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

---

## 📂 Repository Structure

```
.
├── V1_Linear_Flow/
├── V2_Modular_Expansion/
├── V3_Intent_Driven_Minimalism/
├── AGENT_PROMPT.txt (each version)
├── n8n_workflow.json
├── webhook_handler.py
├── README.md (per version)
├── GETTING_STARTED.txt
├── PROJECT_VISION.txt
├── CONTRIBUTING.txt
├── LICENSE.txt
├── PROMPT_DESIGN_GUIDELINES.txt
├── PROMPT_STYLE_GUIDELINES.txt
├── OBSERVER_ECHO.txt
├── RELEASE_NOTES.txt
├── REPOSITORY_METADATA.txt
```

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