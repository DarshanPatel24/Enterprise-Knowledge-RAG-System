"""RBAC + ABAC authorization: the policy engine (handbook 12).

Evaluates a governed operation against the principal's role permissions (RBAC)
and clearance versus resource classification (ABAC), returning an immutable
:class:`PolicyDecision`. ``authorize`` raises on denial so governance is an
execution prerequisite, not an afterthought.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from contracts.enums import ClassificationClearance
from domain.governance.classification import is_cleared
from domain.governance.errors import GovernanceError, GovernanceErrorType
from domain.governance.identity import Principal, Role


class Permission(StrEnum):
    """Fine-grained governed operations (handbook 12)."""

    INVOKE_TOOL = "invoke_tool"
    READ_MEMORY = "read_memory"
    WRITE_MEMORY = "write_memory"
    INVOKE_AGENT = "invoke_agent"
    GENERATE_RESPONSE = "generate_response"
    RETRIEVE_CONTEXT = "retrieve_context"
    MODIFY_CONTEXT = "modify_context"
    APPROVE_EXECUTION = "approve_execution"
    MANAGE_POLICY = "manage_policy"


_ALL_PERMISSIONS: frozenset[Permission] = frozenset(Permission)

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: _ALL_PERMISSIONS,
    Role.POWER_USER: frozenset(
        {
            Permission.INVOKE_TOOL,
            Permission.READ_MEMORY,
            Permission.WRITE_MEMORY,
            Permission.INVOKE_AGENT,
            Permission.GENERATE_RESPONSE,
            Permission.RETRIEVE_CONTEXT,
            Permission.MODIFY_CONTEXT,
            Permission.APPROVE_EXECUTION,
        }
    ),
    Role.USER: frozenset(
        {
            Permission.GENERATE_RESPONSE,
            Permission.RETRIEVE_CONTEXT,
            Permission.READ_MEMORY,
        }
    ),
    Role.SERVICE: frozenset(
        {
            Permission.INVOKE_TOOL,
            Permission.INVOKE_AGENT,
            Permission.RETRIEVE_CONTEXT,
            Permission.GENERATE_RESPONSE,
        }
    ),
    Role.AGENT: frozenset(
        {Permission.INVOKE_TOOL, Permission.RETRIEVE_CONTEXT}
    ),
}


class AccessRequest(BaseModel):
    """A request to perform ``permission`` on a classified resource."""

    model_config = ConfigDict(frozen=True)

    principal: Principal
    permission: Permission
    resource: str
    resource_classification: ClassificationClearance = ClassificationClearance.INTERNAL


class PolicyDecision(BaseModel):
    """Immutable policy evaluation outcome (handbook 12.12)."""

    model_config = ConfigDict(frozen=True)

    allowed: bool
    reason: str
    policy_version: str = "v1"


def granted_permissions(principal: Principal) -> frozenset[Permission]:
    """Return the union of permissions granted by a principal's roles."""
    granted: set[Permission] = set()
    for role in principal.roles:
        granted |= ROLE_PERMISSIONS.get(role, frozenset())
    return frozenset(granted)


class PolicyEngine:
    """Evaluate governed operations against RBAC roles and ABAC clearance."""

    def __init__(
        self, *, enforce_authorization: bool = True, policy_version: str = "v1"
    ) -> None:
        self._enforce = enforce_authorization
        self._policy_version = policy_version

    def evaluate(self, request: AccessRequest) -> PolicyDecision:
        """Return an allow/deny decision for a governed operation."""
        if not self._enforce:
            return PolicyDecision(
                allowed=True,
                reason="authorization_disabled",
                policy_version=self._policy_version,
            )
        if request.permission not in granted_permissions(request.principal):
            return PolicyDecision(
                allowed=False,
                reason=f"role_missing_permission:{request.permission.value}",
                policy_version=self._policy_version,
            )
        if not is_cleared(
            request.principal.clearance, request.resource_classification
        ):
            return PolicyDecision(
                allowed=False,
                reason=(
                    "insufficient_clearance:"
                    f"{request.principal.clearance.value}"
                    f"<{request.resource_classification.value}"
                ),
                policy_version=self._policy_version,
            )
        return PolicyDecision(
            allowed=True, reason="granted", policy_version=self._policy_version
        )

    def authorize(self, request: AccessRequest) -> PolicyDecision:
        """Evaluate ``request`` and raise :class:`GovernanceError` on denial."""
        decision = self.evaluate(request)
        if not decision.allowed:
            error_type = (
                GovernanceErrorType.CLEARANCE_VIOLATION
                if decision.reason.startswith("insufficient_clearance")
                else GovernanceErrorType.UNAUTHORIZED
            )
            raise GovernanceError(error_type, f"access denied: {decision.reason}")
        return decision
