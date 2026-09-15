import csv
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / 'ember_signal.db'
OUT = Path(__file__).resolve().parent / 'source_coverage_matrix.csv'
PLATFORMS = ('website', 'google_maps', 'facebook', 'tiktok')

with sqlite3.connect(DB) as conn:
    rows = conn.execute('''
        SELECT i.id, i.name, i.city, i.township, i.type, i.status,
               s.platform, s.url, s.verification_status, s.is_official
        FROM institutions i
        LEFT JOIN institution_sources s ON s.institution_id = i.id
        ORDER BY i.id, s.platform, s.id
    ''').fetchall()

records = {}
for institution_id, name, city, township, kind, status, platform, url, verification, official in rows:
    rec = records.setdefault(institution_id, {
        'institution_id': institution_id, 'name': name or '', 'city': city or '',
        'township': township or '', 'type': kind or '', 'status': status or '',
        **{f'{p}_url': '' for p in PLATFORMS},
        **{f'{p}_state': 'missing' for p in PLATFORMS},
        'verified_platform_count': 0, 'missing_platforms': ''
    })
    if platform in PLATFORMS and url:
        key = f'{platform}_url'
        if not rec[key]:
            rec[key] = url
            rec[f'{platform}_state'] = verification or 'unverified'

for rec in records.values():
    rec['verified_platform_count'] = sum(rec[f'{p}_state'] == 'verified' for p in PLATFORMS)
    rec['missing_platforms'] = ','.join(p for p in PLATFORMS if rec[f'{p}_state'] == 'missing')

fields = ['institution_id','name','city','township','type','status']
for p in PLATFORMS:
    fields.extend([f'{p}_url', f'{p}_state'])
fields.extend(['verified_platform_count','missing_platforms'])
with OUT.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records.values())

print(f'institutions={len(records)} output={OUT}')
for p in PLATFORMS:
    print(p, sum(r[f'{p}_state'] == 'verified' for r in records.values()), 'verified')
print('fully_missing_all', sum(r['missing_platforms'] == ','.join(PLATFORMS) for r in records.values()))
