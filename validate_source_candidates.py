from __future__ import annotations
import argparse
import re
import sqlite3
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
DB = BASE / 'ember_signal.db'
UA = 'EmberSignalSourceValidator/1.0 (+https://kanpi1inburma.manus.space/ember-signal)'

class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.title=[]; self.in_title=False
    def handle_starttag(self, tag, attrs): self.in_title = tag == 'title'
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.title.append(re.sub(r'\s+', ' ', data).strip())

def robots_allowed(url):
    p=urlparse(url); rp=RobotFileParser(f'{p.scheme}://{p.netloc}/robots.txt')
    try:
        rp.read(); return rp.can_fetch(UA, url)
    except Exception:
        return False

def check(url, timeout):
    p=urlparse(url)
    if p.scheme not in {'http','https'}: return ('invalid_scheme', None, None, '')
    if not robots_allowed(url): return ('robots_denied_or_unavailable', None, None, '')
    try:
        req=Request(url, headers={'User-Agent':UA, 'Accept':'text/html,application/xhtml+xml'})
        with urlopen(req, timeout=timeout) as r:
            ctype=r.headers.get_content_type(); raw=r.read(200_000)
            title=''
            if ctype in {'text/html','application/xhtml+xml'}:
                parser=TitleParser(); parser.feed(raw.decode('utf-8','replace')); title=' '.join(parser.title)[:500]
            return ('accessible', getattr(r,'status',200), ctype, title)
    except Exception as exc:
        return (type(exc).__name__ + ': ' + str(exc)[:300], None, None, '')

def main(delay, timeout):
    now=datetime.now(timezone.utc).isoformat(); checked=0
    with sqlite3.connect(DB) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS source_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, source_id INTEGER NOT NULL,
            checked_at TEXT NOT NULL, outcome TEXT NOT NULL, http_status INTEGER,
            content_type TEXT, page_title TEXT, UNIQUE(source_id, checked_at)
        )''')
        rows=conn.execute("SELECT id,url FROM institution_sources WHERE verification_status != 'verified' ORDER BY id").fetchall()
        for source_id,url in rows:
            outcome,status,ctype,title=check(url, timeout); checked += 1
            conn.execute('INSERT INTO source_checks(source_id,checked_at,outcome,http_status,content_type,page_title) VALUES (?,?,?,?,?,?)', (source_id,now,outcome,status,ctype,title))
            conn.commit(); time.sleep(max(0.5,delay))
    print({'checked':checked,'checked_at':now})

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--delay',type=float,default=1.0); p.add_argument('--timeout',type=int,default=10); a=p.parse_args(); main(a.delay,a.timeout)
