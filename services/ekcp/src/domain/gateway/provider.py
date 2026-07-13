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
from domain.observability import (
    get_correlation_id,
    get_logger,
    get_session_id,
    get_tenant_id,
)

_USER_REQUEST_MARKER = "User request:"

# Process-wide cache of built LCEL chains keyed by the model's identifying
# parameters. The HuggingFace pipeline loads multi-GB weights from disk, so
# building the chain once and reusing it is essential: without this the model
# would be reloaded on every request.
_CHAIN_CACHE: dict[tuple[str, str, str, float, int, str, str, float, int], ChatModelLike] = {}
# Raw chat models (before the StrOutputParser) keyed identically. HuggingFace token
# streaming needs the underlying transformers pipeline, which the LCEL chain hides;
# both caches reference the same built model so weights load exactly once.
_RAW_MODEL_CACHE: dict[tuple[str, str, str, float, int, str, str, float, int], Any] = {}
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

    def __init__(self, *, callbacks: list[Any] | None = None) -> None:
        # Langfuse (or other LangChain) callbacks attached to every chain run so
        # LLM generations are traced when observability is enabled. Empty/None
        # keeps the offline path callback-free.
        self._callbacks: list[Any] | None = list(callbacks) if callbacks else None

    @property
    def runtime(self) -> str:
        return "langchain"

    def _invoke_config(self) -> dict[str, Any] | None:
        """Return the LCEL run config carrying tracing callbacks, or None.

        When callbacks are present the config also carries the request's
        correlation, tenant, and session identifiers so the Langfuse trace is
        attributable to the originating client (for example the web UI). The
        ``langfuse_*`` metadata keys are read by the Langfuse callback handler.
        """
        if not self._callbacks:
            return None
        correlation_id = get_correlation_id()
        tenant_id = get_tenant_id()
        session_id = get_session_id() or correlation_id
        metadata: dict[str, Any] = {}
        if session_id:
            metadata["langfuse_session_id"] = session_id
        if tenant_id:
            metadata["langfuse_user_id"] = tenant_id
        if correlation_id:
            metadata["correlation_id"] = correlation_id
        config: dict[str, Any] = {"callbacks": self._callbacks}
        if metadata:
            config["metadata"] = metadata
        return config

    def generate(
        self, descriptor: ModelDescriptor, prompt_text: str, constraints: ResponseConstraints
    ) -> str:
        chain = self._chain(descriptor)
        try:
            output = chain.invoke(
                self._model_input(descriptor, prompt_text), config=self._invoke_config()
            )
        except Exception as exc:  # noqa: BLE001 - isolate any provider failure
            raise ProviderInvocationError(str(exc)) from exc
        return str(output)

    def stream(
        self, descriptor: ModelDescriptor, prompt_text: str, constraints: ResponseConstraints
    ) -> Iterator[str]:
        # The HuggingFace provider streams real tokens through a transformers
        # TextIteratorStreamer (LangChain's ``chain.stream`` does not stream a local
        # pipeline). Providers with native streaming (ollama) stream through LCEL,
        # falling back to a single full generation only if streaming yields nothing.
        if descriptor.provider == "huggingface":
            yield from self._stream_huggingface(descriptor, prompt_text)
            return
        chain = self._chain(descriptor)
        model_input = self._model_input(descriptor, prompt_text)
        streamed_any = False
        try:
            for chunk in chain.stream(model_input, config=self._invoke_config()):
                text = str(chunk)
                if text:
                    streamed_any = True
                    yield text
        except Exception as exc:  # noqa: BLE001 - isolate any provider failure
            if streamed_any:
                raise ProviderInvocationError(str(exc)) from exc
        else:
            if streamed_any:
                return
        yield from self._generate_fragment(descriptor, prompt_text)

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
    def _model_key(
        descriptor: ModelDescriptor,
    ) -> tuple[str, str, str, float, int, str, str, float, int]:
        return (
            descriptor.provider,
            descriptor.model_name,
            descriptor.base_url,
            descriptor.temperature,
            descriptor.max_output_tokens,
            descriptor.device,
            descriptor.torch_dtype,
            descriptor.top_p,
            descriptor.top_k,
        )

    @classmethod
    def _raw_model(cls, descriptor: ModelDescriptor) -> Any:  # noqa: ANN401 - concrete chat model type varies by provider
        """Build and cache the raw chat model so weights load exactly once."""
        key = cls._model_key(descriptor)
        cached = _RAW_MODEL_CACHE.get(key)
        if cached is not None:
            return cached
        try:
            model = build_chat_model(
                descriptor.provider,
                descriptor.model_name,
                base_url=descriptor.base_url or "http://localhost:11434",
                temperature=descriptor.temperature,
                top_p=descriptor.top_p,
                top_k=descriptor.top_k,
                max_new_tokens=descriptor.max_output_tokens,
                device=descriptor.device,
                torch_dtype=descriptor.torch_dtype,
            )
        except Exception as exc:  # noqa: BLE001 - isolate any model-load failure (offline cache miss, missing weights, OOM) so the gateway can fall back instead of crashing
            raise ProviderInvocationError(str(exc)) from exc
        _RAW_MODEL_CACHE[key] = model
        _logger.info(
            "chat_model_loaded",
            extra={
                "model_id": descriptor.model_id,
                "device": descriptor.device or "cpu",
                "cache_size": len(_RAW_MODEL_CACHE),
            },
        )
        return model

    @classmethod
    def _chain(cls, descriptor: ModelDescriptor) -> ChatModelLike:
        key = cls._model_key(descriptor)
        cached = _CHAIN_CACHE.get(key)
        if cached is not None:
            return cached
        try:
            from langchain_core.output_parsers import StrOutputParser
        except ImportError as exc:
            raise ProviderInvocationError(
                "langchain-core is required for the LangChain chat provider"
            ) from exc
        chain = cast("ChatModelLike", cls._raw_model(descriptor) | StrOutputParser())
        _CHAIN_CACHE[key] = chain
        return chain

    def _stream_huggingface(
        self, descriptor: ModelDescriptor, prompt_text: str
    ) -> Iterator[str]:
        """Stream real tokens from a local HuggingFace pipeline as they are produced.

        Generation runs in a background thread feeding a ``TextIteratorStreamer`` so
        each decoded token is yielded the instant the model emits it. If the raw
        pipeline cannot be reached, it degrades to a single full-text generation so
        the answer is never lost.
        """
        model = self._raw_model(descriptor)
        hf_pipeline = getattr(getattr(model, "llm", None), "pipeline", None)
        hf_model = getattr(hf_pipeline, "model", None)
        tokenizer = getattr(hf_pipeline, "tokenizer", None)
        if hf_model is None or tokenizer is None:
            yield from self._generate_fragment(descriptor, prompt_text)
            return
        try:
            import threading

            from transformers import TextIteratorStreamer
        except ImportError as exc:
            raise ProviderInvocationError(str(exc)) from exc

        messages: list[dict[str, str]] = []
        if descriptor.system_prompt:
            messages.append({"role": "system", "content": descriptor.system_prompt})
        messages.append({"role": "user", "content": prompt_text})
        try:
            encoded = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
                return_dict=True,
            )
        except Exception:  # noqa: BLE001 - tokenizer without a usable chat template
            encoded = tokenizer(prompt_text, return_tensors="pt")
        encoded = encoded.to(hf_model.device)
        streamer: Any = TextIteratorStreamer(
            tokenizer, skip_prompt=True, skip_special_tokens=True
        )
        generation_kwargs: dict[str, Any] = {
            "streamer": streamer,
            "max_new_tokens": descriptor.max_output_tokens or 512,
            "do_sample": descriptor.temperature > 0.0,
        }
        if descriptor.temperature > 0.0:
            generation_kwargs["temperature"] = descriptor.temperature
            # top_p/top_k narrow the sampling pool to the most relevant tokens;
            # they only apply when sampling is on. Skip neutral values.
            if 0.0 < descriptor.top_p < 1.0:
                generation_kwargs["top_p"] = descriptor.top_p
            if descriptor.top_k > 0:
                generation_kwargs["top_k"] = descriptor.top_k
        errors: list[Exception] = []

        def _generate() -> None:
            try:
                hf_model.generate(**encoded, **generation_kwargs)
            except Exception as exc:  # noqa: BLE001 - surfaced after the stream drains
                errors.append(exc)
            finally:
                # Always release the consumer: on a generation error the model never
                # signals end-of-stream, which would otherwise deadlock the
                # ``for text in streamer`` iteration forever.
                streamer.end()

        thread = threading.Thread(target=_generate, daemon=True)
        thread.start()
        try:
            for text in streamer:
                if text:
                    yield text
        finally:
            thread.join()
        if errors:
            raise ProviderInvocationError(str(errors[0])) from errors[0]

    def _generate_fragment(
        self, descriptor: ModelDescriptor, prompt_text: str
    ) -> Iterator[str]:
        """Yield the full generation as one fragment (non-streaming fallback)."""
        chain = self._chain(descriptor)
        try:
            output = chain.invoke(
                self._model_input(descriptor, prompt_text), config=self._invoke_config()
            )
        except Exception as exc:  # noqa: BLE001 - isolate any provider failure
            raise ProviderInvocationError(str(exc)) from exc
        text = str(output)
        if text:
            yield text


def default_provider_registry() -> dict[str, ChatModelProvider]:
    """Return the provider registry with the deterministic offline default."""
    return {"deterministic": DeterministicEchoProvider()}


def provider_registry_from_settings(
    runtime: str, *, callbacks: list[Any] | None = None
) -> dict[str, ChatModelProvider]:
    """Return the provider registry, adding the LangChain provider when selected.

    ``callbacks`` are attached to the LangChain provider's chain runs so LLM
    generations are traced (Langfuse) when observability is enabled.
    """
    registry = default_provider_registry()
    if runtime == "langchain":
        registry["langchain"] = LangChainChatProvider(callbacks=callbacks)
    return registry
