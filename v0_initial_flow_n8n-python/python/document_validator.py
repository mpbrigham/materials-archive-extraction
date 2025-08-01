#!/usr/bin/env python3
"""
Document Validator - Creates initial state object and validates PDF attachments from file paths
"""

import os
from common import log_debug, create_error_response

def create_initial_state(input_data):
    """Create the initial state object from a list of file data objects from n8n"""

    first_item_json = input_data[0].get('json', {})
    
    state = {
        "email_context": {
            "from": first_item_json.get('from'),
            "to": os.environ.get('EMAIL_USER'),
            "subject": first_item_json.get('subject'),
            "messageId": first_item_json.get('metadata', {}).get('message-id', first_item_json.get('messageId')),
            "date": first_item_json.get('date')
        },
        "files": [],
        "errors": []
    }
    
    # Process each file that was written to disk
    for item in input_data:
        item_json = item.get('json', {})
        file_path = item_json.get('fileName') # The 'Write to File' node outputs the path in 'fileName'
        
        if not file_path:
            state['errors'].append({"error": "Received an item with no fileName."})
            continue

        file_name = os.path.basename(file_path)
        
        # Validate that the file exists
        if not os.path.exists(file_path):
            state['files'].append({
                "fileName": file_name,
                "status": "failed",
                "error": f"File not found at path: {file_path}"
            })
            continue

        # Check if it's a PDF by extension
        if file_name.lower().endswith('.pdf'):
            state['files'].append({
                "fileName": file_name,
                "filePath": file_path,
                "status": "pending"
            })
        else:
            # Not a PDF file
            state['files'].append({
                "fileName": file_name,
                "filePath": file_path,
                "status": "failed",
                "error": "Not a PDF file"
            })
            
    # If no valid PDF files were found to process, add a global error
    pdf_count = sum(1 for f in state['files'] if f.get('status') == 'pending')
    if pdf_count == 0:
        state['errors'].append({
            "error": "No valid PDF files were found to process"
        })
    
    return state

def process(input_data):
    """Process file data from n8n's Write Files node and validate attachments"""
    
    try:
        execution_id = os.environ.get('EXECUTION_ID', 'unknown')
        
        # Log input
        log_debug(execution_id, "Document Validator", "input", input_data)
        
        if not isinstance(input_data, list) or not input_data:
            raise ValueError('No input data received from Write Files node')
        
        # Create initial state object from the list of written files
        state = create_initial_state(input_data)
        
        # Log output
        log_debug(execution_id, "Document Validator", "output", state)
        
        # Return a single state object for the next node
        return [{"json": state}]
        
    except Exception as e:
        return create_error_response(e)
