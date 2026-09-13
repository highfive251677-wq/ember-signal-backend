import json
import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "ember_signal.db")))
EVIDENCE_PATH = Path(
    os.getenv("EVIDENCE_PATH", str(BASE_DIR / "ember-signal-evidence.json"))
)

# The repository stores index.html at the project root.
app = Flask(__name__, template_folder=str(BASE_DIR))
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")


@app.after_request
def add_api_headers(response):
    """Allow the hosted Ember Signal surface to read this API."""
    origin = request.headers.get("Origin", "")
    allowed = {
        "https://kanpi1inburma.manus.space",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
    if origin in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    return response


def init_db():
    """Create the required schema without deleting existing data."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS institutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT,
                township TEXT,
                type TEXT,
                status TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS institution_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                label TEXT,
                url TEXT NOT NULL,
                is_official INTEGER NOT NULL DEFAULT 0,
                last_checked_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(institution_id, url)
            )
        """)
        source_columns = {row[1] for row in conn.execute("PRAGMA table_info(institution_sources)")}
        for column, definition in {
            "verification_status": "TEXT NOT NULL DEFAULT 'unverified'",
            "confidence": "REAL",
            "verification_notes": "TEXT",
            "verified_at": "TEXT",
        }.items():
            if column not in source_columns:
                conn.execute(f"ALTER TABLE institution_sources ADD COLUMN {column} {definition}")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution_id TEXT NOT NULL,
                source_id INTEGER,
                source_url TEXT NOT NULL,
                platform TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                title TEXT,
                excerpt TEXT,
                signal_type TEXT,
                confidence REAL,
                review_status TEXT NOT NULL DEFAULT 'unreviewed',
                content_hash TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(institution_id, source_url, content_hash),
                FOREIGN KEY(source_id) REFERENCES institution_sources(id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_institution ON institution_sources(institution_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_institution ON evidence_items(institution_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_observed ON evidence_items(observed_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_review ON evidence_items(review_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_signal ON evidence_items(signal_type)")
        conn.commit()


def get_db_data():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, name, city, township, type, status "
            "FROM institutions ORDER BY name"
        ).fetchall()
    return rows


def row_to_dict(row):
    return {
        "id": row[0],
        "name": row[1],
        "city": row[2],
        "township": row[3],
        "type": row[4],
        "status": row[5],
    }


def query_institutions():
    """Return filtered institutions plus pagination metadata."""
    search = request.args.get("q", "").strip()
    city = request.args.get("city", "").strip()
    institution_type = request.args.get("type", "").strip()
    status = request.args.get("status", "").strip()
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1
    try:
        per_page = min(100, max(1, int(request.args.get("per_page", "25"))))
    except ValueError:
        per_page = 25

    clauses = []
    params = []
    if search:
        clauses.append("(name LIKE ? OR city LIKE ? OR township LIKE ?)")
        needle = f"%{search}%"
        params.extend([needle, needle, needle])
    if city:
        clauses.append("city = ?")
        params.append(city)
    if institution_type:
        clauses.append("type = ?")
        params.append(institution_type)
    if status:
        clauses.append("status = ?")
        params.append(status)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM institutions{where}", params
        ).fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            "SELECT id, name, city, township, type, status "
            f"FROM institutions{where} ORDER BY name LIMIT ? OFFSET ?",
            params + [per_page, offset],
        ).fetchall()
    return {
        "data": [row_to_dict(row) for row in rows],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
        },
        "filters": {"q": search, "city": city, "type": institution_type, "status": status},
    }


def get_json_evidence():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, title, source_url, observed_at, review_status, excerpt "
            "FROM evidence_items ORDER BY observed_at DESC LIMIT 100"
        ).fetchall()
    return {"records": [
        {"id": r[0], "title": r[1], "source": r[2], "observedAt": r[3],
         "status": r[4], "summary": r[5]}
        for r in rows
    ]}


init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/signals")
def get_signals():
    return jsonify({
        "top_brands": get_db_data(),
        "evidence": get_json_evidence(),
    })


@app.route("/api/institutions")
def institutions():
    return jsonify(query_institutions())


@app.route("/api/institutions/<institution_id>")
def institution_detail(institution_id):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id, name, city, township, type, status "
            "FROM institutions WHERE id = ?",
            (institution_id,),
        ).fetchone()
    if row is None:
        return jsonify({"error": "Institution not found"}), 404
    return jsonify({"data": row_to_dict(row)})


@app.route("/api/summary")
def summary():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM institutions").fetchone()[0]
        by_city = conn.execute(
            "SELECT city, COUNT(*) FROM institutions GROUP BY city ORDER BY COUNT(*) DESC"
        ).fetchall()
        by_type = conn.execute(
            "SELECT type, COUNT(*) FROM institutions GROUP BY type ORDER BY COUNT(*) DESC"
        ).fetchall()
    return jsonify({
        "total": total,
        "by_city": [{"name": name, "count": count} for name, count in by_city],
        "by_type": [{"name": name, "count": count} for name, count in by_type],
    })


@app.route("/api/health")
def health():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM institutions").fetchone()[0]
        sources = conn.execute("SELECT COUNT(*) FROM institution_sources").fetchone()[0]
        evidence = conn.execute("SELECT COUNT(*) FROM evidence_items").fetchone()[0]
    return jsonify({"status": "ok", "database": "ok", "records": total, "sources": sources, "evidence": evidence})


@app.route("/api/dashboard")
def dashboard():
    """Return one payload for the premium overview dashboard."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        totals = {
            "institutions": conn.execute("SELECT COUNT(*) FROM institutions").fetchone()[0],
            "sources": conn.execute(
                "SELECT COUNT(*) FROM institution_sources WHERE verification_status = 'verified'"
            ).fetchone()[0],
            "evidence": conn.execute(
                """SELECT COUNT(*) FROM evidence_items e JOIN institution_sources s
                ON s.id = e.source_id WHERE s.verification_status = 'verified'"""
            ).fetchone()[0],
            "unreviewed": conn.execute(
                """SELECT COUNT(*) FROM evidence_items e JOIN institution_sources s
                ON s.id = e.source_id WHERE s.verification_status = 'verified'
                AND e.review_status = 'unreviewed'"""
            ).fetchone()[0],
        }
        covered = conn.execute(
            "SELECT COUNT(*) FROM institutions i WHERE EXISTS "
            "(SELECT 1 FROM institution_sources s WHERE s.institution_id = i.id "
            "AND s.verification_status = 'verified')"
        ).fetchone()[0]
        signal_mix = conn.execute(
            "SELECT COALESCE(e.signal_type, 'unclassified'), COUNT(*) "
            "FROM evidence_items e JOIN institution_sources s ON s.id = e.source_id "
            "WHERE s.verification_status = 'verified' "
            "GROUP BY COALESCE(e.signal_type, 'unclassified') "
            "ORDER BY COUNT(*) DESC"
        ).fetchall()
        recent = conn.execute(
            "SELECT e.id, e.institution_id, i.name, e.platform, e.title, "
            "e.signal_type, e.review_status, e.observed_at, e.source_url "
            "FROM evidence_items e JOIN institutions i ON i.id = e.institution_id "
            "JOIN institution_sources s ON s.id = e.source_id "
            "WHERE s.verification_status = 'verified' "
            "ORDER BY e.observed_at DESC LIMIT 10"
        ).fetchall()
    totals["source_coverage_percent"] = round(
        covered / totals["institutions"] * 100, 1
    ) if totals["institutions"] else 0
    return jsonify({
        "totals": totals,
        "signal_mix": [{"name": name, "count": count} for name, count in signal_mix],
        "recent_evidence": [
            {"id": r[0], "institution_id": r[1], "institution_name": r[2],
             "platform": r[3], "title": r[4], "signal_type": r[5],
             "review_status": r[6], "observed_at": r[7], "source_url": r[8]}
            for r in recent
        ],
    })


@app.route("/api/coverage")
def coverage():
    """Show which institutions have public sources and evidence coverage."""
    init_db()
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1
    per_page = min(100, max(1, int(request.args.get("per_page", "25"))))
    offset = (page - 1) * per_page
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM institutions").fetchone()[0]
        rows = conn.execute(
            """
            SELECT i.id, i.name, i.city, i.township, i.type,
                   COUNT(DISTINCT CASE WHEN s.verification_status = 'verified' THEN s.id END),
                   COUNT(DISTINCT CASE WHEN s.verification_status = 'verified' THEN e.id END)
            FROM institutions i
            LEFT JOIN institution_sources s ON s.institution_id = i.id
            LEFT JOIN evidence_items e ON e.institution_id = i.id AND e.source_id = s.id
            GROUP BY i.id, i.name, i.city, i.township, i.type
            ORDER BY i.name LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        ).fetchall()
    return jsonify({
        "data": [
            {
                "id": row[0], "name": row[1], "city": row[2],
                "township": row[3], "type": row[4],
                "source_count": row[5], "evidence_count": row[6],
            }
            for row in rows
        ],
        "pagination": {"page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page},
    })


@app.route("/api/institutions/<institution_id>/sources")
def institution_sources(institution_id):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, platform, label, url, is_official, last_checked_at, "
            "verification_status, confidence, verification_notes, verified_at "
            "FROM institution_sources WHERE institution_id = ? ORDER BY platform, label",
            (institution_id,),
        ).fetchall()
    return jsonify({"data": [
        {"id": r[0], "platform": r[1], "label": r[2], "url": r[3], "is_official": bool(r[4]),
         "last_checked_at": r[5], "verification_status": r[6], "confidence": r[7],
         "verification_notes": r[8], "verified_at": r[9]}
        for r in rows
    ]})


@app.route("/api/institutions/<institution_id>/evidence")
def institution_evidence(institution_id):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, source_id, source_url, platform, observed_at, title, excerpt, "
            "signal_type, confidence, review_status, content_hash "
            "FROM evidence_items WHERE institution_id = ? ORDER BY observed_at DESC",
            (institution_id,),
        ).fetchall()
    return jsonify({"data": [
        {"id": r[0], "source_id": r[1], "source_url": r[2], "platform": r[3], "observed_at": r[4],
         "title": r[5], "excerpt": r[6], "signal_type": r[7], "confidence": r[8],
         "review_status": r[9], "content_hash": r[10]}
        for r in rows
    ]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, threaded=False)
