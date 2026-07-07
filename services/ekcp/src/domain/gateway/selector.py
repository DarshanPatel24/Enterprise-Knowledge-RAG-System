"""Model selector: deterministic, observable model routing (handbook 14.8-14.9).

Selects a primary model and an ordered fallback chain from the registry based on
the requirements and the configured routing strategy. Selection is deterministic
and governance-aware: only servable (approved or production) models are eligible.
"""

from __future__ import annotations

from domain.gateway.errors import GatewayError, GatewayErrorType
from domain.gateway.models import (
    ModelDescriptor,
    ModelRequirements,
    RoutingStrategy,
)
from domain.gateway.registry import ModelRegistry


class ModelSelector:
    """Select a model and fallback chain deterministically from the registry."""

    def __init__(
        self, *, strategy: RoutingStrategy, require_approved: bool = True
    ) -> None:
        self._strategy = strategy
        self._require_approved = require_approved

    def select(
        self,
        registry: ModelRegistry,
        requirements: ModelRequirements,
        *,
        preferred_model_id: str | None = None,
    ) -> list[ModelDescriptor]:
        """Return the ordered candidate chain (primary first) for a request."""
        candidates = [
            model
            for model in registry.all()
            if self._eligible(model, requirements)
        ]
        if not candidates:
            raise GatewayError(
                GatewayErrorType.MODEL_UNAVAILABLE,
                "no model satisfies the request requirements",
            )
        candidates.sort(key=self._sort_key)
        if preferred_model_id is not None:
            candidates.sort(key=lambda m: 0 if m.model_id == preferred_model_id else 1)
        return candidates

    def _eligible(
        self, model: ModelDescriptor, requirements: ModelRequirements
    ) -> bool:
        if self._require_approved and not model.is_servable:
            return False
        if not requirements.required_modalities <= model.modalities:
            return False
        if requirements.required_context_window > model.context_window:
            return False
        if (
            requirements.max_latency_ms > 0.0
            and model.avg_latency_ms > requirements.max_latency_ms
        ):
            return False
        return not (
            requirements.cost_ceiling > 0.0
            and self._unit_cost(model) > requirements.cost_ceiling
        )

    def _sort_key(self, model: ModelDescriptor) -> tuple[float, float, str]:
        if self._strategy is RoutingStrategy.COST:
            return (self._unit_cost(model), model.avg_latency_ms, model.model_id)
        if self._strategy is RoutingStrategy.LATENCY:
            return (model.avg_latency_ms, self._unit_cost(model), model.model_id)
        if self._strategy is RoutingStrategy.QUALITY:
            return (-model.quality_score, model.avg_latency_ms, model.model_id)
        # capability, policy, and hybrid balance quality then latency then cost.
        return (-model.quality_score, model.avg_latency_ms, model.model_id)

    @staticmethod
    def _unit_cost(model: ModelDescriptor) -> float:
        return (
            model.cost_profile.prompt_cost_per_1k
            + model.cost_profile.completion_cost_per_1k
        )
