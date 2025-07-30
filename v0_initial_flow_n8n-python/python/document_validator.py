#!/usr/bin/env python3
"""
Document Validator - Creates initial state object and validates PDF attachments
"""

import json
import sys
import os
from datetime import datetime

def log_debug(execution_id, node_name, phase, data):
    """Log debug information to file"""
    
    log_entry = {
        "timestamp": datetime.now(datetime.UTC).isoformat(),
        "executionId": execution_id,
        "node": node_name,
        "phase": phase,
        "data": data
    }
    with open('/home/node/data/debug.log', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def parse_n8n_input(input_data):
    """Parse input that may be wrapped by n8n's Execute Command node"""
    
    # If input is a string, parse it
    if isinstance(input_data, str):
        input_data = json.loads(input_data)
    
    # If it's a single item with n8n wrapper structure
    if (len(input_data) == 1 and 
        isinstance(input_data[0], dict) and 
        'json' in input_data[0] and 
        'stdout' in input_data[0].get('json', {})):
        # Extract the actual output from stdout
        stdout_data = input_data[0]['json']['stdout']
        return json.loads(stdout_data)
    
    return input_data

def create_initial_state(email_data):
    """Create the initial state object from email data"""
    
    state = {
        "email_context": {
            "from": email_data.get('from'),
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

def main():
    """Main validation logic"""
    
    try:
        # Read input from command-line argument
        if len(sys.argv) < 2:
            raise ValueError('No input data provided. Expected JSON data as command-line argument.')
        
        input_data = parse_n8n_input(sys.argv[1])
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
        
        # Return state to n8n (wrapped in array as n8n expects)
        print(json.dumps([{"json": state}]))
        
    except Exception as e:
        error_state = {
            "email_context": {},
            "files": [],
            "errors": [{
                "error": str(e)
            }]
        }
        print(json.dumps([{"json": error_state}]))
        sys.exit(1)

if __name__ == '__main__':
    main()
