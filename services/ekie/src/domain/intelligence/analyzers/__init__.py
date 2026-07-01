"""Analyzer plugins for the Document Intelligence Framework."""

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
from domain.intelligence.analyzers.quality import QualityAnalyzer
from domain.intelligence.analyzers.sensitive import SensitiveContentAnalyzer
from domain.intelligence.analyzers.structure import StructureAnalyzer


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


__all__ = [
    "Analyzer",
    "ClassificationAnalyzer",
    "CodeAnalyzer",
    "FigureAnalyzer",
    "IntelligenceReportBuilder",
    "LanguageAnalyzer",
    "QualityAnalyzer",
    "SensitiveContentAnalyzer",
    "StructureAnalyzer",
    "TableAnalyzer",
    "default_analyzers",
]
