from devcontrol import config


def test_default_db_path_is_separate(monkeypatch):
    monkeypatch.delenv("DEV_CONTROL_DB_PATH", raising=False)

    path = config.get_db_path()

    assert path.name == "devcontrol.db"
    assert "aegis.db" not in str(path).lower()


def test_db_path_env_override(tmp_path, monkeypatch):
    target = tmp_path / "custom.db"
    monkeypatch.setenv("DEV_CONTROL_DB_PATH", str(target))

    assert config.get_db_path() == target.resolve()


def test_limits_are_bounded():
    assert config.MAX_LIMIT == 50
    assert 1 <= config.DEFAULT_LIMIT <= config.MAX_LIMIT
