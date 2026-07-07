"""Chat model provider adapters behind the gateway seam.

Providers are the only components that touch a concrete model runtime; the
gateway depends on the :class:`ChatModelProvider` ABC so EKCP stays
model-agnostic (handbook 14.20). The deterministic echo provider is the
local-first offline default; the LangChain provider wraps the configured
HuggingFace or Ollama chat model via LCEL and is imported lazily.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import cast

from domain.gateway.errors import ProviderInvocationError
from domain.gateway.models import ModelDescriptor, ResponseConstraints
from domain.integrations import (
    ChatModelLike,
    LangChainResourceError,
    build_chat_model,
)

_USER_REQUEST_MARKER = "User request:"


class ChatModelProvider(ABC):
    """Abstract chat model provider adapter."""

    @property
    @abstractmethod
    def runtime(self) -> str:
        """Return the runtime name this provider serves (e.g. ``deterministic``)."""

    @abstractmethod
    def generate(
        self, descriptor: ModelDescriptor, prompt_text: str, constraints: ResponseConstraints
    ) -> str:
        """Generate a complete response for ``prompt_text``."""

    @abstractmethod
    def stream(
        self, descriptor: ModelDescriptor, prompt_text: str, constraints: ResponseConstraints
    ) -> Iterator[str]:
        """Stream the response for ``prompt_text`` as incremental text fragments."""


def _extract_request(prompt_text: str) -> str:
    """Return the user request line from an assembled prompt, or the last line."""
    for line in reversed(prompt_text.splitlines()):
        stripped = line.strip()
        if stripped.startswith(_USER_REQUEST_MARKER):
            return stripped[len(_USER_REQUEST_MARKER) :].strip()
    for line in reversed(prompt_text.splitlines()):
        if line.strip():
            return line.strip()
    return prompt_text.strip()


class DeterministicEchoProvider(ChatModelProvider):
    """Deterministic, dependency-free provider (local-first offline default)."""

    @property
    def runtime(self) -> str:
        return "deterministic"

    def generate(
        self, descriptor: ModelDescriptor, prompt_text: str, constraints: ResponseConstraints
    ) -> str:
        request = _extract_request(prompt_text)
        return (
            f"Based on the assembled context, here is a grounded response to: {request}"
        )

    def stream(
        self, descriptor: ModelDescriptor, prompt_text: str, constraints: ResponseConstraints
    ) -> Iterator[str]:
        text = self.generate(descriptor, prompt_text, constraints)
        for index, token in enumerate(text.split()):
            yield token if index == 0 else f" {token}"


class LangChainChatProvider(ChatModelProvider):
    """Provider that invokes the configured chat model via LCEL (lazy imports)."""

    @property
    def runtime(self) -> str:
        return "langchain"

    def generate(
        self, descriptor: ModelDescriptor, prompt_text: str, constraints: ResponseConstraints
    ) -> str:
        chain = self._chain(descriptor)
        try:
            output = chain.invoke(prompt_text)
        except Exception as exc:  # noqa: BLE001 - isolate any provider failure
            raise ProviderInvocationError(str(exc)) from exc
        return str(output)

    def stream(
        self, descriptor: ModelDescriptor, prompt_text: str, constraints: ResponseConstraints
    ) -> Iterator[str]:
        chain = self._chain(descriptor)
        try:
            for chunk in chain.stream(prompt_text):
                yield str(chunk)
        except Exception as exc:  # noqa: BLE001 - isolate any provider failure
            raise ProviderInvocationError(str(exc)) from exc

    @staticmethod
    def _chain(descriptor: ModelDescriptor) -> ChatModelLike:
        try:
            from langchain_core.output_parsers import StrOutputParser
        except ImportError as exc:
            raise ProviderInvocationError(
                "langchain-core is required for the LangChain chat provider"
            ) from exc
        try:
            model = build_chat_model(
                descriptor.provider,
                descriptor.model_name,
                base_url=descriptor.base_url or "http://localhost:11434",
                temperature=descriptor.temperature,
            )
        except LangChainResourceError as exc:
            raise ProviderInvocationError(str(exc)) from exc
        return cast("ChatModelLike", model | StrOutputParser())  # type: ignore[operator]


def default_provider_registry() -> dict[str, ChatModelProvider]:
    """Return the provider registry with the deterministic offline default."""
    return {"deterministic": DeterministicEchoProvider()}


def provider_registry_from_settings(runtime: str) -> dict[str, ChatModelProvider]:
    """Return the provider registry, adding the LangChain provider when selected."""
    registry = default_provider_registry()
    if runtime == "langchain":
        registry["langchain"] = LangChainChatProvider()
    return registry
