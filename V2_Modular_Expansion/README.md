# V2_Linear_Flow Patch

This archive contains the final components for the V2 version of the Materials Intake Pipeline.
This includes all prompts, templates, wiring documentation, and n8n workflow for import.

Pipeline Overview:
- Intake via IMAP
- Supervisor Agent performs initial checks and dispatches to Extraction Agent
- Metadata Extraction Agent uses OCR and LLM to extract structured metadata
- Verifier Agent checks for schema and semantic correctness
- Results emailed back to sender (success/failure templates included)