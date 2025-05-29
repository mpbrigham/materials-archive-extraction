#!/usr/bin/env python3
"""
IMIS V1 - Enhanced Webhook Handler
Production-ready implementation with proper error handling and logging
"""

import os
import json
import logging
import time
from datetime import datetime
import uuid
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
log_path = os.getenv('LOG_PATH', './logs')
os.makedirs(log_path, exist_ok=True)

logger = logging.getLogger('imis_webhook')
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)

# File handler with rotation
file_handler = RotatingFileHandler(
    os.path.join(log_path, 'webhook.log'),
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Initialize Flask app
app = Flask(__name__)

# Create storage directory
upload_folder = os.getenv('STORAGE_PATH', './storage')
os.makedirs(upload_folder, exist_ok=True)

# Configure maximum allowed upload size - 20MB
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024


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
    
    lifecycle_log_path = os.path.join(log_path, 'document_lifecycle.json')
    
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


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Main webhook handler endpoint"""
    start_time = time.time()
    document_id = f"doc-{uuid.uuid4()}"
    
    try:
        # Check content type
        content_type = request.headers.get('Content-Type', '')
        
        if 'multipart/form-data' in content_type:
            # Handle file upload
            if 'file' not in request.files:
                logger.warning(f"No file part in request")
                save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler", "No file in request")
                return jsonify({"error": "No file part"}), 400
                
            file = request.files['file']
            
            if file.filename == '':
                logger.warning(f"No file selected")
                save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler", "Empty filename")
                return jsonify({"error": "No file selected"}), 400
                
            if file:
                # Security: use secure_filename to prevent path traversal
                filename = secure_filename(file.filename)
                
                # Only accept PDFs
                if not filename.lower().endswith('.pdf'):
                    logger.warning(f"Invalid file type: {filename}")
                    save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler", "Not a PDF file")
                    return jsonify({"error": "Only PDF files are accepted"}), 400
                
                # Create unique filename with timestamp and document ID
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                safe_filename = f"{timestamp}_{document_id}_{filename}"
                filepath = os.path.join(upload_folder, safe_filename)
                
                # Save the file
                file.save(filepath)
                logger.info(f"File saved: {filepath}")
                
                # Log document lifecycle
                save_document_lifecycle(document_id, "RECEIVED", "STORED", "webhook_handler", f"File saved as {safe_filename}")
                
                # Prepare response for n8n
                # In production, this would trigger the n8n workflow
                response = {
                    "task": "extract_metadata",
                    "file_path": filepath,
                    "document_type": "supplier_material",
                    "sender": request.form.get('sender', 'unknown'),
                    "subject": request.form.get('subject', filename),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "document_id": document_id
                }
                
                logger.info(f"Webhook processed in {time.time() - start_time:.2f}s")
                return jsonify(response), 200
        
        elif 'application/json' in content_type:
            # Handle JSON input (e.g., for OCR text that's already extracted)
            data = request.json
            
            # Validate required fields
            if not data.get('text'):
                logger.warning("Missing 'text' field in JSON payload")
                save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler", "Missing 'text' field")
                return jsonify({"error": "Missing 'text' field"}), 400
            
            # Log received data to file for processing
            text_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{document_id}.txt"
            text_filepath = os.path.join(upload_folder, text_filename)
            
            with open(text_filepath, 'w') as f:
                f.write(data['text'])
            
            logger.info(f"OCR text saved: {text_filepath}")
            save_document_lifecycle(document_id, "RECEIVED", "STORED", "webhook_handler", "OCR text saved")
            
            # Prepare response for n8n
            response = {
                "task": "extract_metadata",
                "file_path": text_filepath,
                "document_type": "supplier_material_ocr",
                "sender": data.get('sender', 'unknown'),
                "subject": data.get('subject', 'OCR Text'),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "document_id": document_id
            }
            
            logger.info(f"Webhook processed in {time.time() - start_time:.2f}s")
            return jsonify(response), 200
        
        else:
            logger.warning(f"Unsupported content type: {content_type}")
            save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler", f"Unsupported content type: {content_type}")
            return jsonify({"error": "Unsupported content type"}), 415
    
    except Exception as e:
        logger.exception(f"Error processing webhook: {str(e)}")
        save_document_lifecycle(document_id, "RECEIVED", "FAILED", "webhook_handler", f"Exception: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "v1.2.1"
    }), 200


@app.route('/status/<document_id>', methods=['GET'])
def document_status(document_id):
    """Get processing status for a specific document"""
    lifecycle_log_path = os.path.join(log_path, 'document_lifecycle.json')
    
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


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
    
    logger.info(f"Starting IMIS Webhook Handler v1.2.1 on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"Upload folder: {upload_folder}")
    logger.info(f"Log path: {log_path}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
