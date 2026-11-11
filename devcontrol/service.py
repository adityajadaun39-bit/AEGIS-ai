"""Business rules for DevControl."""

import sqlite3
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable

from devcontrol import config, repository
from devcontrol.models import (
    TASK_PRIORITIES,
    TASK_STATUSES,
    TEST_STATUSES,
    ToolResponse,
)


def _safe(fn: Callable[..., ToolResponse]) -> Callable[..., ToolResponse]:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> ToolResponse:
        try:
            return fn(*args, **kwargs)
        except sqlite3.Error:
            return ToolResponse.failure(
                "DATABASE_ERROR",
                "A database error occurred",
            )

    return wrapper


def _parse_since(value: str | None) -> tuple[str | None, ToolResponse | None]:
    if value is None:
        return None, None

    text = value.strip()
    if not text:
        return None, ToolResponse.failure(
            "INVALID_SINCE",
            "since cannot be empty",
        )

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None, ToolResponse.failure(
            "INVALID_SINCE",
            "since must be an ISO 8601 timestamp",
        )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc).isoformat(), None


@_safe
def create_task(
    project_id: str,
    title: str,
    description: str,
    priority: str,
    created_by: str,
) -> ToolResponse:
    project_id = project_id.strip()
    title = title.strip()
    description = description.strip()
    created_by = created_by.strip()

    if not project_id or not title or not created_by:
        return ToolResponse.failure(
            "INVALID_ARGUMENT",
            "project_id, title, and created_by are required",
        )

    if priority not in TASK_PRIORITIES:
        return ToolResponse.failure(
            "INVALID_PRIORITY",
            "priority must be low, medium, high, or urgent",
        )

    if not repository.project_exists(project_id):
        return ToolResponse.failure(
            "UNKNOWN_PROJECT",
            "Project does not exist",
        )

    task = repository.create_task(
        project_id,
        title,
        description,
        priority,
        created_by,
    )

    return ToolResponse.success(task)


@_safe
def update_task(
    task_id: str,
    actor: str,
    status: str | None,
    assignee: str | None,
) -> ToolResponse:
    task_id = task_id.strip()
    actor = actor.strip()

    if not task_id or not actor:
        return ToolResponse.failure(
            "INVALID_ARGUMENT",
            "task_id and actor are required",
        )

    if status is not None and status not in TASK_STATUSES:
        return ToolResponse.failure(
            "INVALID_STATUS",
            "Unknown task status",
        )

    if assignee is not None:
        assignee = assignee.strip()
        if not assignee:
            return ToolResponse.failure(
                "INVALID_ARGUMENT",
                "assignee cannot be empty",
            )

    if status is None and assignee is None:
        return ToolResponse.failure(
            "INVALID_ARGUMENT",
            "Provide status, assignee, or both",
        )

    if not repository.task_exists(task_id):
        return ToolResponse.failure(
            "UNKNOWN_TASK",
            "Task does not exist",
        )

    task = repository.update_task(task_id, actor, status, assignee)

    if task is None:
        return ToolResponse.failure(
            "UNKNOWN_TASK",
            "Task does not exist",
        )

    return ToolResponse.success(task)


@_safe
def list_tasks(
    project_id: str,
    status: str | None,
    limit: int,
) -> ToolResponse:
    project_id = project_id.strip()

    if not project_id:
        return ToolResponse.failure(
            "INVALID_ARGUMENT",
            "project_id is required",
        )

    if limit < 1 or limit > config.MAX_LIMIT:
        return ToolResponse.failure(
            "INVALID_LIMIT",
            f"limit must be between 1 and {config.MAX_LIMIT}",
        )

    if status is not None and status not in TASK_STATUSES:
        return ToolResponse.failure(
            "INVALID_STATUS",
            "Unknown task status",
        )

    if not repository.project_exists(project_id):
        return ToolResponse.failure(
            "UNKNOWN_PROJECT",
            "Project does not exist",
        )

    tasks = repository.list_tasks(project_id, status, limit)

    return ToolResponse.success(
        {
            "tasks": tasks,
            "count": len(tasks),
        }
    )


@_safe
def log_activity(
    project_id: str,
    actor: str,
    activity_type: str,
    summary: str,
) -> ToolResponse:
    project_id = project_id.strip()
    actor = actor.strip()
    activity_type = activity_type.strip()
    summary = summary.strip()

    if not project_id or not actor or not activity_type or not summary:
        return ToolResponse.failure(
            "INVALID_ARGUMENT",
            "project_id, actor, activity_type, and summary are required",
        )

    if not repository.project_exists(project_id):
        return ToolResponse.failure(
            "UNKNOWN_PROJECT",
            "Project does not exist",
        )

    activity = repository.log_activity(
        project_id,
        actor,
        activity_type,
        summary,
    )

    return ToolResponse.success(activity)


@_safe
def list_activity(
    project_id: str,
    since: str | None,
    limit: int,
) -> ToolResponse:
    project_id = project_id.strip()

    if not project_id:
        return ToolResponse.failure(
            "INVALID_ARGUMENT",
            "project_id is required",
        )

    if limit < 1 or limit > config.MAX_LIMIT:
        return ToolResponse.failure(
            "INVALID_LIMIT",
            f"limit must be between 1 and {config.MAX_LIMIT}",
        )

    since_value, error = _parse_since(since)
    if error is not None:
        return error

    if not repository.project_exists(project_id):
        return ToolResponse.failure(
            "UNKNOWN_PROJECT",
            "Project does not exist",
        )

    activity = repository.list_activity(project_id, since_value, limit)

    return ToolResponse.success(
        {
            "activity": activity,
            "count": len(activity),
        }
    )


@_safe
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
) -> ToolResponse:
    project_id = project_id.strip()
    actor = actor.strip()
    suite = suite.strip()

    if not project_id or not actor or not suite:
        return ToolResponse.failure(
            "INVALID_ARGUMENT",
            "project_id, actor, and suite are required",
        )

    if status not in TEST_STATUSES:
        return ToolResponse.failure(
            "INVALID_STATUS",
            "Unknown test status",
        )

    if min(total, passed, failed, skipped) < 0:
        return ToolResponse.failure(
            "INVALID_TEST_COUNTS",
            "Test counts cannot be negative",
        )

    if passed + failed + skipped > total:
        return ToolResponse.failure(
            "INVALID_TEST_COUNTS",
            "passed + failed + skipped cannot exceed total",
        )

    if task_id is not None:
        task_id = task_id.strip()
        if not task_id:
            return ToolResponse.failure(
                "INVALID_ARGUMENT",
                "task_id cannot be empty",
            )

    if not repository.project_exists(project_id):
        return ToolResponse.failure(
            "UNKNOWN_PROJECT",
            "Project does not exist",
        )

    if task_id is not None and not repository.task_exists(task_id, project_id):
        return ToolResponse.failure(
            "UNKNOWN_TASK",
            "Task does not exist in this project",
        )

    result = repository.record_test_result(
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
    )

    return ToolResponse.success(result)


@_safe
def get_project_status(project_id: str) -> ToolResponse:
    project_id = project_id.strip()

    if not project_id:
        return ToolResponse.failure(
            "INVALID_ARGUMENT",
            "project_id is required",
        )

    status = repository.get_project_status(project_id)

    if status is None:
        return ToolResponse.failure(
            "UNKNOWN_PROJECT",
            "Project does not exist",
        )

    return ToolResponse.success(status)
