"""Analyzer plugins for the Document Intelligence Framework."""

from typing import Protocol

from domain.intelligence.analyzers.base import Analyzer, IntelligenceReportBuilder
from domain.intelligence.analyzers.content import (
    CodeAnalyzer,
    FigureAnalyzer,
    TableAnalyzer,
)
from domain.intelligence.analyzers.language import (
    ClassificationAnalyzer,
    LanguageAnalyzer,
)
from domain.intelligence.analyzers.llm import LlmAnalyzer
from domain.intelligence.analyzers.quality import QualityAnalyzer
from domain.intelligence.analyzers.sensitive import SensitiveContentAnalyzer
from domain.intelligence.analyzers.structure import StructureAnalyzer


class AnalyzerSettingsLike(Protocol):
    """Structural type for the settings that gate optional analyzers."""

    enable_llm_analysis: bool


def default_analyzers() -> list[Analyzer]:
    """Return the default analyzer pipeline in deterministic execution order.

    Structure runs first to populate sections; detection analyzers follow;
    quality runs last so it can inspect prior findings.
    """
    return [
        StructureAnalyzer(),
        TableAnalyzer(),
        FigureAnalyzer(),
        CodeAnalyzer(),
        LanguageAnalyzer(),
        ClassificationAnalyzer(),
        SensitiveContentAnalyzer(),
        QualityAnalyzer(),
    ]


def analyzers_from_settings(settings: AnalyzerSettingsLike) -> list[Analyzer]:
    """Build the analyzer pipeline from configuration.

    The deterministic pipeline is always used so the offline path stays
    reproducible. The optional :class:`LlmAnalyzer` is appended only when LLM
    analysis is enabled, keeping the default path free of the LangChain
    dependency.
    """
    analyzers = default_analyzers()
    if settings.enable_llm_analysis:
        analyzers.append(LlmAnalyzer())
    return analyzers


__all__ = [
    "Analyzer",
    "AnalyzerSettingsLike",
    "ClassificationAnalyzer",
    "CodeAnalyzer",
    "FigureAnalyzer",
    "IntelligenceReportBuilder",
    "LanguageAnalyzer",
    "LlmAnalyzer",
    "QualityAnalyzer",
    "SensitiveContentAnalyzer",
    "StructureAnalyzer",
    "TableAnalyzer",
    "analyzers_from_settings",
    "default_analyzers",
]
