# PythonAnywhere deployment

This repository includes `pythonanywhere_manager.py`, a small management client for the documented PythonAnywhere API. It supports web-app status inspection, source-file uploads, and web-app reloads.

## Credentials and configuration

Create the following environment variables in the deployment environment. Do not commit the API key or place it in a `.env` file tracked by Git.

```sh
export PYTHONANYWHERE_USERNAME=Kbnb
export PYTHONANYWHERE_DOMAIN=kbnb.pythonanywhere.com
export PYTHONANYWHERE_HOST=www.pythonanywhere.com
export PYTHONANYWHERE_API_KEY='[set this privately]'
```

PythonAnywhere's official API uses the `Authorization: Token <token>` header. The client accepts `API_TOKEN` as a fallback because PythonAnywhere pre-populates that variable in its own consoles, web apps, and tasks.

## Commands

Install dependencies first:

```sh
python3 -m pip install -r requirements.txt
```

Inspect the configured web app:

```sh
python3 pythonanywhere_manager.py status
python3 pythonanywhere_manager.py list
```

All mutating commands require `--apply`. Without it, reload is only announced and deployment is a dry run.

```sh
# Preview the files that would be uploaded. Runtime database files are excluded.
python3 pythonanywhere_manager.py deploy \
  --source . \
  --remote /home/Kbnb/ember-signal-backend-staging

# Upload source files, then reload the web app.
python3 pythonanywhere_manager.py deploy \
  --source . \
  --remote /home/Kbnb/ember-signal-backend-staging \
  --reload --apply

# Reload without uploading files.
python3 pythonanywhere_manager.py reload --apply
```

The deploy command uploads files one by one through the PythonAnywhere Files API. It deliberately excludes `.git`, virtual environments, bytecode, `.env`, and `ember_signal.db`; runtime data must remain on the host and should be backed up separately. The client does not delete remote files, disable the site, or change web-app configuration.

A release should be validated after reload:

```sh
curl --fail --silent https://kbnb.pythonanywhere.com/api/health
curl --fail --silent https://kbnb.pythonanywhere.com/api/summary
```

The PythonAnywhere API has a documented limit of 40 requests per minute for ordinary endpoints. The client performs no polling and uses a bounded request timeout.

## Existing manual deployment

The existing manual workflow remains supported. Upload `ember-signal-backend-main.zip` into `/home/Kbnb/ember-signal-backend-staging/`, extract it, compile `app.py` and `wsgi.py`, and reload the web app. The management client is intended for controlled source synchronization and repeatable reloads, not for merging or publishing unreviewed database quality changes.
