"""Structure and semantic analyzer: sections, complexity, topic (handbook 8.6, 8.13)."""

from __future__ import annotations

import re
from typing import ClassVar

from domain.intelligence.analysis import (
    AnalyzedDocument,
    count_tokens,
    reading_time_seconds,
)
from domain.intelligence.analyzers.base import Analyzer, IntelligenceReportBuilder
from domain.intelligence.markdown_ast import MarkdownBlock
from domain.intelligence.models import (
    BlockType,
    DocumentComplexity,
    SectionIntelligence,
)
from domain.intelligence.policy import IntelligencePolicy

_WARNING = re.compile(r"\b(warning|caution|danger|important)\b", re.IGNORECASE)
_ORDERED_LIST = re.compile(r"^\s*\d+\.\s", re.MULTILINE)
_PROCEDURE = re.compile(r"\b(procedure|step\s+\d+|instructions)\b", re.IGNORECASE)


class StructureAnalyzer(Analyzer):
    """Derives section intelligence, complexity, and the primary topic."""

    name: ClassVar[str] = "structure"

    def analyze(
        self,
        document: AnalyzedDocument,
        builder: IntelligenceReportBuilder,
        policy: IntelligencePolicy,
    ) -> None:
        """Populate section intelligence and document-level semantic signals."""
        total_tokens = sum(count_tokens(block.text) for block in document.blocks)
        content_blocks = sum(1 for block in document.blocks if block.text.strip())
        builder.token_count = total_tokens
        builder.knowledge_density = (
            round(content_blocks / len(document.blocks), 3) if document.blocks else 0.0
        )
        builder.primary_topic = self._primary_topic(document)
        builder.complexity = self._complexity(document, policy)

        for section in document.sections:
            blocks = document.blocks_for_section(section.section_id)
            tokens = sum(count_tokens(block.text) for block in blocks)
            builder.sections.append(
                SectionIntelligence(
                    section_id=section.section_id,
                    parent_id=section.parent_id,
                    heading_level=section.level,
                    token_count=tokens,
                    reading_time_seconds=reading_time_seconds(tokens),
                    contains_table=any(b.block_type is BlockType.TABLE for b in blocks),
                    contains_image=any(b.block_type is BlockType.IMAGE for b in blocks),
                    contains_code=any(b.block_type is BlockType.CODE for b in blocks),
                    contains_warning=self._contains_warning(section.title, blocks),
                    contains_procedure=self._contains_procedure(section.title, blocks),
                )
            )

    @staticmethod
    def _primary_topic(document: AnalyzedDocument) -> str | None:
        title = document.front_matter.get("title")
        if title:
            return title
        for section in document.sections:
            if section.level == 1:
                return section.title
        return document.sections[0].title if document.sections else None

    def _complexity(
        self, document: AnalyzedDocument, policy: IntelligencePolicy
    ) -> DocumentComplexity:
        section_count = len(document.sections)
        max_depth = max((section.level for section in document.sections), default=0)
        if section_count >= policy.high_complexity_section_threshold or max_depth >= 4:
            return DocumentComplexity.HIGH
        if section_count >= 4 or max_depth >= 3:
            return DocumentComplexity.MEDIUM
        return DocumentComplexity.LOW

    @staticmethod
    def _contains_warning(title: str, blocks: list[MarkdownBlock]) -> bool:
        if _WARNING.search(title):
            return True
        return any(
            block.block_type is BlockType.NOTE and _WARNING.search(block.text)
            for block in blocks
        )

    @staticmethod
    def _contains_procedure(title: str, blocks: list[MarkdownBlock]) -> bool:
        if _PROCEDURE.search(title):
            return True
        return any(
            _ORDERED_LIST.search(block.text) or _PROCEDURE.search(block.text)
            for block in blocks
        )
