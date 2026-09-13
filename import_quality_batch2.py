from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import app

DB_PATH = Path(__file__).resolve().parent / 'ember_signal.db'
VERIFIED_AT = datetime.now(timezone.utc).isoformat()

# institution_id, official website, public social URLs, verification note
BATCH = [
 ('1','https://mcu.edu.mm/', [('facebook','https://www.facebook.com/MyanmarCommercialCollege/')], 'Official domain identifies Myanmar Commercial College in Mandalay and public Facebook identity matches.'),
 ('2','https://www.lbu.edu.mm/', [('facebook','https://www.facebook.com/LBUMandalay'),('youtube','https://www.youtube.com/channel/UCqo6ZbwprQbiZcRvMe1sWxw'),('tiktok','https://www.tiktok.com/@lbu_mandalay')], 'Official LBU domain directly links the public social identities and identifies the Mandalay campus.'),
 ('3','https://stiedu.net/', [('youtube','https://www.youtube.com/@stimyanmar_official'),('linkedin','https://www.linkedin.com/company/sti-myanmar-universtiy/')], 'Official STI website identifies the Mandalay campus and directly links the public YouTube and LinkedIn identities.'),
 ('4','https://sti.edu.mm/', [('facebook','https://www.facebook.com/STIMU.MDY/about/')], 'Official STI site identifies Health Science faculty and Mandalay campus; public page identifies STI Mandalay Campus.'),
 ('5','https://ctu.edu.mm/', [], 'Official CTU domain and Mandalay campus/contact pages verify the institution; no social URL independently verified.'),
 ('6','https://strategyfirst.edu.mm/', [('instagram','https://www.instagram.com/strategyfirst_sfic/'),('youtube','https://www.youtube.com/@strategyfirst-intl-college')], 'Official website confirms Mandalay campuses and directly links the public Instagram and YouTube pages.'),
 ('7','https://www.nvl-college.com/', [], 'Official NVL domain and contact page verify the Mandalay institution; social pages were login-gated and excluded.'),
 ('8','https://mibacollege.com/', [('youtube','https://www.youtube.com/@miba_college1892'),('facebook','https://www.facebook.com/mandalaymiba/')], 'Official MIBA website verifies Mandalay campus; public YouTube and indexed Facebook identities match.'),
 ('11','https://www.inet.edu.mm/', [('facebook','https://www.facebook.com/iNetCollegeMyanmar/'),('tiktok','https://www.tiktok.com/@inetcollege')], 'Official iNet website directly links the public Facebook and TikTok identities and identifies Mandalay.'),
 ('12','https://clceducollege.com/', [], 'Official CLC website verifies the Mandalay campus; social page was not independently verified.'),
 ('13','https://newnextcollege.com/', [], 'Official New Next domain verifies the Mandalay institution; social pages were login-gated and excluded.'),
 ('29','https://gusto-education.com/', [('linkedin','https://mm.linkedin.com/company/gusto-university')], 'Official GUSTO website verifies Yangon; public LinkedIn organization page matches identity and location.'),
]

app.init_db()
with sqlite3.connect(DB_PATH) as conn:
    for institution_id, website, socials, notes in BATCH:
        entries = [('website', website, 1)] + [(p, u, 0) for p, u in socials]
        for platform, url, official in entries:
            conn.execute(
                """INSERT INTO institution_sources
                (institution_id, platform, label, url, is_official,
                 verification_status, confidence, verification_notes, verified_at)
                VALUES (?, ?, ?, ?, ?, 'verified', 0.9, ?, ?)
                ON CONFLICT(institution_id, url) DO UPDATE SET
                    platform=excluded.platform, label=excluded.label,
                    is_official=excluded.is_official,
                    verification_status=excluded.verification_status,
                    confidence=excluded.confidence,
                    verification_notes=excluded.verification_notes,
                    verified_at=excluded.verified_at""",
                (institution_id, platform, 'Quality batch 2', url, official, notes, VERIFIED_AT),
            )
    conn.commit()
    print('sources', conn.execute('SELECT COUNT(*) FROM institution_sources').fetchone()[0])
    print('verified', conn.execute("SELECT COUNT(*) FROM institution_sources WHERE verification_status='verified'").fetchone()[0])
