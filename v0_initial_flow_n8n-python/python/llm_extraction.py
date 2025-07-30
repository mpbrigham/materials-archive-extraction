#!/usr/bin/env python3
"""
LLM Extraction - Extract material metadata from PDFs using Google Gemini
"""

import json
import sys
import os
from datetime import datetime
import google.generativeai as genai

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

def process_pdf(item, api_key, model_name):
    """Process a single PDF with Gemini AI"""
    
    # Skip email context items
    if item.get('json', {}).get('email') and not item.get('json', {}).get('fileName'):
        return item
    
    # Skip invalid items
    if not item.get('json', {}).get('valid'):
        return item
    
    # Get file path from the item
    file_path = item.get('json', {}).get('filePath')
    
    if not file_path or not os.path.exists(file_path):
        return {
            'json': {
                **item.get('json', {}),
                'valid': False,
                'error': f'PDF file not found at path: {file_path}',
                'errorType': 'extraction'
            }
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
                        'value': item['json']['fileName'],
                        'confidence': 1.0
                    }
        
        return {
            'json': {
                **item.get('json', {}),
                'valid': True,
                'extractedData': extracted_data,
                'productCount': len(extracted_data.get('products', []))
            }
        }
        
    except Exception as e:
        return {
            'json': {
                **item.get('json', {}),
                'valid': False,
                'error': str(e),
                'errorType': 'extraction'
            }
        }

def main():
    """Main extraction logic"""
    try:
        # Read input from command-line argument
        if len(sys.argv) < 2:
            raise ValueError('No input data provided. Expected JSON data as command-line argument.')
        
        input_data = json.loads(sys.argv[1])
        execution_id = os.environ.get('EXECUTION_ID', 'unknown')
        
        # Get API credentials
        api_key = os.environ.get('LLM_API_KEY')
        model_name = os.environ.get('LLM_MODEL')
        
        if not api_key:
            raise ValueError('LLM_API_KEY is not defined in environment variables.')
        
        if not model_name:
            raise ValueError('LLM_MODEL is not defined in environment variables.')
        
        # Process each item
        results = []
        for item in input_data:
            # Log input
            log_debug(execution_id, "LLM Extraction", "input", item)
            
            result = process_pdf(item, api_key, model_name)
            
            # Log output
            log_debug(execution_id, "LLM Extraction", "output", result)
            
            results.append(result)
        
        # Return results to n8n
        print(json.dumps(results))
        
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
