"""LLM Gateway: the single boundary for all model invocations (handbook 14.20).

The gateway selects a model, enforces token and cost governance, invokes the
provider adapter, applies automatic fallback across the candidate chain, and
normalizes the response into the Model Invocation Contract output. No platform
component ever calls a model provider directly. Invocation is deterministic
given a deterministic provider, keeping the offline path reproducible.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from time import perf_counter

from domain.context.tokens import estimate_tokens
from domain.gateway.errors import (
    GatewayError,
    GatewayErrorType,
    ProviderInvocationError,
)
from domain.gateway.governance import BudgetGuard, BudgetLedger
from domain.gateway.models import (
    GatewayStreamEvent,
    GenerationRequest,
    ModelDescriptor,
    NormalizedResponse,
    StreamEventType,
    TokenUsage,
)
from domain.gateway.policy import GatewayPolicy
from domain.gateway.provider import ChatModelProvider
from domain.gateway.registry import ModelRegistry
from domain.gateway.selector import ModelSelector
from domain.observability import get_logger

logger = get_logger("ekcp.gateway")


class LLMGateway:
    """Model-agnostic gateway: route, govern, invoke, fall back, normalize."""

    def __init__(
        self,
        *,
        registry: ModelRegistry,
        selector: ModelSelector,
        providers: dict[str, ChatModelProvider],
        policy: GatewayPolicy,
        ledger: BudgetLedger | None = None,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        self._registry = registry
        self._selector = selector
        self._providers = providers
        self._policy = policy
        self._ledger = ledger or BudgetLedger()
        self._guard = BudgetGuard(
            max_tokens_per_request=policy.max_tokens_per_request,
            max_cost_per_request=policy.max_cost_per_request,
        )
        self._clock = clock

    @property
    def ledger(self) -> BudgetLedger:
        """Return the budget ledger accumulating per-tenant usage."""
        return self._ledger

    def invoke(self, request: GenerationRequest) -> NormalizedResponse:
        """Route, govern, and invoke a model, returning the normalized response."""
        prompt_tokens = self._tokens(request.prompt_text)
        candidates = self._candidates(request, prompt_tokens)

        last_error: ProviderInvocationError | None = None
        for index, descriptor in enumerate(candidates):
            provider = self._providers.get(descriptor.runtime)
            if provider is None:
                continue
            try:
                start = self._clock()
                output_text = provider.generate(
                    descriptor, request.prompt_text, request.constraints
                )
                latency_ms = (self._clock() - start) * 1000.0
            except ProviderInvocationError as exc:
                last_error = exc
                logger.warning(
                    "gateway_provider_failed",
                    extra={"model_id": descriptor.model_id, "error": exc.message},
                )
                if not self._policy.enable_fallback:
                    raise GatewayError(
                        GatewayErrorType.PROVIDER_FAILED, exc.message
                    ) from exc
                continue

            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=self._tokens(output_text),
            )
            cost = descriptor.cost_profile.estimate(
                usage.prompt_tokens, usage.completion_tokens
            )
            self._guard.check_usage(usage, cost)
            self._ledger.record(
                request.tenant_id, tokens=usage.total_tokens, cost=cost
            )
            logger.info(
                "gateway_invocation",
                extra={
                    "model_id": descriptor.model_id,
                    "latency_ms": round(latency_ms, 3),
                    "total_tokens": usage.total_tokens,
                    "cost_estimate": cost,
                    "fallback_used": index > 0,
                },
            )
            return NormalizedResponse(
                model_id=descriptor.model_id,
                provider=descriptor.provider,
                output_text=output_text,
                response_type=request.constraints.response_type,
                token_usage=usage,
                latency_ms=round(latency_ms, 3),
                cost_estimate=cost,
                fallback_used=index > 0,
                provider_metadata={"runtime": descriptor.runtime},
            )

        message = last_error.message if last_error else "no provider produced a response"
        raise GatewayError(GatewayErrorType.FALLBACK_EXHAUSTED, message)

    def stream(self, request: GenerationRequest) -> Iterator[GatewayStreamEvent]:
        """Stream a model response as token events followed by a done event.

        Falls back to the next candidate model when a provider fails before any
        token is emitted (e.g. the configured chat model cannot be loaded), so a
        model-load failure degrades gracefully instead of crashing the stream.
        Once tokens have been emitted a mid-stream failure surfaces as an error
        event because partial output cannot be safely restarted.
        """
        prompt_tokens = self._tokens(request.prompt_text)
        candidates = self._candidates(request, prompt_tokens)

        last_error: ProviderInvocationError | None = None
        for descriptor in candidates:
            provider = self._providers.get(descriptor.runtime)
            if provider is None:
                continue

            fragments: list[str] = []
            try:
                for fragment in provider.stream(
                    descriptor, request.prompt_text, request.constraints
                ):
                    fragments.append(fragment)
                    yield GatewayStreamEvent(
                        event_type=StreamEventType.TOKEN,
                        text=fragment,
                        model_id=descriptor.model_id,
                    )
            except ProviderInvocationError as exc:
                last_error = exc
                logger.warning(
                    "gateway_stream_provider_failed",
                    extra={"model_id": descriptor.model_id, "error": exc.message},
                )
                if fragments or not self._policy.enable_fallback:
                    yield GatewayStreamEvent(
                        event_type=StreamEventType.ERROR,
                        model_id=descriptor.model_id,
                        error_message=exc.message,
                    )
                    return
                continue

            output_text = "".join(fragments)
            usage = TokenUsage(
                prompt_tokens=prompt_tokens, completion_tokens=self._tokens(output_text)
            )
            cost = descriptor.cost_profile.estimate(
                usage.prompt_tokens, usage.completion_tokens
            )
            self._ledger.record(request.tenant_id, tokens=usage.total_tokens, cost=cost)
            yield GatewayStreamEvent(
                event_type=StreamEventType.DONE,
                model_id=descriptor.model_id,
                finish_reason="stop",
                token_usage=usage,
                cost_estimate=cost,
            )
            return

        message = (
            last_error.message if last_error else "no provider produced a response"
        )
        yield GatewayStreamEvent(
            event_type=StreamEventType.ERROR, error_message=message
        )

    def _candidates(
        self, request: GenerationRequest, prompt_tokens: int
    ) -> list[ModelDescriptor]:
        preferred = request.model_id or self._policy.default_model_id
        chain = self._selector.select(
            self._registry, request.requirements, preferred_model_id=preferred
        )
        fitting = [m for m in chain if prompt_tokens <= m.context_window]
        if not fitting:
            raise GatewayError(
                GatewayErrorType.TOKEN_LIMIT_EXCEEDED,
                f"prompt {prompt_tokens} tokens exceeds every candidate context window",
            )
        return fitting if self._policy.enable_fallback else fitting[:1]

    def _tokens(self, text: str) -> int:
        return estimate_tokens(text, chars_per_token=self._policy.chars_per_token)
