"""LangChain resource template: one config-driven factory for the chat model.

Consolidates LangChain chat-model initialization in a single place so the model
gateway never constructs LangChain clients inline. All third-party imports are
lazy so the deterministic offline path never loads LangChain. The provider and
every parameter are supplied by the caller from settings, so no model runtime is
hardcoded and EKCP stays model-agnostic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Iterator

_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


class LangChainResourceError(RuntimeError):
    """Raised when a LangChain chat model cannot be built or invoked."""


class ChatModelLike(Protocol):
    """Minimal structural view of a LangChain chat model.

    Kept structural so the gateway can depend on the seam without importing a
    concrete LangChain model type on the offline path.
    """

    def invoke(self, input: Any, **kwargs: Any) -> Any: ...  # noqa: A002, ANN401

    def stream(self, input: Any, **kwargs: Any) -> Iterator[Any]: ...  # noqa: A002, ANN401


def build_chat_model(
    provider: str,
    model: str,
    *,
    base_url: str = _DEFAULT_OLLAMA_BASE_URL,
    temperature: float = 0.0,
) -> ChatModelLike:
    """Build a LangChain chat model for ``provider`` and ``model``.

    The single provider-abstracted factory for chat models across EKCP. Supports
    ``huggingface`` (local transformers pipeline) and ``ollama``; the provider
    and every parameter are supplied by the caller from settings so no runtime is
    hardcoded. Imports are lazy so the offline path never loads LangChain.
    """
    if provider == "huggingface":
        try:
            from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
        except ImportError as exc:
            raise LangChainResourceError(
                "langchain-huggingface is not installed; install it to use a "
                "HuggingFace chat model"
            ) from exc
        pipeline = HuggingFacePipeline.from_model_id(
            model_id=model,
            task="text-generation",
            pipeline_kwargs={"temperature": temperature, "do_sample": temperature > 0.0},
        )
        return cast("ChatModelLike", ChatHuggingFace(llm=pipeline))
    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise LangChainResourceError(
                "langchain-ollama is not installed; install it to use an Ollama chat model"
            ) from exc
        return cast(
            "ChatModelLike",
            ChatOllama(model=model, base_url=base_url, temperature=temperature),
        )
    raise LangChainResourceError(
        f"chat model provider {provider!r} is not supported; use 'huggingface' or 'ollama'"
    )
