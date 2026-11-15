
"""SQLite storage for AEGIS human approval requests."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from backend.schemas.approval import ApprovalRequest, ApprovalStatus


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "aegis.db"


@contextmanager
def _get_connection() -> Iterator[sqlite3.Connection]:
    """Provide a transaction-managed SQLite connection."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        with connection:
            yield connection
    finally:
        connection.close()

def initialize_approval_db() -> None:

    """Create the approval table if it does not exist."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_requests (
                approval_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )



def create_approval(request: ApprovalRequest) -> bool:
    """Store a new approval request without overwriting existing IDs."""

    initialize_approval_db()

    try:
        with _get_connection() as connection:
            connection.execute(
                """
                INSERT INTO approval_requests (
                    approval_id,
                    agent_id,
                    action,
                    resource,
                    payload_hash,
                    status,
                    created_at,
                    expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.approval_id,
                    request.agent_id,
                    request.action,
                    request.resource,
                    request.payload_hash,
                    request.status.value,
                    request.created_at.isoformat(),
                    request.expires_at.isoformat(),
                ),
            )

        return True

    except sqlite3.IntegrityError:
        return False


def get_approval(approval_id: str) -> ApprovalRequest | None:
    """Retrieve an approval request by its unique ID."""

    initialize_approval_db()

    with _get_connection() as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT * FROM approval_requests
            WHERE approval_id = ?
            """,
            (approval_id,),
        ).fetchone()

    if row is None:
        return None

    return ApprovalRequest(
        approval_id=row["approval_id"],
        agent_id=row["agent_id"],
        action=row["action"],
        resource=row["resource"],
        payload_hash=row["payload_hash"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]),
    )

def list_approvals(
    status: ApprovalStatus | None = None,
) -> list[ApprovalRequest]:
    initialize_approval_db()
    now = datetime.now(timezone.utc).isoformat()

    with _get_connection() as connection:
        connection.execute(
            """
            UPDATE approval_requests
            SET status = ?
            WHERE status = ?
            AND expires_at <= ?
            """,
            (
                ApprovalStatus.EXPIRED.value,
                ApprovalStatus.PENDING.value,
                now,
            ),
        )
    """List approval requests, optionally filtered by status."""

    initialize_approval_db()

    with _get_connection() as connection:
        if status is None:
            rows = connection.execute(
                """
                SELECT * FROM approval_requests
                ORDER BY created_at DESC
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM approval_requests
                WHERE status = ?
                ORDER BY created_at DESC
                """,
                (status.value,),
            ).fetchall()

    return [
        ApprovalRequest(
            approval_id=row["approval_id"],
            agent_id=row["agent_id"],
            action=row["action"],
            resource=row["resource"],
            payload_hash=row["payload_hash"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
        )
        for row in rows
    ]


def update_approval_status(
    approval_id: str,
    new_status: ApprovalStatus,
    expected_status: ApprovalStatus = ApprovalStatus.PENDING,
) -> bool:
    """Atomically change status only when the expected status still matches."""

    if new_status == ApprovalStatus.PENDING:
        return False

    initialize_approval_db()

    with _get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE approval_requests
            SET status = ?
            WHERE approval_id = ?
            AND status = ?
            """,
            (
                new_status.value,
                approval_id,
                expected_status.value,
            ),
        )

        return cursor.rowcount == 1
