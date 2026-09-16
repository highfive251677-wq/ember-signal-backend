import json
import sqlite3
from pathlib import Path

DB = Path(__file__).with_name('ember_signal.db')
OUT = Path(__file__).with_name('review_batch_01.json')

with sqlite3.connect(DB) as conn:
    rows = conn.execute('''
        SELECT e.id, e.institution_id, i.name, e.platform, e.title,
               e.signal_type, e.confidence, e.review_status,
               s.verification_status, e.source_url, e.observed_at, e.excerpt
        FROM evidence_items e
        JOIN institutions i ON CAST(i.id AS TEXT) = e.institution_id
        LEFT JOIN institution_sources s ON s.id = e.source_id
        WHERE e.review_status = 'unreviewed'
          AND e.platform = 'website'
          AND s.verification_status = 'verified'
        ORDER BY e.id
        LIMIT 10
    ''').fetchall()

fields = ['evidence_id', 'institution_id', 'institution_name', 'platform',
          'title', 'signal_type', 'confidence', 'review_status',
          'source_verification_status', 'source_url', 'observed_at', 'excerpt']
records = [dict(zip(fields, row)) for row in rows]
OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'count': len(records), 'ids': [r['evidence_id'] for r in records], 'output': str(OUT)}, ensure_ascii=False))

if len(records) != 10:
    raise SystemExit('Expected 10 records in the first review batch')
