# IMIS V1.5 Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Intelligent Materials Intake System (IMIS) V1.5 pipeline with enhanced visual verification to a production environment.

## Prerequisites

- Python 3.8+ with pip
- n8n installed and configured
- SMTP server access for email notifications
- IMAP server access for email monitoring
- API keys for a vision-capable LLM provider (Gemini Pro Vision, Claude 3, etc.)
- Poppler-utils for PDF processing

## Installation Steps

### 1. Prepare the Environment

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask requests python-dotenv werkzeug pdf2image pillow

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y poppler-utils

# For CentOS/RHEL
# sudo yum install poppler-utils
```

### 2. Configure Environment Variables

Copy the provided environment template to your deployment directory and update the values:

```bash
# Copy the template
cp env-template.txt .env

# Edit the configuration
nano .env  # or use any text editor
```

Ensure all credentials, API keys, and vision model details are correctly set.

### 3. Create Required Directories

```bash
# Create main directories
mkdir -p storage logs

# Create subdirectories for image processing
mkdir -p storage/pages storage/crops

# Set permissions
chmod 755 storage logs storage/pages storage/crops
```

### 4. Set Up n8n Workflow

1. Start n8n: `n8n start`
2. Access the n8n web interface (default: http://localhost:5678)
3. Import the V1.5 workflow file: `workflow_Materials_Intake_V1.5.json`
4. Update API credentials in the n8n UI
5. Create n8n environment variables matching your `.env` file:
   - Add `LLM_VISION_API_ENDPOINT` for multimodal model access
   - Add `LLM_VISION_MODEL` for the model capable of PDF analysis (e.g., gemini-pro-vision, claude-3-opus)
   - Set `STORAGE_PATH` for image storage
   - Set `PROMPTS_PATH` for prompt file locations
6. Install required system dependencies:
   ```bash
   # For PDF image processing
   apt-get update
   apt-get install -y poppler-utils
   ```
7. Install Python dependencies:
   ```bash
   pip install pdf2image pillow
   ```
8. Activate the workflow

> Note: This V1.5 workflow uses a multi-turn visual verification approach for higher accuracy and better evidence collection.

### 5. Validate the Installation

Run the validation script to ensure all components are correctly installed and configured:

```bash
# Run validation script
python scripts/validate_v1.5_setup.py

# If webhook is not running yet (skip API check)
python scripts/validate_v1.5_setup.py --skip-api-check
```

This script will:
- Check system dependencies including poppler-utils
- Verify required Python packages
- Test image processing capabilities
- Validate directory structure and permissions
- Verify environment variables are properly set
- Check n8n workflow files
- Test the webhook if running
- Verify prompt files

If any issues are found, the script provides detailed error messages and remediation steps.

### 6. Deploy the Webhook Handler

```bash
# Start the webhook handler
python webhook_handler.py

# For production use with gunicorn:
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 'webhook_handler:app'

# For deployment with systemd, create a service file:
sudo nano /etc/systemd/system/imis-webhook.service
```

Example systemd service file:

```ini
[Unit]
Description=IMIS V1.5 Webhook Handler
After=network.target

[Service]
User=imis
WorkingDirectory=/path/to/imis/folder
Environment="PATH=/path/to/imis/venv/bin"
ExecStart=/path/to/imis/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 'webhook_handler:app'
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable imis-webhook
sudo systemctl start imis-webhook
```

### 7. Test the Deployment

Run the testing script to verify everything is working correctly:

```bash
python testing_script.py --webhook http://localhost:5000/webhook
```

## Image Processing Configuration

The enhanced visual verification requires additional configuration for optimal image processing:

### Image Quality Settings

In the `.env` file, configure the following settings:

```
# Image processing settings
PDF_DPI=300
CROP_PADDING=20
IMAGE_FORMAT=jpg
IMAGE_QUALITY=85
```

### Storage Management

Due to increased storage requirements for images:

```bash
# Set up automatic cleanup of old images (keep last 30 days)
cat > /etc/cron.daily/imis-cleanup << 'EOF'
#!/bin/bash
find /path/to/imis/storage/pages -type f -mtime +30 -delete
find /path/to/imis/storage/crops -type f -mtime +30 -delete
EOF
chmod +x /etc/cron.daily/imis-cleanup
```

## Monitoring and Maintenance

### Health Checks

The webhook server provides a health check endpoint:

```
GET http://your-server:5000/health
```

Configure monitoring to periodically check this endpoint.

### Log Rotation

Log files are managed with rotation by the application, but it's recommended to also configure system-level log rotation:

```bash
sudo nano /etc/logrotate.d/imis
```

Example config:

```
/path/to/imis/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 imis imis
}
```

### Backup Strategy

1. Schedule regular backups of:
   - Document lifecycle logs
   - Uploaded PDF files
   - Configuration files
   - Generated image evidence

2. Example backup script:

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
IMIS_DIR="/path/to/imis"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$TIMESTAMP

# Backup logs and configuration
cp -r $IMIS_DIR/logs $BACKUP_DIR/$TIMESTAMP/
cp $IMIS_DIR/.env $BACKUP_DIR/$TIMESTAMP/
cp $IMIS_DIR/workflow_Materials_Intake_V1.5.json $BACKUP_DIR/$TIMESTAMP/
cp $IMIS_DIR/scripts/*.js $BACKUP_DIR/$TIMESTAMP/
cp -r $IMIS_DIR/prompts $BACKUP_DIR/$TIMESTAMP/

# Backup important evidence (most recent only)
find $IMIS_DIR/storage -type f -mtime -7 -exec cp --parents {} $BACKUP_DIR/$TIMESTAMP/ \;

# Compress backup
cd $BACKUP_DIR
tar -czf imis_backup_$TIMESTAMP.tar.gz $TIMESTAMP
rm -rf $TIMESTAMP

# Prune old backups (keep last 30 days)
find $BACKUP_DIR -name "imis_backup_*.tar.gz" -mtime +30 -delete
```

## Performance Tuning

### Vision Model Optimization

1. Configure batch sizes for vision API calls:
   - In `.env`: `VISION_BATCH_SIZE=4` for parallel processing
   
2. Optimize image resolution:
   - Higher DPI (300+) for initial extraction
   - Lower DPI (150-200) for batch processing

### Processing Optimization

1. Parallel image processing:
   - Set thread count in `image_processing.py`: `thread_count=os.cpu_count()`
   
2. Image caching:
   - Enable caching of common crops: `ENABLE_CROP_CACHE=true`

## Troubleshooting

### Common Issues

1. **PDF conversion errors**: Ensure poppler-utils is installed and accessible
2. **Image cropping failures**: Check file permissions and paths
3. **Vision API errors**: Verify API keys and rate limits
4. **Missing evidence in reports**: Check storage permissions and paths

### Debugging Steps

1. Check application logs: `/path/to/imis/logs/webhook.log`
2. Check image processing logs: `/path/to/imis/logs/image_processor.log`
3. Test PDF conversion manually:
   ```
   python -m scripts.utils.image_processing paginate /path/to/test.pdf --output ./test_output
   ```

## Version Management

When upgrading from V1 to V1.5:

1. Back up all configurations and data
2. Install the new dependencies for image processing
3. Update the n8n workflow to the V1.5 version
4. Validate with test documents before full deployment
5. Monitor storage usage more closely due to increased image storage