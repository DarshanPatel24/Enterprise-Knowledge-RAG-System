"""Tests for EKCP settings (defaults and environment overrides)."""

from __future__ import annotations

from config.settings import EkcpSettings


def test_defaults_are_local_first() -> None:
    settings = EkcpSettings(_env_file=None)
    assert settings.app_name == "ekcp"
    assert settings.environment == "local"
    assert settings.gateway.port == 8003
    assert settings.security.require_security_context is True
    assert settings.redis.enabled is False
    assert settings.control_plane.driver == "inmemory"
    assert settings.observability.langfuse_enabled is False


def test_env_override(monkeypatch) -> None:
    monkeypatch.setenv("EKCP_GATEWAY__PORT", "9100")
    monkeypatch.setenv("EKCP_SECURITY__REQUIRE_SECURITY_CONTEXT", "false")
    monkeypatch.setenv("EKCP_CONTROL_PLANE__DRIVER", "mssql")
    settings = EkcpSettings()
    assert settings.gateway.port == 9100
    assert settings.security.require_security_context is False
    assert settings.control_plane.driver == "mssql"
