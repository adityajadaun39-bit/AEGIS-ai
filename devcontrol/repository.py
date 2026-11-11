"""Parameterized SQLite operations for DevControl."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from devcontrol import config, db
from devcontrol.models import TASK_STATUSES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


def _audit(
    connection: sqlite3.Connection,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str | None,
    summary: str,
) -> None:
    connection.execute(
        """
        INSERT INTO devcontrol_audit
        (id, created_at, actor, action, entity_type, entity_id, summary, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (_new_id(), _now(), actor, action, entity_type, entity_id, summary[:2000], "{}"),
    )


def project_exists(project_id: str) -> bool:
    with db.connect() as connection:
        row = connection.execute(
            "SELECT 1 FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        return row is not None


def task_exists(task_id: str, project_id: str | None = None) -> bool:
    query = "SELECT 1 FROM tasks WHERE id = ?"
    params: list[Any] = [task_id]

    if project_id is not None:
        query += " AND project_id = ?"
        params.append(project_id)

    with db.connect() as connection:
        row = connection.execute(query, params).fetchone()
        return row is not None


def create_task(
    project_id: str,
    title: str,
    description: str,
    priority: str,
    created_by: str,
) -> dict[str, Any]:
    task_id = _new_id()
    created_at = _now()

    with db.connect() as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO tasks
                (id, project_id, title, description, status, priority, assignee,
                 created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'todo', ?, NULL, ?, ?, ?)
                """,
                (
                    task_id,
                    project_id,
                    title,
                    description,
                    priority,
                    created_by,
                    created_at,
                    created_at,
                ),
            )
            connection.execute(
                """
                INSERT INTO task_events
                (id, task_id, actor, event_type, summary, metadata_json, created_at)
                VALUES (?, ?, ?, 'created', ?, '{}', ?)
                """,
                (
                    _new_id(),
                    task_id,
                    created_by,
                    "Task created with status todo",
                    created_at,
                ),
            )
            _audit(
                connection,
                created_by,
                "create_task",
                "task",
                task_id,
                f"Created task: {title}",
            )
            row = connection.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()

    return dict(row)


def get_task(task_id: str) -> dict[str, Any] | None:
    with db.connect() as connection:
        task = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        if task is None:
            return None

        events = connection.execute(
            """
            SELECT * FROM task_events
            WHERE task_id = ?
            ORDER BY created_at ASC
            """,
            (task_id,),
        ).fetchall()

    return {"task": dict(task), "events": [dict(event) for event in events]}


def update_task(
    task_id: str,
    actor: str,
    status: str | None,
    assignee: str | None,
) -> dict[str, Any] | None:
    changes: list[str] = []
    values: list[Any] = []

    if status is not None:
        changes.append("status = ?")
        values.append(status)

    if assignee is not None:
        changes.append("assignee = ?")
        values.append(assignee)

    updated_at = _now()
    changes.append("updated_at = ?")
    values.append(updated_at)
    values.append(task_id)

    metadata = json.dumps({"status": status, "assignee": assignee})

    with db.connect() as connection:
        with connection:
            connection.execute(
                f"UPDATE tasks SET {', '.join(changes)} WHERE id = ?",
                values,
            )
            connection.execute(
                """
                INSERT INTO task_events
                (id, task_id, actor, event_type, summary, metadata_json, created_at)
                VALUES (?, ?, ?, 'updated', ?, ?, ?)
                """,
                (
                    _new_id(),
                    task_id,
                    actor,
                    "Task updated",
                    metadata,
                    updated_at,
                ),
            )
            _audit(
                connection,
                actor,
                "update_task",
                "task",
                task_id,
                f"Updated task: {metadata}",
            )
            row = connection.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()

    return dict(row) if row is not None else None


def list_tasks(
    project_id: str,
    status: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM tasks WHERE project_id = ?"
    params: list[Any] = [project_id]

    if status is not None:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY updated_at DESC, created_at DESC LIMIT ?"
    params.append(limit)

    with db.connect() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def log_activity(
    project_id: str,
    actor: str,
    activity_type: str,
    summary: str,
) -> dict[str, Any]:
    activity_id = _new_id()
    created_at = _now()

    with db.connect() as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO activity
                (id, project_id, actor, activity_type, summary, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, '{}', ?)
                """,
                (activity_id, project_id, actor, activity_type, summary, created_at),
            )
            _audit(
                connection,
                actor,
                "log_activity",
                "activity",
                activity_id,
                f"Logged {activity_type}: {summary}",
            )
            row = connection.execute(
                "SELECT * FROM activity WHERE id = ?",
                (activity_id,),
            ).fetchone()

    return dict(row)


def list_activity(
    project_id: str,
    since: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM activity WHERE project_id = ?"
    params: list[Any] = [project_id]

    if since is not None:
        query += " AND created_at >= ?"
        params.append(since)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with db.connect() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def record_test_result(
    project_id: str,
    task_id: str | None,
    actor: str,
    suite: str,
    status: str,
    total: int,
    passed: int,
    failed: int,
    skipped: int,
    duration_ms: int | None,
) -> dict[str, Any]:
    result_id = _new_id()
    created_at = _now()

    with db.connect() as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO test_results
                (id, project_id, task_id, actor, suite, status, total, passed,
                 failed, skipped, duration_ms, command, output, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                """,
                (
                    result_id,
                    project_id,
                    task_id,
                    actor,
                    suite,
                    status,
                    total,
                    passed,
                    failed,
                    skipped,
                    duration_ms,
                    created_at,
                ),
            )
            _audit(
                connection,
                actor,
                "record_test_result",
                "test_result",
                result_id,
                f"Recorded {status} test result for {suite}",
            )
            row = connection.execute(
                "SELECT * FROM test_results WHERE id = ?",
                (result_id,),
            ).fetchone()

    return dict(row)


def list_test_results(
    project_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    with db.connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM test_results
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (project_id, limit),
        ).fetchall()

    return [dict(row) for row in rows]


def list_decisions(
    project_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    with db.connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM decisions
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (project_id, limit),
        ).fetchall()

    return [dict(row) for row in rows]


def get_project_status(project_id: str) -> dict[str, Any] | None:
    with db.connect() as connection:
        project = connection.execute(
            "SELECT id, name, root_path, created_at FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()

        if project is None:
            return None

        total_row = connection.execute(
            "SELECT COUNT(*) AS total FROM tasks WHERE project_id = ?",
            (project_id,),
        ).fetchone()

        status_rows = connection.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM tasks
            WHERE project_id = ?
            GROUP BY status
            """,
            (project_id,),
        ).fetchall()

        latest_activity = connection.execute(
            """
            SELECT * FROM activity
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (project_id,),
        ).fetchall()

        latest_tests = connection.execute(
            """
            SELECT * FROM test_results
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (project_id,),
        ).fetchall()

        recent_decisions = connection.execute(
            """
            SELECT * FROM decisions
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (project_id,),
        ).fetchall()

    tasks_by_status = {status: 0 for status in TASK_STATUSES}
    for row in status_rows:
        tasks_by_status[row["status"]] = row["count"]

    activity_rows = [dict(row) for row in latest_activity]
    summary = {
        "total_tasks": total_row["total"],
        "open_tasks": sum(
            tasks_by_status[status]
            for status in ("todo", "in_progress", "blocked", "review")
        ),
        "blocked_tasks": tasks_by_status["blocked"],
        "completed_tasks": tasks_by_status["done"],
        "cancelled_tasks": tasks_by_status["cancelled"],
        "latest_activity_at": activity_rows[0]["created_at"] if activity_rows else None,
    }

    return {
        "project": dict(project),
        "total_tasks": total_row["total"],
        "tasks_by_status": tasks_by_status,
        "latest_activity": activity_rows,
        "latest_test_results": [dict(row) for row in latest_tests],
        "recent_decisions": [dict(row) for row in recent_decisions],
        "summary": summary,
    }
