import json
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "ember_signal.db"
with sqlite3.connect(DB) as conn:
    checks = {
        "institutions": conn.execute("select count(*) from institutions").fetchone()[0],
        "duplicate_candidates": conn.execute("select count(*) from duplicate_candidates").fetchone()[0],
        "pending_candidates": conn.execute("select count(*) from duplicate_candidates where status='pending'").fetchone()[0],
        "decisions": conn.execute("select count(*) from duplicate_decisions").fetchone()[0],
    }
    rows = conn.execute("""
        select id, institution_a_id, institution_b_id, match_score, match_class,
               match_reasons, source_count, evidence_count, status
        from duplicate_candidates order by id limit 10
    """).fetchall()
print(json.dumps({"counts": checks, "sample": [dict(zip([
    "candidate_id", "a_id", "b_id", "score", "class", "reasons", "sources", "evidence", "status"
], row)) for row in rows]}, ensure_ascii=False, indent=2))
