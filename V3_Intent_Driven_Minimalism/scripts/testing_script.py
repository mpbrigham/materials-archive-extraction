#!/usr/bin/env python3
"""
IMIS V3 - Comprehensive Testing Script
Tests the entire V3 pipeline with various document types and feedback mechanisms
"""

import os
import sys
import json
import time
import requests
import logging
from datetime import datetime
import argparse
import subprocess
from pathlib import Path
import hashlib
import concurrent.futures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_results_v3.log')
    ]
)
logger = logging.getLogger('imis_tester_v3')

# Default paths and settings
DEFAULT_WEBHOOK_URL = "http://localhost:5000/v3/webhook"
DEFAULT_SAMPLES_DIR = "./samples"
DEFAULT_N8N_URL = "http://localhost:5678/webhook/materials-intake-v3"
DEFAULT_FEEDBACK_URL = "http://localhost:5000/v3/feedback"
DEFAULT_STATUS_URL = "http://localhost:5000/v3/status"
DEFAULT_METADATA_URL = "http://localhost:5000/v3/metadata"


def check_webhook_health(webhook_url):
    """Check if the webhook server is running and responsive"""
    try:
        health_url = webhook_url.replace('/v3/webhook', '/health')
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            logger.info(f"Webhook server is healthy: {response.json()}")
            return True
        else:
            logger.error(f"Webhook server returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to webhook server: {str(e)}")
        return False


def upload_pdf(webhook_url, pdf_path, sender="test@example.com", api_key=None):
    """Upload a PDF file to the webhook endpoint"""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            files = {'file': (os.path.basename(pdf_path), pdf_file, 'application/pdf')}
            data = {
                'sender': sender,
                'subject': f"Test Upload: {os.path.basename(pdf_path)}"
            }
            
            headers = {}
            if api_key:
                headers['X-API-Key'] = api_key
                
            logger.info(f"Uploading {pdf_path} to {webhook_url}")
            response = requests.post(webhook_url, files=files, data=data, headers=headers)
            
            if response.status_code in [200, 202]:
                logger.info(f"Upload successful: {response.json()}")
                return response.json().get('request_id')
            else:
                logger.error(f"Upload failed with status code {response.status_code}: {response.text}")
                return None
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        return None


def upload_ocr_text(webhook_url, ocr_text, sender="test@example.com", filename="test_ocr.txt", api_key=None):
    """Upload OCR text to the webhook endpoint"""
    try:
        data = {
            'text': ocr_text,
            'sender': sender,
            'filename': filename
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if api_key:
            headers['X-API-Key'] = api_key
            
        logger.info(f"Uploading OCR text to {webhook_url}")
        response = requests.post(webhook_url, json=data, headers=headers)
        
        if response.status_code in [200, 202]:
            logger.info(f"OCR upload successful: {response.json()}")
            return response.json().get('request_id')
        else:
            logger.error(f"OCR upload failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error uploading OCR text: {str(e)}")
        return None


def check_document_status(status_url, request_id, timeout=300, poll_interval=5, max_attempts=60):
    """Poll document status until completion or timeout"""
    endpoint = f"{status_url}/{request_id}"
    start_time = time.time()
    attempts = 0
    
    logger.info(f"Polling status for document {request_id}")
    while time.time() - start_time < timeout and attempts < max_attempts:
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                status_data = response.json()
                current_state = status_data.get('current_state')
                logger.info(f"Document {request_id} current state: {current_state}")
                
                # Check if processing is complete or failed
                if current_state in ['COMPLETED', 'FLAGGED', 'FAILED']:
                    return status_data
            else:
                logger.warning(f"Status check failed with code {response.status_code}: {response.text}")
            
            time.sleep(poll_interval)
            attempts += 1
        except Exception as e:
            logger.error(f"Error checking document status: {str(e)}")
            time.sleep(poll_interval)
            attempts += 1
    
    logger.error(f"Timeout or max attempts reached waiting for document {request_id} to complete processing")
    return None


def get_document_metadata(metadata_url, request_id):
    """Retrieve the extracted metadata for a document"""
    endpoint = f"{metadata_url}/{request_id}"
    
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            logger.info(f"Successfully retrieved metadata for {request_id}")
            return response.json()
        else:
            logger.warning(f"Metadata retrieval failed with code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving metadata: {str(e)}")
        return None


def submit_feedback(feedback_url, request_id, corrections=None, comment=None, feedback_token=None):
    """Submit feedback for a processed document"""
    try:
        if not corrections and not comment:
            logger.warning("No corrections or comment provided")
            return False
        
        feedback_data = {}
        
        if feedback_token:
            feedback_data["feedback_token"] = feedback_token
            
        if corrections:
            feedback_data["corrections"] = corrections
        
        if comment:
            feedback_data["comment"] = comment
        
        logger.info(f"Submitting feedback for document {request_id}")
        response = requests.post(
            f"{feedback_url}/{request_id}", 
            json=feedback_data, 
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"Feedback submitted successfully: {response.json()}")
            return True
        else:
            logger.error(f"Feedback submission failed with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return False


def extract_feedback_token(status_data):
    """Extract feedback token from status data if available"""
    # In a real implementation, this might be in the metadata or status data
    # This is a simplified version for testing
    return f"fb-{datetime.now().timestamp()}-{status_data['request_id'][-8:]}"


def validate_metadata(metadata):
    """Validate that the metadata has the expected structure and fields"""
    if not metadata:
        return False, "No metadata available"
    
    required_mvs_fields = ["name", "brand", "dimensions", "summary"]
    missing_fields = [field for field in required_mvs_fields if not metadata.get(field)]
    
    if missing_fields:
        return False, f"Missing required MVS fields: {', '.join(missing_fields)}"
    
    # Check for metadata structure
    if "_metadata" not in metadata:
        return False, "Missing _metadata section"
    
    return True, "Metadata validation passed"


def test_document(webhook_url, document_path, status_url, metadata_url, feedback_url, api_key=None, test_feedback=False):
    """Test processing a single document through the V3 pipeline"""
    logger.info(f"Testing document: {document_path}")
    
    # Upload document
    if document_path.lower().endswith('.pdf'):
        request_id = upload_pdf(webhook_url, document_path, api_key=api_key)
    else:
        # Assume it's a text file for OCR
        with open(document_path, 'r') as f:
            text = f.read()
        request_id = upload_ocr_text(webhook_url, text, filename=os.path.basename(document_path), api_key=api_key)
    
    if not request_id:
        return {
            'file': document_path,
            'status': 'UPLOAD_FAILED',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Check status until completion
    status_data = check_document_status(status_url, request_id)
    if not status_data:
        return {
            'file': document_path,
            'request_id': request_id,
            'status': 'PROCESSING_TIMEOUT',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Get the final state
    final_state = status_data.get('current_state', 'UNKNOWN')
    
    # Get the metadata if available
    metadata = None
    if status_data.get('metadata_available'):
        metadata = get_document_metadata(metadata_url, request_id)
    
    # Validate metadata if available
    metadata_valid = False
    validation_message = "Metadata not available"
    if metadata:
        metadata_valid, validation_message = validate_metadata(metadata)
    
    result = {
        'file': document_path,
        'request_id': request_id,
        'final_state': final_state,
        'status': 'SUCCESS' if final_state == 'COMPLETED' else 'FLAGGED' if final_state == 'FLAGGED' else 'FAILED',
        'metadata_valid': metadata_valid,
        'metadata_message': validation_message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Test feedback if enabled
    if test_feedback and final_state in ['COMPLETED', 'FLAGGED']:
        feedback_token = extract_feedback_token(status_data)
        
        feedback_success = submit_feedback(
            feedback_url,
            request_id,
            corrections={'brand': 'Corrected Brand Name'},
            comment='Test feedback from V3 testing script',
            feedback_token=feedback_token
        )
        
        result['feedback_submitted'] = feedback_success
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Test IMIS V3 Pipeline')
    parser.add_argument('--webhook', default=DEFAULT_WEBHOOK_URL, help='Webhook URL')
    parser.add_argument('--samples', default=DEFAULT_SAMPLES_DIR, help='Directory with sample documents')
    parser.add_argument('--status', default=DEFAULT_STATUS_URL, help='Status URL')
    parser.add_argument('--metadata', default=DEFAULT_METADATA_URL, help='Metadata URL')
    parser.add_argument('--feedback', default=DEFAULT_FEEDBACK_URL, help='Feedback URL')
    parser.add_argument('--n8n', default=DEFAULT_N8N_URL, help='n8n webhook URL')
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument('--start-webhook', action='store_true', help='Start webhook server if not running')
    parser.add_argument('--timeout', type=int, default=300, help='Processing timeout in seconds')
    parser.add_argument('--test-feedback', action='store_true', help='Test feedback submission')
    parser.add_argument('--parallel', type=int, default=1, help='Number of parallel tests to run')
    parser.add_argument('--extensions', default='.pdf,.txt', help='Comma-separated list of file extensions to process')
    
    args = parser.parse_args()
    
    # Parse extensions
    extensions = args.extensions.split(',')
    
    # Check if webhook server is running
    webhook_running = check_webhook_health(args.webhook)
    
    if not webhook_running and args.start_webhook:
        logger.info("Starting webhook server...")
        try:
            # Start webhook server in background
            webhook_process = subprocess.Popen(
                ["python", "webhook_handler.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Wait for server to start
            time.sleep(2)
            webhook_running = check_webhook_health(args.webhook)
        except Exception as e:
            logger.error(f"Failed to start webhook server: {str(e)}")
    
    if not webhook_running:
        logger.error("Webhook server is not running. Exiting.")
        return 1
    
    # Get list of sample documents
    samples_dir = Path(args.samples)
    document_files = []
    
    for ext in extensions:
        document_files.extend(list(samples_dir.glob(f'*{ext}')))
    
    if not document_files:
        logger.error(f"No document files found in {args.samples} with extensions {extensions}. Exiting.")
        return 1
    
    logger.info(f"Found {len(document_files)} documents for testing")
    
    # Test results
    results = {
        'total': len(document_files),
        'success': 0,
        'flagged': 0,
        'failed': 0,
        'feedback': 0,
        'details': []
    }
    
    # Process documents in parallel or sequentially
    if args.parallel > 1:
        logger.info(f"Running {args.parallel} parallel tests")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
            future_to_doc = {
                executor.submit(
                    test_document, 
                    args.webhook, 
                    str(doc), 
                    args.status, 
                    args.metadata,
                    args.feedback,
                    args.api_key,
                    args.test_feedback
                ): doc for doc in document_files
            }
            
            for future in concurrent.futures.as_completed(future_to_doc):
                result = future.result()
                results['details'].append(result)
                
                if result['status'] == 'SUCCESS':
                    results['success'] += 1
                elif result['status'] == 'FLAGGED':
                    results['flagged'] += 1
                else:
                    results['failed'] += 1
                
                if result.get('feedback_submitted', False):
                    results['feedback'] += 1
    else:
        # Process sequentially
        for doc in document_files:
            result = test_document(
                args.webhook,
                str(doc),
                args.status,
                args.metadata,
                args.feedback,
                args.api_key,
                args.test_feedback
            )
            
            results['details'].append(result)
            
            if result['status'] == 'SUCCESS':
                results['success'] += 1
            elif result['status'] == 'FLAGGED':
                results['flagged'] += 1
            else:
                results['failed'] += 1
            
            if result.get('feedback_submitted', False):
                results['feedback'] += 1
    
    # Save results to file
    results_file = f"test_results_v3_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Testing complete. Results saved to {results_file}")
    logger.info(f"Success: {results['success']}/{results['total']} ({results['success']/results['
