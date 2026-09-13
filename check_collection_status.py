import sqlite3

with sqlite3.connect("ember_signal.db") as conn:
    checks = [
        ("institutions", "select count(*) from institutions"),
        ("sources", "select count(*) from institution_sources"),
        ("verified_sources", "select count(*) from institution_sources where verification_status='verified'"),
        ("evidence", "select count(*) from evidence_items"),
        ("unreviewed", "select count(*) from evidence_items where review_status='unreviewed'"),
    ]
    for label, query in checks:
        print(f"{label}: {conn.execute(query).fetchone()[0]}")
