"""
LLM Extraction - Extract material metadata from single PDF attachment
"""

import json
import os
import base64
from google import genai
from google.genai import types

service_name = "LLM Extraction"

def extract_from_attachment(state, api_key, model_name, prompt, response_schema):
    """Process single PDF with Gemini AI"""
    
    attachment = state['attachments']
    pdf_base64 = attachment['data']
    file_name = attachment['fileName']
    
    try:
        pdf_bytes = base64.b64decode(pdf_base64)
    except Exception as e:
        state['errors'].append(f"[{service_name}] Attachment {file_name} failed base64 decoding: {e}")
        attachment["status"] = f"{service_name} failed"
        return state
        
    try:
        client = genai.Client(api_key=api_key)
        
        pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf')
        contents = [prompt, pdf_part]
        
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=response_schema
        )

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )
        
        if hasattr(response, "parsed"):
            attachment["status"] = f"{service_name} pass"
            attachment.update(response.parsed)
            return state
            
        else:
            state['errors'].append(
                f"[{service_name}] Attachment {file_name} failed LLM processing: no output JSON"
            )
            attachment["status"] = f"{service_name} failed"
            return state

    except Exception as e:
        state['errors'].append(
            f"[{service_name}] Attachment {file_name} failed LLM processing: {str(e)}"
        )
        attachment["status"] = f"{service_name} failed"
        return state

def process(state):
    """Process single attachment and extract PDF metadata"""
    
    model_name = os.environ['LLM_MODEL']  
    api_key = os.environ.get('LLM_API_KEY')
    attachment = state['attachments']
    
    try:
        filepath = '/app/prompts/llm_extraction.txt'
        with open(filepath, 'r') as f:
            prompt = f.read()
            
    except Exception as e:
        state['errors'].append(f'[{service_name}] Could not open prompt {filepath}: {e}')
        attachment['status'] = f"{service_name} failed"
        return state
        
    try:
        filepath = '/app/prompts/materials_schema.json'
        with open(filepath, 'r') as f:
            response_schema = json.load(f)
            
    except Exception as e:
        state['errors'].append(f'[{service_name}] Could not open schema {filepath}: {e}')
        attachment['status'] = f"{service_name} failed"
        return state

    state = extract_from_attachment(
        state, api_key, model_name, prompt, response_schema
    )

    if 'data' in attachment:
        del attachment['data']

    return state
