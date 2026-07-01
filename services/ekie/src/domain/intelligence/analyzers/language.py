"""Language detection and content classification analyzers (handbook 8.10-8.11)."""

from __future__ import annotations

import re
from typing import ClassVar

from domain.intelligence.analysis import AnalyzedDocument
from domain.intelligence.analyzers.base import Analyzer, IntelligenceReportBuilder
from domain.intelligence.models import BlockType, DocumentCategory
from domain.intelligence.policy import IntelligencePolicy

_STOPWORDS: dict[str, frozenset[str]] = {
    "en": frozenset({"the", "and", "of", "to", "in", "is", "for"}),
    "de": frozenset({"der", "die", "und", "das", "mit", "nicht", "ist"}),
    "fr": frozenset({"le", "la", "les", "des", "et", "une", "pour"}),
    "es": frozenset({"el", "la", "los", "las", "para", "con", "una"}),
}
_WORD = re.compile(r"[a-zA-Z\u00c0-\u024f]+")

_CLASSIFICATION_RULES: tuple[tuple[DocumentCategory, re.Pattern[str]], ...] = (
    (
        DocumentCategory.API_DOCUMENTATION,
        re.compile(r"\b(api|endpoint|request|response)\b", re.I),
    ),
    (
        DocumentCategory.ARCHITECTURE,
        re.compile(r"\b(architecture|component diagram|system design)\b", re.I),
    ),
    (
        DocumentCategory.MAINTENANCE_GUIDE,
        re.compile(r"\b(maintenance|inspection|lubricat)\b", re.I),
    ),
    (
        DocumentCategory.MEETING_NOTES,
        re.compile(r"\b(agenda|attendees|minutes|action items)\b", re.I),
    ),
    (
        DocumentCategory.TRAINING_MATERIAL,
        re.compile(r"\b(training|lesson|exercise|course)\b", re.I),
    ),
    (DocumentCategory.POLICY, re.compile(r"\bpolic(y|ies)\b", re.I)),
    (
        DocumentCategory.PROCEDURE,
        re.compile(r"\b(procedure|step\s+\d+|shutdown|startup)\b", re.I),
    ),
    (
        DocumentCategory.TECHNICAL_SPECIFICATION,
        re.compile(r"\b(specification|requirements|spec)\b", re.I),
    ),
    (DocumentCategory.MANUAL, re.compile(r"\b(manual|guide|handbook)\b", re.I)),
)

_CODE_SOURCE_TYPES = frozenset(
    {"py", "java", "js", "ts", "json", "xml", "yaml", "yml", "sql", "sh"}
)


def _plain_text(document: AnalyzedDocument) -> str:
    return "\n".join(
        block.text
        for block in document.blocks
        if block.block_type is not BlockType.CODE
    )


class LanguageAnalyzer(Analyzer):
    """Detects the dominant language of a document."""

    name: ClassVar[str] = "language"

    def analyze(
        self,
        document: AnalyzedDocument,
        builder: IntelligenceReportBuilder,
        policy: IntelligencePolicy,
    ) -> None:
        """Resolve document language from front matter or a script/stopword heuristic."""
        declared = document.front_matter.get("language")
        if declared:
            builder.language = declared
            return
        if not policy.detect_language:
            builder.language = policy.default_language
            return
        builder.language = self._detect(_plain_text(document), policy.default_language)

    @staticmethod
    def _detect(text: str, default: str) -> str:
        for char in text:
            code = ord(char)
            if 0x3040 <= code <= 0x30FF:
                return "ja"
            if 0xAC00 <= code <= 0xD7A3:
                return "ko"
            if 0x4E00 <= code <= 0x9FFF:
                return "zh"
            if 0x0400 <= code <= 0x04FF:
                return "ru"
        words = [word.lower() for word in _WORD.findall(text)]
        if not words:
            return default
        best_language = default
        best_score = 0
        for language, stopwords in _STOPWORDS.items():
            score = sum(1 for word in words if word in stopwords)
            if score > best_score:
                best_score = score
                best_language = language
        return best_language


class ClassificationAnalyzer(Analyzer):
    """Classifies the document into a governance category."""

    name: ClassVar[str] = "classification"

    def analyze(
        self,
        document: AnalyzedDocument,
        builder: IntelligenceReportBuilder,
        policy: IntelligencePolicy,
    ) -> None:
        """Assign a :class:`DocumentCategory` using deterministic keyword rules."""
        if not policy.classify_content:
            builder.classification = DocumentCategory.GENERAL
            return
        source_type = document.front_matter.get("source_type", "").lower()
        if source_type in _CODE_SOURCE_TYPES:
            builder.classification = DocumentCategory.SOURCE_CODE
            return
        haystack = "\n".join(
            [document.front_matter.get("title", ""), *(b.text for b in document.blocks)]
        )
        for category, pattern in _CLASSIFICATION_RULES:
            if pattern.search(haystack):
                builder.classification = category
                return
        builder.classification = DocumentCategory.GENERAL
