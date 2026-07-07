"""Model registry: the authoritative catalog of registered models.

Only models in an approved lifecycle state serve production workloads
(handbook 14.16). The default registry ships a deterministic offline model so
the gateway runs with no external provider; a configured runtime adds a
LangChain-backed model behind the same registry interface.
"""

from __future__ import annotations

from domain.gateway.errors import GatewayError, GatewayErrorType
from domain.gateway.models import (
    CostProfile,
    Modality,
    ModelDescriptor,
    ModelLifecycleState,
)

DETERMINISTIC_MODEL_ID = "ekcp-echo"


class ModelRegistry:
    """Registry of model descriptors keyed by model id."""

    def __init__(self) -> None:
        self._models: dict[str, ModelDescriptor] = {}

    def register(self, descriptor: ModelDescriptor) -> None:
        """Register (or replace) a model descriptor."""
        self._models[descriptor.model_id] = descriptor

    def get(self, model_id: str) -> ModelDescriptor:
        """Return the descriptor for ``model_id``, or raise ``UNKNOWN_MODEL``."""
        descriptor = self._models.get(model_id)
        if descriptor is None:
            raise GatewayError(
                GatewayErrorType.UNKNOWN_MODEL, f"unknown model {model_id!r}"
            )
        return descriptor

    def list_servable(self) -> tuple[ModelDescriptor, ...]:
        """Return all models eligible to serve production workloads."""
        return tuple(m for m in self._models.values() if m.is_servable)

    def all(self) -> tuple[ModelDescriptor, ...]:
        """Return every registered model descriptor."""
        return tuple(self._models.values())


def deterministic_model() -> ModelDescriptor:
    """Return the deterministic, offline-default model descriptor."""
    return ModelDescriptor(
        model_id=DETERMINISTIC_MODEL_ID,
        provider="deterministic",
        model_name="echo",
        runtime="deterministic",
        modalities=frozenset(
            {Modality.TEXT, Modality.STREAMING, Modality.JSON_OUTPUT}
        ),
        context_window=32000,
        max_output_tokens=4096,
        cost_profile=CostProfile(),
        avg_latency_ms=1.0,
        quality_score=0.5,
        lifecycle_state=ModelLifecycleState.PRODUCTION,
    )


def default_model_registry() -> ModelRegistry:
    """Return a registry containing the deterministic offline-default model."""
    registry = ModelRegistry()
    registry.register(deterministic_model())
    return registry
