"""Token and cost governance for the model gateway (handbook 14.14, 14.17).

Token accounting is mandatory. The budget guard enforces per-request token and
cost ceilings before and after generation, and the ledger accumulates
per-tenant token and cost totals for enterprise cost governance. Guards are
deterministic and dependency-free.
"""

from __future__ import annotations

from domain.gateway.errors import GatewayError, GatewayErrorType
from domain.gateway.models import ModelDescriptor, TokenUsage


class BudgetLedger:
    """Append-only per-tenant token and cost accumulator."""

    def __init__(self) -> None:
        self._tokens: dict[str, int] = {}
        self._cost: dict[str, float] = {}

    def record(self, tenant_id: str, *, tokens: int, cost: float) -> None:
        """Accumulate token and cost totals for a tenant."""
        self._tokens[tenant_id] = self._tokens.get(tenant_id, 0) + tokens
        self._cost[tenant_id] = round(self._cost.get(tenant_id, 0.0) + cost, 6)

    def tokens_for(self, tenant_id: str) -> int:
        """Return the accumulated token total for a tenant."""
        return self._tokens.get(tenant_id, 0)

    def cost_for(self, tenant_id: str) -> float:
        """Return the accumulated cost total for a tenant."""
        return self._cost.get(tenant_id, 0.0)


class BudgetGuard:
    """Enforce per-request token and cost ceilings (0 means unlimited)."""

    def __init__(self, *, max_tokens_per_request: int, max_cost_per_request: float) -> None:
        self._max_tokens = max_tokens_per_request
        self._max_cost = max_cost_per_request

    def check_prompt_fits(
        self, descriptor: ModelDescriptor, prompt_tokens: int
    ) -> None:
        """Raise ``TOKEN_LIMIT_EXCEEDED`` when the prompt exceeds the context window."""
        if prompt_tokens > descriptor.context_window:
            raise GatewayError(
                GatewayErrorType.TOKEN_LIMIT_EXCEEDED,
                (
                    f"prompt {prompt_tokens} tokens exceeds model context window "
                    f"{descriptor.context_window}"
                ),
            )

    def check_usage(self, usage: TokenUsage, cost: float) -> None:
        """Raise ``BUDGET_EXCEEDED`` when usage or cost exceeds the request ceiling."""
        if self._max_tokens > 0 and usage.total_tokens > self._max_tokens:
            raise GatewayError(
                GatewayErrorType.BUDGET_EXCEEDED,
                (
                    f"invocation used {usage.total_tokens} tokens, over the per-request "
                    f"limit of {self._max_tokens}"
                ),
            )
        if self._max_cost > 0.0 and cost > self._max_cost:
            raise GatewayError(
                GatewayErrorType.BUDGET_EXCEEDED,
                f"invocation cost {cost} over the per-request limit of {self._max_cost}",
            )
