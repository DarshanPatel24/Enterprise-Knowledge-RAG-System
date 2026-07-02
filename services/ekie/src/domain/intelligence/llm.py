"""Chat-model factory for optional LLM-based document intelligence (handbook 8.11).

Builds a LangChain chat model bound to a locally hosted Ollama runtime behind a
narrow, engine-owned seam so the core stays model-independent (reference stack:
LangChain for LLM intelligence, Ollama for the model runtime). LangChain is an
optional dependency that is not installed on the default offline path; it is
imported lazily so the deterministic heuristic analyzers remain fully usable and
reproducible unless LLM analysis is explicitly enabled by configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:

    class ChatModel(Protocol):
        """Structural type for the LangChain chat model used by the analyzer."""

        def invoke(self, input: object) -> object: ...


class LlmConfigLike(Protocol):
    """Structural type for the settings needed to build a chat model."""

    llm_provider: str
    llm_model: str
    llm_base_url: str
    llm_temperature: float
    llm_request_timeout_seconds: float


class LlmUnavailableError(RuntimeError):
    """Raised when the configured LLM runtime or its client cannot be used."""


def build_chat_model(config: LlmConfigLike) -> ChatModel:
    """Build a chat model for the configured provider.

    Supports 'ollama' and 'huggingface' providers. Dependency packages are
    imported lazily and translated into :class:`LlmUnavailableError` when
    absent, so the default deterministic path never requires them.
    """
    if config.llm_provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise LlmUnavailableError(
                "langchain-ollama is not installed; install it to enable Ollama analysis"
            ) from exc
        client = ChatOllama(
            model=config.llm_model,
            base_url=config.llm_base_url,
            temperature=config.llm_temperature,
            client_kwargs={"timeout": config.llm_request_timeout_seconds},
        )
        return cast("ChatModel", client)
    elif config.llm_provider == "huggingface":
        try:
            from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
        except ImportError as exc:
            raise LlmUnavailableError(
                "langchain-huggingface is not installed; install it to enable HuggingFace local analysis"
            ) from exc
        
        # HuggingFacePipeline downloads the model and runs it in the Python process
        pipeline = HuggingFacePipeline.from_model_id(
            model_id=config.llm_model,
            task="text-generation",
            pipeline_kwargs={
                "max_new_tokens": 1024,
                "temperature": config.llm_temperature or 0.1,
            },
        )
        client = ChatHuggingFace(llm=pipeline)
        return cast("ChatModel", client)
    else:
        raise LlmUnavailableError(
            f"unsupported llm provider {config.llm_provider!r}; expected 'ollama' or 'huggingface'"
        )
