# V2 Deployment Guide

This guide provides comprehensive instructions for deploying the V2 Modular Expansion version of the Intelligent Materials Intake System (IMIS) in a production environment.

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
# Create and activate Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask requests python-dotenv werkzeug gunicorn
```

### 2. Configuration

Copy the example environment configuration file and customize it:

```bash
# Copy the template
cp .env.example .env

# Edit the configuration
nano .env  # Or use any text editor
```

Ensure that you update all the settings according to your environment, especially:
- Email credentials
- LLM API keys
- Storage paths
- Webhook URLs

### 3. Directory Structure

Create the necessary directories for logs, storage, and prompts:

```bash
# Create required directories
mkdir -p storage logs logs/feedback prompts
```

Copy the prompt files to the prompts directory:

```bash
cp metadata_extraction_prompt.txt prompts/
cp verifier_agent_prompt.txt prompts/
```

### 4. n8n Workflow Configuration

1. Start your n8n instance:
   ```bash
   n8n start
   ```

2. Import the workflow into n8n:
   - Open the n8n web interface (default: http://localhost:5678)
   - Navigate to Workflows → Import from File
   - Select `workflow_Materials_Intake_FullFlow.json`

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

### 5. Webhook Server Deployment

For testing environments, start the webhook server directly:

```bash
# Start the webhook server
python webhook_handler.py
```

For production environments, use a proper WSGI server:

```bash
# Install gunicorn (if not already installed)
pip install gunicorn

# Start with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 'webhook_handler:app'
```

### 6. Systemd Service Configuration (Production)

For reliable operation in production, create a systemd service:

```bash
# Create service file
sudo nano /etc/systemd/system/imis-webhook-v2.service
```

Example systemd service file:

```ini
[Unit]
Description=IMIS V2 Webhook Handler
After=network.target

[Service]
User=imis
WorkingDirectory=/path/to/imis/V2_Modular_Expansion
Environment="PATH=/path/to/imis/venv/bin"
EnvironmentFile=/path/to/imis/V2_Modular_Expansion/.env
ExecStart=/path/to/imis/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 'webhook_handler:app'
Restart=always
RestartSec=5
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable imis-webhook-v2
sudo systemctl start imis-webhook-v2
```

### 7. Testing the Deployment

Run the comprehensive testing script to verify your installation:

```bash
python testing_script.py
```

For more targeted testing:

```bash
# Test with just one sample file
python testing_script.py --samples ./specific_sample_folder

# Test with feedback submission
python testing_script.py --test-feedback

# Set custom timeout
python testing_script.py --timeout 600
```

## Production Hardening

### Security Configuration

1. Set up HTTPS:
   - Use a reverse proxy (Nginx, Apache) with Let's Encrypt
   - Example Nginx configuration:

```nginx
server {
    listen 443 ssl;
    server_name intake.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/intake.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/intake.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. Enable rate limiting:
   - Set `ENABLE_API_RATE_LIMITING=true` in your `.env` file
   - Adjust `MAX_REQUESTS_PER_MINUTE` as needed

3. Use secure credential storage:
   - Consider using a secrets manager like HashiCorp Vault
   - Update your code to fetch credentials from the manager

### Monitoring and Alerting

1. Set up health check monitoring:
   - Configure a monitoring service (Prometheus, Grafana, Datadog)
   - Monitor the `/health` endpoint
   - Set up alerts for service disruptions

2. Log monitoring:
   - Send structured logs to a log management system
   - Track errors and performance issues
   - Set up alerts for critical errors

### Backup Strategy

1. Set up regular backups:
   ```bash
   #!/bin/bash
   # backup.sh
   BACKUP_DIR="/path/to/backups/v2"
   IMIS_DIR="/path/to/imis/V2_Modular_Expansion"
   TIMESTAMP=$(date +%Y%m%d%H%M%S)

   # Create backup directory
   mkdir -p $BACKUP_DIR/$TIMESTAMP

   # Backup configuration and logs
   cp -r $IMIS_DIR/logs $BACKUP_DIR/$TIMESTAMP/
   cp $IMIS_DIR/.env $BACKUP_DIR/$TIMESTAMP/
   cp $IMIS_DIR/workflow_Materials_Intake_FullFlow.json $BACKUP_DIR/$TIMESTAMP/

   # Compress the backup
   tar -czf $BACKUP_DIR/imis_v2_backup_$TIMESTAMP.tar.gz -C $BACKUP_DIR $TIMESTAMP
   rm -rf $BACKUP_DIR/$TIMESTAMP

   # Cleanup old backups (keep last 30 days)
   find $BACKUP_DIR -name "imis_v2_backup_*.tar.gz" -mtime +30 -delete
   ```

2. Add to crontab:
   ```
   0 1 * * * /path/to/backup.sh
   ```

## Scaling Strategies

### Horizontal Scaling

1. Deploy multiple webhook handlers behind a load balancer
2. Use a shared database for document lifecycle logging
3. Configure sticky sessions for document processing

### Vertical Scaling

1. Increase resources (CPU, RAM) for webhook server
2. Optimize database and file operations
3. Tune n8n for better performance

### Queue-Based Architecture (Advanced)

For high-volume deployments, consider:
1. Adding a message queue (RabbitMQ, Kafka)
2. Separating document reception from processing
3. Using worker pools for parallel processing

## Troubleshooting

### Common Issues

1. **Webhook server doesn't start:**
   - Check Python version (3.8+ required)
   - Verify all dependencies are installed
   - Check port availability

2. **n8n workflow fails:**
   - Verify credentials in n8n
   - Check environment variables
   - Examine n8n execution logs
   - Validate that the webhook URL is correct and accessible

3. **LLM API errors:**
   - Verify API key and permissions
   - Check quota and rate limits
   - Ensure endpoint URLs are correct

4. **Email notifications not working:**
   - Validate SMTP credentials
   - Check for email service restrictions
   - Verify recipient email addresses

### Logs and Diagnostics

- Webhook logs: `logs/webhook_v2.log`
- Document lifecycle: `logs/document_lifecycle_v2.json`
- Structured logs: `logs/webhook_structured.json`
- n8n logs: Available in the n8n web interface

## Upgrade Path

When upgrading from V1:

1. Back up all V1 data and configurations
2. Install V2 in a separate directory
3. Migrate relevant configurations (email settings, etc.)
4. Test thoroughly before switching production traffic

## Maintenance

Regular maintenance tasks:

1. Monitor disk usage in storage and log directories
2. Rotate and archive logs
3. Update Python dependencies
4. Check for LLM API changes and adjust as needed
5. Review and optimize n8n workflows

## Support and Resources

- For issues with the webhook server, check the logs and the health endpoint
- For workflow issues, review n8n execution history
- Document all deployment-specific configurations for future reference

## Appendix: Environment Variables Reference

See `.env.example` for a complete list of configurable options with descriptions.

## Appendix: API Endpoints

- `/webhook/v2` - Main document intake endpoint (POST)
- `/health` - System health check (GET)
- `/status/v2/{document_id}` - Document status check (GET)
- `/feedback/v2/{document_id}` - Submit feedback for a document (POST)
