"""config.py computes its constants at import time, so these tests reload the
module after changing env vars to re-trigger that computation."""
import importlib

import dotenv


def _reload_config(monkeypatch, **env):
    # Isolate this from whatever the real .env happens to set (e.g. a
    # developer may have CHECKPOINTER="sqlite" there) so these tests exercise
    # config.py's own default logic, not the contents of a gitignored file.
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("CHECKPOINTER", raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import config

    importlib.reload(config)
    return config


def test_checkpointer_defaults_to_sqlite_locally(monkeypatch):
    config = _reload_config(monkeypatch)
    assert config.CHECKPOINTER == "sqlite"


def test_checkpointer_defaults_to_memory_on_render(monkeypatch):
    config = _reload_config(monkeypatch, RENDER="true")
    assert config.CHECKPOINTER == "memory"


def test_checkpointer_explicit_value_overrides_the_render_default(monkeypatch):
    config = _reload_config(monkeypatch, RENDER="true", CHECKPOINTER="sqlite")
    assert config.CHECKPOINTER == "sqlite"
