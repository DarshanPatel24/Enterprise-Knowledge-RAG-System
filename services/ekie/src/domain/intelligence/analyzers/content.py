"""Table, figure, and code-block detection analyzers (handbook 8.7-8.9)."""

from __future__ import annotations

import re
from typing import ClassVar

from domain.intelligence.analysis import AnalyzedDocument
from domain.intelligence.analyzers.base import Analyzer, IntelligenceReportBuilder
from domain.intelligence.markdown_ast import MarkdownBlock
from domain.intelligence.models import (
    BlockType,
    CodeBlockInfo,
    FigureInfo,
    TableInfo,
)
from domain.intelligence.policy import IntelligencePolicy

_NUMBER = re.compile(r"^-?\d[\d,.]*$")
_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_IDENTIFIER = re.compile(r"\b[A-Z]{2,}-?\d+\b")


class TableAnalyzer(Analyzer):
    """Classifies detected tables with structural metadata."""

    name: ClassVar[str] = "table"

    def analyze(
        self,
        document: AnalyzedDocument,
        builder: IntelligenceReportBuilder,
        policy: IntelligencePolicy,
    ) -> None:
        """Emit a :class:`TableInfo` for each detected table block."""
        counter = 0
        for block in document.blocks:
            if block.block_type is not BlockType.TABLE or not block.table_rows:
                continue
            counter += 1
            builder.tables.append(self._classify(block, counter))

    @staticmethod
    def _classify(block: MarkdownBlock, counter: int) -> TableInfo:
        rows = block.table_rows
        header = rows[0] if rows else []
        data_rows = rows[1:]
        columns = max((len(row) for row in rows), default=0)
        non_empty_header = sum(1 for cell in header if cell.strip())
        header_confidence = round(non_empty_header / columns, 2) if columns else 0.0
        cells = [cell for row in data_rows for cell in row]
        return TableInfo(
            table_id=f"TBL-{counter}",
            section_id=block.section_id,
            rows=len(data_rows),
            columns=columns,
            header_confidence=header_confidence,
            contains_numeric=any(_NUMBER.match(cell.strip()) for cell in cells),
            contains_dates=any(_DATE.search(cell) for cell in cells),
            contains_ids=any(_IDENTIFIER.search(cell) for cell in cells),
        )


class FigureAnalyzer(Analyzer):
    """Detects images and figures with their captions and references."""

    name: ClassVar[str] = "figure"

    def analyze(
        self,
        document: AnalyzedDocument,
        builder: IntelligenceReportBuilder,
        policy: IntelligencePolicy,
    ) -> None:
        """Emit a :class:`FigureInfo` for each image block."""
        counter = 0
        for block in document.blocks:
            if block.block_type is not BlockType.IMAGE:
                continue
            counter += 1
            builder.figures.append(
                FigureInfo(
                    figure_id=f"FIG-{counter}",
                    section_id=block.section_id,
                    caption=block.text,
                    reference=block.language,
                )
            )


class CodeAnalyzer(Analyzer):
    """Detects fenced code blocks and captures their metadata."""

    name: ClassVar[str] = "code"

    def analyze(
        self,
        document: AnalyzedDocument,
        builder: IntelligenceReportBuilder,
        policy: IntelligencePolicy,
    ) -> None:
        """Emit a :class:`CodeBlockInfo` for each fenced code block."""
        counter = 0
        for block in document.blocks:
            if block.block_type is not BlockType.CODE:
                continue
            counter += 1
            line_count = len(block.text.split("\n")) if block.text else 0
            builder.code_blocks.append(
                CodeBlockInfo(
                    block_id=f"CODE-{counter}",
                    section_id=block.section_id,
                    language=block.language or "text",
                    line_count=line_count,
                )
            )
