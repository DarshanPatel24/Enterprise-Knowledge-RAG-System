"""Token-window chunking strategy for LLM optimization (handbook 9.7, 9.14)."""

from __future__ import annotations

from typing import ClassVar

from domain.chunking.context import ChunkingContext, SectionView
from domain.chunking.models import ChunkStrategy
from domain.chunking.policy import ChunkingPolicy
from domain.chunking.rendering import render_block
from domain.chunking.strategies.base import ChunkDraft, ChunkStrategyPlugin
from domain.chunking.tokens import estimate_tokens
from domain.intelligence import BlockType, MarkdownBlock


class TokenWindowChunkStrategy(ChunkStrategyPlugin):
    """Packs blocks into fixed token windows within each section boundary.

    Unlike character splitters, windows still respect section boundaries and
    keep whole blocks together, but they favour filling the token budget over
    semantic grouping (handbook 9.14).
    """

    strategy: ClassVar[ChunkStrategy] = ChunkStrategy.TOKEN_BASED

    def generate(
        self, context: ChunkingContext, policy: ChunkingPolicy
    ) -> list[ChunkDraft]:
        """Generate token-budget windows, one stream per section."""
        drafts: list[ChunkDraft] = []
        for view in context.sections:
            drafts.extend(self._window_section(view, policy))
        return drafts

    def _window_section(
        self, view: SectionView, policy: ChunkingPolicy
    ) -> list[ChunkDraft]:
        drafts: list[ChunkDraft] = []
        buffer: list[MarkdownBlock] = []
        buffer_tokens = 0
        for block in view.blocks:
            block_tokens = estimate_tokens(render_block(block))
            if buffer and buffer_tokens + block_tokens > policy.target_token_budget:
                drafts.append(self._draft(view, buffer, policy))
                buffer = []
                buffer_tokens = 0
            buffer.append(block)
            buffer_tokens += block_tokens
        if buffer:
            drafts.append(self._draft(view, buffer, policy))
        return drafts

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
