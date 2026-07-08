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
from typing import Any, cast

from domain.gateway.errors import ProviderInvocationError
from domain.gateway.models import ModelDescriptor, ResponseConstraints
from domain.integrations import (
    ChatModelLike,
    build_chat_model,
)
from domain.observability import get_logger

_USER_REQUEST_MARKER = "User request:"

# Process-wide cache of built LCEL chains keyed by the model's identifying
# parameters. The HuggingFace pipeline loads multi-GB weights from disk, so
# building the chain once and reusing it is essential: without this the model
# would be reloaded on every request.
_CHAIN_CACHE: dict[tuple[str, str, str, float, int, str, str], ChatModelLike] = {}
_logger = get_logger("ekcp.gateway.provider")


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
            output = chain.invoke(self._model_input(descriptor, prompt_text))
        except Exception as exc:  # noqa: BLE001 - isolate any provider failure
            raise ProviderInvocationError(str(exc)) from exc
        return str(output)

    def stream(
        self, descriptor: ModelDescriptor, prompt_text: str, constraints: ResponseConstraints
    ) -> Iterator[str]:
        chain = self._chain(descriptor)
        try:
            for chunk in chain.stream(self._model_input(descriptor, prompt_text)):
                yield str(chunk)
        except Exception as exc:  # noqa: BLE001 - isolate any provider failure
            raise ProviderInvocationError(str(exc)) from exc

    @staticmethod
    def _model_input(descriptor: ModelDescriptor, prompt_text: str) -> Any:  # noqa: ANN401 - chat model accepts str or message list
        """Build the model input, prepending the system prompt as a system role.

        The system prompt fixes the assistant's role and enforces context-only
        answers. Passing messages (not a formatted string) avoids brace/format
        issues with arbitrary retrieved content.
        """
        if not descriptor.system_prompt:
            return prompt_text
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
        except ImportError as exc:
            raise ProviderInvocationError(
                "langchain-core is required for the LangChain chat provider"
            ) from exc
        return [
            SystemMessage(content=descriptor.system_prompt),
            HumanMessage(content=prompt_text),
        ]

    @staticmethod
    def _chain(descriptor: ModelDescriptor) -> ChatModelLike:
        key = (
            descriptor.provider,
            descriptor.model_name,
            descriptor.base_url,
            descriptor.temperature,
            descriptor.max_output_tokens,
            descriptor.device,
            descriptor.torch_dtype,
        )
        cached = _CHAIN_CACHE.get(key)
        if cached is not None:
            return cached
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
                max_new_tokens=descriptor.max_output_tokens,
                device=descriptor.device,
                torch_dtype=descriptor.torch_dtype,
            )
        except Exception as exc:  # noqa: BLE001 - isolate any model-load failure (offline cache miss, missing weights, OOM) so the gateway can fall back instead of crashing
            raise ProviderInvocationError(str(exc)) from exc
        chain = cast("ChatModelLike", model | StrOutputParser())  # type: ignore[operator]
        _CHAIN_CACHE[key] = chain
        _logger.info(
            "chat_model_loaded",
            extra={
                "model_id": descriptor.model_id,
                "device": descriptor.device or "cpu",
                "cache_size": len(_CHAIN_CACHE),
            },
        )
        return chain


def default_provider_registry() -> dict[str, ChatModelProvider]:
    """Return the provider registry with the deterministic offline default."""
    return {"deterministic": DeterministicEchoProvider()}


def provider_registry_from_settings(runtime: str) -> dict[str, ChatModelProvider]:
    """Return the provider registry, adding the LangChain provider when selected."""
    registry = default_provider_registry()
    if runtime == "langchain":
        registry["langchain"] = LangChainChatProvider()
    return registry
