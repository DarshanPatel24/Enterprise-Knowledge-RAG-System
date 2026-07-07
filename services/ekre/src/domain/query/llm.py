"""Optional LangChain LLM query interpreter (handbook Chapter 9, story S1-5).

Feature-flagged and off by default. When enabled it rewrites and normalizes the
query and extracts entities via a LangChain LCEL chain
(``ChatPromptTemplate | llm | PydanticOutputParser``). Any failure --- missing
dependency, unavailable model, or invalid output --- degrades gracefully to the
deterministic Query Understanding Engine, so retrieval planning stays
reproducible. All model parameters come from settings; nothing is hardcoded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from pydantic import BaseModel, Field

from domain.integrations import (
    ChatModelLike,
    LangChainResourceError,
)
from domain.integrations import (
    build_chat_model as _build_chat_model,
)
from domain.observability import get_logger
from domain.query.prompts import (
    QUERY_HUMAN_TEMPLATE,
    QUERY_SYSTEM_PROMPT,
    truncate_query,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

_logger = get_logger("ekre.query.llm")


class LlmConfigLike(Protocol):
    """Structural view of the LLM configuration the interpreter needs."""

    enable_llm_interpreter: bool
    llm_provider: str
    llm_model: str
    llm_base_url: str
    llm_temperature: float
    llm_request_timeout_seconds: float


class LlmUnavailableError(RuntimeError):
    """Raised when the configured chat model cannot be constructed."""


class LlmQueryInterpretation(BaseModel):
    """Validated structured output returned by the LLM query interpreter."""

    normalized_query: str = Field(description="cleaned, normalized query text")
    rewritten_query: str = Field(description="an improved rewrite of the query")
    entities: list[str] = Field(default_factory=list, description="salient entities")
    language: str = Field(default="en", description="ISO language code of the query")


def build_chat_model(config: LlmConfigLike) -> ChatModelLike:
    """Build the interpreter chat model via the shared LangChain seam.

    Delegates to the single provider-abstracted factory in ``domain.integrations``
    and maps its error to the query-domain :class:`LlmUnavailableError`. All model
    parameters come from settings; nothing is hardcoded.
    """
    try:
        return _build_chat_model(
            config.llm_provider,
            config.llm_model,
            base_url=config.llm_base_url,
            temperature=config.llm_temperature,
        )
    except LangChainResourceError as exc:
        raise LlmUnavailableError(str(exc)) from exc


class QueryLlmInterpreter:
    """LangChain LCEL interpreter that enriches deterministic understanding."""

    def __init__(self, config: LlmConfigLike) -> None:
        self._config = config

    @property
    def enabled(self) -> bool:
        """Return whether the LLM interpreter is enabled by configuration."""
        return self._config.enable_llm_interpreter

    def interpret(self, raw_query: str) -> LlmQueryInterpretation | None:
        """Return a validated interpretation, or ``None`` on graceful failure."""
        if not self._config.enable_llm_interpreter:
            return None
        try:
            from langchain_core.output_parsers import PydanticOutputParser
            from langchain_core.prompts import ChatPromptTemplate

            parser = PydanticOutputParser(pydantic_object=LlmQueryInterpretation)
            prompt = ChatPromptTemplate.from_messages(
                [("system", QUERY_SYSTEM_PROMPT), ("human", QUERY_HUMAN_TEMPLATE)]
            ).partial(format_instructions=parser.get_format_instructions())
            llm = build_chat_model(self._config)
            chain = prompt | llm | parser  # type: ignore[operator]
            variables: Mapping[str, str] = {"query": truncate_query(raw_query)}
            result = chain.invoke(variables)
            return cast("LlmQueryInterpretation", result)
        except Exception as exc:  # noqa: BLE001 - degrade gracefully to deterministic
            _logger.warning(
                "query_llm_interpreter_degraded",
                extra={"reason": type(exc).__name__},
            )
            return None
