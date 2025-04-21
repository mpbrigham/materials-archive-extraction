# V3 Intent-Driven Minimalism: Deployment Guide

This guide provides comprehensive instructions for deploying the V3 Intent-Driven Minimalism version of the Intelligent Materials Intake System (IMIS) in a production environment.

## Prerequisites

- Python 3.8+ with pip
- n8n 0.214.0+ installed and configured
- SMTP server for sending email notifications
- IMAP server for monitoring incoming emails
- API key for your chosen LLM provider (OpenAI, Gemini, or Anthropic)
- Optional: Slack workspace for notifications

## Installation Steps

### 1. Environment Setup

```bash
# Create a project directory
mkdir -p imis-v3
cd imis-v3

# Create and activate Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask requests python-dotenv werkzeug gunicorn pyjwt cryptography
```

### 2. Project Structure

Create the necessary directory structure:

```bash
# Create core directories
mkdir -p storage archives feedback logs prompts

# Create log subdirectories
mkdir -p logs/feedback logs/archive
```

### 3. Configuration

Copy the example environment configuration file and customize it:

```bash
# Copy the template
cp .env.example .env

# Edit the configuration
nano .env  # Or use any text editor
```

Ensure you update all settings according to your environment, especially:
- LLM API credentials
- Email settings
- Security parameters
- Storage paths

### 4. Webhook Server Setup

#### Development Mode

For testing and development:

```bash
# Start the webhook server directly
python webhook_handler.py
```

#### Production Mode

For production deployment, use Gunicorn:

```bash
# Install gunicorn if not already installed
pip install gunicorn

# Start with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 'webhook_handler:app'
```

#### Systemd Service Configuration

For reliable operation in production, create a systemd service:

```bash
# Create service file
sudo nano /etc/systemd/system/imis-webhook-v3.service
```

Example systemd service file:

```ini
[Unit]
Description=IMIS V3 Webhook Handler
After=network.target

[Service]
User=imis
WorkingDirectory=/path/to/imis-v3
Environment="PATH=/path/to/imis-v3/venv/bin"
EnvironmentFile=/path/to/imis-v3/.env
ExecStart=/path/to/imis-v3/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 'webhook_handler:app'
Restart=always
RestartSec=5
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable imis-webhook-v3
sudo systemctl start imis-webhook-v3
```

### 5. n8n Workflow Configuration

1. Start your n8n instance:
   ```bash
   n8n start
   ```

2. Import the workflow into n8n:
   - Open the n8n web interface (default: http://localhost:5678)
   - Navigate to Workflows → Import from File
   - Select `workflow_intent_driven.json`

3. Configure Credentials:
   - In n8n, go to Settings → Credentials
   - Add credentials for:
     - IMAP Email
     - SMTP Email
     - LLM API (OpenAI, Gemini, or Anthropic)
     - Slack (if using notifications)

4. Set up n8n Environment Variables:
   - In n8n, go to Settings → Variables
   - Create variables that match your `.env` file keys
   - These will be referenced in the workflow using `$env`

5. Activate the Workflow:
   - Open the imported workflow
   - Click the "Activate" toggle in the top-right corner

### 6. Prompt Configuration

Ensure that the prompt files are properly placed in the prompts directory:

```bash
# Copy the prompt files to the prompts directory
cp AGENT_PROMPT.txt prompts/
```

Verify that the `PROMPTS_PATH` variable in your `.env` file points to this directory.

### 7. Testing

Run the comprehensive testing script to verify your installation:

```bash
python testing_script.py
```

For more targeted testing:

```bash
# Test with specific samples
python testing_script.py --samples ./specific_sample_folder

# Test with API key authentication
python testing_script.py --api-key your-api-key

# Test with feedback submission
python testing_script.py --test-feedback

# Run multiple tests in parallel
python testing_script.py --parallel 4
```

## Production Hardening

### Security Configuration

1. HTTPS Setup with Nginx:

```nginx
server {
    listen 443 ssl;
    server_name intake.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/intake.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/intake.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'" always;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name intake.yourdomain.com;
    return 301 https://$host$request_uri;
}
```

2. API Key Management:

Configure multiple API keys for different integration points and rotate them regularly:

```bash
# In your .env file
API_KEYS=key1,key2,key3
```

3. Rate Limiting:

Enable rate limiting in your `.env` file:

```bash
ENABLE_API_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=60
```

### Monitoring Setup

1. Prometheus Integration:

To monitor the health and performance of the V3 system, install a Prometheus exporter:

```bash
pip install prometheus-flask-exporter
```

Add this to your `webhook_handler.py`:

```python
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)
```

2. Grafana Dashboard:

Create a Grafana dashboard to visualize metrics:
- Request rates and response times
- Error rates
- Document processing status
- Queue lengths
- System resource usage

3. Alerting:

Set up alerts for critical conditions:
- High error rates
- Slow processing times
- Service unavailability
- Disk space issues

### Backup Strategy

1. Document Data Backup:

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/path/to/backups/v3"
IMIS_DIR="/path/to/imis-v3"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$TIMESTAMP

# Backup documents and metadata
cp -r $IMIS_DIR/storage $BACKUP_DIR/$TIMESTAMP/
cp -r $IMIS_DIR/archives $BACKUP_DIR/$TIMESTAMP/
cp -r $IMIS_DIR/feedback $BACKUP_DIR/$TIMESTAMP/

# Backup logs
cp -r $IMIS_DIR/logs $BACKUP_DIR/$TIMESTAMP/

# Backup configuration
cp $IMIS_DIR/.env $BACKUP_DIR/$TIMESTAMP/
cp $IMIS_DIR/workflow_intent_driven.json $BACKUP_DIR/$TIMESTAMP/

# Compress
tar -czf $BACKUP_DIR/imis_v3_backup_$TIMESTAMP.tar.gz -C $BACKUP_DIR $TIMESTAMP
rm -rf $BACKUP_DIR/$TIMESTAMP

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "imis_v3_backup_*.tar.gz" -mtime +30 -delete
```

2. Database Backup (if using a database):

If you've integrated a database for storing document lifecycle, set up regular backups:

```bash
# For PostgreSQL
pg_dump -U username -h localhost imis_db > $BACKUP_DIR/$TIMESTAMP/imis_db.sql
```

3. Automated Schedule:

Add to crontab:
```
0 2 * * * /path/to/backup.sh
```

## Scaling Strategies

### Horizontal Scaling

1. Load Balancer Configuration:

Deploy multiple webhook handlers behind a load balancer:

```nginx
upstream imis_webhook {
    server backend1.example.com:5000;
    server backend2.example.com:5000;
    server backend3.example.com:5000;
}

server {
    listen 443 ssl;
    server_name intake.yourdomain.com;
    
    # SSL configuration...
    
    location / {
        proxy_pass http://imis_webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. State Management:

For a distributed deployment, use Redis for shared state:

```bash
pip install redis
```

Update your webhook handler to use Redis for rate limiting and state coordination.

### Advanced Queue Architecture

For high-volume processing, implement a message queue:

1. Install and configure RabbitMQ or Kafka

2. Modify the webhook handler to queue documents:

```python
def enqueue_document(request_id, file_path):
    """Add document to processing queue"""
    message = {
        'request_id': request_id,
        'file_path': file_path,
        'timestamp': datetime.utcnow().isoformat() + "Z"
    }
    publish_to_queue('documents_to_process', message)
```

3. Create worker processes to handle the queue:

```python
def process_queue():
    """Worker to process documents from queue"""
    while True:
        message = consume_from_queue('documents_to_process')
        if message:
            process_document(message['request_id'], message['file_path'])
```

## Troubleshooting

### Common Issues

1. **API Connectivity Issues**:
   - Check if the LLM API key is valid and has sufficient quota
   - Verify network connectivity from the server to the API
   - Check if any firewalls are blocking requests

2. **Document Processing Failures**:
   - Check the document lifecycle logs for errors
   - Verify that the document is a valid PDF or text
   - Check if the LLM is generating valid JSON output

3. **Email Delivery Issues**:
   - Verify SMTP credentials and server connectivity
   - Check spam filters are not blocking automated emails
   - Verify email templates are correctly formatted

### Diagnostic Commands

```bash
# Check webhook server status
systemctl status imis-webhook-v3

# View logs
journalctl -u imis-webhook-v3 -f

# Test webhook directly
curl -X POST -H "Content-Type: application/json" -d '{"text":"Sample text"}' http://localhost:5000/v3/webhook

# Check document status
curl http://localhost:5000/v3/status/req-123456
```

## Upgrade Path

When upgrading from an earlier version:

1. Back up all data and configurations
2. Deploy the new version alongside the existing one
3. Test thoroughly before switching traffic
4. Implement a migration strategy for existing documents
5. Update external integrations to use new APIs

## Maintenance

Regular maintenance tasks:

1. Update dependencies monthly
2. Review and rotate API keys quarterly
3. Check and optimize storage usage weekly
4. Review logs for error patterns
5. Test the backup and restore process

## Contact & Support

For issues with deployment, check:
- System logs for detailed error messages
- The GitHub repository for known issues
- The documentation for updated instructions

## Appendix: Advanced Configuration

### Using Custom SSL Certificates with Flask

To configure the webhook server to use SSL directly:

```bash
# Generate self-signed certs for development
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Update .env
USE_SSL=true
SSL_CERT=/path/to/cert.pem
SSL_KEY=/path/to/key.pem
```

### Configuring Document Storage with S3

For cloud-based document storage:

```bash
# Install boto3
pip install boto3

# Update .env
STORAGE_TYPE=s3
S3_BUCKET=imis-documents
S3_PREFIX=v3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2
```

Modify the webhook handler to use S3 for storage operations.
