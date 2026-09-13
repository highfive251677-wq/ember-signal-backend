from datetime import datetime, timezone
from pathlib import Path
import sqlite3

import app

DB_PATH = Path(__file__).resolve().parent / 'ember_signal.db'
VERIFIED_AT = datetime.now(timezone.utc).isoformat()

# Only sources independently verified from official pages or cross-platform identity.
# Medium-confidence rows are retained as needs_review, never marked verified.
BATCH = [
    ('AIE College', 'Yangon', None, [('facebook', 'https://www.facebook.com/aiecollegemm/'), ('instagram', 'https://www.instagram.com/aie_college/'), ('tiktok', 'https://www.tiktok.com/@aiecollege')], 'high', 'Social identities cross-link and match Yangon institution details; no official website verified.'),
    ('AIM International College', 'Mandalay', 'https://www.aim.edu.mm/', [('facebook', 'https://www.facebook.com/AIMMdy/')], 'high', 'Official website identifies the Mandalay institution and directly links the Facebook page.'),
    ('ATBC International College', 'Yangon', 'https://atbc.edu.mm/', [('facebook', 'https://www.facebook.com/atbcinternationalcollege2019/'), ('linkedin', 'https://mm.linkedin.com/company/atbcedu')], 'high', 'Official website, Facebook, and LinkedIn cross-link and match Yangon identity.'),
    ('AU MIT MYANMAR College', 'Mandalay', 'https://www.aumitmyanmar.com/', [('facebook', 'https://www.facebook.com/aumitmyanmarmdy/about/')], 'high', 'Official website verifies Mandalay campus; public Facebook identity matches.'),
    ('AU MIT Myanmar College', 'Yangon', 'https://www.aumitmyanmar.com/', [('facebook', 'https://www.facebook.com/AUMITMyanmarCollege/about/')], 'high', 'Official website verifies Yangon campus; public Facebook identity matches.'),
    ('AUSTON College', 'Mandalay', 'https://auston.edu.mm/', [('facebook', 'https://www.facebook.com/austoncollege/'), ('linkedin', 'https://mm.linkedin.com/company/auston-college-myanmar'), ('youtube', 'https://www.youtube.com/@austoncollegemyanmar')], 'high', 'Official website directly links the social identities and confirms Mandalay campus.'),
    ('AUSTON College', 'Yangon', 'https://auston.edu.mm/', [('facebook', 'https://www.facebook.com/austoncollege/'), ('linkedin', 'https://th.linkedin.com/company/auston-college-myanmar')], 'high', 'Official website confirms Yangon campus; LinkedIn identity cross-links to the site.'),
    ('BIY College', 'Yangon', None, [('facebook', 'https://www.facebook.com/BusinessInstituteYangonBIY/')], 'medium', 'Public BIY page matches Yangon and institution-specific announcements; website DNS was not verified.'),
    ('Brain Box Acumen School of Management College', 'Mandalay', 'https://brainboxacumen.edu.mm/', [('facebook', 'https://www.facebook.com/brainboxacumen/')], 'high', 'Institution-specific website, address, and public Facebook identity match.'),
    ('British United College', 'Yangon', 'https://buc.edu.mm/', [('facebook', 'https://www.facebook.com/BritishUnitedCollege/'), ('youtube', 'https://www.youtube.com/@britishunitedcollege'), ('tiktok', 'https://www.tiktok.com/@britishunitedcollege'), ('linkedin', 'https://mm.linkedin.com/company/british-united-college')], 'high', 'Official website and multiple public channels cross-link and match Yangon identity.'),
    ('Chindwin Technological College', 'Yangon', 'https://ctu.edu.mm/', [], 'high', 'Official website and Yangon addresses verified; no social URL included because public identity was not independently verified.'),
    ('Compu Tech ICT College', 'Yangon', None, [('facebook', 'https://www.facebook.com/computechictcollege/'), ('youtube', 'https://www.youtube.com/@COMPUTECHICTCollege')], 'medium', 'Public social identities match the institution name and Yangon; no official website verified.'),
]

app.init_db()
with sqlite3.connect(DB_PATH) as conn:
    for name, city, website, social_urls, confidence, notes in BATCH:
        institution = conn.execute(
            'SELECT id FROM institutions WHERE name = ? AND city = ? ORDER BY id LIMIT 1',
            (name, city),
        ).fetchone()
        if not institution:
            print('NOT FOUND', name, city)
            continue
        institution_id = str(institution[0])
        entries = []
        if website:
            entries.append(('website', website, True))
        entries.extend((platform, url, False) for platform, url in social_urls)
        for platform, url, official in entries:
            conn.execute(
                """INSERT INTO institution_sources
                (institution_id, platform, label, url, is_official,
                 verification_status, confidence, verification_notes, verified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(institution_id, url) DO UPDATE SET
                    platform = excluded.platform,
                    label = excluded.label,
                    is_official = excluded.is_official,
                    verification_status = excluded.verification_status,
                    confidence = excluded.confidence,
                    verification_notes = excluded.verification_notes,
                    verified_at = excluded.verified_at""",
                (institution_id, platform, f'Quality batch: {name}', url, int(official),
                 'verified' if confidence == 'high' else 'needs_review',
                 0.9 if confidence == 'high' else 0.6, notes, VERIFIED_AT),
            )
    conn.commit()
    print('sources', conn.execute('SELECT COUNT(*) FROM institution_sources').fetchone()[0])
    print('verified', conn.execute("SELECT COUNT(*) FROM institution_sources WHERE verification_status='verified'").fetchone()[0])
    print('needs_review', conn.execute("SELECT COUNT(*) FROM institution_sources WHERE verification_status='needs_review'").fetchone()[0])
