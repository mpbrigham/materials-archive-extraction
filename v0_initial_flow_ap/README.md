# Materials Intake Pipeline - ActivePieces Implementation

Email → PDF extraction → LLM metadata → Send results

## Core Workflow

**Request-response email service:**
1. User sends email with PDF attachments to bot@brigham.be
2. Bot extracts materials metadata from PDFs using Gemini AI
3. Bot emails results back to the original sender

## Architecture

IMAP Trigger → Read Config → Document Validator → Loop → LLM Extraction → Result Processor → Send Email

## Key Differences from n8n Version

This is a migration from n8n to ActivePieces with the following changes:

### 1. **Platform**
- **n8n**: Traditional workflow automation
- **ActivePieces**: Modern workflow automation with different architecture

### 2. **File Handling**
- **n8n**: Direct binary data access (`item.binary.pdf.data`)
- **ActivePieces**: File references (likely `"db://..."` format)
- Debug logging added to capture actual attachment structure

### 3. **Configuration**
- No silent fallbacks - fails fast on missing configuration
- Direct model name via `LLM_MODEL` env var (no endpoint parsing)
- All paths hardcoded to `/data/` (container volume)

### 4. **Error Philosophy**
- Explicit error throwing for missing values
- No default values or assumptions
- Better to fail immediately than process incorrectly

## Environment Variables

```bash
# Email Configuration
IMAP_HOST='imap.hostinger.com'
IMAP_PORT=993
SMTP_HOST='smtp.hostinger.com'
SMTP_PORT=465
EMAIL_USER='bot@brigham.be'
EMAIL_PASS='your-password'

# LLM Configuration
LLM_API_KEY='your-gemini-api-key'
LLM_MODEL='gemini-2.5-flash'  # No fallback - required
```

## Files

```
.
├── activepieces.json                        # ActivePieces workflow definition
├── docker-compose.yml                       # Container setup
├── .env                                     # Environment configuration
├── prompts/
│   └── llm_extraction.txt                   # LLM prompt
├── schema/
│   └── materials_schema.json                # Data structure definition
├── email_templates/
│   ├── success.html                         # Success template
│   └── failure.html                         # Error template
├── docs/
│   └── MIGRATION_NOTES.md                   # Detailed migration notes
└── tests/
    └── debug-attachments.js                 # Attachment structure debugger
```

## Debugging

The implementation includes comprehensive debug logging:

1. **All nodes log input/output** to `/data/debug.log`
2. **Attachment structure debugging** in LLM Extraction node
3. **No silent failures** - explicit errors for missing data

### To Debug Attachments:
1. Send test email with PDFs
2. Check `/data/debug.log` for "attachment-debug" entries
3. Update code based on actual attachment format

## Current Status

⚠️ **Attachment Handling Needs Verification**

The code currently throws an informative error when processing attachments, logging the actual structure provided by ActivePieces. This is intentional - we need to see the real attachment format before implementing the handler.

## Next Steps

1. **Test with real email**:
   - Send email with PDF attachments to bot email
   - Let ActivePieces process it
   - Check debug logs for attachment structure

2. **Update attachment handling**:
   - Based on debug logs, implement proper handling
   - Remove the debug throw in `extract_metadata`

3. **Verify end-to-end**:
   - Ensure PDFs are processed correctly
   - Check email responses are formatted properly
   - Validate all error cases

## Testing

```bash
# Check debug logs after processing
tail -f /data/debug.log | grep "attachment-debug"

# View all logs
cat /data/debug.log | jq .
```

## Design Principles

1. **Fail Fast**: No silent failures or fallbacks
2. **Debug Everything**: Comprehensive logging at all stages
3. **Explicit Over Implicit**: All values must be provided
4. **Simple**: Minimal code, clear flow
5. **Complete**: Full feature parity with n8n version

## PROJECT_SPEC
```spec
NAME: Materials Library Extraction Pipeline (ActivePieces)
DOMAIN: Document Processing Automation
PRIMARY_TOOLS: ActivePieces, Gemini AI, Node.js, IMAP/SMTP, Docker
PIPELINE_STAGES:
  1. IMAP trigger receives email with attachments
  2. Read config loads prompts and templates
  3. Document validator separates email context from PDFs
  4. Loop processes each item (email context + PDFs)
  5. LLM extraction analyzes PDFs using Gemini AI
  6. Result processor combines all results into HTML
  7. Send email returns results to sender
KEY_COMPONENTS:
- `activepieces.json`: Workflow definition
- `email_templates/*.html`: Response templates
- `prompts/llm_extraction.txt`: LLM extraction prompt
- `/data/debug.log`: Debug logging output
DATA_STRUCTURE:
- Email context: First item with email metadata
- PDF items: Valid/invalid items with attachment references
- Results: HTML tables with extracted metadata
DESIGN_CONSTRAINTS:
- No silent failures or default values
- Debug logging at all stages
- File paths hardcoded to /data/
- Attachment format TBD (needs verification)
- Fails fast on any missing configuration
```
