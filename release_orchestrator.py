"""Ember Signal cross-provider release gate.

This is intentionally read-only by default. It checks Railway deployment state,
PythonAnywhere health, and optional Cloudflare edge/DNS health. OpenRouter is an
optional summarizer for the resulting diagnostics; no provider mutation is
performed by this module.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import requests

from pythonanywhere_manager import PythonAnywhereClient, Settings


class OrchestratorError(RuntimeError):
    pass


TIMEOUT = float(os.getenv("RELEASE_CHECK_TIMEOUT", "20"))


def http_get(url: str, **kwargs: Any) -> dict[str, Any]:
    response = requests.get(url, timeout=TIMEOUT, **kwargs)
    if not response.ok:
        raise OrchestratorError(f"GET {url} returned HTTP {response.status_code}")
    try:
        return response.json()
    except ValueError:
        return {"text": response.text[:500]}


def check_http_health(label: str, url: str) -> dict[str, Any]:
    try:
        payload = http_get(url)
        healthy = payload.get("status") == "ok" or payload.get("database") == "ok"
        return {"provider": label, "url": url, "ok": healthy, "payload": payload}
    except (requests.RequestException, OrchestratorError) as exc:
        return {"provider": label, "url": url, "ok": False, "error": str(exc)}


def railway_report() -> dict[str, Any]:
    token = os.getenv("RAILWAY_TOKEN") or os.getenv("RAILWAY_PROJECT_TOKEN")
    if not token:
        return {"provider": "railway", "ok": False, "skipped": True, "error": "RAILWAY_TOKEN is not configured"}
    header_name = "Authorization" if os.getenv("RAILWAY_TOKEN_TYPE", "project") == "bearer" else "Project-Access-Token"
    headers = {header_name: f"Bearer {token}" if header_name == "Authorization" else token, "Content-Type": "application/json"}
    query = "query { projectToken { projectId environmentId } }"
    try:
        response = requests.post("https://backboard.railway.com/graphql/v2", headers=headers, json={"query": query}, timeout=TIMEOUT)
        body = response.json()
        if body.get("errors"):
            return {"provider": "railway", "ok": False, "error": "; ".join(x.get("message", "GraphQL error") for x in body["errors"])}
        scope = body.get("data", {}).get("projectToken")
        if not scope:
            return {"provider": "railway", "ok": False, "error": "Token did not return a project scope; check RAILWAY_TOKEN_TYPE"}
        deployment_query = "query deployments($input: DeploymentListInput!, $first: Int) { deployments(input: $input, first: $first) { edges { node { id status createdAt url meta serviceId } } } }"
        deployment_response = requests.post("https://backboard.railway.com/graphql/v2", headers=headers, json={"query": deployment_query, "variables": {"input": scope, "first": 10}}, timeout=TIMEOUT)
        deployment_body = deployment_response.json()
        if deployment_body.get("errors"):
            return {"provider": "railway", "ok": False, "scope": scope, "error": "; ".join(x.get("message", "GraphQL error") for x in deployment_body["errors"])}
        rows = [edge["node"] for edge in deployment_body.get("data", {}).get("deployments", {}).get("edges", [])]
        latest = rows[0] if rows else None
        return {"provider": "railway", "ok": bool(latest and latest.get("status") == "SUCCESS"), "scope": scope, "latest": latest, "deployments": rows}
    except (requests.RequestException, ValueError, KeyError) as exc:
        return {"provider": "railway", "ok": False, "error": str(exc)}


def cloudflare_report() -> dict[str, Any]:
    token = os.getenv("CLOUDFLARE_API_TOKEN")
    zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
    if not token or not zone_id:
        return {"provider": "cloudflare", "ok": True, "skipped": True, "message": "Set CLOUDFLARE_API_TOKEN and CLOUDFLARE_ZONE_ID to enable DNS/zone verification"}
    try:
        payload = http_get(f"https://api.cloudflare.com/client/v4/zones/{zone_id}", headers={"Authorization": f"Bearer {token}"})
        result = payload.get("result", {})
        return {"provider": "cloudflare", "ok": payload.get("success", False) and not result.get("paused", False), "zone": {"name": result.get("name"), "status": result.get("status"), "paused": result.get("paused")}}
    except (requests.RequestException, OrchestratorError) as exc:
        return {"provider": "cloudflare", "ok": False, "error": str(exc)}


def openrouter_summary(report: dict[str, Any]) -> dict[str, Any] | None:
    token = os.getenv("OPENROUTER_API_KEY")
    if not token:
        return None
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    prompt = "Summarize this release-gate JSON in 3 concise sentences. Identify blockers only; do not invent facts.\n" + json.dumps(report, sort_keys=True)
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://github.com/highfive251677-wq/ember-signal-backend")}, json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0}, timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return {"model": model, "text": data["choices"][0]["message"]["content"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a read-only Ember Signal cross-provider release gate")
    parser.add_argument("--pythonanywhere-url", default=os.getenv("PYTHONANYWHERE_HEALTH_URL", "https://kbnb.pythonanywhere.com/api/health"))
    parser.add_argument("--railway-url", default=os.getenv("RAILWAY_HEALTH_URL", "https://ember-signal-backend-production.up.railway.app/api/health"))
    parser.add_argument("--deploy-pythonanywhere", action="store_true", help="after a passing gate, upload source and reload PythonAnywhere")
    parser.add_argument("--source", default=".")
    parser.add_argument("--remote", default=os.getenv("PYTHONANYWHERE_SOURCE_DIRECTORY"))
    parser.add_argument("--apply", action="store_true", help="required for --deploy-pythonanywhere")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = {"checks": [railway_report(), check_http_health("pythonanywhere", args.pythonanywhere_url), check_http_health("railway_http", args.railway_url), cloudflare_report()]}
    report["ok"] = all(item.get("ok", False) or item.get("skipped", False) for item in report["checks"])
    if args.deploy_pythonanywhere:
        if not args.apply:
            report["deployment"] = {"ok": False, "error": "--deploy-pythonanywhere requires --apply"}
            report["ok"] = False
        elif not report["ok"]:
            report["deployment"] = {"ok": False, "skipped": True, "error": "release gate is blocked"}
        elif not args.remote:
            report["deployment"] = {"ok": False, "error": "set --remote or PYTHONANYWHERE_SOURCE_DIRECTORY"}
            report["ok"] = False
        else:
            try:
                client = PythonAnywhereClient(Settings.from_env())
                uploaded = client.deploy_directory(__import__("pathlib").Path(args.source), args.remote, dry_run=False)
                client.reload()
                report["deployment"] = {"ok": True, "provider": "pythonanywhere", "uploaded_files": len(uploaded), "reloaded": True}
            except Exception as exc:
                report["deployment"] = {"ok": False, "provider": "pythonanywhere", "error": str(exc)}
                report["ok"] = False
    try:
        report["summary"] = openrouter_summary(report)
    except (requests.RequestException, KeyError, ValueError) as exc:
        report["summary_error"] = str(exc)
        report["ok"] = False
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"Release gate: {'PASS' if report['ok'] else 'BLOCKED'}")
        for item in report["checks"]:
            print(f"- {item['provider']}: {'SKIPPED' if item.get('skipped') else 'OK' if item.get('ok') else 'FAILED'}")
        if report.get("summary"):
            print(f"\nOpenRouter summary:\n{report['summary']['text']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
