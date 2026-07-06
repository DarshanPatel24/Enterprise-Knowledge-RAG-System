"""Hermetic local-first settings for EKIE integration tests.

Integration tests exercise the full ingestion pipeline in-process. They must not
depend on the developer's local ``.env`` file: that file may select real
provider backends (HuggingFace embeddings, a remote Qdrant vector database,
Langfuse tracing, a LangGraph runner) which are not available in a plain test
run and would cause the publish stage to dead-letter.

``local_first_settings`` returns settings that force the deterministic,
dependency-free local pipeline (hash embeddings, in-memory vector provider,
sequential runner, tracing disabled) while ignoring the ``.env`` file and any
leaked ``EKIE_*`` process environment variables for the provider selections that
matter to determinism. Module name is underscore-prefixed so pytest does not
collect it.
"""

from __future__ import annotations

from config.settings import (
    EkieSettings,
    EmbeddingSettings,
    ObservabilitySettings,
    OrchestrationSettings,
    PublishingSettings,
)


def local_first_settings() -> EkieSettings:
    """Return hermetic local-first settings independent of any ``.env`` file."""
    return EkieSettings(
        _env_file=None,
        embedding=EmbeddingSettings(_env_file=None, provider="local"),
        publishing=PublishingSettings(_env_file=None, provider="local"),
        orchestration=OrchestrationSettings(
            _env_file=None, runner="sequential", enable_tracing=False
        ),
        observability=ObservabilitySettings(_env_file=None, langfuse_enabled=False),
    )
