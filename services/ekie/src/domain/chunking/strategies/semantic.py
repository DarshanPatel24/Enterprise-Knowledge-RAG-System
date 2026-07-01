"""Semantic, structure-aware chunking strategy (handbook 9.8-9.11, ADR-017)."""

from __future__ import annotations

from typing import ClassVar

from domain.chunking.context import ChunkingContext, SectionView
from domain.chunking.models import ChunkStrategy
from domain.chunking.policy import ChunkingPolicy
from domain.chunking.rendering import render_block
from domain.chunking.strategies.base import ChunkDraft, ChunkStrategyPlugin
from domain.chunking.tokens import estimate_tokens
from domain.intelligence import BlockType, MarkdownBlock


class SemanticChunkStrategy(ChunkStrategyPlugin):
    """Default strategy: section-aware with atomic tables and code (ADR-017).

    Chunks never cross section boundaries. Tables and code blocks are preserved
    intact as their own chunks so rows and functions are never split
    (handbook 9.10-9.11). A hierarchical breadcrumb preserves context
    (handbook 9.13) without duplicating body text across chunks.
    """

    strategy: ClassVar[ChunkStrategy] = ChunkStrategy.SEMANTIC

    def generate(
        self, context: ChunkingContext, policy: ChunkingPolicy
    ) -> list[ChunkDraft]:
        """Generate section-scoped chunks respecting the token budget."""
        drafts: list[ChunkDraft] = []
        for view in context.sections:
            drafts.extend(self._chunk_section(view, policy))
        return drafts

    def _chunk_section(
        self, view: SectionView, policy: ChunkingPolicy
    ) -> list[ChunkDraft]:
        drafts: list[ChunkDraft] = []
        buffer: list[MarkdownBlock] = []
        buffer_tokens = 0

        def flush() -> None:
            nonlocal buffer, buffer_tokens
            if buffer:
                drafts.append(self._draft(view, buffer, policy))
                buffer = []
                buffer_tokens = 0

        for block in view.blocks:
            rendered = render_block(block)
            block_tokens = estimate_tokens(rendered)
            if self._is_atomic(block, policy):
                heading_prefix = buffer if self._only_headings(buffer) else None
                if heading_prefix is None:
                    flush()
                    drafts.append(self._draft(view, [block], policy))
                else:
                    drafts.append(self._draft(view, [*heading_prefix, block], policy))
                    buffer = []
                    buffer_tokens = 0
                continue
            if buffer and buffer_tokens + block_tokens > policy.target_token_budget:
                flush()
            buffer.append(block)
            buffer_tokens += block_tokens

        flush()
        return drafts

    @staticmethod
    def _is_atomic(block: MarkdownBlock, policy: ChunkingPolicy) -> bool:
        if block.block_type is BlockType.TABLE:
            return policy.preserve_tables
        if block.block_type is BlockType.CODE:
            return policy.preserve_code
        return False

    @staticmethod
    def _only_headings(blocks: list[MarkdownBlock]) -> bool:
        return bool(blocks) and all(
            block.block_type is BlockType.HEADING for block in blocks
        )

    @staticmethod
    def _draft(
        view: SectionView, blocks: list[MarkdownBlock], policy: ChunkingPolicy
    ) -> ChunkDraft:
        body = "\n\n".join(render_block(block) for block in blocks)
        if policy.include_breadcrumb_context:
            content = f"> Context: {view.breadcrumb}\n\n{body}"
        else:
            content = body
        return ChunkDraft(
            section_id=view.section_id,
            section_title=view.title,
            breadcrumb=view.breadcrumb,
            heading_level=view.level,
            content=content,
            token_count=estimate_tokens(content),
            contains_table=any(b.block_type is BlockType.TABLE for b in blocks),
            contains_code=any(b.block_type is BlockType.CODE for b in blocks),
            contains_image=any(b.block_type is BlockType.IMAGE for b in blocks),
        )
