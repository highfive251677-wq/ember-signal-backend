"""Prepare and independently review one high-confidence duplicate candidate.

Gemini only recommends a human decision. This script never merges, deletes,
remaps foreign keys, or changes candidate status.
"""
from __future__ import annotations
import json
import os
import sqlite3
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DB = "ember_signal.db"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def packet() -> dict | None:
    with sqlite3.connect(DB) as c:
        c.row_factory = sqlite3.Row
        row = c.execute("""
          SELECT c.id candidate_id,c.match_score,c.match_class,c.match_reasons,
                 a.id a_id,a.name a_name,a.city a_city,a.township a_township,a.type a_type,
                 b.id b_id,b.name b_name,b.city b_city,b.township b_township,b.type b_type
          FROM duplicate_candidates c
          JOIN institutions a ON a.id=c.institution_a_id
          JOIN institutions b ON b.id=c.institution_b_id
          WHERE c.status='pending' AND c.match_class='HIGH_CONFIDENCE_CANDIDATE'
          ORDER BY c.match_score DESC,c.id LIMIT 1
        """).fetchone()
        if not row:
            return None
        out = dict(row)
        for side in ("a", "b"):
            out[side+"_sources"] = [dict(x) for x in c.execute("SELECT id,platform,label,url,is_official,verification_status FROM institution_sources WHERE institution_id=?", (out[side+"_id"],)).fetchall()]
            out[side+"_evidence"] = [dict(x) for x in c.execute("SELECT id,source_url,title,excerpt,review_status,observed_at FROM evidence_items WHERE institution_id=?", (out[side+"_id"],)).fetchall()]
        return out


def review(item: dict) -> dict:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    prompt = """You are an independent data-integrity reviewer. Review exactly one duplicate institution candidate for Ember Signal. Do not merge, delete, remap, or approve anything. Return JSON only with: verdict (MERGE_CANDIDATE, KEEP_SEPARATE, or NEEDS_HUMAN_EVIDENCE), reasons (array), missing_evidence (array), and human_checks (array). Exact name/location similarity is not proof of identity; branches may be separate. Use only supplied facts.""" + "\nCANDIDATE:\n" + json.dumps(item, ensure_ascii=False)
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    req = Request(URL, data=json.dumps(payload, ensure_ascii=False).encode(), method="POST", headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=60) as r:
            result = json.loads(r.read().decode())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini HTTP {exc.code}: {detail[:700]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Gemini network error: {exc.reason}") from exc
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    return {"provider": "Gemini", "model": MODEL, "recommendation": json.loads(text), "production_changed": False}


def main() -> int:
    item = packet()
    if not item:
        print("No pending high-confidence candidate available")
        return 0
    result = {"mode": "report-only", "candidate": item, "independent_review": review(item), "human_decision_required": True}
    with open("/tmp/ember-high-confidence-review.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("PAUSED: human adjudication required; no merge performed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
