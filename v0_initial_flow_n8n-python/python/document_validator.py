#!/usr/bin/env python3
"""
Document Validator - Validates PDF attachments from email
"""

import json
import sys
import os
from datetime import datetime

def log_debug(execution_id, node_name, phase, data):
    """Log debug information to file"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "executionId": execution_id,
        "node": node_name,
        "phase": phase,
        "data": data
    }
    with open('/home/node/data/debug.log', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def main():
    """Main validation logic"""
    try:
        # Read input from command-line argument
        if len(sys.argv) < 2:
            raise ValueError('No input data provided. Expected JSON data as command-line argument.')
        
        input_data = json.loads(sys.argv[1])
        execution_id = os.environ.get('EXECUTION_ID', 'unknown')
        
        # Log input
        log_debug(execution_id, "Document Validator", "input", input_data)
        
        items = []
        
        for item in input_data:
            email = item.get('json', {})
            
            # Validate required email fields
            if not email.get('from'):
                raise ValueError('Email missing required "from" field. Cannot process email without sender information.')
            
            email_context = {
                'email': {
                    'subject': email.get('subject'),
                    'from': email.get('from'),
                    'messageId': email.get('metadata', {}).get('message-id', email.get('messageId')),
                    'date': email.get('date')
                }
            }
            
            items.append({'json': email_context})
            
            pdf_count = 0
            
            # Check for attachments with file paths (n8n saves them to disk)
            attachments = email.get('attachments', [])
            
            for attachment in attachments:
                # Check if it's a PDF based on mime type or filename
                mime_type = attachment.get('mimeType', '')
                file_name = attachment.get('fileName', '')
                file_path = attachment.get('filePath', '')
                
                if mime_type == 'application/pdf' or file_name.lower().endswith('.pdf'):
                    if file_path and os.path.exists(file_path):
                        # Get file size from disk
                        file_size = os.path.getsize(file_path)
                        
                        process_item = {
                            'json': {
                                'fileName': file_name,
                                'filePath': file_path,
                                'fileSize': file_size,
                                'mimeType': mime_type,
                                'valid': True
                            }
                        }
                        items.append(process_item)
                        pdf_count += 1
                    else:
                        items.append({
                            'json': {
                                'fileName': file_name,
                                'valid': False,
                                'error': f'PDF file not found at path: {file_path}',
                                'errorType': 'validation'
                            }
                        })
            
            if pdf_count == 0:
                items.append({
                    'json': {
                        'fileName': 'no-pdfs-found',
                        'valid': False,
                        'error': 'No PDF attachments found',
                        'errorType': 'validation'
                    }
                })
        
        # Log output
        log_debug(execution_id, "Document Validator", "output", items)
        
        # Return results to n8n
        print(json.dumps(items))
        
    except Exception as e:
        error_result = [{
            'json': {
                'error': str(e),
                'errorType': 'system'
            }
        }]
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == '__main__':
    main()
