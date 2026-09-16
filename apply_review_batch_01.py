import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / 'ember_signal.db'
AUDIT = BASE / 'evidence_review_audit.jsonl'
REVIEWER = 'human-quality-review-2026-09-16'
NOW = datetime.now(timezone.utc).isoformat()

# Approval is limited to unique, verified official website observations whose claims
# were confirmed on the public page. Repeated observations are retained but not published.
DECISIONS = {
    1: {
        'status': 'approved', 'signal_type': 'admissions', 'confidence': 0.90,
        'excerpt': 'STI Myanmar College’s official website describes Foundation-to-Master’s pathways, University of Bedfordshire validation, Yangon/Mandalay/Nay Pyi Taw campuses, and three annual intakes.'
    },
    11: {
        'status': 'approved', 'signal_type': 'campaign', 'confidence': 0.86,
        'excerpt': 'AIM International College’s official website presents scholarships, alumni success stories, and business and management programmes in Mandalay, including ABE and OTHM qualifications.'
    },
    12: {
        'status': 'approved', 'signal_type': 'admissions', 'confidence': 0.91,
        'excerpt': 'ATBC International College’s official website identifies the institution as a private education provider established in 2019 and lists business, management, diploma, and master’s programmes.'
    },
    13: {
        'status': 'approved', 'signal_type': 'course', 'confidence': 0.93,
        'excerpt': 'Auston College Myanmar’s official website describes tertiary Engineering and IT education and lists Pre-Foundation, Integrated HND, and Bachelor programmes, with campuses in Yangon and Mandalay.'
    },
    16: {
        'status': 'approved', 'signal_type': 'partnership', 'confidence': 0.92,
        'excerpt': 'British United College’s official website describes the institution as a private higher-education provider established in 2017 and states that it collaborates with universities in Singapore and the UK.'
    },
    19: {
        'status': 'approved', 'signal_type': 'course', 'confidence': 0.94,
        'excerpt': 'Chindwin College’s official website describes its HND pathway, BTEC Pearson approval, degree partnerships including the University of Portsmouth, and campuses in Yangon, Mandalay, and Taunggyi.'
    },
    15: {
        'status': 'rejected', 'signal_type': 'course', 'confidence': 0.99,
        'reason': 'Duplicate observation of evidence 13 from the same official source; institution identity mapping differs and requires denominator adjudication before reuse.'
    },
    24: {
        'status': 'rejected', 'signal_type': 'campaign', 'confidence': 0.99,
        'reason': 'Duplicate observation of evidence 11 from the same official source and timestamp window; retain only one public signal.'
    },
    25: {
        'status': 'rejected', 'signal_type': 'admissions', 'confidence': 0.99,
        'reason': 'Duplicate observation of evidence 12 from the same official source and timestamp window; retain only one public signal.'
    },
    29: {
        'status': 'rejected', 'signal_type': 'partnership', 'confidence': 0.99,
        'reason': 'Duplicate observation of evidence 16 from the same official source and timestamp window; retain only one public signal.'
    },
}

with sqlite3.connect(DB) as conn:
    conn.execute('BEGIN')
    for evidence_id, decision in DECISIONS.items():
        row = conn.execute('''
            SELECT e.id, e.review_status, s.verification_status
            FROM evidence_items e
            LEFT JOIN institution_sources s ON s.id = e.source_id
            WHERE e.id = ?
        ''', (evidence_id,)).fetchone()
        if not row:
            raise RuntimeError(f'evidence {evidence_id} not found')
        if row[1] != 'unreviewed':
            raise RuntimeError(f'evidence {evidence_id} is already {row[1]}')
        if row[2] != 'verified':
            raise RuntimeError(f'evidence {evidence_id} source is not verified')
        if decision['status'] == 'approved':
            conn.execute('''
                UPDATE evidence_items
                SET review_status = ?, signal_type = ?, confidence = ?, excerpt = ?
                WHERE id = ?
            ''', (decision['status'], decision['signal_type'], decision['confidence'], decision['excerpt'], evidence_id))
        else:
            conn.execute('''
                UPDATE evidence_items
                SET review_status = ?, confidence = ?
                WHERE id = ?
            ''', (decision['status'], decision['confidence'], evidence_id))
    conn.commit()

with AUDIT.open('a', encoding='utf-8') as handle:
    for evidence_id, decision in DECISIONS.items():
        handle.write(json.dumps({
            'reviewed_at': NOW, 'reviewer': REVIEWER,
            'evidence_id': evidence_id, 'decision': decision['status'],
            'signal_type': decision.get('signal_type'),
            'confidence': decision['confidence'],
            'reason': decision.get('reason', 'Official public page confirmed institution identity and claim.'),
            'source_check': 'public official website fetched 2026-09-16',
        }, ensure_ascii=False) + '\n')

with sqlite3.connect(DB) as conn:
    print('review_status_counts', conn.execute('SELECT review_status, COUNT(*) FROM evidence_items GROUP BY review_status ORDER BY review_status').fetchall())
    print('approved_ids', [r[0] for r in conn.execute("SELECT id FROM evidence_items WHERE review_status='approved' ORDER BY id")])
    print('public_verified_approved', conn.execute('''
        SELECT COUNT(*) FROM evidence_items e JOIN institution_sources s ON s.id=e.source_id
        WHERE e.review_status='approved' AND s.verification_status='verified'
    ''').fetchone()[0])
print(f'audit_log={AUDIT}')
