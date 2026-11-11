
"""SQLite audit logging, execution traces, and attack correlation."""

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "aegis.db"


@contextmanager
def _get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_audit_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                trace_id TEXT,
                attack_id TEXT,
                approval_id TEXT,
                tool_invoked INTEGER NOT NULL DEFAULT 0,
                tool_succeeded INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        existing = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(audit_logs)"
            ).fetchall()
        }

        migrations = {
            "trace_id": "ALTER TABLE audit_logs ADD COLUMN trace_id TEXT",
            "attack_id": "ALTER TABLE audit_logs ADD COLUMN attack_id TEXT",
            "approval_id": "ALTER TABLE audit_logs ADD COLUMN approval_id TEXT",
            "tool_invoked": (
                "ALTER TABLE audit_logs ADD COLUMN "
                "tool_invoked INTEGER NOT NULL DEFAULT 0"
            ),
            "tool_succeeded": (
                "ALTER TABLE audit_logs ADD COLUMN "
                "tool_succeeded INTEGER NOT NULL DEFAULT 0"
            ),
        }

        for column, statement in migrations.items():
            if column not in existing:
                connection.execute(statement)

        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_trace_id "
            "ON audit_logs(trace_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_attack_id "
            "ON audit_logs(attack_id)"
        )


def log_decision(
    agent_id: str,
    action: str,
    resource: str,
    decision: str,
    reason: str,
    trace_id: str | None = None,
    attack_id: str | None = None,
    approval_id: str | None = None,
    tool_invoked: bool = False,
    tool_succeeded: bool = False,
) -> int:
    initialize_audit_db()
    event_trace_id = trace_id or str(uuid.uuid4())

    with _get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO audit_logs (
                timestamp, agent_id, action, resource,
                decision, reason, trace_id, attack_id,
                approval_id, tool_invoked, tool_succeeded
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                agent_id,
                action,
                resource,
                decision,
                reason,
                event_trace_id,
                attack_id,
                approval_id,
                int(tool_invoked),
                int(tool_succeeded),
            ),
        )
        return int(cursor.lastrowid)


def get_audit_logs(
    limit: int = 100,
    trace_id: str | None = None,
    decision: str | None = None,
    agent_id: str | None = None,
    attack_id: str | None = None,
) -> list[dict]:
    initialize_audit_db()
    limit = max(1, min(limit, 500))

    conditions = []
    parameters = []

    for column, value in (
        ("trace_id", trace_id),
        ("decision", decision),
        ("agent_id", agent_id),
        ("attack_id", attack_id),
    ):
        if value:
            conditions.append(f"{column} = ?")
            parameters.append(value)

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    query = f"""
        SELECT * FROM audit_logs
        {where_clause}
        ORDER BY id DESC
        LIMIT ?
    """
    parameters.append(limit)

    with _get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    events = []
    for row in rows:
        event = dict(row)
        event["tool_invoked"] = bool(event["tool_invoked"])
        event["tool_succeeded"] = bool(event["tool_succeeded"])
        events.append(event)

    return events


def get_audit_trace(trace_id: str) -> list[dict]:
    return list(reversed(
        get_audit_logs(limit=500, trace_id=trace_id)
    ))


def get_attack_trace(attack_id: str) -> list[dict]:
    """Retrieve all actions correlated with one security incident."""
    return list(reversed(
        get_audit_logs(limit=500, attack_id=attack_id)
    ))
