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
    try:
        with EVIDENCE_PATH.open("r", encoding="utf-8") as evidence_file:
            return json.load(evidence_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"error": "Evidence file not found"}


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
    return jsonify({"status": "ok", "database": "ok", "records": total})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, threaded=False)
