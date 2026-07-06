"""Recursive character chunking strategy (LangChain-backed, opt-in).

Splits each section's rendered Markdown with LangChain's
``RecursiveCharacterTextSplitter`` using a configurable size/overlap and a
separator ladder. Unlike the semantic strategy it does not keep tables or code
blocks atomic; the character-overlap window preserves cross-boundary context
instead (handbook 9.7). It is selected only when the configured chunking
strategy is ``recursive`` (``EKIE_CHUNKING__DEFAULT_STRATEGY=recursive``); the
semantic strategy remains the default.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol, cast

from domain.chunking.context import ChunkingContext, SectionView
from domain.chunking.errors import ChunkingError, ChunkingErrorType
from domain.chunking.models import ChunkStrategy
from domain.chunking.policy import ChunkingPolicy
from domain.chunking.rendering import render_block
from domain.chunking.strategies.base import ChunkDraft, ChunkStrategyPlugin
from domain.chunking.tokens import estimate_tokens

if TYPE_CHECKING:

    class _TextSplitter(Protocol):
        """Structural type for the LangChain recursive splitter."""

        def split_text(self, text: str) -> list[str]: ...


def _build_splitter(policy: ChunkingPolicy) -> _TextSplitter:
    """Construct the LangChain recursive splitter from the chunking policy."""
    if policy.recursive_chunk_overlap >= policy.recursive_chunk_size:
        raise ChunkingError(
            ChunkingErrorType.VALIDATION_FAILURE,
            "recursive_chunk_overlap must be smaller than recursive_chunk_size",
        )
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as exc:  # pragma: no cover - exercised via skipif test
        raise ChunkingError(
            ChunkingErrorType.STRATEGY_UNAVAILABLE,
            "recursive chunking requires the 'langchain-text-splitters' package",
        ) from exc
    splitter = RecursiveCharacterTextSplitter(
        separators=list(policy.recursive_separators),
        chunk_size=policy.recursive_chunk_size,
        chunk_overlap=policy.recursive_chunk_overlap,
        keep_separator=True,
    )
    return cast("_TextSplitter", splitter)


def _contains_table(text: str) -> bool:
    """Return True when ``text`` includes a Markdown table separator row."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and "-" in stripped and set(stripped) <= {"|", "-", ":", " "}:
            return True
    return False


class RecursiveCharacterChunkStrategy(ChunkStrategyPlugin):
    """Splits each section with a recursive character splitter and overlap.

    Section boundaries and inherited metadata are preserved (section id, title,
    breadcrumb, heading level); the split happens within each section so chunk
    lineage and validation remain identical to the other strategies.
    """

    strategy: ClassVar[ChunkStrategy] = ChunkStrategy.RECURSIVE

    def generate(
        self, context: ChunkingContext, policy: ChunkingPolicy
    ) -> list[ChunkDraft]:
        """Generate recursive character chunks, one stream per section."""
        splitter = _build_splitter(policy)
        drafts: list[ChunkDraft] = []
        for view in context.sections:
            drafts.extend(self._split_section(view, policy, splitter))
        return drafts

    def _split_section(
        self, view: SectionView, policy: ChunkingPolicy, splitter: _TextSplitter
    ) -> list[ChunkDraft]:
        body = "\n\n".join(render_block(block) for block in view.blocks).strip()
        if not body:
            return []
        drafts: list[ChunkDraft] = []
        for piece in splitter.split_text(body):
            text = piece.strip()
            if not text:
                continue
            drafts.append(self._draft(view, text, policy))
        return drafts

    @staticmethod
    def _draft(view: SectionView, text: str, policy: ChunkingPolicy) -> ChunkDraft:
        if policy.include_breadcrumb_context:
            content = f"> Context: {view.breadcrumb}\n\n{text}"
        else:
            content = text
        return ChunkDraft(
            section_id=view.section_id,
            section_title=view.title,
            breadcrumb=view.breadcrumb,
            heading_level=view.level,
            content=content,
            token_count=estimate_tokens(content),
            contains_table=_contains_table(text),
            contains_code="```" in text,
            contains_image="![" in text,
        )
