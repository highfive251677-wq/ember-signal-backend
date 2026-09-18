# Ember Signal release automation

`release_orchestrator.py` is a read-only-by-default release gate that combines Railway, Render, PythonAnywhere, optional Cloudflare, and optional OpenRouter diagnostics without putting secrets in the repository.

## What it checks

| Provider | Check | Mutation behavior |
|---|---|---|
| Railway | Project-token scope, latest deployments, and latest status | Read-only |
| Render | Service metadata and optional public health endpoint | Read-only |
| PythonAnywhere | Public health endpoint | Read-only unless explicit deployment is requested |
| Cloudflare | Optional zone status through the API or configured connector | Read-only |
| OpenRouter | Optional concise blocker summary | Inference only |

## Environment

```sh
export RAILWAY_TOKEN='[set privately]'
export RAILWAY_TOKEN_TYPE=project
export RAILWAY_HEALTH_URL=https://ember-signal-backend-production.up.railway.app/api/health

export RENDER_API_KEY='[set privately]'
export RENDER_SERVICE_ID='[from Render dashboard after service creation]'
export RENDER_HEALTH_URL='[Render public URL]/api/health'

export PYTHONANYWHERE_USERNAME=Kbnb
export PYTHONANYWHERE_DOMAIN=kbnb.pythonanywhere.com
export PYTHONANYWHERE_API_KEY='[set privately]'
export PYTHONANYWHERE_HEALTH_URL=https://kbnb.pythonanywhere.com/api/health

export OPENROUTER_API_KEY='[set privately]'
export OPENROUTER_MODEL=openai/gpt-4o-mini
```

## Read-only release gate

```sh
python3 release_orchestrator.py --json
```

The command exits `0` only when enabled checks pass. Missing Render configuration is skipped until the Render service exists. Set `RENDER_SERVICE_ID` and `RENDER_HEALTH_URL` after deployment to make Render part of the gate.

## Render deployment

The repository includes `render.yaml`. In Render, use **New → Blueprint** and select this public GitHub repository. The Blueprint configures a Python web service with:

```text
Build: pip install -r requirements.txt
Start: gunicorn --bind 0.0.0.0:$PORT wsgi:application
Health: /api/health
Branch: main
Auto deploy: enabled
```

Render's API rejected automatic service creation until payment information was present on the account. The service was not created by automation. A Render account owner must satisfy that account-level requirement in the Render Dashboard first; the Blueprint is ready afterward.

## PythonAnywhere deployment

```sh
python3 release_orchestrator.py \
  --deploy-pythonanywhere \
  --source . \
  --remote /home/Kbnb/ember-signal-backend-staging \
  --apply
```

This requires a passing gate and explicit `--apply`. It excludes runtime database files, `.env`, Git metadata, virtual environments, and bytecode.

## Termius / SSH clarification

A Render web service is an HTTP container, not an SSH server. It cannot provide a persistent Termius host. Use a separate SSH-capable VM or VPS, such as an eligible Oracle Cloud Free Tier VM, for Termius. Keep Render and Railway as HTTP deployment targets for the API.

## Security

Never commit API keys, SSH private keys, GitHub tokens, runtime databases, or passwords. Credentials supplied in chat should be revoked and replaced. Public source code does not make secrets safe to publish.
