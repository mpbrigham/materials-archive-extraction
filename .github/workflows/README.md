# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the Materials Archive Extraction project.

## Workflows

### deploy-materials-extraction.yml
**Path-based deployment workflow** that automatically deploys changes to production based on which directories were modified.

- **Trigger**: Push to `v0_initial_flow` branch
- **n8n Deployment**: Triggered by changes in `v0_initial_flow/` directory
- **ActivePieces Deployment**: Triggered by changes in `v0_initial_flow_ap/` directory
- **Smart Detection**: Only tests and deploys what changed

### validate_output.yml
Validates the output structure of extraction results against defined schemas.

## Required GitHub Secrets

Configure these in your repository settings under Settings > Secrets and variables > Actions:

```bash
# Server Access
DEPLOY_HOST           # Production server IP address
DEPLOY_SSH_KEY        # SSH private key for deployment user

# Email Configuration
IMAP_HOST            # IMAP server hostname
IMAP_PORT            # IMAP port (usually 993)
SMTP_HOST            # SMTP server hostname
SMTP_PORT            # SMTP port (usually 465 or 587)
EMAIL_USER           # Email account username
EMAIL_PASS           # Email account password

# LLM Configuration
LLM_API_KEY          # Gemini API key
LLM_MODEL            # Model name (e.g., gemini-2.0-flash)

# n8n Specific
N8N_ENCRYPTION_KEY   # n8n encryption key (32+ chars)
```

## Deployment Strategy

The project uses a **monorepo with path-based triggers**:

1. Both n8n and ActivePieces versions live in the same repository
2. Changes to specific directories trigger specific deployments
3. Shared resources (prompts, schemas) can be symlinked
4. Single branch (`v0_initial_flow`) for both versions

## Monitoring

- Check the Actions tab in GitHub for deployment status
- Each deployment run shows which components were deployed
- Failed deployments include detailed error logs

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Test the deployment workflow
act push -W .github/workflows/deploy-materials-extraction.yml
```
