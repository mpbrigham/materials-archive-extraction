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

def main():
    """Main extraction logic"""
    
    try:
        # Read input from command-line argument
        if len(sys.argv) < 2:
            raise ValueError('No input data provided. Expected JSON data as command-line argument.')
        
        input_data = parse_n8n_input(sys.argv[1])
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
        
        # Return updated state to n8n
        print(json.dumps([{"json": state}]))
        
    except Exception as e:
        # Try to preserve state if possible
        try:
            if 'state' in locals():
                state['errors'].append({
                    "error": str(e)
                })
                print(json.dumps([{"json": state}]))
            else:
                raise
        except:
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
