# PythonAnywhere deployment

Upload `ember-signal-backend-main.zip` into:

```text
/home/Kbnb/ember-signal-backend-staging/
```

In a Bash console, run:

```sh
cd ~/ember-signal-backend-staging
unzip -q ember-signal-backend-main.zip
cp -a ember-signal-backend-main/. .
rm -rf ember-signal-backend-main
python3 -m py_compile app.py wsgi.py
python3 -c 'import app; c=app.app.test_client(); r=c.get("/api/health"); print(r.status_code); print(r.data.decode())'
```

Expected status is `200` and the JSON response should contain `"status":"ok"` and `"database":"ok"`.

Create/select a PythonAnywhere virtualenv and install dependencies:

```sh
mkvirtualenv --python=/usr/bin/python3.13 ember-signal-env
pip install -r ~/ember-signal-backend-staging/requirements.txt
```

If `mkvirtualenv` is unavailable:

```sh
python3 -m venv ~/.virtualenvs/ember-signal-env
source ~/.virtualenvs/ember-signal-env/bin/activate
pip install -r ~/ember-signal-backend-staging/requirements.txt
```

In the PythonAnywhere Web tab, set the WSGI file to:

```text
/home/Kbnb/ember-signal-backend-staging/wsgi.py
```

Use this WSGI configuration content if the file is edited through the Web tab:

```python
import sys
path = '/home/Kbnb/ember-signal-backend-staging'
if path not in sys.path:
    sys.path.insert(0, path)
from app import app as application
```

Set the web app's virtualenv to:

```text
/home/Kbnb/.virtualenvs/ember-signal-env
```

Then reload the web app and check:

```text
https://<your-pythonanywhere-domain>/api/health
```
