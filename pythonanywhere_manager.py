"""PythonAnywhere web-app deployment and reload client.

Uses the documented PythonAnywhere API v0 endpoints. The API token is read
from PYTHONANYWHERE_API_KEY or API_TOKEN and is never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import requests


class PythonAnywhereError(RuntimeError):
    """Raised when the PythonAnywhere API returns an unsuccessful response."""


@dataclass(frozen=True)
class Settings:
    username: str
    domain: str
    token: str
    host: str = "www.pythonanywhere.com"
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("PYTHONANYWHERE_API_KEY") or os.getenv("API_TOKEN")
        missing = [name for name, value in {
            "PYTHONANYWHERE_USERNAME": os.getenv("PYTHONANYWHERE_USERNAME"),
            "PYTHONANYWHERE_DOMAIN": os.getenv("PYTHONANYWHERE_DOMAIN"),
            "PYTHONANYWHERE_API_KEY (or API_TOKEN)": token,
        }.items() if not value]
        if missing:
            raise PythonAnywhereError("Missing required environment variable(s): " + ", ".join(missing))
        return cls(
            username=os.environ["PYTHONANYWHERE_USERNAME"],
            domain=os.environ["PYTHONANYWHERE_DOMAIN"],
            token=token,
            host=os.getenv("PYTHONANYWHERE_HOST", "www.pythonanywhere.com"),
            timeout=float(os.getenv("PYTHONANYWHERE_TIMEOUT", "30")),
        )


class PythonAnywhereClient:
    def __init__(self, settings: Settings, session: requests.Session | None = None):
        self.settings = settings
        self.session = session or requests.Session()
        self.session.headers.update({"Authorization": f"Token {settings.token}", "Accept": "application/json"})
        self.base_url = f"https://{settings.host}/api/v0/user/{quote(settings.username, safe='') }"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self.session.request(method, self.base_url + path, timeout=self.settings.timeout, **kwargs)
        if not response.ok:
            detail = response.text[:500].replace(self.settings.token, "[REDACTED]")
            raise PythonAnywhereError(f"PythonAnywhere API {response.status_code} for {method} {path}: {detail}")
        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def list_webapps(self) -> Any:
        return self._request("GET", "/webapps/")

    def webapp(self) -> Any:
        return self._request("GET", f"/webapps/{quote(self.settings.domain, safe='')}/")

    def reload(self) -> Any:
        return self._request("POST", f"/webapps/{quote(self.settings.domain, safe='')}/reload/")

    def update_webapp(self, **configuration: Any) -> Any:
        allowed = {"python_version", "source_directory", "virtualenv_path", "force_https",
                   "password_protection_enabled", "password_protection_username", "password_protection_password"}
        payload = {key: value for key, value in configuration.items() if key in allowed and value is not None}
        if not payload:
            raise PythonAnywhereError("No supported web-app configuration values were provided")
        return self._request("PATCH", f"/webapps/{quote(self.settings.domain, safe='')}/", data=payload)

    def upload_file(self, remote_path: str, local_path: Path) -> Any:
        # The API expects the multipart field to be named content.
        with local_path.open("rb") as handle:
            return self._request("POST", f"/files/path{quote(remote_path, safe='/')}", files={"content": (local_path.name, handle)})

    def deploy_directory(self, local_dir: Path, remote_dir: str, *, dry_run: bool = True,
                         include: Iterable[str] | None = None) -> list[str]:
        local_dir = local_dir.resolve()
        if not local_dir.is_dir():
            raise PythonAnywhereError(f"Deployment directory does not exist: {local_dir}")
        excluded = {".git", ".env", ".venv", "__pycache__", "ember_signal.db", "*.pyc"}
        files: list[Path] = []
        for path in sorted(local_dir.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(local_dir)
            parts = set(relative.parts)
            if parts & {".git", ".venv", "__pycache__"} or path.name in {".env", "ember_signal.db"} or path.suffix == ".pyc":
                continue
            if include and str(relative) not in set(include):
                continue
            files.append(path)
        uploaded: list[str] = []
        for path in files:
            remote = f"{remote_dir.rstrip('/')}/{path.relative_to(local_dir).as_posix()}"
            uploaded.append(remote)
            if not dry_run:
                self.upload_file(remote, path)
        return uploaded


def _json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage an Ember Signal web app on PythonAnywhere")
    parser.add_argument("--apply", action="store_true", help="perform uploads/reload; without it mutating commands are dry-run")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("list")
    sub.add_parser("reload")
    deploy = sub.add_parser("deploy", help="upload source files, excluding runtime data, then optionally reload")
    deploy.add_argument("--source", default=".")
    deploy.add_argument("--remote", default=None, help="remote source directory; defaults to the web app source directory")
    deploy.add_argument("--reload", action="store_true", help="reload after a successful upload")
    args = parser.parse_args(argv)
    try:
        client = PythonAnywhereClient(Settings.from_env())
        if args.command == "status":
            _json(client.webapp())
        elif args.command == "list":
            _json(client.list_webapps())
        elif args.command == "reload":
            if not args.apply:
                print("DRY RUN: would reload the configured web app; rerun with --apply", file=sys.stderr)
            else:
                _json(client.reload())
        elif args.command == "deploy":
            remote = args.remote
            if remote is None:
                remote = client.webapp().get("source_directory") if args.apply else os.getenv("PYTHONANYWHERE_SOURCE_DIRECTORY", "")
            if not remote:
                raise PythonAnywhereError("Set --remote or PYTHONANYWHERE_SOURCE_DIRECTORY for a dry-run deployment")
            uploaded = client.deploy_directory(Path(args.source), remote, dry_run=not args.apply)
            print(("Uploaded" if args.apply else "DRY RUN; would upload") + f" {len(uploaded)} files to {remote}")
            if args.apply and args.reload:
                _json(client.reload())
            else:
                print("Reload skipped; use --reload --apply to reload after deployment", file=sys.stderr)
        return 0
    except (PythonAnywhereError, requests.RequestException) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
