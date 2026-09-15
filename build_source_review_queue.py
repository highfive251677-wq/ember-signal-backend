import csv
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

DB = Path(__file__).resolve().parent / 'ember_signal.db'
OUT = Path(__file__).resolve().parent / 'SOURCE_REVIEW_QUEUE.csv'
GENERIC_PATHS = {'', '/', '/share', '/share/'}
with sqlite3.connect(DB) as conn:
    rows = conn.execute('''
        SELECT s.id, s.institution_id, i.name, i.city, s.platform, s.url,
               s.verification_status, s.is_official, s.verification_notes
        FROM institution_sources s JOIN institutions i ON i.id = s.institution_id
        WHERE s.verification_status != 'verified'
        ORDER BY s.id
    ''').fetchall()

out = []
for sid, iid, name, city, platform, url, status, official, notes in rows:
    parsed = urlparse(url or '')
    path = parsed.path.rstrip('/') if parsed.path else ''
    if platform != 'website' and (path in GENERIC_PATHS or '/share/' in (parsed.path or '')):
        decision = 'REJECT_CANDIDATE'
        reason = 'generic host or share link does not identify an official public account'
    elif platform in {'facebook','instagram','tiktok','youtube','linkedin','x'}:
        decision = 'VERIFY_IDENTITY'
        reason = 'check account title, institution name, city, and link relationship against an official source'
    else:
        decision = 'VERIFY_SOURCE'
        reason = 'confirm public source identity and ownership'
    out.append({'source_id':sid,'institution_id':iid,'institution_name':name or '', 'city':city or '', 'platform':platform, 'url':url, 'current_status':status, 'decision':decision, 'reason':reason})

fields=list(out[0]) if out else ['source_id','institution_id','institution_name','city','platform','url','current_status','decision','reason']
with OUT.open('w', newline='', encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(out)
print('candidates', len(out), 'output', OUT)
print('reject_candidates', sum(x['decision']=='REJECT_CANDIDATE' for x in out))
print('verify_identity', sum(x['decision']=='VERIFY_IDENTITY' for x in out))
