"""Optional LLM reranker (handbook Chapter 25.11, story S5-2).

Feature-flagged and off by default. The deterministic evidence-weighted ordering
is always the default and the fallback. When enabled, an LCEL chain
(``ChatPromptTemplate | llm | PydanticOutputParser``) refines the ordering of the
top candidates; any failure degrades gracefully to the deterministic order, so
ranking stays reproducible. All model parameters come from settings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Protocol, cast

from pydantic import BaseModel, Field

from domain.integrations import LangChainResourceError, build_chat_model
from domain.observability import get_logger
from domain.ranking.prompts import (
    RERANK_HUMAN_TEMPLATE,
    RERANK_SYSTEM_PROMPT,
    truncate_passage,
)

_logger = get_logger("ekre.ranking.reranker")


class RerankConfigLike(Protocol):
    """Structural view of the reranker configuration."""

    enable_llm_reranker: bool
    llm_provider: str
    llm_model: str
    llm_base_url: str
    llm_temperature: float


class RerankOrder(BaseModel):
    """Validated ordered candidate ids returned by the LLM reranker."""

    ordered_ids: list[str] = Field(default_factory=list)


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


class LlmReranker(Reranker):
    """LangChain LCEL reranker with a deterministic fallback."""

    def __init__(self, config: RerankConfigLike) -> None:
        self._config = config

    @property
    def enabled(self) -> bool:
        """Return whether the LLM reranker is enabled by configuration."""
        return self._config.enable_llm_reranker

    def rerank(self, query: str, items: Sequence[tuple[str, str]]) -> list[str]:
        """Return an LLM-refined order, or the input order on graceful failure."""
        original = [identifier for identifier, _ in items]
        if not self._config.enable_llm_reranker or not items:
            return original
        try:
            from langchain_core.output_parsers import PydanticOutputParser
            from langchain_core.prompts import ChatPromptTemplate

            parser = PydanticOutputParser(pydantic_object=RerankOrder)
            prompt = ChatPromptTemplate.from_messages(
                [("system", RERANK_SYSTEM_PROMPT), ("human", RERANK_HUMAN_TEMPLATE)]
            ).partial(format_instructions=parser.get_format_instructions())
            llm = build_chat_model(
                self._config.llm_provider,
                self._config.llm_model,
                base_url=self._config.llm_base_url,
                temperature=self._config.llm_temperature,
            )
            chain = prompt | llm | parser  # type: ignore[operator]
            result = cast(
                "RerankOrder",
                chain.invoke({"query": query, "candidates": _render(items)}),
            )
            return _reconcile(result.ordered_ids, original)
        except LangChainResourceError as exc:
            _logger.warning("reranker_unavailable", extra={"reason": str(exc)})
            return original
        except Exception as exc:  # noqa: BLE001 - degrade gracefully to deterministic
            _logger.warning(
                "reranker_degraded", extra={"reason": type(exc).__name__}
            )
            return original


def _render(items: Sequence[tuple[str, str]]) -> str:
    return "\n".join(
        f"- {identifier}: {truncate_passage(content)}" for identifier, content in items
    )


def _reconcile(ordered: Sequence[str], original: Sequence[str]) -> list[str]:
    """Keep only known ids in the model order, then append any that are missing."""
    known = set(original)
    result = [identifier for identifier in ordered if identifier in known]
    seen = set(result)
    result.extend(identifier for identifier in original if identifier not in seen)
    return result
