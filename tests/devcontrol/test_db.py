from devcontrol import config, db

EXPECTED_TABLES = {
    "projects",
    "tasks",
    "task_events",
    "activity",
    "decisions",
    "file_changes",
    "test_results",
    "devcontrol_audit",
}


def test_init_creates_expected_tables(db_path):
    with db.connect() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert EXPECTED_TABLES <= tables


def test_pragmas_are_configured(db_path):
    with db.connect() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000


def test_project_is_seeded(db_path):
    with db.connect() as connection:
        row = connection.execute(
            "SELECT id, name, root_path FROM projects WHERE id = ?",
            (config.PROJECT_ID,),
        ).fetchone()

    assert row is not None
    assert row["id"] == "AEGIS"
    assert row["name"] == "AEGIS"
    assert row["root_path"] == config.PROJECT_ROOT


def test_historical_tables_do_not_cascade(db_path):
    with db.connect() as connection:
        schema = "\n".join(
            row[0]
            for row in connection.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
            )
        )

    assert "ON DELETE CASCADE" not in schema.upper()


def test_indexes_are_created(db_path):
    with db.connect() as connection:
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }

    assert "idx_tasks_project_status" in indexes
    assert "idx_tasks_assignee" in indexes
    assert "idx_tasks_created_at" in indexes
