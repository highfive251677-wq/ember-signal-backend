"""Duplicate institution candidate and adjudication workflow.

Safe by design:
- generates candidate pairs/groups deterministically;
- records evidence counts and matching reasons;
- never deletes, merges, or remaps institutions automatically;
- records human decisions separately for later reviewed implementation.

Examples:
  python duplicate_workflow.py generate
  python duplicate_workflow.py list
  python duplicate_workflow.py decide --candidate 1 --action KEEP_SEPARATE --reviewer "name" --notes "Different township"
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parent / "ember_signal.db"
ACTIONS = {"KEEP_SEPARATE", "MERGE_APPROVED", "NEEDS_REVIEW"}


def norm(value: str | None) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = re.sub(r"[^\w\u1000-\u109f]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def init() -> None:
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS duplicate_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution_a_id TEXT NOT NULL,
                institution_b_id TEXT NOT NULL,
                match_score REAL NOT NULL,
                match_class TEXT NOT NULL,
                match_reasons TEXT NOT NULL,
                source_count INTEGER NOT NULL DEFAULT 0,
                evidence_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                UNIQUE(institution_a_id, institution_b_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS duplicate_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                canonical_institution_id TEXT,
                reviewer TEXT NOT NULL,
                notes TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(candidate_id) REFERENCES duplicate_candidates(id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_duplicate_candidates_status ON duplicate_candidates(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_duplicate_decisions_candidate ON duplicate_decisions(candidate_id)")
        conn.commit()


def fetch_institutions(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT id,name,city,township,type,status FROM institutions ORDER BY id").fetchall()
    return [dict(zip(["id", "name", "city", "township", "type", "status"], row)) for row in rows]


def candidate(a: dict, b: dict, conn: sqlite3.Connection) -> dict | None:
    name_a, name_b = norm(a["name"]), norm(b["name"])
    city_a, city_b = norm(a["city"]), norm(b["city"])
    township_a, township_b = norm(a["township"]), norm(b["township"])
    type_a, type_b = norm(a["type"]), norm(b["type"])
    name_ratio = difflib.SequenceMatcher(None, name_a, name_b).ratio()
    reasons = []
    if name_a and name_a == name_b:
        reasons.append("exact_normalized_name")
    elif name_ratio >= 0.92:
        reasons.append(f"similar_normalized_name:{name_ratio:.3f}")
    else:
        return None
    if city_a and city_a == city_b:
        reasons.append("same_city")
    if township_a and township_a == township_b:
        reasons.append("same_township")
    if type_a and type_a == type_b:
        reasons.append("same_type")
    if len(reasons) < 2:
        return None
    same_location = "same_township" in reasons
    same_type = "same_type" in reasons
    score = min(1.0, 0.65 * name_ratio + 0.15 * ("same_city" in reasons) + 0.15 * same_location + 0.05 * same_type)
    match_class = "HIGH_CONFIDENCE_CANDIDATE" if name_ratio == 1 and same_location and same_type else "REVIEW_CANDIDATE"
    source_count, evidence_count = conn.execute("""
        SELECT (SELECT COUNT(*) FROM institution_sources WHERE institution_id IN (?,?)),
               (SELECT COUNT(*) FROM evidence_items WHERE institution_id IN (?,?))
    """, (a["id"], b["id"], a["id"], b["id"])).fetchone()
    return {"a": a["id"], "b": b["id"], "score": round(score, 4), "class": match_class, "reasons": reasons, "sources": source_count, "evidence": evidence_count}


def generate() -> None:
    init()
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB) as conn:
        rows = fetch_institutions(conn)
        created = 0
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                item = candidate(a, b, conn)
                if not item:
                    continue
                cur = conn.execute("""
                    INSERT OR IGNORE INTO duplicate_candidates
                    (institution_a_id,institution_b_id,match_score,match_class,match_reasons,source_count,evidence_count,status,created_at)
                    VALUES (?,?,?,?,?,?,?,'pending',?)
                """, (item["a"], item["b"], item["score"], item["class"], json.dumps(item["reasons"], ensure_ascii=False), item["sources"], item["evidence"], now))
                created += cur.rowcount
        conn.commit()
    print(json.dumps({"created": created, "message": "Candidates recorded; no institution was changed."}, ensure_ascii=False, indent=2))


def list_candidates() -> None:
    init()
    with sqlite3.connect(DB) as conn:
        rows = conn.execute("""
            SELECT c.id,c.institution_a_id,a.name,c.institution_b_id,b.name,c.match_score,c.match_class,c.match_reasons,c.source_count,c.evidence_count,c.status
            FROM duplicate_candidates c JOIN institutions a ON a.id=c.institution_a_id JOIN institutions b ON b.id=c.institution_b_id
            ORDER BY c.match_class DESC,c.match_score DESC,c.id
        """).fetchall()
    for row in rows:
        print(json.dumps(dict(zip(["candidate_id","a_id","a_name","b_id","b_name","score","class","reasons","sources","evidence","status"], row)), ensure_ascii=False))
    print(f"total_candidates={len(rows)}")


def decide(args: argparse.Namespace) -> None:
    if args.action not in ACTIONS:
        raise SystemExit(f"action must be one of {sorted(ACTIONS)}")
    if args.action == "MERGE_APPROVED" and not args.canonical:
        raise SystemExit("--canonical is required for MERGE_APPROVED")
    init()
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB) as conn:
        row = conn.execute("SELECT id FROM duplicate_candidates WHERE id=?", (args.candidate,)).fetchone()
        if not row:
            raise SystemExit("candidate not found")
        conn.execute("""
            INSERT INTO duplicate_decisions(candidate_id,action,canonical_institution_id,reviewer,notes,created_at)
            VALUES (?,?,?,?,?,?)
        """, (args.candidate, args.action, args.canonical, args.reviewer, args.notes, now))
        conn.execute("UPDATE duplicate_candidates SET status=? WHERE id=?", (args.action.lower(), args.candidate))
        conn.commit()
    print(json.dumps({"candidate_id": args.candidate, "action": args.action, "recorded": True, "data_changed": False}, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate")
    sub.add_parser("list")
    d = sub.add_parser("decide")
    d.add_argument("--candidate", type=int, required=True)
    d.add_argument("--action", required=True)
    d.add_argument("--reviewer", required=True)
    d.add_argument("--notes", required=True)
    d.add_argument("--canonical")
    args = parser.parse_args()
    {"generate": generate, "list": list_candidates, "decide": lambda: decide(args)}[args.command]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
