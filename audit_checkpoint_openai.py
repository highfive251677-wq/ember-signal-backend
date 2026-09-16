"""Report-only operational audit for the duplicate-workflow checkpoint."""
from __future__ import annotations
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL = "https://api.openai.com/v1/responses"
FACTS = {
    "railway_public_endpoints": {"/api/health": 200, "/api/dashboard": 200, "/api/methodology": 200, "/api/signals": 200},
    "github_issues": 0,
    "github_pull_requests": 0,
    "institutions": 357,
    "duplicate_candidates": 79,
    "pending_candidates": 79,
    "human_decisions": 0,
    "automatic_merges": 0,
    "railway_internal_logs": "not inspected; Railway CLI/token unavailable",
}


def main() -> int:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    prompt = "Audit these checkpoint facts for data-integrity risk. Do not invent facts. Return JSON only with fields: verdict (PASS, WARN, or BLOCK), material_risks (array), required_before_adjudication (array), recommended_next_step (string). Emphasize that public HTTP 200 does not prove internal logs are clean and that 79 candidates are not confirmed duplicates.\nFACTS:\n" + json.dumps(FACTS, ensure_ascii=False)
    payload = {"model": "gpt-4o-mini", "input": prompt, "max_output_tokens": 300}
    request = Request(URL, data=json.dumps(payload).encode(), method="POST", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail[:700]}") from exc
    except URLError as exc:
        raise RuntimeError(f"OpenAI network error: {exc.reason}") from exc
    text = result.get("output", [{}])[0].get("content", [{}])[0].get("text", "")
    print(json.dumps({"provider": "OpenAI", "mode": "report-only", "facts": FACTS, "audit": text, "production_changed": False}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
