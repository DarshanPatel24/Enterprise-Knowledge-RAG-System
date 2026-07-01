"""Policy-driven embedding model selection (handbook 10.9, ADR-024)."""

from __future__ import annotations

from domain.embedding.model_registry import EmbeddingModelRegistry, UnknownModelError
from domain.embedding.models import EmbeddingModelSpec, ModelStatus
from domain.embedding.policy import EmbeddingPolicy


class ModelSelectionError(RuntimeError):
    """Raised when no usable model can be selected for a document."""


_USABLE_STATUSES = frozenset({ModelStatus.ACTIVE, ModelStatus.APPROVED})


class ModelSelector:
    """Selects an approved embedding model based on policy and context.

    The default selection returns the policy default model. The signature
    accepts document language and classification so selection can be extended
    to language- or classification-specific models without changing callers
    (handbook 10.9).
    """

    def __init__(self, registry: EmbeddingModelRegistry) -> None:
        self._registry = registry

    def select(
        self, policy: EmbeddingPolicy, *, language: str, classification: str
    ) -> EmbeddingModelSpec:
        """Return an approved model spec for the given document context."""
        try:
            model = self._registry.get(policy.default_model)
        except UnknownModelError as exc:
            raise ModelSelectionError(
                f"model {policy.default_model!r} is not in the approved registry"
            ) from exc
        if model.status not in _USABLE_STATUSES:
            raise ModelSelectionError(
                f"model {model.name!r} has non-usable status {model.status.value!r}"
            )
        return model
