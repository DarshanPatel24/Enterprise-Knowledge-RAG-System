"""Governance guard: the policy enforcement point (handbook 12.2, 12.12).

The guard is the single facade the platform uses to enforce governance before a
governed operation runs: it authorizes against the policy engine, records the
decision to the audit trail (allow or deny), masks PII from outbound responses,
and packages the security context for downstream propagation. Governance is a
prerequisite: denied operations raise before any effect.
"""

from __future__ import annotations

from contracts.enums import ClassificationClearance
from domain.governance.audit import (
    AuditAction,
    AuditResult,
    AuditSink,
    build_audit_record,
)
from domain.governance.authorization import (
    AccessRequest,
    Permission,
    PolicyDecision,
    PolicyEngine,
)
from domain.governance.identity import Principal
from domain.governance.masking import Masker
from domain.governance.policy import GovernancePolicy
from domain.governance.propagation import SecurityContextPropagator

# Map a permission to its (granted, denied) audit actions.
_ACTION_MAP: dict[Permission, tuple[AuditAction, AuditAction]] = {
    Permission.INVOKE_AGENT: (AuditAction.AGENT_INVOKED, AuditAction.AGENT_DENIED),
    Permission.INVOKE_TOOL: (AuditAction.TOOL_INVOKED, AuditAction.TOOL_DENIED),
    Permission.READ_MEMORY: (AuditAction.MEMORY_READ, AuditAction.MEMORY_DENIED),
    Permission.WRITE_MEMORY: (AuditAction.MEMORY_WRITE, AuditAction.MEMORY_DENIED),
    Permission.GENERATE_RESPONSE: (
        AuditAction.RESPONSE_GENERATED,
        AuditAction.POLICY_DENIED,
    ),
    Permission.RETRIEVE_CONTEXT: (
        AuditAction.CONTEXT_RETRIEVED,
        AuditAction.POLICY_DENIED,
    ),
}


class GovernanceGuard:
    """Enforce policy, audit decisions, mask responses, and propagate context."""

    def __init__(
        self,
        engine: PolicyEngine,
        sink: AuditSink,
        masker: Masker,
        propagator: SecurityContextPropagator,
        *,
        policy: GovernancePolicy,
    ) -> None:
        self._engine = engine
        self._sink = sink
        self._masker = masker
        self._propagator = propagator
        self._policy = policy

    @property
    def audit_sink(self) -> AuditSink:
        """Return the audit sink for compliance evidence retrieval."""
        return self._sink

    def evaluate(self, request: AccessRequest) -> PolicyDecision:
        """Evaluate a policy decision without auditing or raising (read-only)."""
        return self._engine.evaluate(request)

    def authorize(
        self,
        principal: Principal,
        permission: Permission,
        resource: str,
        *,
        classification: ClassificationClearance = ClassificationClearance.INTERNAL,
    ) -> PolicyDecision:
        """Authorize a governed operation, auditing the decision and raising on deny."""
        request = AccessRequest(
            principal=principal,
            permission=permission,
            resource=resource,
            resource_classification=classification,
        )
        decision = self._engine.evaluate(request)
        granted_action, denied_action = _ACTION_MAP.get(
            permission, (AuditAction.POLICY_GRANTED, AuditAction.POLICY_DENIED)
        )
        self._audit(
            actor=principal.user_id,
            action=granted_action if decision.allowed else denied_action,
            result=AuditResult.ALLOWED if decision.allowed else AuditResult.DENIED,
            resource=resource,
            tenant_id=principal.tenant_id,
            reason=decision.reason,
        )
        if not decision.allowed:
            return self._engine.authorize(request)
        return decision

    def mask_response(
        self, text: str, *, actor: str, tenant_id: str, resource: str = "response"
    ) -> tuple[str, int]:
        """Mask PII from an outbound response, auditing when redactions occur."""
        masked, count = self._masker.mask_text(text)
        if count > 0:
            self._audit(
                actor=actor,
                action=AuditAction.RESPONSE_FILTERED,
                result=AuditResult.ALLOWED,
                resource=resource,
                tenant_id=tenant_id,
                reason=f"redactions={count}",
                detail={"redactions": str(count)},
            )
        return masked, count

    def propagate_security_context(
        self,
        principal: Principal,
        *,
        target_classification: ClassificationClearance | None = None,
        resource: str = "ekre",
    ) -> dict[str, str]:
        """Package the security context for a downstream EKRE request and audit it."""
        payload = self._propagator.propagate(
            principal, target_classification=target_classification
        )
        self._audit(
            actor=principal.user_id,
            action=AuditAction.SECURITY_CONTEXT_PROPAGATED,
            result=AuditResult.ALLOWED,
            resource=resource,
            tenant_id=principal.tenant_id,
            reason=f"clearance={payload['classification_clearance']}",
        )
        return payload

    def _audit(
        self,
        *,
        actor: str,
        action: AuditAction,
        result: AuditResult,
        resource: str,
        tenant_id: str,
        reason: str = "",
        detail: dict[str, str] | None = None,
    ) -> None:
        if not self._policy.enable_audit:
            return
        self._sink.record(
            build_audit_record(
                actor=actor,
                action=action,
                result=result,
                resource=resource,
                tenant_id=tenant_id,
                reason=reason,
                policy_version=self._policy.policy_version,
                detail=detail,
            )
        )
