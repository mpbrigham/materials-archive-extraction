#!/usr/bin/env python3
"""
Document Validator - Creates initial state object and validates PDF attachments
"""

import os
from common import log_debug, create_error_response

def create_initial_state(email_data):
    """Create the initial state object from email data"""
    
    state = {
        "email_context": {
            "from": email_data.get('from'),
            "to": os.environ.get('EMAIL_USER'),  # Add bot's email
            "subject": email_data.get('subject'),
            "messageId": email_data.get('metadata', {}).get('message-id', email_data.get('messageId')),
            "date": email_data.get('date')
        },
        "files": [],
        "errors": []
    }
    
    # Process attachments
    attachments = email_data.get('attachments', [])
    
    for attachment in attachments:
        mime_type = attachment.get('mimeType', '')
        file_name = attachment.get('fileName', '')
        file_path = attachment.get('filePath', '')
        
        # Check if it's a PDF
        is_pdf = mime_type == 'application/pdf' or file_name.lower().endswith('.pdf')
        
        if is_pdf:
            if file_path and os.path.exists(file_path):
                # Valid PDF file
                state['files'].append({
                    "fileName": file_name,
                    "filePath": file_path,
                    "mimeType": mime_type,
                    "status": "pending"
                })
            else:
                # PDF file not found
                state['files'].append({
                    "fileName": file_name,
                    "filePath": file_path,
                    "status": "failed",
                    "error": f'PDF file not found at path: {file_path}'
                })
        else:
            # Not a PDF file
            state['files'].append({
                "fileName": file_name,
                "filePath": file_path,
                "mimeType": mime_type,
                "status": "failed",
                "error": "Not a PDF file"
            })
    
    # If no PDF files found, add a global error
    pdf_count = sum(1 for f in state['files'] if f.get('mimeType', '').lower().startswith('application/pdf') or f.get('fileName', '').lower().endswith('.pdf'))
    if pdf_count == 0:
        state['errors'].append({
            "error": "No PDF attachments found in the email"
        })
    
    return state

def process(input_data):
    """Process email data and validate attachments"""
    
    try:
        execution_id = os.environ.get('EXECUTION_ID', 'unknown')
        
        # Log input
        log_debug(execution_id, "Document Validator", "input", input_data)
        
        # Extract email data (should be first item from Email Trigger)
        if not input_data or len(input_data) == 0:
            raise ValueError('No input data received from Email Trigger')
        
        email_item = input_data[0]
        email_data = email_item.get('json', {})
        
        # Validate required email fields
        if not email_data.get('from'):
            raise ValueError('Email missing required "from" field. Cannot process email without sender information.')
        
        # Create initial state object
        state = create_initial_state(email_data)
        
        # Log output
        log_debug(execution_id, "Document Validator", "output", state)
        
        # Return state
        return [{"json": state}]
        
    except Exception as e:
        return create_error_response(e)
