#!/usr/bin/env python3
"""
Document Validator - Creates initial state object and validates PDF attachments from base64 array
"""

import os
import base64  # For optional decoding/size check
from common import log_debug, create_error_response

def create_initial_state(input_data):
    """Create the initial state object from input JSON"""
    email_context = input_data.get('email_context', {})
    attachments = input_data.get('attachments', [])
    files = []
    for attachment in attachments:
        file_name = attachment.get('fileName')
        mime_type = attachment.get('mimeType', '')
        data = attachment.get('data')
        if not data:
            files.append({
                "fileName": file_name,
                "status": "failed",
                "error": "Missing data"
            })
            continue
        # Validate MIME/extension (prioritize MIME)
        if mime_type != 'application/pdf' and not file_name.lower().endswith('.pdf'):
            files.append({
                "fileName": file_name,
                "status": "failed",
                "error": "Not a PDF file"
            })
            continue
        # Optional: Check base64 validity and size (~4MB decoded limit)
        try:
            pdf_bytes = base64.b64decode(data)
            if len(pdf_bytes) > 4 * 1024 * 1024:
                files.append({
                    "fileName": file_name,
                    "status": "failed",
                    "error": "PDF too large (>4MB)"
                })
                continue
        except base64.binascii.Error:
            files.append({
                "fileName": file_name,
                "status": "failed",
                "error": "Invalid base64 data"
            })
            continue
        files.append({
            "fileName": file_name,
            "mimeType": mime_type,
            "data": data,  # Keep base64 for state
            "status": "pending"
        })
    errors = []
    if not any(f["status"] == "pending" for f in files):
        errors.append({"error": "No valid PDF files found"})
    return {"email_context": email_context, "files": files, "errors": errors}

def process(input_data):
    """Process input JSON and validate attachments"""
    execution_id = os.environ.get('EXECUTION_ID', 'unknown')
    log_input = input_data.copy()
    if 'attachments' in log_input:
        log_input['attachments'] = [{"fileName": a['fileName'], "mimeType": a['mimeType']} for a in log_input['attachments']]
    log_debug(execution_id, "Document Validator", "input", log_input)
    try:
        state = create_initial_state(input_data)
        log_debug(execution_id, "Document Validator", "output", state)
        return [{"json": state}]
    except Exception as e:
        return create_error_response(e)
