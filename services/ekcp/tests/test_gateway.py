"""Tests for the model gateway: registry, selector, governance, invoke, stream."""

from __future__ import annotations

import pytest

from config.settings import ModelGatewaySettings
from domain.gateway import (
    CostProfile,
    GatewayError,
    GatewayErrorType,
    GatewayPolicy,
    GenerationRequest,
    LLMGateway,
    Modality,
    ModelLifecycleState,
    ModelRegistry,
    ModelRequirements,
    ModelSelector,
    RoutingStrategy,
    StreamEventType,
    default_model_registry,
    default_provider_registry,
    deterministic_model,
)


def _gateway(
    registry: ModelRegistry | None = None,
    *,
    policy: GatewayPolicy | None = None,
    providers: dict | None = None,
) -> LLMGateway:
    resolved_policy = policy or GatewayPolicy()
    return LLMGateway(
        registry=registry or default_model_registry(),
        selector=ModelSelector(strategy=resolved_policy.routing_strategy),
        providers=providers or default_provider_registry(),
        policy=resolved_policy,
    )


def _request(prompt: str = "User request: what is the policy?") -> GenerationRequest:
    return GenerationRequest(prompt_text=prompt, tenant_id="tenant-a")


def test_registry_only_servable_models_listed() -> None:
    registry = ModelRegistry()
    registry.register(deterministic_model())
    registry.register(
        deterministic_model().model_copy(
            update={"model_id": "draft", "lifecycle_state": ModelLifecycleState.REGISTERED}
        )
    )
    servable = registry.list_servable()
    assert len(servable) == 1
    assert servable[0].model_id == "ekcp-echo"


def test_selector_filters_by_modality() -> None:
    selector = ModelSelector(strategy=RoutingStrategy.HYBRID)
    requirements = ModelRequirements(required_modalities=frozenset({Modality.VISION}))
    with pytest.raises(GatewayError) as exc:
        selector.select(default_model_registry(), requirements)
    assert exc.value.error_type == GatewayErrorType.MODEL_UNAVAILABLE


def test_invoke_returns_normalized_response_with_token_accounting() -> None:
    response = _gateway().invoke(_request())
    assert response.model_id == "ekcp-echo"
    assert response.provider == "deterministic"
    assert response.output_text
    assert response.token_usage.total_tokens > 0
    assert response.fallback_used is False


def test_invoke_deterministic_and_records_ledger() -> None:
    gateway = _gateway()
    first = gateway.invoke(_request())
    second = gateway.invoke(_request())
    assert first.output_text == second.output_text
    assert gateway.ledger.tokens_for("tenant-a") == first.token_usage.total_tokens * 2


def test_cost_estimate_uses_cost_profile() -> None:
    registry = ModelRegistry()
    registry.register(
        deterministic_model().model_copy(
            update={
                "cost_profile": CostProfile(
                    prompt_cost_per_1k=1.0, completion_cost_per_1k=2.0
                )
            }
        )
    )
    response = _gateway(registry).invoke(_request())
    assert response.cost_estimate > 0.0


def test_budget_exceeded_raises() -> None:
    policy = GatewayPolicy(max_tokens_per_request=1)
    with pytest.raises(GatewayError) as exc:
        _gateway(policy=policy).invoke(_request("User request: " + "word " * 50))
    assert exc.value.error_type == GatewayErrorType.BUDGET_EXCEEDED


def test_token_limit_exceeded_when_prompt_over_context_window() -> None:
    registry = ModelRegistry()
    registry.register(deterministic_model().model_copy(update={"context_window": 2}))
    with pytest.raises(GatewayError) as exc:
        _gateway(registry).invoke(_request("User request: " + "word " * 100))
    assert exc.value.error_type == GatewayErrorType.TOKEN_LIMIT_EXCEEDED


def test_stream_yields_tokens_then_done() -> None:
    events = list(_gateway().stream(_request()))
    assert events[0].event_type is StreamEventType.TOKEN
    done = events[-1]
    assert done.event_type is StreamEventType.DONE
    assert done.token_usage is not None
    assert done.token_usage.total_tokens > 0


def test_fallback_used_when_primary_provider_missing() -> None:
    # Two models; the primary runtime has no registered provider, so the gateway
    # falls back to the deterministic model.
    registry = ModelRegistry()
    registry.register(
        deterministic_model().model_copy(
            update={
                "model_id": "primary",
                "runtime": "unavailable",
                "quality_score": 0.9,
            }
        )
    )
    registry.register(deterministic_model())
    response = _gateway(registry).invoke(_request())
    assert response.model_id == "ekcp-echo"


def test_policy_from_settings() -> None:
    settings = ModelGatewaySettings(_env_file=None, routing_strategy="cost")
    policy = GatewayPolicy.from_settings(settings)
    assert policy.routing_strategy is RoutingStrategy.COST
    assert policy.default_model_id == "ekcp-echo"
