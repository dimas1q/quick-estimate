from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import app.main as main_module


def _patch_failed_checks(monkeypatch):
    monkeypatch.setattr(main_module, "_is_test_env", lambda: False)
    monkeypatch.setattr(main_module, "_check_configuration_loaded", lambda: True)
    monkeypatch.setattr(main_module, "_check_api_initialized", lambda: True)
    monkeypatch.setattr(main_module, "_check_export_subsystem", lambda: False)
    monkeypatch.setattr(
        main_module,
        "_check_database_connection",
        AsyncMock(return_value=False),
    )


def test_startup_in_strict_mode_raises_on_failed_checks(monkeypatch):
    _patch_failed_checks(monkeypatch)
    monkeypatch.setattr(main_module.settings, "STARTUP_STRICT_CHECKS", True)

    with pytest.raises(RuntimeError, match="Startup checks failed"):
        with TestClient(main_module.app):
            pass


def test_startup_in_non_strict_mode_allows_app_boot(monkeypatch):
    _patch_failed_checks(monkeypatch)
    monkeypatch.setattr(main_module.settings, "STARTUP_STRICT_CHECKS", False)

    with TestClient(main_module.app) as client:
        response = client.get("/api/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_returns_degraded_when_non_strict_and_checks_fail(monkeypatch):
    _patch_failed_checks(monkeypatch)
    monkeypatch.setattr(main_module.settings, "STARTUP_STRICT_CHECKS", False)

    with TestClient(main_module.app) as client:
        response = client.get("/api/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["strict"] is False
    assert payload["checks"]["exports"] is False
    assert payload["checks"]["database"] is False
