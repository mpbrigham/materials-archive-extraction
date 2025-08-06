"""
Document Validator - Validates single PDF attachment from root level fields
"""

import base64

pdf_bytes_max = 4 * 1024 * 1024
service_name = "Document Validator"

def validate_attachment(state):
    """Validate single attachment from root level fields"""

    attachment = state['attachments']
    file_name = attachment['fileName']
    mime_type = attachment['mimeType']
    data = attachment['data']
    
    if data=='':
        state['errors'].append(f"[{service_name}] Attachment {file_name} Missing attachment data")
        attachment['status'] = f"{service_name} failed"
        return state    
        
    if mime_type != 'application/pdf':
        state['errors'].append(f"[{service_name}] Attachment {file_name} is not a PDF file")
        attachment['status'] = f"{service_name} failed"
        return state
    
    try:
        pdf_bytes = base64.b64decode(data)
        if len(pdf_bytes) > pdf_bytes_max:
            state['errors'].append(f"[{service_name}] Attachment {file_name} is too large (>4MB)")
            attachment['status'] = f"{service_name} failed"
            return state
            
    except base64.binascii.Error:
        state['errors'].append(f"[{service_name}] Attachment {file_name} has invalid base64 data")
        attachment['status'] = f"{service_name} failed"
        return state

    attachment['status'] = f"{service_name} pass"
    
    return state

def process(state):
    """Process single attachment validation"""
    
    return validate_attachment(state)
