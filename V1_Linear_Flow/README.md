# V1: Linear Flow

## Description
This version represents the simplest pipeline: a straight-line flow of agents that receive input, extract metadata, verify it, and return results.

## Workflow Logic
1. Supervisor Agent receives and validates the PDF input.
2. Metadata Extraction Agent uses the prompt to extract structured JSON.
3. Verifier Agent checks for schema conformity and required fields.
4. Supervisor Response Agent returns the metadata.

## Inputs
- OCR or extracted text from a single supplier PDF.
- Source file name.

## Outputs
- A JSON object conforming to the schema.
- Optional debug log.

## Run Instructions
1. Import `n8n_workflow.json` into n8n.
2. Start the `webhook_handler.py` with Flask to receive test data.
3. Send a sample PDF or OCR data to the intake webhook.