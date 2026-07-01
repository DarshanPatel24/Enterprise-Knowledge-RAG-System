"""Optional LLM-based document analyzer (handbook 8.11, EKIE-S3-5).

Refines the heuristic ``primary_topic`` with a locally hosted chat model when
LLM analysis is enabled by configuration. The analyzer is a no-op unless
``policy.enable_llm_analysis`` is set, and any model or dependency failure
degrades gracefully to the deterministic value produced by earlier analyzers,
so the pipeline stays reproducible and never fails on model unavailability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol, cast

from domain.intelligence.analysis import AnalyzedDocument
from domain.intelligence.analyzers.base import Analyzer, IntelligenceReportBuilder
from domain.intelligence.llm import build_chat_model
from domain.intelligence.models import BlockType
from domain.intelligence.policy import IntelligencePolicy
from domain.intelligence.prompts import (
    TOPIC_SYSTEM_PROMPT,
    TOPIC_USER_TEMPLATE,
    truncate_document,
)
from domain.observability import get_logger

logger = get_logger("ekie.intelligence.llm")

if TYPE_CHECKING:

    class _TopicChain(Protocol):
        """Structural type for the ``prompt | llm | parser`` runnable chain."""

        def invoke(self, input: dict[str, str]) -> str: ...


def _document_text(document: AnalyzedDocument) -> str:
    """Return the document's prose (excluding code) for topic extraction."""
    return "\n".join(
        block.text
        for block in document.blocks
        if block.block_type is not BlockType.CODE and block.text.strip()
    )


class LlmAnalyzer(Analyzer):
    """Refines the document's primary topic using a local chat model."""

    name: ClassVar[str] = "llm"

    def analyze(
        self,
        document: AnalyzedDocument,
        builder: IntelligenceReportBuilder,
        policy: IntelligencePolicy,
    ) -> None:
        """Set ``builder.primary_topic`` from the model, degrading on failure."""
        if not policy.enable_llm_analysis:
            return
        text = _document_text(document)
        if not text.strip():
            return
        try:
            chain = self._build_chain(policy)
            topic = chain.invoke({"document": truncate_document(text)})
        except Exception as exc:  # external LLM boundary; keep heuristic result
            logger.warning(
                "llm_analysis_skipped",
                extra={"reason": str(exc), "model": policy.llm_model},
            )
            return
        cleaned = topic.strip()
        if cleaned:
            builder.primary_topic = cleaned

    @staticmethod
    def _build_chain(policy: IntelligencePolicy) -> _TopicChain:
        """Assemble the ``prompt | llm | parser`` chain for topic extraction."""
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        llm = build_chat_model(policy)
        prompt = ChatPromptTemplate.from_messages(
            [("system", TOPIC_SYSTEM_PROMPT), ("user", TOPIC_USER_TEMPLATE)]
        )
        return cast("_TopicChain", prompt | llm | StrOutputParser())
