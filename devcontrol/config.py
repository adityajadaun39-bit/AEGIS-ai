"""Configuration for the AEGIS Development Control Center."""

import os
from pathlib import Path

PROJECT_ID = "AEGIS"
PROJECT_NAME = "AEGIS"
PROJECT_ROOT = r"C:\Projects\AEGIS"

DEFAULT_LIMIT = 20
MAX_LIMIT = 50

MAX_PROJECT_ID = 100
MAX_TITLE = 200
MAX_DESCRIPTION = 4000
MAX_ACTOR = 100
MAX_ASSIGNEE = 100
MAX_ACTIVITY_TYPE = 100
MAX_SUMMARY = 2000
MAX_SUITE = 200
MAX_COUNT = 1_000_000
MAX_DURATION_MS = 86_400_000


def get_db_path() -> Path:
    """Return the DevControl database path, honoring the environment override."""

    raw = os.getenv("DEV_CONTROL_DB_PATH")
    if raw:
        return Path(raw).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "data" / "devcontrol.db"
