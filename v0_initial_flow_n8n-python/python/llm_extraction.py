#!/usr/bin/env python3
"""
LLM Extraction - Extract material metadata from PDFs using Google Gemini
"""

import json
import os
import google.generativeai as genai
from common import log_debug, create_error_response

def process_pdf(file_info, api_key, model_name):
    """Process a single PDF with Gemini AI"""
    
    file_path = file_info.get('filePath')
    
    if not file_path or not os.path.exists(file_path):
        return {
            "status": "failed",
            "error": f'PDF file not found at path: {file_path}'
        }
    
    try:
        # Read prompt and schema
        with open('/data/prompts/llm_extraction.txt', 'r') as f:
            prompt = f.read()
        
        with open('/data/schema/materials_schema.json', 'r') as f:
            schema = json.load(f)
        
        # Configure Gemini
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
        
        # Read PDF file directly from disk
        with open(file_path, 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()
        
        # Make API request
        response = model.generate_content([
            prompt + "\n\nAnalyze this PDF and extract all product metadata with confidence scores. Return the result as valid JSON matching the required schema.",
            {
                "mime_type": "application/pdf",
                "data": pdf_bytes
            }
        ])
        
        extracted_data = json.loads(response.text)
        
        # Add source file name to products
        if extracted_data.get('products'):
            for product in extracted_data['products']:
                if not product.get('source_file_name'):
                    product['source_file_name'] = {
                        'value': file_info['fileName'],
                        'confidence': 1.0
                    }
        
        return {
            "status": "processed",
            "extractedData": extracted_data
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

def process(input_data):
    """Process state object and extract material data from PDFs"""
    
    try:
        execution_id = os.environ.get('EXECUTION_ID', 'unknown')
        
        # Get API credentials
        api_key = os.environ.get('LLM_API_KEY')
        model_name = os.environ.get('LLM_MODEL')
        
        if not api_key:
            raise ValueError('LLM_API_KEY is not defined in environment variables.')
        
        if not model_name:
            raise ValueError('LLM_MODEL is not defined in environment variables.')
        
        # Extract state object
        if isinstance(input_data, list) and len(input_data) > 0:
            state = input_data[0].get('json', {})
        else:
            raise ValueError('Invalid input format. Expected state object.')
        
        # Log input
        log_debug(execution_id, "LLM Extraction", "input", state)
        
        # Process files with "pending" status
        for file_info in state.get('files', []):
            if file_info.get('status') == 'pending':
                # Process the PDF
                result = process_pdf(file_info, api_key, model_name)
                
                # Update the file info with results
                file_info.update(result)
        
        # Log output
        log_debug(execution_id, "LLM Extraction", "output", state)
        
        # Return updated state
        return [{"json": state}]
        
    except Exception as e:
        # Try to preserve state if possible
        try:
            if 'state' in locals():
                state['errors'].append({
                    "error": str(e)
                })
                return [{"json": state}]
            else:
                raise
        except:
            return create_error_response(e)
