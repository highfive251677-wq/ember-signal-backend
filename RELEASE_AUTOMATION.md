# Ember Signal release automation

`release_orchestrator.py` is a read-only-by-default release gate that combines the available provider credentials and integrations without putting secrets in the repository.

## What it checks

| Provider | Check | Mutation behavior |
|---|---|---|
| Railway | Project-token scope, latest deployments, and latest status | Read-only |
| PythonAnywhere | Public health endpoint | Read-only unless explicit deployment is requested |
| Cloudflare | Optional zone status through `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ZONE_ID` | Read-only |
| OpenRouter | Optional concise blocker summary through `OPENROUTER_API_KEY` | Inference only |

The configured Cloudflare connector was verified with a read-only zone-list request. No Cloudflare DNS, Worker, zone, or account mutation was performed. An OpenRouter connector was not available under the requested name, so the automation supports OpenRouter through its standard HTTPS API when `OPENROUTER_API_KEY` is configured.

## Environment

```sh
export RAILWAY_TOKEN='[set privately]'
# Project tokens use the default header. For an account/workspace token:
# export RAILWAY_TOKEN_TYPE=bearer
export RAILWAY_HEALTH_URL=https://ember-signal-backend-production.up.railway.app/api/health

export PYTHONANYWHERE_USERNAME=Kbnb
export PYTHONANYWHERE_DOMAIN=kbnb.pythonanywhere.com
export PYTHONANYWHERE_API_KEY='[set privately]'
export PYTHONANYWHERE_HEALTH_URL=https://kbnb.pythonanywhere.com/api/health

# Optional direct Cloudflare API checks:
export CLOUDFLARE_API_TOKEN='[set privately]'
export CLOUDFLARE_ZONE_ID='[set privately]'

# Optional AI summary:
export OPENROUTER_API_KEY='[set privately]'
export OPENROUTER_MODEL=openai/gpt-4o-mini
```

## Read-only release gate

```sh
python3 release_orchestrator.py --json
```

The command exits `0` only when all enabled checks pass. A missing optional Cloudflare configuration is reported as skipped; a missing Railway token is reported as a blocker because Railway is part of the release comparison.

## Gated PythonAnywhere deployment

The gate can upload source files and reload PythonAnywhere only when the gate passes and the operator explicitly supplies `--apply`:

```sh
python3 release_orchestrator.py \
  --deploy-pythonanywhere \
  --source . \
  --remote /home/Kbnb/ember-signal-backend-staging \
  --apply
```

This operation uses the existing PythonAnywhere client and excludes runtime database files, `.env`, Git metadata, virtual environments, and bytecode. It does not redeploy Railway, change Cloudflare configuration, or publish unreviewed Ember Signal data. Railway and Cloudflare mutations remain intentionally out of scope for this first automation layer.

## Security

The Railway and PythonAnywhere credentials supplied during setup are not stored in Git, logs, test fixtures, or documentation. Because credentials were shared in chat, revoke and replace them before live execution. Use provider-specific least-privilege tokens and keep the OpenRouter key optional unless AI summaries are needed.
