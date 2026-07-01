"""Mutable report builder and analyzer plugin interface (handbook ADR-015)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

from domain.intelligence.analysis import AnalyzedDocument
from domain.intelligence.models import (
    CodeBlockInfo,
    DocumentCategory,
    DocumentComplexity,
    FigureInfo,
    QualityScore,
    SectionIntelligence,
    SemanticMetadata,
    SensitiveFinding,
    TableInfo,
)
from domain.intelligence.policy import IntelligencePolicy


@dataclass
class IntelligenceReportBuilder:
    """Accumulates analyzer contributions before the report is finalized."""

    language: str = "en"
    classification: DocumentCategory = DocumentCategory.GENERAL
    tables: list[TableInfo] = field(default_factory=list)
    figures: list[FigureInfo] = field(default_factory=list)
    code_blocks: list[CodeBlockInfo] = field(default_factory=list)
    sections: list[SectionIntelligence] = field(default_factory=list)
    sensitive_findings: list[SensitiveFinding] = field(default_factory=list)
    quality: QualityScore | None = None
    primary_topic: str | None = None
    complexity: DocumentComplexity = DocumentComplexity.LOW
    knowledge_density: float = 0.0
    token_count: int = 0

    def semantic_metadata(self, section_count: int) -> SemanticMetadata:
        """Assemble the semantic metadata section of the report."""
        return SemanticMetadata(
            primary_topic=self.primary_topic,
            document_category=self.classification,
            language=self.language,
            complexity=self.complexity,
            knowledge_density=self.knowledge_density,
            token_count=self.token_count,
            section_count=section_count,
        )


class Analyzer(ABC):
    """A pluggable document analyzer (handbook ADR-015)."""

    name: ClassVar[str]

    @abstractmethod
    def analyze(
        self,
        document: AnalyzedDocument,
        builder: IntelligenceReportBuilder,
        policy: IntelligencePolicy,
    ) -> None:
        """Enrich ``builder`` with insights derived from ``document``."""
