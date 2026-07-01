"""Approved embedding model registry (handbook 10.7).

The registry is the governed source of truth for which embedding models may be
used. It is seeded from configuration so approved models are declared without
code changes, supporting auditing and controlled upgrades.
"""

from __future__ import annotations

from domain.embedding.models import DistanceMetric, EmbeddingModelSpec, ModelStatus
from domain.embedding.policy import EmbeddingPolicy


class UnknownModelError(KeyError):
    """Raised when a requested model is not present in the registry."""


class EmbeddingModelRegistry:
    """Holds governed embedding model specifications (handbook 10.7)."""

    def __init__(self, models: list[EmbeddingModelSpec]) -> None:
        self._models = {model.name: model for model in models}

    def get(self, name: str) -> EmbeddingModelSpec:
        """Return the model spec registered under ``name``."""
        model = self._models.get(name)
        if model is None:
            raise UnknownModelError(name)
        return model

    def register(self, model: EmbeddingModelSpec) -> None:
        """Register or override a model specification."""
        self._models[model.name] = model

    def list_models(self) -> list[EmbeddingModelSpec]:
        """Return all registered model specifications."""
        return list(self._models.values())


def default_model_registry(policy: EmbeddingPolicy) -> EmbeddingModelRegistry:
    """Seed a registry with the local model declared by ``policy``."""
    return EmbeddingModelRegistry(
        [
            EmbeddingModelSpec(
                name=policy.default_model,
                provider=policy.provider,
                dimensions=policy.dimension,
                distance_metric=DistanceMetric(policy.distance_metric),
                max_input_tokens=policy.max_input_tokens,
                status=ModelStatus.ACTIVE,
            )
        ]
    )
