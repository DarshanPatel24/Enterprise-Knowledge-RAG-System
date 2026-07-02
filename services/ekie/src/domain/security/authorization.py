"""RBAC + ABAC authorization and access decisions (handbook 17.5-17.6).

Authorization combines role-based permissions with attribute-based clearance
checks. A decision is reached by: role evaluation (RBAC) -> clearance evaluation
(ABAC) -> allow or deny.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from domain.security.classification import Classification, is_cleared
from domain.security.errors import SecurityError, SecurityErrorType
from domain.security.identity import Principal, Role
from domain.security.policy import SecurityPolicy


class Permission(StrEnum):
    """Fine-grained pipeline permissions guarded by authorization."""

    INGEST_DOCUMENT = "ingest_document"
    TRANSFORM = "transform"
    ENRICH = "enrich"
    CHUNK = "chunk"
    EMBED = "embed"
    PUBLISH = "publish"
    READ_WORKFLOW = "read_workflow"
    MANAGE_PLUGINS = "manage_plugins"


# Role -> granted permissions (handbook 17.5). Admin is granted every permission.
_ALL_PERMISSIONS: frozenset[Permission] = frozenset(Permission)

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: _ALL_PERMISSIONS,
    Role.ENGINEER: frozenset(
        {
            Permission.INGEST_DOCUMENT,
            Permission.TRANSFORM,
            Permission.ENRICH,
            Permission.CHUNK,
            Permission.EMBED,
            Permission.PUBLISH,
            Permission.READ_WORKFLOW,
            Permission.MANAGE_PLUGINS,
        }
    ),
    Role.DATA_SCIENTIST: frozenset(
        {
            Permission.CHUNK,
            Permission.EMBED,
            Permission.PUBLISH,
            Permission.READ_WORKFLOW,
        }
    ),
    Role.VIEWER: frozenset({Permission.READ_WORKFLOW}),
    Role.SERVICE_WORKER: frozenset(
        {
            Permission.INGEST_DOCUMENT,
            Permission.TRANSFORM,
            Permission.ENRICH,
            Permission.CHUNK,
            Permission.EMBED,
            Permission.PUBLISH,
            Permission.READ_WORKFLOW,
        }
    ),
}


class AccessRequest(BaseModel):
    """A request to perform ``permission`` on a classified resource."""

    model_config = {"frozen": True}

    principal: Principal
    permission: Permission
    resource_classification: Classification


class AccessDecision(BaseModel):
    """The outcome of evaluating an :class:`AccessRequest`."""

    model_config = {"frozen": True}

    allowed: bool
    reason: str


def _granted_permissions(principal: Principal) -> frozenset[Permission]:
    """Return the union of permissions granted by a principal's roles."""
    granted: set[Permission] = set()
    for role in principal.roles:
        granted |= ROLE_PERMISSIONS.get(role, frozenset())
    return frozenset(granted)


class PolicyEngine:
    """Evaluates access requests against RBAC roles and ABAC clearance."""

    def __init__(self, policy: SecurityPolicy) -> None:
        self._policy = policy

    def evaluate(self, request: AccessRequest) -> AccessDecision:
        """Return an allow/deny decision for ``request``."""
        if not self._policy.enforce_authorization:
            return AccessDecision(allowed=True, reason="authorization_disabled")

        if request.permission not in _granted_permissions(request.principal):
            return AccessDecision(
                allowed=False,
                reason=f"role_missing_permission:{request.permission.value}",
            )

        if not is_cleared(
            request.principal.clearance, request.resource_classification
        ):
            return AccessDecision(
                allowed=False,
                reason=(
                    "insufficient_clearance:"
                    f"{request.principal.clearance.value}"
                    f"<{request.resource_classification.value}"
                ),
            )

        return AccessDecision(allowed=True, reason="granted")

    def authorize(self, request: AccessRequest) -> AccessDecision:
        """Evaluate ``request`` and raise :class:`SecurityError` on denial."""
        decision = self.evaluate(request)
        if not decision.allowed:
            raise SecurityError(
                SecurityErrorType.UNAUTHORIZED,
                f"Access denied: {decision.reason}",
            )
        return decision
