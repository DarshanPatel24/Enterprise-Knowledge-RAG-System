"""Tests for EKRE settings loading and latency budget helpers."""

from __future__ import annotations

from config.settings import EkreSettings


def test_defaults_are_local_first() -> None:
    settings = EkreSettings(_env_file=None)
    assert settings.app_name == "ekre"
    assert settings.environment == "local"
    assert settings.qdrant.host == "localhost"
    assert settings.qdrant.port == 6333
    assert settings.retrieval.default_collection == "enterprise_documents"
    assert settings.retrieval.search_type == "similarity"
    assert settings.retrieval.default_top_k == 5
    assert settings.embedding.provider == "huggingface"
    assert settings.security.require_security_context is True


def test_latency_budgets_expose_all_stages() -> None:
    budgets = EkreSettings(_env_file=None).retrieval.latency_budgets()
    assert set(budgets) == {
        "query_understanding",
        "vector",
        "ranking",
        "assembly",
        "total",
    }
    assert budgets["total"] == 500.0


def test_env_override_is_applied(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("EKRE_RETRIEVAL__DEFAULT_TOP_K", "12")
    monkeypatch.setenv("EKRE_QDRANT__PORT", "7000")
    settings = EkreSettings(_env_file=None)
    assert settings.retrieval.default_top_k == 12
    assert settings.qdrant.port == 7000
