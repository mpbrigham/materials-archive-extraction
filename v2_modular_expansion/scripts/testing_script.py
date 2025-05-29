#!/usr/bin/env python3
"""
IMIS V2 - Comprehensive Testing Script
Tests the entire V2 pipeline with sample PDFs
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_results_v2.log')
    ]
)
logger = logging.getLogger('imis_tester_v2')

# Default paths and settings
DEFAULT_WEBHOOK_URL = "http://localhost:5000/webhook/v2"
DEFAULT_SAMPLES_DIR = "./samples"
DEFAULT_N8N_URL = "http://localhost:5678/webhook/materials-intake-v2"
DEFAULT_FEEDBACK_URL = "http://localhost:5000/feedback/v2"


def check_webhook_health(webhook_url):
    """Check if the webhook server is running and responsive"""
    try:
        health_url = webhook_url.replace('/webhook/v2', '/health')
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
    status_url = webhook_url.replace('/webhook/v2', f'/status/v2/{document_id}')
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
                if current_state
