"""Discover public social links from already registered official websites.

Only same-page public links are considered. No login, private groups, profiles,
or platform search endpoints are used. Run: python discover_sources.py --once
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(__import__('os').environ.get('DATABASE_PATH', str(BASE_DIR / 'ember_signal.db')))
UA = 'EmberSignalSourceDiscovery/1.0 (+https://kanpi1inburma.manus.space/ember-signal)'
PLATFORMS = {
    'facebook.com': 'facebook', 'fb.com': 'facebook',
    'instagram.com': 'instagram', 'youtube.com': 'youtube', 'youtu.be': 'youtube',
    'tiktok.com': 'tiktok', 'linkedin.com': 'linkedin', 'x.com': 'x', 'twitter.com': 'x',
}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.links.append(href.strip())


def platform_for(url):
    host = urlparse(url).netloc.lower().split(':')[0]
    for domain, platform in PLATFORMS.items():
        if host == domain or host.endswith('.' + domain):
            return platform
    return None


def discover(url, timeout):
    req = Request(url, headers={'User-Agent': UA, 'Accept': 'text/html'})
    with urlopen(req, timeout=timeout) as response:
        if response.headers.get_content_type() not in {'text/html', 'application/xhtml+xml'}:
            return []
        html = response.read(2_000_000).decode('utf-8', errors='replace')
    parser = LinkParser()
    parser.feed(html)
    found = set()
    for href in parser.links:
        absolute = urljoin(url, href)
        platform = platform_for(absolute)
        if platform:
            clean = re.split(r'[?#]', absolute, maxsplit=1)[0].rstrip('/')
            found.add((platform, clean))
    return sorted(found)


def run_once(delay, timeout):
    checked = discovered = errors = 0
    with sqlite3.connect(DB_PATH) as conn:
        sources = conn.execute(
            "SELECT id, institution_id, url FROM institution_sources WHERE platform = 'website'"
        ).fetchall()
        for source_id, institution_id, url in sources:
            checked += 1
            try:
                links = discover(url, timeout)
                for platform, social_url in links:
                    conn.execute(
                        """INSERT OR IGNORE INTO institution_sources
                        (institution_id, platform, label, url, is_official)
                        VALUES (?, ?, ?, ?, 0)""",
                        (institution_id, platform, f'Discovered from official website: {url}', social_url),
                    )
                    discovered += conn.execute('SELECT changes()').fetchone()[0]
            except Exception as exc:
                errors += 1
                print(f'{url}: {exc}')
            conn.commit()
            time.sleep(delay)
    return {'checked': checked, 'discovered': discovered, 'errors': errors}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--delay', type=float, default=2.0)
    parser.add_argument('--timeout', type=int, default=15)
    args = parser.parse_args()
    if not args.once:
        parser.error('use --once')
    print(run_once(args.delay, args.timeout))
