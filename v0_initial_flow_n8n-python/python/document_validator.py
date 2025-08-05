"""
Document Validator - Creates initial state object and validates PDF attachments
"""

import base64

pdf_bytes_max = 4 * 1024 * 1024
service_name = "Document Validator"

def validate_attachments(state):
    """Create the initial state object from input JSON"""
    attachments = state['attachments']
    errors = state['errors']
    attachments_out = []
    
    for attachment in attachments:
        file_name = attachment['fileName']
        mime_type = attachment['mimeType']
        data = attachment['data']
        if mime_type != 'application/pdf':
            errors.append(f"[{service_name}] Attachment {file_name} is not a PDF file")
            continue
        try:
            pdf_bytes = base64.b64decode(data)
            if len(pdf_bytes) > pdf_bytes_max:
                errors.append(f"[{service_name}] Attachment {file_name} is too large (>4MB)")
                continue
        except base64.binascii.Error:
            errors.append(f"[{service_name}] Attachment {file_name} has invalid base64 data")
            continue
        attachments_out.append({
            "fileName": file_name,
            "data": data,
            "status": f"{service_name} pass"
        })
    state["attachments"] = attachments_out
    return state

def process(state):
    """Process input JSON and validate attachments"""
    state = validate_attachments(state)
    return state
