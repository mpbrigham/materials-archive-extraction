#!/usr/bin/env python3
"""
LLM Extraction - Extract material metadata from PDFs using Google Gemini from base64
"""

import json
import os
import base64
import google.generativeai as genai
from common import log_debug, create_error_response

def process_pdf(file_info, api_key, model_name):
    """Process a single PDF with Gemini AI from base64 data"""
    pdf_base64 = file_info.get('data')
    if not pdf_base64:
        return {"status": "failed", "error": "Missing PDF data"}
    try:
        pdf_bytes = base64.b64decode(pdf_base64)
        with open('/app/prompts/llm_extraction.txt', 'r') as f:
            prompt = f.read()
        with open('/app/schema/materials_schema.json', 'r') as f:
            schema = json.load(f)
        genai.configure(api_key=api_key)
        generation_config = {
            "temperature": 0.1,
            "top_k": 32,
            "top_p": 0.95,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
            "response_schema": schema
        }
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )
        response = model.generate_content([
            prompt + "\n\nAnalyze this PDF and extract all product metadata with confidence scores. Return the result as valid JSON matching the required schema.",
            {"mime_type": "application/pdf", "data": pdf_bytes}
        ])
        try:
            extracted_data = json.loads(response.text)
        except json.JSONDecodeError:
            return {"status": "failed", "error": "Invalid JSON from LLM"}
        # Add source file name
        if extracted_data.get('products'):
            for product in extracted_data['products']:
                if not product.get('source_file_name'):
                    product['source_file_name'] = {'value': file_info['fileName'], 'confidence': 1.0}
        return {"status": "processed", "extractedData": extracted_data}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def process(input_data):
    """Process state object and extract material data from PDFs"""
    execution_id = os.environ.get('EXECUTION_ID', 'unknown')
    api_key = os.environ.get('LLM_API_KEY')
    model_name = os.environ.get('LLM_MODEL')
    if not api_key or not model_name:
        raise ValueError('LLM_API_KEY or LLM_MODEL missing')
    state = input_data[0].get('json', {}) if isinstance(input_data, list) else input_data
    log_debug(execution_id, "LLM Extraction", "input", state)
    try:
        for file_info in state.get('files', []):
            if file_info.get('status') == 'pending':
                result = process_pdf(file_info, api_key, model_name)
                file_info.update(result)
        log_debug(execution_id, "LLM Extraction", "output", state)
        return [{"json": state}]
    except Exception as e:
        state.setdefault('errors', []).append({"error": str(e)})
        return [{"json": state}]
