# Deployment Guide

## Prerequisites
- Docker & Docker Compose
- Gmail with app-specific password (or IMAP/SMTP provider)
- Google Gemini API key

## Setup

### 1. Environment
```bash
cp .env.template .env
# Edit .env with your credentials:
# - IMAP_HOST, IMAP_PORT, EMAIL_USER, EMAIL_PASS
# - SMTP_HOST, SMTP_PORT
# - GEMINI_API_KEY
```

### 2. Launch
```bash
docker compose up -d
```

### 3. Configure n8n
1. Open http://localhost:5678
2. Import `materials_archive_extraction.json`
3. Add credentials:
   - IMAP: Settings → Credentials → New → IMAP
   - SMTP: Settings → Credentials → New → SMTP
4. Activate workflow

## Testing

### Quick Test
```bash
./test.sh
```

### Full Test
```bash
# Start test instance (port 5679)
./tests/test-setup.sh

# Test extraction
node tests/test-full-extraction.js
```

### Manual Test
1. Send email with PDF to configured address
2. Check n8n executions
3. Verify response email

## Operations

### Logs
```bash
docker compose logs -f n8n
tail -f data/debug.log | jq .
```

### Restart
```bash
docker compose restart n8n
```

### Stop
```bash
docker compose down
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Email not triggering | Check IMAP credentials, verify email in INBOX |
| Extraction fails | Verify GEMINI_API_KEY, check PDF validity |
| No notification | Check SMTP credentials, check spam folder |
| Port conflict | Change port in docker-compose.yml |

## File Structure

- `materials_archive_extraction.json` - n8n workflow definition
- `docker-compose.yml` - Docker configuration
- `prompts/llm_extraction.txt` - LLM extraction prompt
- `email_templates/` - Email response templates
- `data/` - Working directory (created by Docker)
  - `database.sqlite` - n8n database
  - `debug.log` - Activity logs