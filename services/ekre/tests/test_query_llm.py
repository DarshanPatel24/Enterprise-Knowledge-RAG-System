"""Tests for the optional LLM query interpreter (offline-safe)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from config.settings import QueryIntelligenceSettings
from domain.integrations import LangChainResourceError, build_chat_model
from domain.query import QueryLlmInterpreter, QueryPolicy
from domain.query.llm import LlmUnavailableError
from domain.query.llm import build_chat_model as build_interpreter_chat_model


def _policy(**overrides: object) -> QueryPolicy:
    settings = QueryIntelligenceSettings(_env_file=None, **overrides)  # type: ignore[arg-type]
    return QueryPolicy.from_settings(settings)


def _config(**overrides: object) -> SimpleNamespace:
    base: dict[str, object] = {
        "enable_llm_interpreter": True,
        "llm_provider": "ollama",
        "llm_model": "test-model",
        "llm_base_url": "http://127.0.0.1:1",
        "llm_temperature": 0.0,
        "llm_request_timeout_seconds": 60.0,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_disabled_interpreter_returns_none() -> None:
    interpreter = QueryLlmInterpreter(_policy(enable_llm_interpreter=False))
    assert interpreter.enabled is False
    assert interpreter.interpret("compare a and b") is None


def test_shared_factory_rejects_unsupported_provider() -> None:
    with pytest.raises(LangChainResourceError):
        build_chat_model("openai", "some-model")


def test_interpreter_factory_maps_unsupported_provider_error() -> None:
    with pytest.raises(LlmUnavailableError):
        build_interpreter_chat_model(_config(llm_provider="openai"))


def test_enabled_interpreter_degrades_when_model_unavailable() -> None:
    # Enabled but pointing at an unreachable model -> graceful None (no raise).
    interpreter = QueryLlmInterpreter(
        _policy(
            enable_llm_interpreter=True,
            llm_provider="ollama",
            llm_model="test-model",
            llm_base_url="http://127.0.0.1:1",
        )
    )
    assert interpreter.enabled is True
    assert interpreter.interpret("compare a and b") is None
