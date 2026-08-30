from __future__ import annotations
import sqlite3, json, uuid
from datetime import datetime, timezone
from pathlib import Path
from .config import DB_PATH

SCHEMA_SQL = '''
CREATE TABLE IF NOT EXISTS evaluation_criteria (
    criterion_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    weight REAL NOT NULL,
    max_score REAL NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS rfp_runs (
    rfp_run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS supplier_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfp_run_id TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    submission_date TEXT NOT NULL,
    experience_rating REAL NOT NULL,
    absolute_score REAL NOT NULL,
    ppi REAL NOT NULL,
    final_rank INTEGER NOT NULL,
    result_json TEXT NOT NULL,
    FOREIGN KEY (rfp_run_id) REFERENCES rfp_runs(rfp_run_id)
);
'''

SEED = [
    (1, "Technical Capability", "Architecture, integrations, scalability, technical fit", 30.0, 10.0, 1),
    (2, "Implementation Plan", "Timeline, milestones, staffing, risk plan", 20.0, 10.0, 1),
    (3, "Commercial Value", "Pricing clarity, total cost, assumptions", 20.0, 10.0, 1),
    (4, "Security & Compliance", "Controls, certifications, privacy, auditability", 20.0, 10.0, 1),
    (5, "Support & Experience", "Support model, similar projects, references", 10.0, 10.0, 1),
]

def connect(db_path: Path = DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path = DB_PATH):
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        count = conn.execute("SELECT COUNT(*) FROM evaluation_criteria").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO evaluation_criteria VALUES (?, ?, ?, ?, ?, ?)", SEED
            )
        conn.commit()

def get_active_criteria(db_path: Path = DB_PATH):
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM evaluation_criteria WHERE is_active=1 ORDER BY criterion_id"
        ).fetchall()
    return [dict(r) for r in rows]

def validate_active_weights(criteria):
    total = sum(float(c["weight"]) for c in criteria)
    return abs(total - 100.0) < 1e-9, total

def create_run(db_path: Path = DB_PATH):
    run_id = str(uuid.uuid4())
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO rfp_runs(rfp_run_id, created_at, status) VALUES (?, ?, ?)",
            (run_id, datetime.now(timezone.utc).isoformat(), "RUNNING")
        )
        conn.commit()
    return run_id

def finish_run(run_id: str, status: str = "COMPLETED", db_path: Path = DB_PATH):
    with connect(db_path) as conn:
        conn.execute("UPDATE rfp_runs SET status=? WHERE rfp_run_id=?", (status, run_id))
        conn.commit()

def save_supplier_result(run_id: str, row: dict, db_path: Path = DB_PATH):
    with connect(db_path) as conn:
        conn.execute(
            '''INSERT INTO supplier_results
               (rfp_run_id, supplier_name, submission_date, experience_rating,
                absolute_score, ppi, final_rank, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                run_id, row["supplier_name"], row["submission_date"],
                float(row["experience_rating"]), float(row["absolute_score"]),
                float(row["ppi"]), int(row["final_rank"]),
                json.dumps(row, ensure_ascii=False)
            )
        )
        conn.commit()

def load_run_results(run_id: str, db_path: Path = DB_PATH):
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM supplier_results WHERE rfp_run_id=? ORDER BY final_rank",
            (run_id,)
        ).fetchall()
    return [dict(r) for r in rows]
