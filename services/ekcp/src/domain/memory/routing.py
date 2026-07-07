"""Personal versus organizational routing for memory (handbook Chapter 8, 10.X).

Reuses the intent scope from the S1 intent gate to decide whether a query should
draw on EKCP memory (personal history and preferences), enterprise knowledge via
EKRE (organizational), or both. Memory owns the personal side of this split.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from domain.intent import IntentScope, RoutingTarget


class MemoryRoutingDecision(BaseModel):
    """Immutable decision on which sources a query should draw from."""

    model_config = ConfigDict(frozen=True)

    use_memory: bool
    use_knowledge: bool
    primary_target: RoutingTarget


def route_for_scope(scope: IntentScope) -> MemoryRoutingDecision:
    """Return the routing decision for an intent scope."""
    if scope is IntentScope.PERSONAL:
        return MemoryRoutingDecision(
            use_memory=True, use_knowledge=False, primary_target=RoutingTarget.MEMORY
        )
    if scope is IntentScope.ORGANIZATIONAL:
        return MemoryRoutingDecision(
            use_memory=False, use_knowledge=True, primary_target=RoutingTarget.KNOWLEDGE
        )
    if scope is IntentScope.MIXED:
        return MemoryRoutingDecision(
            use_memory=True, use_knowledge=True, primary_target=RoutingTarget.KNOWLEDGE
        )
    return MemoryRoutingDecision(
        use_memory=False, use_knowledge=False, primary_target=RoutingTarget.NONE
    )
