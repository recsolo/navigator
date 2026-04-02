from __future__ import annotations

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("NAVAGATOR_DATABASE_PATH", str(tmp_path / "test_navagator.db"))
    monkeypatch.setenv("NAVAGATOR_APP_DATA_DIR", str(tmp_path / "appdata"))
    monkeypatch.setenv("NAVAGATOR_SECRET_BACKEND", "file")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    import app.config as config_module

    config_module.get_settings.cache_clear()
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
    config_module.get_settings.cache_clear()
