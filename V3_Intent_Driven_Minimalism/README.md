# V3: Intent-Driven Minimalism

## Description
A refined, state-aware system where agents react to document state and intent rather than a fixed order.

## Workflow Logic
1. Intake Agent determines file nature and initializes a state.
2. Interpreter Agent handles layout recognition + LLM extraction.
3. Verifier Agent inspects field-level logic and integrity.
4. Outbound Agent dispatches output or raises flags.

## Inputs
- `MaterialExtractionRequest`: includes language, filename, extracted text, and document metadata.

## Outputs
- JSON metadata conforming to schema.
- Confidence envelope (optional).
- State marker (`interpreted`, `verified`, `flagged`, etc.)

## Run Instructions
1. Import `n8n_workflow.json` into your n8n instance.
2. Start `webhook_handler.py`.
3. Feed test materials and track document states through the pipeline.