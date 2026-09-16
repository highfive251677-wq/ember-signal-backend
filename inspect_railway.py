"""Read-only Railway project/deployment/log inspector.

Requires RAILWAY_PROJECT_TOKEN in the environment. It never performs mutations.
"""
from __future__ import annotations

import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL = "https://backboard.railway.com/graphql/v2"


def query(document: str, variables: dict | None = None) -> dict:
    token = os.environ.get("RAILWAY_PROJECT_TOKEN")
    if not token:
        raise RuntimeError("RAILWAY_PROJECT_TOKEN is not configured")
    request = Request(URL, data=json.dumps({"query": document, "variables": variables or {}}).encode(), method="POST", headers={"Project-Access-Token": token, "Content-Type": "application/json", "User-Agent": "curl/8.0 ember-signal-readonly-inspector"})
    try:
        with urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode())
            if body.get("errors"):
                raise RuntimeError(json.dumps(body["errors"], ensure_ascii=False))
            return body.get("data", {})
    except HTTPError as exc:
        raise RuntimeError(f"Railway HTTP {exc.code}: {exc.read().decode(errors='replace')[:800]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Railway network error: {exc.reason}") from exc


def main() -> int:
    identity = query("query { projectToken { projectId environmentId } }")
    ids = identity["projectToken"]
    deployments = query("""
      query deployments($input: DeploymentListInput!, $first: Int) {
        deployments(input: $input, first: $first) {
          edges { node { id status createdAt url staticUrl meta serviceId service { id name } } }
        }
      }
    """, {"input": {"projectId": ids["projectId"], "environmentId": ids["environmentId"]}, "first": 10})
    rows = deployments.get("deployments", {}).get("edges", [])
    all_deployments = [x["node"] for x in rows]
    selected = all_deployments[0] if all_deployments else None
    successful = next((x for x in all_deployments if x.get("status") == "SUCCESS"), None)
    failed = next((x for x in all_deployments if x.get("status") == "FAILED"), None)
    result = {"project_token_scope": ids, "deployments": all_deployments, "latest": selected, "latest_success": successful, "latest_failed": failed, "logs": {}}
    for label, deployment in (("latest_failed", failed), ("latest_success", successful)):
        if deployment:
            dep_id = deployment["id"]
            result["logs"][label] = {
                "build": query("query buildLogs($deploymentId: String!, $limit: Int) { buildLogs(deploymentId: $deploymentId, limit: $limit) { timestamp message severity } }", {"deploymentId": dep_id, "limit": 200}).get("buildLogs", []),
                "runtime": query("query deploymentLogs($deploymentId: String!, $limit: Int) { deploymentLogs(deploymentId: $deploymentId, limit: $limit) { timestamp message severity } }", {"deploymentId": dep_id, "limit": 200}).get("deploymentLogs", []),
                "http": query("query httpLogs($deploymentId: String!, $limit: Int) { httpLogs(deploymentId: $deploymentId, limit: $limit) { timestamp requestId method path httpStatus totalDuration } }", {"deploymentId": dep_id, "limit": 200}).get("httpLogs", []),
            }
    if selected and selected.get("serviceId"):
        vars_data = query("query variables($environmentId: String!, $projectId: String!, $serviceId: String, $unrendered: Boolean) { variables(environmentId: $environmentId, projectId: $projectId, serviceId: $serviceId, unrendered: $unrendered) }", {"environmentId": ids["environmentId"], "projectId": ids["projectId"], "serviceId": selected["serviceId"], "unrendered": True})
        variables = vars_data.get("variables", {})
        result["variable_names"] = sorted(variables.keys())
        result["variable_diagnostics"] = [
            {
                "name": name,
                "empty": value in (None, ""),
                "value_length": len(value or ""),
                "looks_like_reference": isinstance(value, str) and "${{" in value,
                "reference_targets": re.findall(r"\$\{\{([^}]*)\}\}", value or "") if isinstance(value, str) else [],
                "looks_malformed_name": name != name.strip() or name.startswith(("'", "‘", '"')) or name.endswith(("'", "’", '"')),
            }
            for name, value in sorted(variables.items())
        ]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
