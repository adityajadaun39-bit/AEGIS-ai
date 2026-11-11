import pytest

from devcontrol import db


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "devcontrol.db"
    monkeypatch.setenv("DEV_CONTROL_DB_PATH", str(path))
    db.init_db()
    return path
