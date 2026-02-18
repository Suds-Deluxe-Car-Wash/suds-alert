"""
Suds Alert — Incident Database (SQLite)
=========================================
Persistent logging of all incidents for audit trail and analytics.
"""

import json
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("suds_alert")

DB_PATH = Path(__file__).parent / "suds_alert.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the incidents table if it doesn't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id     TEXT UNIQUE NOT NULL,
            incident_type   TEXT NOT NULL,
            location        TEXT NOT NULL,
            region          TEXT NOT NULL,
            description     TEXT NOT NULL,
            reporter        TEXT NOT NULL,
            reporter_id     TEXT,
            channel         TEXT NOT NULL,
            recipients      TEXT NOT NULL,
            sms_results     TEXT NOT NULL,
            created_at      TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


def log_incident(
    incident_id: str,
    incident_type: str,
    location: str,
    region: str,
    description: str,
    reporter: str,
    reporter_id: str,
    channel: str,
    recipients: list[str],
    sms_results: list[dict],
):
    """Log an incident to the database."""
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO incidents 
            (incident_id, incident_type, location, region, description, 
             reporter, reporter_id, channel, recipients, sms_results, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            incident_id,
            incident_type,
            location,
            region,
            description,
            reporter,
            reporter_id,
            channel,
            json.dumps(recipients),
            json.dumps(sms_results),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    logger.info(f"Incident {incident_id} logged to database")


def get_incident_count() -> int:
    """Get total number of incidents logged."""
    conn = _get_conn()
    cursor = conn.execute("SELECT COUNT(*) FROM incidents")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_recent_incidents(limit: int = 50) -> list[dict]:
    """Retrieve recent incidents for reporting."""
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_incidents_by_location(location: str, limit: int = 50) -> list[dict]:
    """Retrieve incidents for a specific location."""
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT * FROM incidents WHERE location = ? ORDER BY created_at DESC LIMIT ?",
        (location, limit),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
