import os
import logging
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO)

@app.route('/upload', methods=['POST'])
def handle_upload():
    try:
        if 'file' not in request.files:
            raise ValueError("Missing 'file' field in upload.")

        file = request.files['file']
        if file.filename == '':
            raise ValueError("Empty filename in uploaded file.")

        if not file.filename.endswith('.pdf'):
            raise ValueError("Only PDF files are supported.")

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        logging.info(f"Received and saved file: {filepath}")
        return jsonify({"status": "success", "path": filepath}), 200

    except Exception as e:
        logging.error(f"Upload failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(port=8080)