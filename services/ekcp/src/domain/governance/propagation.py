"""Security context propagation to EKRE (handbook 12; EKCP-S6-3).

Packages the validated principal into the security context payload injected on
every downstream EKRE retrieval request, enforcing monotonic classification so a
propagated context can never weaken the caller's clearance. The payload matches
the shared ``SecurityContext`` contract consumed by EKRE (wired in EKCP-S7).
"""

from __future__ import annotations

from contracts.enums import ClassificationClearance
from domain.governance.classification import ensure_no_downgrade
from domain.governance.identity import Principal


class SecurityContextPropagator:
    """Build the outbound security context payload for downstream services."""

    def __init__(self, *, allow_downgrade: bool = False) -> None:
        self._allow_downgrade = allow_downgrade

    def propagate(
        self,
        principal: Principal,
        *,
        target_classification: ClassificationClearance | None = None,
    ) -> dict[str, str]:
        """Return the security context payload for a downstream EKRE request."""
        clearance = principal.clearance
        if target_classification is not None:
            clearance = ensure_no_downgrade(
                principal.clearance,
                target_classification,
                allow_downgrade=self._allow_downgrade,
            )
        return {
            "user_id": principal.user_id,
            "tenant_id": principal.tenant_id,
            "classification_clearance": clearance.value,
        }
