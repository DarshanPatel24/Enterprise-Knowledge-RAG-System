"""Per-stage governance enforcement (handbook 17.11, 17.14).

Binds authorization, classification propagation, and audit logging into a single
gate invoked before each ingestion stage. Denials raise :class:`SecurityError`
and are recorded to the audit trail; approvals propagate the document
classification forward without downgrade.
"""

from __future__ import annotations

from domain.observability import get_correlation_id, get_tenant_id
from domain.orchestration.state import StageName
from domain.security.audit import (
    AuditAction,
    AuditRecord,
    AuditResult,
    AuditSink,
)
from domain.security.authorization import (
    AccessRequest,
    Permission,
    PolicyEngine,
)
from domain.security.classification import Classification, ensure_no_downgrade
from domain.security.errors import SecurityError, SecurityErrorType
from domain.security.identity import Principal
from domain.security.policy import SecurityPolicy

# Maps each ingestion stage to the permission that guards it (handbook 17.14).
STAGE_PERMISSIONS: dict[StageName, Permission] = {
    StageName.TRANSFORM: Permission.TRANSFORM,
    StageName.INTELLIGENCE: Permission.ENRICH,
    StageName.CHUNK: Permission.CHUNK,
    StageName.EMBED: Permission.EMBED,
    StageName.PUBLISH: Permission.PUBLISH,
}


class StagePolicyGuard:
    """Authorizes, classifies, and audits each per-stage transition."""

    def __init__(
        self,
        policy: SecurityPolicy,
        engine: PolicyEngine,
        audit_sink: AuditSink,
    ) -> None:
        self._policy = policy
        self._engine = engine
        self._audit_sink = audit_sink

    def authorize_stage(
        self,
        principal: Principal,
        stage: StageName,
        classification: Classification,
        *,
        resource: str,
    ) -> None:
        """Enforce authorization for ``stage`` and audit the decision.

        Raises :class:`SecurityError` when the principal lacks the stage
        permission or clearance for the resource classification.
        """
        request = AccessRequest(
            principal=principal,
            permission=STAGE_PERMISSIONS[stage],
            resource_classification=classification,
        )
        decision = self._engine.evaluate(request)
        self._audit(
            actor=principal.subject,
            action=(
                AuditAction.STAGE_AUTHORIZED
                if decision.allowed
                else AuditAction.STAGE_DENIED
            ),
            resource=resource,
            result=AuditResult.ALLOW if decision.allowed else AuditResult.DENY,
            detail=f"stage={stage.value};{decision.reason}",
        )
        if not decision.allowed:
            raise SecurityError(
                SecurityErrorType.UNAUTHORIZED,
                f"Stage {stage.value} denied: {decision.reason}",
            )

    def propagate_classification(
        self,
        source: Classification,
        target: Classification,
        *,
        actor: str,
        resource: str,
    ) -> Classification:
        """Enforce monotonic classification propagation and audit it."""
        try:
            result = ensure_no_downgrade(
                source,
                target,
                allow_downgrade=self._policy.allow_classification_downgrade,
            )
        except SecurityError:
            self._audit(
                actor=actor,
                action=AuditAction.CLASSIFICATION_VIOLATION,
                resource=resource,
                result=AuditResult.DENY,
                detail=f"source={source.value};target={target.value}",
            )
            raise
        self._audit(
            actor=actor,
            action=AuditAction.CLASSIFICATION_PROPAGATED,
            resource=resource,
            result=AuditResult.ALLOW,
            detail=f"classification={result.value}",
        )
        return result

    def _audit(
        self,
        *,
        actor: str,
        action: AuditAction,
        resource: str,
        result: AuditResult,
        detail: str,
    ) -> None:
        """Append an audit record when auditing is enabled."""
        if not self._policy.enable_audit:
            return
        self._audit_sink.record(
            AuditRecord(
                actor=actor,
                action=action,
                resource=resource,
                result=result,
                tenant_id=get_tenant_id(),
                correlation_id=get_correlation_id(),
                detail=detail,
            )
        )
