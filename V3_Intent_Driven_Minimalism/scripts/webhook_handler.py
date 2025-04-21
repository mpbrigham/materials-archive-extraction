#!/usr/bin/env python3
"""
IMIS V3 - Intent-Driven Minimalism
Production-ready webhook handler with state tracking and feedback integration
"""

import os
import json
import logging
import time
import hashlib
import uuid
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, abort, Response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import requests
import threading
import traceback

# Load environment variables
load_dotenv()

# Configure logging
log_path = os.getenv('LOG_PATH', './logs')
os.makedirs(log_path, exist_ok=True)

logger = logging.getLogger('imis_webhook_v3')
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)

# File handler with rotation
file_handler = RotatingFileHandler(
    os.path.join(log_path, 'webhook_v3.log'),
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

# Add structured JSON logging for production environments
if os.getenv('ENABLE_STRUCTURED_LOGS', 'false').lower() == 'true':
    json_handler = RotatingFileHandler(
        os.path.join(log_path, 'webhook_structured_v3.json'),
        maxBytes=10485760,
        backupCount=10
    )
    json_handler.setLevel(logging.INFO)
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            # Add any exception info
            if record.exc_info:
                log_record["exception"] = {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                    "traceback": self.formatException(record.exc_info)
                }
            return json.dumps(log_record)
    
    json_handler.setFormatter(JsonFormatter())
    logger.addHandler(json_handler)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Initialize Flask app
app = Flask(__name__)

# Create storage directories
upload_folder = os.getenv('STORAGE_PATH', './storage')
archive_folder = os.getenv('ARCHIVE_PATH', './archives')
feedback_folder = os.getenv('FEEDBACK_PATH', './feedback')

for folder in [upload_folder, archive_folder, feedback_folder]:
    os.makedirs(folder, exist_ok=True)

# Configure maximum allowed upload size - 30MB for V3
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024

# Rate limiting configuration
RATE_LIMIT_ENABLED = os.getenv('ENABLE_API_RATE_LIMITING', 'false').lower() == 'true'
RATE_LIMIT_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '60'))
rate_limit_data = {}

# API keys for authentication (in production, use a better key management system)
API_KEYS = os.getenv('API_KEYS', '').split(',')

# Security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


def apply_rate_limit(ip_address):
    """Apply rate limiting by IP address"""
    if not RATE_LIMIT_ENABLED:
        return True
    
    current_time = time.time()
    minute_ago = current_time - 60
    
    # Clean up old entries
    for ip in list(rate_limit_data.keys()):
        rate_limit_data[ip] = [timestamp for timestamp in rate_limit_data[ip] if timestamp > minute_ago]
        if not rate_limit_data[ip]:
            del rate_limit_data[ip]
    
    # Check the current IP
    if ip_address not in rate_limit_data:
        rate_limit_data[ip_address] = [current_time]
        return True
    
    # Count requests in the last minute
    rate_limit_data[ip_address].append(current_time)
    request_count = len(rate_limit_data[ip_address])
    
    if request_count > RATE_LIMIT_PER_MINUTE:
        logger.warning(f"Rate limit exceeded for IP: {ip_address}")
        return False
    
    return True


def verify_api_key(api_key):
    """Verify if the provided API key is valid"""
    if not API_KEYS or API_KEYS[0] == '':  # If no keys configured, skip authentication
        return True
    
    return api_key in API_KEYS


def save_document_lifecycle(request_id, state_from, state_to, agent, notes=None):
    """Save document lifecycle event to JSON log file"""
    log_entry = {
        "document_id": request_id,
        "state_from": state_from,
        "state_to": state_to,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": agent,
        "notes": notes
    }
    
    lifecycle_log_path = os.path.join(log_path, 'document_lifecycle_v3.json')
    
    try:
        # Read existing log or create new one
        if os.path.exists(lifecycle_log_path):
            with open(lifecycle_log_path, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Add new entry
        logs.append(log_entry)
        
        # Write updated log
        with open(lifecycle_log_path, 'w') as f:
            json.dump(logs, f, indent=2)
            
        return True
    except Exception as e:
        logger.error(f"Error saving lifecycle log: {str(e)}")
        return False


def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file"""
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read and update hash in chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {str(e)}")
        return None


def detect_language(text):
    """Simple language detection (simplified - in production use a proper NLP library)"""
    # Detect common English words
    english_words = ['the', 'and', 'of', 'to', 'in', 'is', 'it', 'that', 'for', 'with']
    english_count = sum(1 for word in english_words if f" {word} " in f" {text} ".lower())
    
    # Detect common Dutch words
    dutch_words = ['de', 'het', 'een', 'en', 'van', 'in', 'is', 'dat', 'op', 'te']
    dutch_count = sum(1 for word in dutch_words if f" {word} " in f" {text} ".lower())
    
    # Detect common German words
    german_words = ['der', 'die', 'das', 'und', 'in', 'von', 'zu', 'den', 'mit', 'ist']
    german_count = sum(1 for word in german_words if f" {word} " in f" {text} ".lower())
    
    if dutch_count > english_count and dutch_count > german_count:
        return "nl"
    elif german_count > english_count and german_count > dutch_count:
        return "de"
    else:
        return "en"  # Default to English


def validate_pdf_file(file_path):
    """Validate that the file is a valid PDF"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(5)
            # Check for PDF signature
            return header == b'%PDF-'
    except Exception as e:
        logger.error(f"Error validating PDF file: {str(e)}")
        return False


def guess_document_type(filename, text=None):
    """Guess the document type based on filename and optionally content"""
    filename = filename.lower()
    
    if "datasheet" in filename or "data_sheet" in filename or "tech_spec" in filename:
        return "Datasheet"
    elif "catalog" in filename or "catalogue" in filename:
        return "Catalogue"
    elif "manual" in filename or "guide" in filename or "instruction" in filename:
        return "Manual"
    elif "cert" in filename or "certificate" in filename or "compliance" in filename:
        return "Certificate"
    elif "report" in filename or "analysis" in filename or "test" in filename:
        return "Report"
    elif text and ("technical data" in text.lower() or "specifications" in text.lower()):
        return "Datasheet"
    elif text and ("catalogue" in text.lower() or "product line" in text.lower()):
        return "Catalogue"
    
    return "Datasheet"  # Default


def notify_n8n_workflow(payload):
    """Notify the n8n workflow about a new document"""
    n8n_webhook_url = os.getenv('N8N_WEBHOOK_URL')
    if not n8n_webhook_url:
        logger.warning("N8N_WEBHOOK_URL not configured, skipping notification")
        return False
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(n8n_webhook_url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Successfully notified n8n workflow: {response.status_code}")
            return True
        else:
            logger.error(f"Failed to notify n8n workflow: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error notifying n8n workflow: {str(e)}")
        return False


def process_document_async(file_path, request_data):
    """Process document in a background thread"""
    try:
        # Extract some text for language detection and document type guessing
        with open(file_path, 'r', errors='ignore') as f:
            sample_text = f.read(4096)  # Read first 4KB to analyze
        
        language = detect_language(sample_text)
        document_type = guess_document_type(os.path.basename(file_path), sample_text)
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_path)
        
        # Prepare MaterialExtractionRequest
        mer = {
            "request_id": request_data["request_id"],
            "sender": request_data["sender"],
            "source_file_name": request_data["source_file_name"],
            "file_hash": file_hash,
            "language": language,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_channel": request_data["source_channel"],
            "document_type_guess": document_type,
            "file_path": file_path
        }
        
        # Send to n8n for processing
        notify_n8n_workflow(mer)
        
        # Update lifecycle
        save_document_lifecycle(
            request_data["request_id"],
            "RECEIVED",
            "INTERPRETED",
            "webhook_handler_v3",
            f"Language: {language}, Type: {document_type}, Async processing initiated"
        )
        
    except Exception as e:
        logger.error(f"Error in async processing: {str(e)}")
        logger.error(traceback.format_exc())
        
        save_document_lifecycle(
            request_data["request_id"],
            "RECEIVED",
            "FAILED",
            "webhook_handler_v3",
            f"Async processing error: {str(e)}"
        )


@app.route('/v3/webhook', methods=['POST'])
def webhook_v3():
    """V3 webhook handler endpoint"""
    start_time = time.time()
    client_ip = request.remote_addr
    request_id = f"req-{uuid.uuid4()}"
    
    # Apply rate limiting
    if not apply_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        save_document_lifecycle(request_id, "RECEIVED", "RATE_LIMITED", "webhook_handler_v3", f"IP: {client_ip}")
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
    
    # Check API key if in header
    api_key = request.headers.get('X-API-Key')
    if api_key and not verify_api_key(api_key):
        logger.warning(f"Invalid API key from IP: {client_ip}")
        save_document_lifecycle(request_id, "RECEIVED", "UNAUTHORIZED", "webhook_handler_v3", "Invalid API key")
        return jsonify({"error": "Invalid API key"}), 401
    
    try:
        # Check content type
        content_type = request.headers.get('Content-Type', '')
        
        if 'multipart/form-data' in content_type:
            # Handle file upload
            if 'file' not in request.files:
                logger.warning(f"No file part in request")
                save_document_lifecycle(request_id, "RECEIVED", "FAILED", "webhook_handler_v3", "No file in request")
                return jsonify({"error": "No file part"}), 400
                
            file = request.files['file']
            
            if file.filename == '':
                logger.warning(f"No file selected")
                save_document_lifecycle(request_id, "RECEIVED", "FAILED", "webhook_handler_v3", "Empty filename")
                return jsonify({"error": "No file selected"}), 400
                
            if file:
                # Security: use secure_filename to prevent path traversal
                filename = secure_filename(file.filename)
                
                # Only accept PDFs
                if not filename.lower().endswith('.pdf'):
                    logger.warning(f"Invalid file type: {filename}")
                    save_document_lifecycle(request_id, "RECEIVED", "FAILED", "webhook_handler_v3", "Not a PDF file")
                    return jsonify({"error": "Only PDF files are accepted"}), 400
                
                # Create unique filename with timestamp and request ID
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                safe_filename = f"{timestamp}_{request_id}_{filename}"
                filepath = os.path.join(upload_folder, safe_filename)
                
                # Save the file
                file.save(filepath)
                logger.info(f"File saved: {filepath}")
                
                # Validate PDF
                if not validate_pdf_file(filepath):
                    logger.warning(f"Invalid PDF content: {filepath}")
                    save_document_lifecycle(request_id, "RECEIVED", "FAILED", "webhook_handler_v3", "Invalid PDF content")
                    return jsonify({"error": "File is not a valid PDF"}), 400
                
                # Log document lifecycle
                save_document_lifecycle(request_id, "RECEIVED", "STORED", "webhook_handler_v3", f"File saved as {safe_filename}")
                
                # Prepare response according to V3 interface contract
                request_data = {
                    "request_id": request_id,
                    "sender": request.form.get('sender', 'unknown'),
                    "source_file_name": filename,
                    "source_channel": "webhook",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                # Process document asynchronously
                threading.Thread(target=process_document_async, args=(filepath, request_data)).start()
                
                logger.info(f"Webhook processed in {time.time() - start_time:.2f}s")
                return jsonify({
                    "request_id": request_id,
                    "status": "processing",
                    "message": "Document received and processing initiated"
                }), 202
        
        elif 'application/json' in content_type:
            # Handle JSON input
            data = request.json
            
            # Validate required fields
            if not data.get('text') and not data.get('url'):
                logger.warning("Missing 'text' or 'url' field in JSON payload")
                save_document_lifecycle(
