import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / 'ember_signal.db'
OUT = BASE / 'EVIDENCE_REVIEW_QUEUE.md'

with sqlite3.connect(DB) as conn:
    rows = conn.execute('''
        SELECT e.id, i.name, e.platform, e.title, e.source_url,
               e.review_status, e.signal_type, s.verification_status
        FROM evidence_items e
        JOIN institutions i ON CAST(i.id AS TEXT) = e.institution_id
        LEFT JOIN institution_sources s ON s.id = e.source_id
        WHERE e.review_status IN ('unreviewed', 'source_review_required')
        ORDER BY e.id
    ''').fetchall()

lines = [
    '# Evidence Review Queue',
    '',
    f'- Items: **{len(rows)}**',
    '- Policy: fetched public content is not approved automatically; human confirmation is required.',
    '- Scope: only unreviewed or source-review-required evidence remains here; approved and rejected items are retained in the database audit trail.',
    '',
    '| ID | Institution | Platform | Title | Source verification | Recommendation |',
    '|---:|---|---|---|---|---|',
]
for evidence_id, name, platform, title, url, status, signal_type, source_status in rows:
    recommendation = 'SOURCE_REVIEW_REQUIRED' if status == 'source_review_required' else 'NEEDS_REVIEW'
    safe = lambda value: str(value or '').replace('|', '\\|').replace('\n', ' ')
    lines.append(f'| {evidence_id} | {safe(name)} | {safe(platform)} | {safe(title)} | {safe(source_status)} | {recommendation} |')
    lines.append('')
    lines.append(f'Source: {url}')
    lines.append('')
    lines.append(f'Reason: public evidence is retained for human validation before approval. Current signal type: {signal_type or "unclassified"}.')
    lines.append('')

OUT.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
print(f'wrote {len(rows)} queue items to {OUT}')
