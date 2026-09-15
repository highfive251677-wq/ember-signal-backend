"""Run exactly one bounded live-evidence review with Groq.

The script reads one recent public evidence record from the live API and asks
Groq for a report-only classification. It never writes to the database or
production. The result is saved locally for human review.
"""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LIVE = "https://ember-signal-backend-production.up.railway.app/api/dashboard"
EVIDENCE = "https://ember-signal-backend-production.up.railway.app/api/institutions/1/evidence"
GROQ = "https://api.groq.com/openai/v1/chat/completions"


def get_json(url: str) -> dict:
    try:
        with urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"live API error: {exc}") from exc


def call_groq(record: dict) -> dict:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    prompt = {
        "task": "Classify one public evidence record for Ember Signal. Report-only: do not approve or change data.",
        "record": record,
        "allowed_signal_types": ["admissions", "course", "event", "campaign", "partnership", "other"],
        "allowed_review_status": ["unreviewed", "source_review_required", "rejected"],
        "rules": [
            "Use only the supplied record.",
            "Do not invent facts.",
            "If source authority or relevance is uncertain, use source_review_required.",
            "Return compact JSON with signal_type, suggested_review_status, reason, confidence.",
        ],
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "temperature": 0,
        "max_tokens": 180,
        "messages": [
            {"role": "system", "content": "You are a report-only evidence classifier. Return JSON only."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
    }
    request = Request(GROQ, data=json.dumps(payload).encode(), method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"
    })
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Groq HTTP {exc.code}: {detail[:600]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Groq network error: {exc.reason}") from exc
    content = result["choices"][0]["message"]["content"]
    return {"provider": "Groq", "model": result.get("model"), "classification": json.loads(content), "usage": result.get("usage")}


def main() -> int:
    dashboard = get_json(LIVE)
    records = dashboard.get("recent_evidence", [])
    if not records:
        records = get_json(EVIDENCE).get("evidence", [])
    if not records:
        print("No reviewable evidence available")
        return 0
    record = next((r for r in records if r.get("review_status") == "unreviewed"), records[0])
    result = {"mode": "report-only", "record": record, "review": call_groq(record)}
    with open("/tmp/ember-signal-next-review.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("PAUSED: one evidence review completed; no next task started")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
