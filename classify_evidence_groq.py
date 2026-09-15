"""Classify one verified, unreviewed evidence record with Groq.

This is a report-only prototype. It deliberately does not update review_status.
Run with --limit 1 while testing; expand only after KPI review.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DB = "ember_signal.db"
URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "qwen/qwen3.8-27b"


def get_record() -> dict | None:
    with sqlite3.connect(DB) as conn:
        row = conn.execute("""
            SELECT e.id, e.institution_id, e.source_url, e.platform, e.title,
                   e.excerpt, e.review_status, s.verification_status
            FROM evidence_items e
            LEFT JOIN institution_sources s ON s.id=e.source_id
            WHERE e.review_status='unreviewed' AND s.verification_status='verified'
            ORDER BY e.id LIMIT 1
        """).fetchone()
    if not row:
        return None
    keys = ["id", "institution_id", "source_url", "platform", "title", "excerpt", "review_status", "verification_status"]
    return dict(zip(keys, row))


def classify(record: dict) -> dict:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    schema = {
        "type": "object",
        "properties": {
            "signal_type": {"type": "string", "enum": ["admissions", "course", "event", "campaign", "partnership", "other"]},
            "suggested_review_status": {"type": "string", "enum": ["unreviewed", "source_review_required", "rejected"]},
            "reason": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["signal_type", "suggested_review_status", "reason", "confidence"],
        "additionalProperties": False
    }
    payload = {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": 180,
        "messages": [
            {"role": "system", "content": "You are a report-only evidence classifier. Return only JSON matching the schema. Never approve evidence."},
            {"role": "user", "content": json.dumps({"record": record, "schema": schema, "rule": "Use only this record; if uncertain keep suggested_review_status as unreviewed."}, ensure_ascii=False)}
        ],
        "response_format": {"type": "json_schema", "json_schema": {"name": "evidence_classification", "schema": schema}}
    }
    request = Request(URL, data=json.dumps(payload, ensure_ascii=False).encode(), method="POST", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Groq HTTP {exc.code}: {detail[:700]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Groq network error: {exc.reason}") from exc
    content = result["choices"][0]["message"]["content"]
    classification = json.loads(content)
    return {"provider": "Groq", "model": result.get("model"), "classification": classification, "usage": result.get("usage")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, choices=[1], default=1, help="Prototype is intentionally limited to one record")
    args = parser.parse_args()
    record = get_record()
    if not record:
        print("No verified unreviewed evidence available")
        return 0
    result = {"mode": "report-only", "record": record, "review": classify(record), "database_updated": False}
    with open("/tmp/ember-signal-groq-classification.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("PAUSED: one record classified; no status was changed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
