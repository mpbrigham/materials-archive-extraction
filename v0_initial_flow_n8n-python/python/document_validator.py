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
        # Read input from n8n
        input_data = json.loads(sys.stdin.read())
        execution_id = os.environ.get('EXECUTION_ID', 'unknown')
        
        # Log input
        log_debug(execution_id, "Document Validator", "input", input_data)
        
        items = []
        
        for item in input_data:
            email = item.get('json', {})
            attachments = item.get('binary', {})
            
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
            
            for key, attachment in attachments.items():
                if attachment.get('mimeType') == 'application/pdf':
                    process_item = {
                        'json': {
                            'fileName': attachment.get('fileName', key),
                            'fileSize': len(attachment.get('data', '')),
                            'valid': True
                        },
                        'binary': {
                            'pdf': attachment
                        }
                    }
                    items.append(process_item)
                    pdf_count += 1
            
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
