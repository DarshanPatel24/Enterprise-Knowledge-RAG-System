"""Document quality scoring analyzer (handbook 8.14)."""

from __future__ import annotations

from typing import ClassVar

from domain.intelligence.analysis import AnalyzedDocument
from domain.intelligence.analyzers.base import Analyzer, IntelligenceReportBuilder
from domain.intelligence.models import BlockType, QualityScore
from domain.intelligence.policy import IntelligencePolicy


class QualityAnalyzer(Analyzer):
    """Computes an overall quality score with a component breakdown."""

    name: ClassVar[str] = "quality"

    def analyze(
        self,
        document: AnalyzedDocument,
        builder: IntelligenceReportBuilder,
        policy: IntelligencePolicy,
    ) -> None:
        """Score structure, content, table, and image integrity."""
        components = {
            "structure": self._structure_score(document),
            "content": self._content_score(builder),
            "tables": self._table_score(document, builder),
            "images": self._image_score(builder),
        }
        overall = round(sum(components.values()) / len(components))
        builder.quality = QualityScore(overall=overall, components=components)

    @staticmethod
    def _structure_score(document: AnalyzedDocument) -> int:
        if not document.sections:
            return 60
        levels = sorted({section.level for section in document.sections})
        contiguous = levels == list(range(levels[0], levels[0] + len(levels)))
        return 100 if contiguous else 85

    @staticmethod
    def _content_score(builder: IntelligenceReportBuilder) -> int:
        return 100 if builder.token_count > 0 else 0

    @staticmethod
    def _table_score(
        document: AnalyzedDocument, builder: IntelligenceReportBuilder
    ) -> int:
        table_blocks = [
            block for block in document.blocks if block.block_type is BlockType.TABLE
        ]
        if not table_blocks:
            return 100
        ragged = any(
            len({len(row) for row in block.table_rows}) > 1 for block in table_blocks
        )
        low_confidence = any(table.header_confidence < 0.5 for table in builder.tables)
        score = 100
        if ragged:
            score -= 25
        if low_confidence:
            score -= 15
        return max(score, 0)

    @staticmethod
    def _image_score(builder: IntelligenceReportBuilder) -> int:
        if not builder.figures:
            return 100
        captioned = sum(1 for figure in builder.figures if figure.caption.strip())
        return round(captioned / len(builder.figures) * 100)
