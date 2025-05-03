# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## V1_Linear_Flow Commands

- **Run V1 test**: `python V1_Linear_Flow/scripts/testing_script.py`
- **Test single PDF**: `python V1_Linear_Flow/scripts/testing_script.py --samples /path/to/pdf/file.pdf`
- **Start V1 webhook**: `python V1_Linear_Flow/scripts/webhook_handler.py`
- **Process PDF**: `python pdf_ingest/process_pdf.py /path/to/pdf/file.pdf`
- **Start webhook with custom port**: `python V1_Linear_Flow/scripts/webhook_handler.py --port 5001`

## V1_Linear_Flow Structure
- **Agent flow**: Supervisor → Metadata Extractor → Verifier → Response
- **Key files**: functions.js (agent implementations), webhook_handler.py (API), testing_script.py (validation)
- **Schema**: Full schema requires name, brand, category, dimensions; MVS fallback requires only name, dimensions, brand, summary

## Code Style Guidelines

- **Python**: PEP 8, 4-space indentation, docstrings for functions
- **JavaScript**: ES6+ syntax, camelCase, const/let over var
- **Error handling**: Use try/except with specific exceptions, log errors
- **Logging**: Use logging module with INFO/WARNING/ERROR levels
- **Security**: Use secure_filename, validate inputs, sanitize paths
- **Configuration**: Environment variables via dotenv
- **Testing**: Document IDs use "doc-{timestamp}-{sanitized_sender}" format