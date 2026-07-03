"""Tests for environment-backed EKIE settings."""

import pytest
from pydantic import ValidationError

from config.settings import ControlPlaneSettings, EkieSettings


def test_defaults_are_local_first() -> None:
    settings = EkieSettings()
    assert settings.app_name == "ekie"
    assert settings.environment == "local"
    assert settings.qdrant.port == 6333
    assert settings.redis.port == 6379
    assert settings.observability.langfuse_enabled is False


def test_env_override_is_nested(monkeypatch: object) -> None:
    # monkeypatch typing kept loose to avoid importing pytest types here.
    import os

    os.environ["EKIE_ENVIRONMENT"] = "staging"
    os.environ["EKIE_QDRANT__PORT"] = "7000"
    try:
        settings = EkieSettings()
        assert settings.environment == "staging"
        assert settings.qdrant.port == 7000
    finally:
        del os.environ["EKIE_ENVIRONMENT"]
        del os.environ["EKIE_QDRANT__PORT"]


def test_control_plane_url_override_wins() -> None:
    cp = ControlPlaneSettings(url="sqlite+pysqlite:///:memory:")
    assert cp.sqlalchemy_url() == "sqlite+pysqlite:///:memory:"


def test_control_plane_url_built_from_components() -> None:
    cp = ControlPlaneSettings(
        host="db.local",
        port=1433,
        database="ekrag_control_plane",
        user="sa",
        password="p@ss word",
    )
    url = cp.sqlalchemy_url()
    assert url.startswith("mssql+pyodbc://sa:")
    assert "db.local:1433/ekrag_control_plane" in url
    assert "TrustServerCertificate=yes" in url
    # Password special characters must be URL-encoded.
    assert "p%40ss+word" in url


def test_rejects_unknown_embedding_provider() -> None:
    with pytest.raises(ValidationError):
        EkieSettings.model_validate(
            {
                "embedding": {
                    "provider": "openai",
                }
            }
        )


def test_rejects_invalid_intelligence_provider() -> None:
    with pytest.raises(ValidationError):
        EkieSettings.model_validate(
            {
                "intelligence": {
                    "llm_provider": "anthropic",
                }
            }
        )
