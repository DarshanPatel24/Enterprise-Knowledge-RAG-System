"""Chunk strategy registry and selection (handbook 9.7)."""

from __future__ import annotations

from domain.chunking.models import ChunkStrategy
from domain.chunking.strategies.base import ChunkDraft, ChunkStrategyPlugin
from domain.chunking.strategies.semantic import SemanticChunkStrategy
from domain.chunking.strategies.token import TokenWindowChunkStrategy


class ChunkStrategyRegistry:
    """Resolves a :class:`ChunkStrategy` to its plugin implementation."""

    def __init__(self, plugins: list[ChunkStrategyPlugin]) -> None:
        self._plugins = {plugin.strategy: plugin for plugin in plugins}

    def select(self, strategy: ChunkStrategy) -> ChunkStrategyPlugin:
        """Return the plugin registered for ``strategy``.

        Falls back to the semantic strategy when a requested strategy has no
        dedicated plugin, keeping the default behavior deterministic.
        """
        plugin = self._plugins.get(strategy)
        if plugin is None:
            plugin = self._plugins[ChunkStrategy.SEMANTIC]
        return plugin

    def register(self, plugin: ChunkStrategyPlugin) -> None:
        """Register or override a strategy plugin."""
        self._plugins[plugin.strategy] = plugin


def default_registry() -> ChunkStrategyRegistry:
    """Return the default registry with the built-in chunking strategies."""
    return ChunkStrategyRegistry(
        [SemanticChunkStrategy(), TokenWindowChunkStrategy()]
    )


__all__ = [
    "ChunkDraft",
    "ChunkStrategyPlugin",
    "ChunkStrategyRegistry",
    "SemanticChunkStrategy",
    "TokenWindowChunkStrategy",
    "default_registry",
]
