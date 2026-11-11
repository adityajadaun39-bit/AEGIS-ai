from devcontrol import db, repository, service


def test_create_task_records_event_and_audit(db_path):
    result = service.create_task(
        "AEGIS",
        "Build DevControl",
        "Implement the MCP server",
        "high",
        "opencode",
    )

    assert result.ok is True
    assert result.data is not None
    task = result.data
    assert task["status"] == "todo"
    assert task["priority"] == "high"

    detail = repository.get_task(task["id"])
    assert detail is not None
    assert len(detail["events"]) == 1
    assert detail["events"][0]["event_type"] == "created"

    with db.connect() as connection:
        audit_count = connection.execute(
            "SELECT COUNT(*) FROM devcontrol_audit"
        ).fetchone()[0]

    assert audit_count == 1


def test_create_task_rejects_unknown_project(db_path):
    result = service.create_task(
        "UNKNOWN",
        "Task",
        "Description",
        "medium",
        "opencode",
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "UNKNOWN_PROJECT"


def test_update_task_records_change(db_path):
    created = service.create_task(
        "AEGIS",
        "Task",
        "Description",
        "medium",
        "opencode",
    )
    assert created.data is not None

    updated = service.update_task(
        created.data["id"],
        "opencode",
        "in_progress",
        "opencode",
    )

    assert updated.ok is True
    assert updated.data is not None
    assert updated.data["status"] == "in_progress"
    assert updated.data["assignee"] == "opencode"

    detail = repository.get_task(created.data["id"])
    assert detail is not None
    assert len(detail["events"]) == 2
    assert detail["events"][-1]["event_type"] == "updated"


def test_update_task_requires_a_change(db_path):
    created = service.create_task(
        "AEGIS",
        "Task",
        "Description",
        "medium",
        "opencode",
    )
    assert created.data is not None

    result = service.update_task(created.data["id"], "opencode", None, None)

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "INVALID_ARGUMENT"


def test_list_tasks_filters_and_limits(db_path):
    for index in range(3):
        service.create_task(
            "AEGIS",
            f"Task {index}",
            "Description",
            "medium",
            "opencode",
        )

    result = service.list_tasks("AEGIS", "todo", 2)

    assert result.ok is True
    assert result.data is not None
    assert result.data["count"] == 2

    limited = service.list_tasks("AEGIS", None, 51)

    assert limited.ok is False
    assert limited.error is not None
    assert limited.error.code == "INVALID_LIMIT"


def test_log_and_list_activity(db_path):
    logged = service.log_activity(
        "AEGIS",
        "opencode",
        "inspection",
        "Reviewed the backend",
    )

    assert logged.ok is True

    listed = service.list_activity("AEGIS", None, 50)

    assert listed.ok is True
    assert listed.data is not None
    assert listed.data["count"] == 1
    assert listed.data["activity"][0]["activity_type"] == "inspection"


def test_record_test_result_validates_counts(db_path):
    result = service.record_test_result(
        project_id="AEGIS",
        task_id=None,
        actor="opencode",
        suite="pytest",
        status="passed",
        total=10,
        passed=9,
        failed=0,
        skipped=1,
        duration_ms=120,
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["status"] == "passed"

    invalid = service.record_test_result(
        project_id="AEGIS",
        task_id=None,
        actor="opencode",
        suite="pytest",
        status="passed",
        total=2,
        passed=2,
        failed=1,
        skipped=0,
        duration_ms=None,
    )

    assert invalid.ok is False
    assert invalid.error is not None
    assert invalid.error.code == "INVALID_TEST_COUNTS"


def test_record_test_result_rejects_unknown_task(db_path):
    result = service.record_test_result(
        project_id="AEGIS",
        task_id="missing",
        actor="opencode",
        suite="pytest",
        status="passed",
        total=1,
        passed=1,
        failed=0,
        skipped=0,
        duration_ms=None,
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "UNKNOWN_TASK"


def test_get_project_status(db_path):
    service.create_task(
        "AEGIS",
        "Task",
        "Description",
        "high",
        "opencode",
    )
    service.log_activity(
        "AEGIS",
        "opencode",
        "implementation",
        "Started DevControl",
    )
    service.record_test_result(
        project_id="AEGIS",
        task_id=None,
        actor="opencode",
        suite="pytest",
        status="passed",
        total=4,
        passed=4,
        failed=0,
        skipped=0,
        duration_ms=80,
    )

    result = service.get_project_status("AEGIS")

    assert result.ok is True
    assert result.data is not None
    assert result.data["total_tasks"] == 1
    assert result.data["tasks_by_status"]["todo"] == 1
    assert result.data["summary"]["open_tasks"] == 1
    assert len(result.data["latest_activity"]) == 1
    assert len(result.data["latest_test_results"]) == 1
    assert result.data["recent_decisions"] == []
