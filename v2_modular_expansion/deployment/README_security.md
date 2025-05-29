# Security Enhancements for V2_Linear_Flow

## Email Credential Security
- All sensitive values (e.g., IMAP username/password) should be stored in a `.env` file or secret manager.
- Example `.env` template is included: `imap_settings_secure_template.env`

## Recommended Practices
- Use OAuth or App Passwords when available.
- Configure `.gitignore` to exclude `.env` files.
- Rotate credentials regularly.

## Node Secrets in n8n
- Use n8n credential storage for IMAP and SMTP nodes.
- Avoid exposing values in Function nodes or hardcoded text fields.