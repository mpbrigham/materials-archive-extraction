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
        error = f"[{service_name}] Attachment {file_name} failed base64 decoding: {e}"
        return {"status": f"{service_name} failed"}, error
        
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
        
        products = response.parsed       
        products['fileName'] = file_name
        
        return {"status": f"{service_name} pass", "products": products}, None
        
    except Exception as e:
        error = f"[{service_name}] Attachment {file_name} failed LLM processing: {str(e)}"
        return {"status": f"{service_name} failed"}, error

def process(state):
    """Process single attachment and extract PDF metadata"""
    
    model_name = os.environ['LLM_MODEL']  
    api_key = os.environ.get('LLM_API_KEY')
    errors = state.get('errors', [])
    
    try:
        filepath = '/app/prompts/llm_extraction.txt'
        with open(filepath, 'r') as f:
            prompt = f.read()
    except Exception as e:
        error = f'[{service_name}] Could not open prompt {filepath}: {e}'
        errors.append(error)
        state['errors'] = errors
        state['status'] = f"{service_name} failed"
        return state
        
    try:
        filepath = '/app/prompts/materials_schema.json'
        with open(filepath, 'r') as f:
            response_schema = json.load(f)
    except Exception as e:
        error = f'[{service_name}] Could not open schema {filepath}: {e}'
        errors.append(error)
        state['errors'] = errors
        state['status'] = f"{service_name} failed"
        return state

    extracted_data, error = extract_from_attachment(
        state, api_key, model_name, prompt, response_schema
    )
    
    state.update(extracted_data)
    
    if 'data' in state['attachments']:
        del state['attachments']['data']
    
    if error is not None:
        errors.append(error)
    state['errors'] = errors
    
    return state
