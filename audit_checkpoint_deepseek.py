"""One-shot report-only checkpoint audit using DeepSeek."""
from __future__ import annotations
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL = "https://api.deepseek.com/v1/chat/completions"
FACTS = {
    "railway_public_endpoints": {"/api/health": 200, "/api/dashboard": 200, "/api/methodology": 200, "/api/signals": 200},
    "github_issues": 0, "github_pull_requests": 0,
    "institutions": 357, "duplicate_candidates": 79,
    "pending_candidates": 79, "human_decisions": 0,
    "automatic_merges": 0,
    "railway_internal_logs": "not inspected; Railway CLI/token unavailable",
}


def main() -> int:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")
    messages = [
        {"role": "system", "content": "You are a conservative data-integrity auditor. Return JSON only with verdict, material_risks, required_before_adjudication, and recommended_next_step. Do not invent facts. Treat 79 candidates as unconfirmed duplicates. Treat public HTTP 200 as insufficient proof that internal logs are clean."},
        {"role": "user", "content": json.dumps(FACTS, ensure_ascii=False)},
    ]
    payload = {"model": "deepseek-chat", "messages": messages, "temperature": 0, "max_tokens": 350, "response_format": {"type": "json_object"}}
    request = Request(URL, data=json.dumps(payload).encode(), method="POST", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek HTTP {exc.code}: {detail[:700]}") from exc
    except URLError as exc:
        raise RuntimeError(f"DeepSeek network error: {exc.reason}") from exc
    text = result["choices"][0]["message"]["content"]
    print(json.dumps({"provider": "DeepSeek", "mode": "report-only", "facts": FACTS, "audit": json.loads(text), "production_changed": False}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
