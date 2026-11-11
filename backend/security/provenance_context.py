
"""Persistent, server-controlled provenance context and attack correlation."""

import json
import sqlite3
import uuid

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from backend.schemas.provenance import Provenance
from backend.tools.simulated_tools import DOCUMENTS


CONTEXT_TTL_MINUTES = 30

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "aegis.db"


@contextmanager
def _get_connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row

    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_context_db() -> None:
    """Create the persistent provenance context table."""

    with _get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS provenance_contexts (
                context_id TEXT PRIMARY KEY,
                resource TEXT NOT NULL,
                records_json TEXT NOT NULL,
                attack_id TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_context_expiry
            ON provenance_contexts(expires_at)
            """
        )


def register_document_context(
    resource: str,
    provenance_data: dict,
) -> str:
    """
    Verify document provenance and persist a server-generated context.

    The client cannot supply or choose the attack ID.
    """

    initialize_context_db()

    document = DOCUMENTS.get(resource)
    if document is None:
        raise ValueError("Unknown document")

    supplied = Provenance.model_validate(provenance_data)
    expected = document["provenance"]

    if supplied.model_dump(mode="json") != expected.model_dump(mode="json"):
        raise ValueError("Document provenance verification failed")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=CONTEXT_TTL_MINUTES)

    context_id = str(uuid.uuid4())

    attack_id = (
        str(uuid.uuid4())
        if expected.contains_untrusted_instructions
        else None
    )

    records_json = json.dumps(
        [expected.model_dump(mode="json")],
        separators=(",", ":"),
    )

    with _get_connection() as connection:
        connection.execute(
            """
            INSERT INTO provenance_contexts (
                context_id,
                resource,
                records_json,
                attack_id,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                context_id,
                resource,
                records_json,
                attack_id,
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )

    return context_id


def resolve_context_details(
    context_id: str | None,
) -> dict | None:
    """
    Resolve provenance and attack correlation from persistent storage.

    Invalid and expired context IDs fail closed.
    """

    if not context_id:
        return None

    initialize_context_db()

    with _get_connection() as connection:
        row = connection.execute(
            """
            SELECT resource, records_json, attack_id, expires_at
            FROM provenance_contexts
            WHERE context_id = ?
            """,
            (context_id,),
        ).fetchone()

        if row is None:
            return None

        expires_at = datetime.fromisoformat(row["expires_at"])

        if datetime.now(timezone.utc) >= expires_at:
            connection.execute(
                """
                DELETE FROM provenance_contexts
                WHERE context_id = ?
                """,
                (context_id,),
            )
            return None

        try:
            raw_records = json.loads(row["records_json"])
            records = [
                Provenance.model_validate(item)
                for item in raw_records
            ]
        except (ValueError, TypeError, KeyError):
            return None

        return {
            "records": records,
            "attack_id": row["attack_id"],
            "resource": row["resource"],
        }


def resolve_provenance_context(
    context_id: str | None,
) -> list[Provenance] | None:
    """Backward-compatible provenance-only resolver."""

    details = resolve_context_details(context_id)

    if details is None:
        return None

    return details["records"]


def clear_provenance_contexts() -> None:
    """Clear contexts for isolated tests."""

    initialize_context_db()

    with _get_connection() as connection:
        connection.execute("DELETE FROM provenance_contexts")


def cleanup_expired_contexts() -> int:
    """Delete expired contexts and return the number removed."""

    initialize_context_db()

    now = datetime.now(timezone.utc).isoformat()

    with _get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM provenance_contexts
            WHERE expires_at <= ?
            """,
            (now,),
        )

        return cursor.rowcount
