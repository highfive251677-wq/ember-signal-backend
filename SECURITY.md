# Security Policy

## Reporting a vulnerability

Do not open a public issue containing credentials, private data, exploit details, or an active vulnerability. Contact the repository maintainers privately through the GitHub repository owner.

## Secrets

Never commit Railway, Render, PythonAnywhere, Cloudflare, OpenRouter, GitHub, SSH, database, or signing credentials. Store them in the provider's secret manager or CI secret store. If a credential appears in chat, logs, a screenshot, an attachment, or Git history, revoke it immediately and issue a replacement.

## Deployment safety

Release automation is read-only by default. Deployment and reload actions require explicit flags and should be run only after health checks and data-quality review pass. Runtime SQLite files must not be treated as source code or committed working data.
