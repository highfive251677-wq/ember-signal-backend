from pathlib import Path
import sqlite3
import openpyxl

DB_PATH = Path(__file__).resolve().parent / 'ember_signal.db'
WORKBOOK = Path('/tmp/sheet.xlsx')
wb = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=True)
ws = wb['Combined Data']

sources = []
for record_number, row in enumerate(list(ws.iter_rows(values_only=True))[5:], 1):
    if not row[1] or not row[4] or not row[8]:
        continue
    url = str(row[8]).strip()
    if url.startswith(('http://', 'https://')):
        sources.append((str(record_number), 'website', 'Official website', url, 1))

with sqlite3.connect(DB_PATH) as conn:
    conn.executemany(
        """INSERT OR IGNORE INTO institution_sources
        (institution_id, platform, label, url, is_official)
        VALUES (?, ?, ?, ?, ?)""",
        sources,
    )
    conn.commit()
    count = conn.execute('SELECT COUNT(*) FROM institution_sources').fetchone()[0]

print(f'seeded {len(sources)} official website sources; total sources={count}')
