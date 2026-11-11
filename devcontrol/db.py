"""SQLite setup for DevControl."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from devcontrol import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    root_path TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('todo','in_progress','blocked','review','done','cancelled')),
    priority TEXT NOT NULL CHECK (priority IN ('low','medium','high','urgent')),
    assignee TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_events (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    actor TEXT NOT NULL,
    event_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    actor TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL,
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('proposed','accepted','rejected','superseded')),
    decided_by TEXT NOT NULL,
    supersedes_id TEXT REFERENCES decisions(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS file_changes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    task_id TEXT REFERENCES tasks(id),
    actor TEXT NOT NULL,
    path TEXT NOT NULL,
    change_type TEXT NOT NULL CHECK (change_type IN ('added','modified','deleted','renamed')),
    summary TEXT NOT NULL,
    diff TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS test_results (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    task_id TEXT REFERENCES tasks(id),
    actor TEXT NOT NULL,
    suite TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('passed','failed','error','skipped')),
    total INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    failed INTEGER NOT NULL,
    skipped INTEGER NOT NULL,
    duration_ms INTEGER,
    command TEXT,
    output TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS devcontrol_audit (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    summary TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_task_events_task_created ON task_events(task_id, created_at);
CREATE INDEX IF NOT EXISTS idx_activity_project_created ON activity(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_decisions_project_created ON decisions(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_file_changes_project_created ON file_changes(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_test_results_project_created ON test_results(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_devcontrol_audit_created ON devcontrol_audit(created_at);
"""


@contextmanager
def connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open one configured SQLite connection for a single operation."""

    path = db_path or config.get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")

    try:
        yield connection
    finally:
        connection.close()


def init_db(db_path: Path | None = None) -> None:
    """Create the schema and seed the AEGIS project if needed."""

    with connect(db_path) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            """
            INSERT OR IGNORE INTO projects (id, name, root_path, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                config.PROJECT_ID,
                config.PROJECT_NAME,
                config.PROJECT_ROOT,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        connection.commit()
