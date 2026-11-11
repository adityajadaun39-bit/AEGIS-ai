"""MCP server for the AEGIS Development Control Center."""

from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field

from devcontrol import config, service
from devcontrol.models import TaskPriority, TaskStatus, TestStatus, ToolResponse

mcp = MCPServer(
    "AEGIS DevControl",
    instructions=(
        "Use these tools to record and inspect AEGIS development coordination state. "
        "Create tasks before starting work, update their status, log activity, and "
        "record test results. Data is stored in data/devcontrol.db. These tools must "
        "never be used for the AEGIS security gateway."
    ),
)


@mcp.tool(structured_output=True)
def create_task(
    project_id: Annotated[str, Field(min_length=1, max_length=config.MAX_PROJECT_ID)],
    title: Annotated[str, Field(min_length=1, max_length=config.MAX_TITLE)],
    description: Annotated[str, Field(max_length=config.MAX_DESCRIPTION)],
    priority: TaskPriority,
    created_by: Annotated[str, Field(min_length=1, max_length=config.MAX_ACTOR)],
) -> ToolResponse:
    """Create a task and record its creation event."""

    return service.create_task(project_id, title, description, priority, created_by)


@mcp.tool(structured_output=True)
def update_task(
    task_id: Annotated[str, Field(min_length=1, max_length=64)],
    actor: Annotated[str, Field(min_length=1, max_length=config.MAX_ACTOR)],
    status: TaskStatus | None = None,
    assignee: Annotated[
        str | None,
        Field(min_length=1, max_length=config.MAX_ASSIGNEE),
    ] = None,
) -> ToolResponse:
    """Update a task status or assignee and record the change."""

    return service.update_task(task_id, actor, status, assignee)


@mcp.tool(structured_output=True)
def list_tasks(
    project_id: Annotated[str, Field(min_length=1, max_length=config.MAX_PROJECT_ID)],
    status: TaskStatus | None = None,
    limit: Annotated[int, Field(ge=1, le=config.MAX_LIMIT)] = config.DEFAULT_LIMIT,
) -> ToolResponse:
    """Return matching tasks for a project."""

    return service.list_tasks(project_id, status, limit)


@mcp.tool(structured_output=True)
def log_activity(
    project_id: Annotated[str, Field(min_length=1, max_length=config.MAX_PROJECT_ID)],
    actor: Annotated[str, Field(min_length=1, max_length=config.MAX_ACTOR)],
    activity_type: Annotated[
        str,
        Field(min_length=1, max_length=config.MAX_ACTIVITY_TYPE),
    ],
    summary: Annotated[str, Field(min_length=1, max_length=config.MAX_SUMMARY)],
) -> ToolResponse:
    """Record development activity."""

    return service.log_activity(project_id, actor, activity_type, summary)


@mcp.tool(structured_output=True)
def list_activity(
    project_id: Annotated[str, Field(min_length=1, max_length=config.MAX_PROJECT_ID)],
    since: Annotated[str | None, Field(max_length=64)] = None,
    limit: Annotated[int, Field(ge=1, le=config.MAX_LIMIT)] = config.DEFAULT_LIMIT,
) -> ToolResponse:
    """Return recent development activity."""

    return service.list_activity(project_id, since, limit)


@mcp.tool(structured_output=True)
def record_test_result(
    project_id: Annotated[str, Field(min_length=1, max_length=config.MAX_PROJECT_ID)],
    actor: Annotated[str, Field(min_length=1, max_length=config.MAX_ACTOR)],
    suite: Annotated[str, Field(min_length=1, max_length=config.MAX_SUITE)],
    status: TestStatus,
    total: Annotated[int, Field(ge=0, le=config.MAX_COUNT)],
    passed: Annotated[int, Field(ge=0, le=config.MAX_COUNT)],
    failed: Annotated[int, Field(ge=0, le=config.MAX_COUNT)],
    skipped: Annotated[int, Field(ge=0, le=config.MAX_COUNT)],
    task_id: Annotated[str | None, Field(min_length=1, max_length=64)] = None,
    duration_ms: Annotated[
        int | None,
        Field(ge=0, le=config.MAX_DURATION_MS),
    ] = None,
) -> ToolResponse:
    """Record a test result after validating the counts."""

    return service.record_test_result(
        project_id=project_id,
        task_id=task_id,
        actor=actor,
        suite=suite,
        status=status,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        duration_ms=duration_ms,
    )


@mcp.tool(structured_output=True)
def get_project_status(
    project_id: Annotated[str, Field(min_length=1, max_length=config.MAX_PROJECT_ID)],
) -> ToolResponse:
    """Return the current project summary."""

    return service.get_project_status(project_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
