"""Collect evidence from explicitly registered public institution sources.

This collector intentionally does not log in, bypass robots.txt, scrape private
profiles/groups, or collect personal profile data. It reads only URLs already
registered in institution_sources and stores a content hash plus a short excerpt.
Run once from cron: python collector.py --once
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(__import__("os").environ.get("DATABASE_PATH", str(BASE_DIR / "ember_signal.db")))
USER_AGENT = "EmberSignalPublicCollector/1.0 (+https://kanpi1inburma.manus.space/ember-signal)"
KEYWORDS = {
    "admissions": ("admission", "enrol", "enroll", "intake", "application", "လျှောက်လွှာ"),
    "course": ("course", "class", "training", "certificate", "diploma", "သင်တန်း"),
    "campaign": ("scholarship", "discount", "promotion", "open day", "အခွင့်အရေး"),
    "event": ("event", "seminar", "workshop", "ပွဲ", "ဆွေးနွေး"),
    "partnership": ("partner", "partnership", "agreement", "collaboration"),
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = []
        self.description = ""
        self.body = []
        self._in_title = False
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta" and attrs.get("name", "").lower() in {"description", "og:description"}:
            self.description = attrs.get("content", "")[:1000]

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript", "svg"} and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._skip:
            return
        cleaned = re.sub(r"\s+", " ", data).strip()
        if not cleaned:
            return
        if self._in_title:
            self.title.append(cleaned)
        self.body.append(cleaned)


def allowed_by_robots(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser(robots_url)
    try:
        parser.read()
        return parser.can_fetch(USER_AGENT, url)
    except Exception:
        # Fail closed when robots.txt cannot be checked.
        return False


def classify(text: str) -> str | None:
    lowered = text.lower()
    for signal_type, words in KEYWORDS.items():
        if any(word.lower() in lowered for word in words):
            return signal_type
    return None


def collect_url(url: str, timeout: int, max_bytes: int) -> dict:
    if urlparse(url).scheme not in {"http", "https"}:
        raise ValueError("only http(s) public URLs are allowed")
    if not allowed_by_robots(url):
        raise PermissionError("robots.txt does not permit this collector")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"unsupported content type: {content_type}")
        raw = response.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError("response exceeds configured size limit")
    parser = PageParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    title = " ".join(parser.title).strip()[:500]
    text = re.sub(r"\s+", " ", " ".join(parser.body)).strip()
    excerpt = (parser.description or text)[:1200]
    return {
        "title": title or url,
        "excerpt": excerpt,
        "signal_type": classify(f"{title} {excerpt}"),
        "content_hash": hashlib.sha256(raw).hexdigest(),
    }


def run_once(delay: float, timeout: int, max_bytes: int) -> dict:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    checked = stored = skipped = errors = 0
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        sources = conn.execute(
            "SELECT id, institution_id, platform, url FROM institution_sources ORDER BY id"
        ).fetchall()
        for source_id, institution_id, platform, url in sources:
            checked += 1
            try:
                item = collect_url(url, timeout, max_bytes)
                conn.execute(
                    """INSERT OR IGNORE INTO evidence_items
                    (institution_id, source_id, source_url, platform, observed_at,
                     title, excerpt, signal_type, confidence, review_status, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unreviewed', ?)""",
                    (institution_id, source_id, url, platform, now, item["title"],
                     item["excerpt"], item["signal_type"], 0.5, item["content_hash"]),
                )
                stored += conn.execute("SELECT changes()").fetchone()[0]
            except PermissionError:
                skipped += 1
            except Exception as exc:
                errors += 1
                print(json.dumps({"url": url, "error": str(exc)}, ensure_ascii=False))
            conn.execute(
                "UPDATE institution_sources SET last_checked_at = ? WHERE id = ?",
                (now, source_id),
            )
            conn.commit()
            time.sleep(delay)
    return {"checked": checked, "stored": stored, "skipped": skipped, "errors": errors}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="run one collection pass")
    parser.add_argument("--delay", type=float, default=2.0, help="seconds between sources")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    args = parser.parse_args()
    if not args.once:
        parser.error("use --once; schedule this command externally")
    print(json.dumps(run_once(args.delay, args.timeout, args.max_bytes), ensure_ascii=False))
