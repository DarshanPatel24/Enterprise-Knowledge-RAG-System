"""LangChain integration seam (chat model factory)."""

from domain.integrations.langchain_resources import (
    ChatModelLike,
    LangChainResourceError,
    build_chat_model,
)

__all__ = [
    "ChatModelLike",
    "LangChainResourceError",
    "build_chat_model",
]
