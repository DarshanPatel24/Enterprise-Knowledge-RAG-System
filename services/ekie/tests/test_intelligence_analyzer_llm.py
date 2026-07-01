"""Unit tests for the optional LLM analyzer and chat-model factory (EKIE-S3-5)."""

import importlib.util
from dataclasses import dataclass

import pytest

from domain.intelligence import (
    IntelligencePolicy,
    LlmAnalyzer,
    LlmUnavailableError,
    analyzers_from_settings,
    build_analyzed_document,
    build_chat_model,
    default_analyzers,
    parse_markdown,
)
from domain.intelligence.analyzers.base import IntelligenceReportBuilder

_LANGCHAIN_INSTALLED = importlib.util.find_spec("langchain_ollama") is not None

_MARKDOWN = "# Pump Maintenance\n\nThis guide describes routine pump maintenance."


@dataclass
class _AnalyzerSettings:
    enable_llm_analysis: bool


@dataclass
class _IntelligenceSettings:
    detect_language: bool = True
    classify_content: bool = True
    detect_sensitive_content: bool = True
    default_language: str = "en"
    high_complexity_section_threshold: int = 12
    enable_llm_analysis: bool = True
    llm_provider: str = "ollama"
    llm_model: str = "llama3.1"
    llm_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.0
    llm_request_timeout_seconds: float = 60.0


def _document() -> object:
    return build_analyzed_document(parse_markdown(_MARKDOWN))


def test_llm_analyzer_name() -> None:
    assert LlmAnalyzer().name == "llm"


def test_llm_analyzer_is_noop_when_disabled() -> None:
    builder = IntelligenceReportBuilder()
    builder.primary_topic = "heuristic-topic"
    LlmAnalyzer().analyze(_document(), builder, IntelligencePolicy())
    assert builder.primary_topic == "heuristic-topic"


def test_default_analyzers_excludes_llm() -> None:
    names = {analyzer.name for analyzer in default_analyzers()}
    assert "llm" not in names


def test_analyzers_from_settings_excludes_llm_when_disabled() -> None:
    analyzers = analyzers_from_settings(_AnalyzerSettings(enable_llm_analysis=False))
    assert all(analyzer.name != "llm" for analyzer in analyzers)


def test_analyzers_from_settings_appends_llm_when_enabled() -> None:
    analyzers = analyzers_from_settings(_AnalyzerSettings(enable_llm_analysis=True))
    assert isinstance(analyzers[-1], LlmAnalyzer)


def test_policy_from_settings_maps_llm_fields() -> None:
    policy = IntelligencePolicy.from_settings(_IntelligenceSettings())
    assert policy.enable_llm_analysis is True
    assert policy.llm_provider == "ollama"
    assert policy.llm_model == "llama3.1"
    assert policy.llm_base_url == "http://localhost:11434"
    assert policy.llm_request_timeout_seconds == 60.0


def test_build_chat_model_rejects_unknown_provider() -> None:
    policy = IntelligencePolicy(enable_llm_analysis=True, llm_provider="openai")
    with pytest.raises(LlmUnavailableError):
        build_chat_model(policy)


@pytest.mark.skipif(
    _LANGCHAIN_INSTALLED, reason="langchain-ollama is installed; missing-path not testable"
)
def test_build_chat_model_raises_when_langchain_missing() -> None:
    policy = IntelligencePolicy(enable_llm_analysis=True)
    with pytest.raises(LlmUnavailableError):
        build_chat_model(policy)


@pytest.mark.skipif(
    _LANGCHAIN_INSTALLED, reason="langchain-ollama is installed; degradation not testable"
)
def test_llm_analyzer_degrades_when_langchain_missing() -> None:
    builder = IntelligenceReportBuilder()
    builder.primary_topic = "heuristic-topic"
    policy = IntelligencePolicy(enable_llm_analysis=True)
    LlmAnalyzer().analyze(_document(), builder, policy)
    assert builder.primary_topic == "heuristic-topic"
