# IMIS V1 Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Intelligent Materials Intake System (IMIS) V1 pipeline to a production environment.

## Prerequisites

- Python 3.8+ with pip
- n8n installed and configured
- SMTP server access for email notifications
- IMAP server access for email monitoring
- API keys for your chosen LLM provider (OpenAI, Gemini, or Anthropic)

## Installation Steps

### 1. Prepare the Environment

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask requests python-dotenv werkzeug
```

### 2. Configure Environment Variables

Copy the provided `.env` file to your deployment directory and update the values:

```bash
# Copy the template
cp env-config.txt .env

# Edit the configuration
nano .env  # or use any text editor
```

Ensure all credentials, API keys, and server details are correctly set.

### 3. Create Required Directories

```bash
mkdir -p storage logs
chmod 755 storage logs
```

### 4. Set Up n8n Workflow

1. Start n8n: `n8n start`
2. Access the n8n web interface (default: http://localhost:5678)
3. Import the provided `workflow_Materials_Intake_FullFlow.json`
4. Update API credentials in the n8n UI
5. Create n8n environment variables matching your `.env` file
6. Activate the workflow

### 5. Deploy the Webhook Handler

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
Description=IMIS Webhook Handler
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

### 6. Test the Deployment

Run the testing script to verify everything is working correctly:

```bash
python testing_script.py --webhook http://localhost:5000/webhook
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
cp $IMIS_DIR/workflow_Materials_Intake_FullFlow.json $BACKUP_DIR/$TIMESTAMP/

# Backup uploaded files (optional, could be large)
# cp -r $IMIS_DIR/storage $BACKUP_DIR/$TIMESTAMP/

# Compress backup
cd $BACKUP_DIR
tar -czf imis_backup_$TIMESTAMP.tar.gz $TIMESTAMP
rm -rf $TIMESTAMP

# Prune old backups (keep last 30 days)
find $BACKUP_DIR -name "imis_backup_*.tar.gz" -mtime +30 -delete
```

### Security Considerations

1. Set up SSL/TLS for the webhook endpoint
2. Configure API rate limiting
3. Implement IP whitelisting if applicable
4. Use environment variables for all sensitive data
5. Regularly rotate API keys and credentials

## Scaling Strategies

### Horizontal Scaling

1. Deploy multiple instances of the webhook handler
2. Set up a load balancer (Nginx, HAProxy)
3. Configure sticky sessions if needed

### Vertical Scaling

1. Increase resources (CPU, RAM) for the webhook server
2. Optimize database queries and file operations
3. Tune n8n performance settings

## Troubleshooting

### Common Issues

1. **Webhook unavailable**: Check if the service is running with `systemctl status imis-webhook`
2. **n8n workflow not triggering**: Verify webhook connections and credentials
3. **Email notifications not sending**: Check SMTP settings and server accessibility
4. **Missing PDFs or logs**: Verify directory permissions

### Debugging Steps

1. Check application logs: `/path/to/imis/logs/webhook.log`
2. Check systemd logs: `journalctl -u imis-webhook`
3. Test endpoints manually with curl:
   ```
   curl -X GET http://localhost:5000/health
   ```

## Support and Resources

- For bug reports and feature requests, create an issue in the repository
- Review the `PROMPT_DESIGN_GUIDELINES.txt` for LLM optimization
- Check `CONFIDENCE_POLICY_GUIDELINES_v1.txt` for tuning verification thresholds

## Version Management

When upgrading to newer versions of IMIS:

1. Back up all configurations and data
2. Review the release notes for breaking changes
3. Test in a staging environment before production deployment
4. Update prompt templates if model versions have changed
