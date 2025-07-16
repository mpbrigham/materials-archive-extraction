# n8n vs ActivePieces Implementation Comparison

Both implementations provide the same email-to-extraction functionality but use different workflow automation platforms.

## Feature Comparison

| Feature | n8n | ActivePieces |
|---------|-----|--------------|
| **Port** | 5678 | 5679 |
| **Workflow Format** | JSON with nodes | JSON with actions |
| **Deployment Method** | Export/Import pattern | Direct configuration |
| **Database** | SQLite | PostgreSQL |
| **Additional Services** | None | Redis (for queue) |
| **Debug Logging** | Via workflow nodes | Built-in to `/data/debug.log` |
| **Error Handling** | Configurable per node | Explicit with no fallbacks |
| **UI** | Drag-and-drop canvas | Flow-based editor |

## Technical Differences

### n8n
- Uses export/import pattern for credentials and workflows
- Simpler infrastructure (just n8n container)
- Well-established in the automation community
- Extensive node library

### ActivePieces
- Direct configuration approach
- More modern architecture with PostgreSQL + Redis
- Comprehensive debug logging built-in
- Newer platform with growing ecosystem

## When to Use Which?

### Use n8n if:
- You're already familiar with n8n
- You need access to n8n's extensive node library
- You prefer a simpler infrastructure
- You want a more mature platform

### Use ActivePieces if:
- You want built-in debug logging
- You prefer PostgreSQL over SQLite
- You're exploring alternatives to n8n
- You want to try a newer platform

## Migration Between Platforms

Both implementations use the same:
- Prompts (`/prompts/llm_extraction.txt`)
- Schema (`/schema/materials_schema.json`)
- Email templates (`/email_templates/*.html`)
- Core logic flow

This makes it easy to switch between platforms if needed.

## Deployment

Both use the same GitHub Actions workflow with path-based triggers:
- Changes to `v0_initial_flow/` deploy n8n
- Changes to `v0_initial_flow_ap/` deploy ActivePieces

## Current Status

- **n8n**: Production-ready, battle-tested
- **ActivePieces**: Beta implementation, needs attachment format verification
