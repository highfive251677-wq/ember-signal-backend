# Ember Signal Backend

Ember Signal is a Flask API for public-source intelligence about Myanmar colleges and education institutions. It exposes institution, source, evidence, coverage, summary, dashboard, and health endpoints.

## Run locally

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

The API is served on `http://127.0.0.1:5000` by the Flask development server. For production, use the WSGI entrypoint:

```sh
gunicorn --bind 0.0.0.0:$PORT wsgi:application
```

## Providers and release automation

The repository includes a read-only-by-default release gate in `release_orchestrator.py`. It can compare Railway, Render, PythonAnywhere, and optional Cloudflare health, then optionally ask OpenRouter for a concise blocker summary. PythonAnywhere upload/reload support is provided by `pythonanywhere_manager.py`.

```sh
python3 release_orchestrator.py --json
```

Provider credentials must be supplied through environment variables or a platform secret manager. Never commit `.env` files, API keys, SSH keys, tokens, runtime databases, or passwords.

## Render deployment

`render.yaml` is a Render Blueprint for a free-plan web service when the Render account is eligible. It uses:

```text
Build: pip install -r requirements.txt
Start: gunicorn --bind 0.0.0.0:$PORT wsgi:application
Health: /api/health
```

Render may require payment information even for a free-plan service. That is an account-level requirement and cannot be bypassed by the API.

A Render web service is an HTTP application container, **not an SSH server**. It cannot be used as a persistent Termius host. Use an SSH-capable VM such as Oracle Cloud Free Tier or another VPS for Termius access; keep Render for the public API deployment.

## Data and release status

The SQLite file in this historical repository snapshot is not a production backup policy. Runtime databases should live outside the source tree, be backed up separately, and be migrated deliberately. Duplicate institution and evidence-review gates must be resolved independently of infrastructure health.

## License

Application source code is licensed under the MIT License. Public-source data, database snapshots, third-party trademarks, and external URLs are not automatically relicensed; review their respective rights before redistribution.

See [LICENSE](LICENSE), [SECURITY.md](SECURITY.md), and [RELEASE_AUTOMATION.md](RELEASE_AUTOMATION.md).
