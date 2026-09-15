from datetime import datetime, timezone
from pathlib import Path
import sqlite3

DB = Path(__file__).resolve().parent / 'ember_signal.db'
# Source IDs approved by three independent read-only identity reviews.
APPROVED = {
    2: 'Official STI website; public About page confirms institution and Yangon campus.',
    3: 'Official STI website; public About page confirms institution and Yangon campus for duplicate record.',
    9: 'Public Instagram account exactly matches STI Myanmar College Official, links to stiedu.net, and identifies Yangon campus.',
    10: 'Public LinkedIn organization profile names STI Myanmar University/College, links to stiedu.net, and lists Yangon headquarters.',
    11: 'Public YouTube channel exactly matches STI Myanmar College and links/corroborates official STI identity.',
    15: 'Public YouTube channel exactly matches STI Myanmar College and corroborates multi-campus STI identity for duplicate record.',
}
now = datetime.now(timezone.utc).isoformat()
with sqlite3.connect(DB) as conn:
    for source_id, note in APPROVED.items():
        conn.execute('''UPDATE institution_sources
                        SET verification_status='verified', confidence=0.9,
                            verification_notes=?, verified_at=?
                        WHERE id=?''', (note, now, source_id))
    conn.commit()
    print('promoted', conn.execute("SELECT COUNT(*) FROM institution_sources WHERE id IN (%s) AND verification_status='verified'" % ','.join(map(str, APPROVED))).fetchone()[0])
    print('verified_total', conn.execute("SELECT COUNT(*) FROM institution_sources WHERE verification_status='verified'").fetchone()[0])
