"""Cross-encoder reranker (handbook Chapter 25.11, story S5-2).

Feature-flagged and off by default. The deterministic evidence-weighted ordering
is always the default and the fallback. When enabled, a purpose-built reranker
model (for example ``Qwen/Qwen3-VL-Reranker-2B``) scores each (query, passage)
pair and reorders the top candidates; the model performs no chat generation
(that is EKCP). Any failure degrades gracefully to the deterministic order, so
ranking stays reproducible. All model parameters come from settings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Protocol

from domain.integrations import LangChainResourceError, build_cross_encoder
from domain.observability import get_logger
from domain.ranking.prompts import truncate_passage

_logger = get_logger("ekre.ranking.reranker")


class RerankConfigLike(Protocol):
    """Structural view of the cross-encoder reranker configuration."""

    enable_reranker: bool
    reranker_model: str
    reranker_device: str
    reranker_torch_dtype: str
    reranker_trust_remote_code: bool


class Reranker(ABC):
    """Reorders candidate ids for a query."""

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Return whether reranking is active."""

    @abstractmethod
    def rerank(self, query: str, items: Sequence[tuple[str, str]]) -> list[str]:
        """Return the candidate ids ordered from most to least relevant."""


class IdentityReranker(Reranker):
    """Deterministic no-op reranker: preserves the input order."""

    @property
    def enabled(self) -> bool:
        """Return ``False``; the identity reranker never changes ordering."""
        return False

    def rerank(self, query: str, items: Sequence[tuple[str, str]]) -> list[str]:
        """Return the ids in their given (deterministic) order."""
        return [identifier for identifier, _ in items]


class CrossEncoderReranker(Reranker):
    """Cross-encoder reranker that scores query/document relevance.

    Loads a purpose-built reranker model (for example ``Qwen/Qwen3-VL-Reranker-2B``)
    lazily, scores each (query, passage) pair, and reorders by score. The model
    is loaded once and cached. Any failure (model unavailable, scoring error)
    degrades gracefully to the deterministic input order.
    """

    def __init__(self, config: RerankConfigLike) -> None:
        self._config = config
        self._model: object | None = None

    @property
    def enabled(self) -> bool:
        """Return whether the cross-encoder reranker is configured and enabled."""
        return self._config.enable_reranker and bool(self._config.reranker_model)

    def rerank(self, query: str, items: Sequence[tuple[str, str]]) -> list[str]:
        """Return the cross-encoder order, or the input order on graceful failure."""
        original = [identifier for identifier, _ in items]
        if not self.enabled or not items:
            return original
        try:
            model = self._load()
            pairs = [[query, truncate_passage(content)] for _, content in items]
            scores = model.predict(pairs)  # type: ignore[attr-defined]
            return _order_by_scores(original, [float(score) for score in scores])
        except LangChainResourceError as exc:
            _logger.warning("reranker_unavailable", extra={"reason": str(exc)})
            return original
        except Exception as exc:  # noqa: BLE001 - degrade gracefully to deterministic
            _logger.warning("reranker_degraded", extra={"reason": type(exc).__name__})
            return original

    def _load(self) -> object:
        if self._model is None:
            self._model = build_cross_encoder(
                self._config.reranker_model,
                device=self._config.reranker_device,
                torch_dtype=self._config.reranker_torch_dtype,
                trust_remote_code=self._config.reranker_trust_remote_code,
            )
            _logger.info(
                "reranker_model_loaded", extra={"model": self._config.reranker_model}
            )
        return self._model


def _order_by_scores(ids: Sequence[str], scores: Sequence[float]) -> list[str]:
    """Return ``ids`` ordered by descending score with a stable original-order tie-break.

    If the score count does not match the ids, the deterministic input order is
    returned so ranking never breaks on an unexpected model output shape.
    """
    if len(scores) != len(ids):
        return list(ids)
    indexed = sorted(enumerate(ids), key=lambda pair: (-scores[pair[0]], pair[0]))
    return [identifier for _, identifier in indexed]
