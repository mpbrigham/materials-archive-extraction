#!/usr/bin/env python3
"""
IMIS V2 - Production-Ready Webhook Handler
Enhanced implementation with proper error handling, security, and modularity
"""

import os
import json
import logging
import time
import hashlib
from datetime import datetime
import uuid
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configure logging
log_path = os.getenv('LOG_PATH', './logs')
os.makedirs(log_path, exist_ok=True)

logger = logging.getLogger('imis_webhook_v2')
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)

# File handler with rotation
file_handler = RotatingFileHandler(
    os.path.join(log_path, 'webhook_v2.log'),
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

# Add structured JSON logging for production environments
if os.getenv('ENABLE_STRUCTURED_LOGS', 'false').lower() == 'true':
    json_handler = RotatingFileHandler(
        os.path.join(log_path, 'webhook_structured.json'),
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

# Create storage directory
upload_folder = os.getenv('STORAGE_PATH', './storage')
os.makedirs(upload_folder, exist_ok=True)

# Configure maximum allowed upload size - 20MB
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

# Rate limiting configuration (simple implementation)
RATE_LIMIT_ENABLED = os.getenv('ENABLE_API_RATE_LIMITING', 'false').lower() == 'true'
RATE_LIMIT_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '60'))
rate_limit_data = {}

# Security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
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


def save_document_lifecycle(document_id, from_state, to_state, agent, notes=None):
    """Save document lifecycle event to JSON log file"""
    log_entry = {
        "document_id": document_id,
        "from_state": from_state,
        "to_state": to_state,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": agent,
        "notes": notes
    }
    
    lifecycle_log_path = os.path.join(log_path, 'document_lifecycle_v2.json')
    
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


@app.route('/webhook/v2', methods=['POST'])
def webhook_handler_v2():
    """V2 webhook handler endpoint"""
    start_time = time.time()
    client_ip = request.remote_addr
    document_id = f"doc-v2-{uuid.uuid4()}"
    
    # Apply rate limiting
    if not apply_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        save_document_lifecycle(document_id, "RECEIVED", "RATE_LIMITED", "webhook_handler_v2", f"IP: {client_ip}")
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
    
    try:
        # Check content type
        content_type = request.headers.get('Content-Type', '')
        
        if 'multipart/form-data' in content_type:
            # Handle file upload
            if 'file' not in request.files:
                logger.warning(f"No file part in request")
                save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler_v2", "No file in request")
                return jsonify({"error": "No file part"}), 400
                
            file = request.files['file']
            
            if file.filename == '':
                logger.warning(f"No file selected")
                save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler_v2", "Empty filename")
                return jsonify({"error": "No file selected"}), 400
                
            if file:
                # Security: use secure_filename to prevent path traversal
                filename = secure_filename(file.filename)
                
                # Only accept PDFs
                if not filename.lower().endswith('.pdf'):
                    logger.warning(f"Invalid file type: {filename}")
                    save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler_v2", "Not a PDF file")
                    return jsonify({"error": "Only PDF files are accepted"}), 400
                
                # Create unique filename with timestamp and document ID
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                safe_filename = f"{timestamp}_{document_id}_{filename}"
                filepath = os.path.join(upload_folder, safe_filename)
                
                # Save the file
                file.save(filepath)
                logger.info(f"File saved: {filepath}")
                
                # Validate PDF and calculate hash
                if not validate_pdf_file(filepath):
                    logger.warning(f"Invalid PDF content: {filepath}")
                    save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler_v2", "Invalid PDF content")
                    return jsonify({"error": "File is not a valid PDF"}), 400
                
                file_hash = calculate_file_hash(filepath)
                
                # Log document lifecycle
                save_document_lifecycle(document_id, "RECEIVED", "STORED", "webhook_handler_v2", f"File saved as {safe_filename}")
                
                # Prepare response according to V2 interface contract
                payload = {
                    "document_id": document_id,
                    "sender": request.form.get('sender', 'unknown'),
                    "subject": request.form.get('subject', filename),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "file_path": filepath,
                    "file_hash": file_hash
                }
                
                # Notify n8n workflow
                notify_n8n_workflow(payload)
                
                logger.info(f"Webhook processed in {time.time() - start_time:.2f}s")
                return jsonify(payload), 200
        
        elif 'application/json' in content_type:
            # Handle JSON input (e.g., for OCR text that's already extracted)
            data = request.json
            
            # Validate required fields
            if not data.get('text'):
                logger.warning("Missing 'text' field in JSON payload")
                save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler_v2", "Missing 'text' field")
                return jsonify({"error": "Missing 'text' field"}), 400
            
            # Log received data to file for processing
            text_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{document_id}.txt"
            text_filepath = os.path.join(upload_folder, text_filename)
            
            with open(text_filepath, 'w') as f:
                f.write(data['text'])
            
            # Calculate text hash
            text_hash = hashlib.sha256(data['text'].encode()).hexdigest()
            
            logger.info(f"OCR text saved: {text_filepath}")
            save_document_lifecycle(document_id, "RECEIVED", "STORED", "webhook_handler_v2", "OCR text saved")
            
            # Prepare response according to V2 interface contract
            payload = {
                "document_id": document_id,
                "sender": data.get('sender', 'unknown'),
                "subject": data.get('subject', 'OCR Text'),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "file_path": text_filepath,
                "file_hash": text_hash
            }
            
            # Notify n8n workflow
            notify_n8n_workflow(payload)
            
            logger.info(f"Webhook processed in {time.time() - start_time:.2f}s")
            return jsonify(payload), 200
        
        else:
            logger.warning(f"Unsupported content type: {content_type}")
            save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler_v2", f"Unsupported content type: {content_type}")
            return jsonify({"error": "Unsupported content type"}), 415
    
    except Exception as e:
        logger.exception(f"Error processing webhook: {str(e)}")
        save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler_v2", f"Exception: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "version": "v2.1",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {
            "webhook": "healthy",
            "storage": os.path.exists(upload_folder) and os.access(upload_folder, os.W_OK),
            "logging": os.path.exists(log_path) and os.access(log_path, os.W_OK)
        }
    }), 200


@app.route('/status/v2/<document_id>', methods=['GET'])
def document_status_v2(document_id):
    """Get processing status for a specific document (V2)"""
    lifecycle_log_path = os.path.join(log_path, 'document_lifecycle_v2.json')
    
    try:
        if os.path.exists(lifecycle_log_path):
            with open(lifecycle_log_path, 'r') as f:
                logs = json.load(f)
            
            # Find entries for the specified document
            document_logs = [log for log in logs if log.get('document_id') == document_id]
            
            if document_logs:
                # Sort by timestamp to get the latest state
                document_logs.sort(key=lambda x: x.get('timestamp', ''))
                latest_state = document_logs[-1].get('to_state', 'UNKNOWN')
                
                return jsonify({
                    "document_id": document_id,
                    "current_state": latest_state,
                    "history": document_logs,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }), 200
            else:
                return jsonify({"error": "Document not found"}), 404
        else:
            return jsonify({"error": "No log file exists yet"}), 404
    
    except Exception as e:
        logger.exception(f"Error retrieving document status: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route('/feedback/v2/<document_id>', methods=['POST'])
def document_feedback_v2(document_id):
    """Submit feedback for a document (V2)"""
    try:
        # Validate content type
        if request.headers.get('Content-Type') != 'application/json':
            return jsonify({"error": "Content-Type must be application/json"}), 415
        
        # Validate feedback data
        feedback_data = request.json
        if not feedback_data:
            return jsonify({"error": "Missing feedback data"}), 400
        
        if 'corrections' not in feedback_data and 'comment' not in feedback_data:
            return jsonify({"error": "Must provide either corrections or comment"}), 400
        
        # Add document ID and timestamp to feedback
        feedback_data['document_id'] = document_id
        feedback_data['timestamp'] = datetime.utcnow().isoformat() + "Z"
        
        # Save feedback to file
        feedback_dir = os.path.join(log_path, 'feedback')
        os.makedirs(feedback_dir, exist_ok=True)
        
        feedback_file = os.path.join(feedback_dir, f"{document_id}_feedback.json")
        with open(feedback_file, 'w') as f:
            json.dump(feedback_data, f, indent=2)
        
        # Log the feedback
        logger.info(f"Feedback received for document {document_id}")
        save_document_lifecycle(document_id, "COMPLETED", "FLAGGED", "feedback_handler_v2", "User feedback received")
        
        # Notify n8n workflow about feedback
        notify_n8n_workflow({
            "document_id": document_id,
            "event_type": "feedback",
            "feedback": feedback_data
        })
        
        return jsonify({
            "status": "success",
            "message": "Feedback received",
            "document_id": document_id,
            "timestamp": feedback_data['timestamp']
        }), 200
    
    except Exception as e:
        logger.exception(f"Error processing feedback: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
    
    logger.info(f"Starting IMIS Webhook Handler V2 on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"Upload folder: {upload_folder}")
    logger.info(f"Log path: {log_path}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
