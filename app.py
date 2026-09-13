import json
import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "ember_signal.db")))
EVIDENCE_PATH = Path(
    os.getenv("EVIDENCE_PATH", str(BASE_DIR / "ember-signal-evidence.json"))
)

# The repository stores index.html at the project root.
app = Flask(__name__, template_folder=str(BASE_DIR))
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")


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
            "FROM institutions ORDER BY name LIMIT 100"
        ).fetchall()
    return rows


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, threaded=False)
