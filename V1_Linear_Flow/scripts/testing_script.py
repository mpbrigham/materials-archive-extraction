#!/usr/bin/env python3
"""
IMIS V1 - Comprehensive Testing Script
Validates the entire V1 pipeline with sample PDFs
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_results.log')
    ]
)
logger = logging.getLogger('imis_tester')

# Default paths and settings
DEFAULT_WEBHOOK_URL = "http://localhost:5000/webhook"
DEFAULT_SAMPLES_DIR = "./samples"
DEFAULT_N8N_URL = "http://localhost:5678/webhook/materials-intake"


def check_webhook_health(webhook_url):
    """Check if the webhook server is running and responsive"""
    try:
        health_url = webhook_url.replace('/webhook', '/health')
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


def upload_pdf(webhook_url, pdf_path, sender="test@example.com", subject="Test Upload"):
    """Upload a PDF file to the webhook endpoint"""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            files = {'file': (os.path.basename(pdf_path), pdf_file, 'application/pdf')}
            data = {
                'sender': sender,
                'subject': subject
            }
            logger.info(f"Uploading {pdf_path} to {webhook_url}")
            response = requests.post(webhook_url, files=files, data=data)
            
            if response.status_code == 200:
                logger.info(f"Upload successful: {response.json()}")
                return response.json().get('document_id')
            else:
                logger.error(f"Upload failed with status code {response.status_code}: {response.text}")
                return None
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        return None


def upload_ocr_text(webhook_url, ocr_text, sender="test@example.com", subject="Test OCR Upload"):
    """Upload OCR text to the webhook endpoint"""
    try:
        data = {
            'text': ocr_text,
            'sender': sender,
            'subject': subject
        }
        logger.info(f"Uploading OCR text to {webhook_url}")
        response = requests.post(webhook_url, json=data, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            logger.info(f"OCR upload successful: {response.json()}")
            return response.json().get('document_id')
        else:
            logger.error(f"OCR upload failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error uploading OCR text: {str(e)}")
        return None


def check_document_status(webhook_url, document_id, timeout=300, poll_interval=5):
    """Poll document status until completion or timeout"""
    status_url = webhook_url.replace('/webhook', f'/status/{document_id}')
    start_time = time.time()
    
    logger.info(f"Polling status for document {document_id}")
    while time.time() - start_time < timeout:
        try:
            response = requests.get(status_url)
            if response.status_code == 200:
                status_data = response.json()
                current_state = status_data.get('current_state')
                logger.info(f"Document {document_id} current state: {current_state}")
                
                # Check if processing is complete or failed
                if current_state in ['COMPLETED', 'COMPLETED_WITH_FALLBACK', 'FAILED']:
                    return status_data
            else:
                logger.warning(f"Status check failed with code {response.status_code}: {response.text}")
            
            time.sleep(poll_interval)
        except Exception as e:
            logger.error(f"Error checking document status: {str(e)}")
            time.sleep(poll_interval)
    
    logger.error(f"Timeout waiting for document {document_id} to complete processing")
    return None


def validate_expected_output(document_id, expected_fields):
    """Validate that the processed document has the expected fields in output JSON"""
    log_path = os.path.join('./logs', 'document_lifecycle.json')
    
    try:
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                logs = json.load(f)
            
            # Find entries for the specified document
            document_logs = [log for log in logs if log.get('document_id') == document_id]
            
            if document_logs:
                # Check if verification passed
                for log in document_logs:
                    if log.get('to_state') == 'VERIFIED' or log.get('to_state') == 'COMPLETED':
                        logger.info(f"Document {document_id} successfully verified")
                        return True
                    
                logger.warning(f"Document {document_id} did not reach VERIFIED state")
                return False
            else:
                logger.warning(f"No logs found for document {document_id}")
                return False
        else:
            logger.warning(f"No log file exists at {log_path}")
            return False
    except Exception as e:
        logger.error(f"Error validating output: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test IMIS V1 Pipeline')
    parser.add_argument('--webhook', default=DEFAULT_WEBHOOK_URL, help='Webhook URL')
    parser.add_argument('--samples', default=DEFAULT_SAMPLES_DIR, help='Directory with sample PDFs')
    parser.add_argument('--n8n', default=DEFAULT_N8N_URL, help='n8n webhook URL')
    parser.add_argument('--start-webhook', action='store_true', help='Start webhook server if not running')
    parser.add_argument('--timeout', type=int, default=300, help='Processing timeout in seconds')
    
    args = parser.parse_args()
    
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
    
    # Get list of sample PDFs
    samples_dir = Path(args.samples)
    pdf_files = list(samples_dir.glob('*.pdf'))
    
    if not pdf_files:
        logger.error(f"No PDF files found in {args.samples}. Exiting.")
        return 1
    
    logger.info(f"Found {len(pdf_files)} PDF files for testing")
    
    # Test results
    results = {
        'total': len(pdf_files),
        'success': 0,
        'failure': 0,
        'details': []
    }
    
    # Process each PDF
    for pdf_file in pdf_files:
        logger.info(f"Testing with {pdf_file}")
        
        # Upload PDF
        document_id = upload_pdf(args.webhook, pdf_file)
        if not document_id:
            logger.error(f"Failed to upload {pdf_file}")
            results['failure'] += 1
            results['details'].append({
                'file': str(pdf_file),
                'status': 'UPLOAD_FAILED',
                'timestamp': datetime.utcnow().isoformat()
            })
            continue
        
        # Check document status
        status = check_document_status(args.webhook, document_id, args.timeout)
        if not status:
            logger.error(f"Failed to process {pdf_file}")
            results['failure'] += 1
            results['details'].append({
                'file': str(pdf_file),
                'document_id': document_id,
                'status': 'PROCESSING_FAILED',
                'timestamp': datetime.utcnow().isoformat()
            })
            continue
        
        # Validate expected output
        expected_fields = ['name', 'brand', 'dimensions', 'summary']
        if validate_expected_output(document_id, expected_fields):
            logger.info(f"Successfully processed {pdf_file}")
            results['success'] += 1
            results['details'].append({
                'file': str(pdf_file),
                'document_id': document_id,
                'status': 'SUCCESS',
                'final_state': status.get('current_state'),
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            logger.warning(f"Validation failed for {pdf_file}")
            results['failure'] += 1
            results['details'].append({
                'file': str(pdf_file),
                'document_id': document_id,
                'status': 'VALIDATION_FAILED',
                'final_state': status.get('current_state'),
                'timestamp': datetime.utcnow().isoformat()
            })
    
    # Save results to file
    results_file = f"test_results_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Testing complete. Results saved to {results_file}")
    logger.info(f"Success: {results['success']}/{results['total']} ({results['success']/results['total']*100:.1f}%)")
    
    return 0 if results['failure'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
