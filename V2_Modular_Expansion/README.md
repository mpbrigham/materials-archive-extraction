# V2: Modular Expansion

## Description
A more expressive and maintainable pipeline where each agent has a specific purpose.

## Workflow Logic
1. Intake Agent listens for incoming material requests.
2. Preprocessing Agent determines OCR quality and structure.
3. Metadata Extraction Agent uses LLMs for JSON generation.
4. Verifier Agent confirms semantic accuracy and field consistency.
5. Responder Agent completes the cycle.

## Inputs
- Structured text, layout-type hints, or scanned/OCR’d text.
- Detected or provided language.
- Filename metadata.

## Outputs
- JSON object with metadata.
- Status flag (e.g., verified, flagged).

## Run Instructions
1. Import the `n8n_workflow.json` file.
2. Serve the `webhook_handler.py` as a test interface.
3. Send simulated supplier PDF input and validate output flow.