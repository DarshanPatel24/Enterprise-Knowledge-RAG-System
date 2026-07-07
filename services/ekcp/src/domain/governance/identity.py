"""Principal identity: the authenticated actor with roles and clearance.

A :class:`Principal` is derived from the validated security context plus the
role assignment. Roles drive RBAC; clearance drives ABAC. Principals are frozen.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from contracts.enums import ClassificationClearance
from contracts.security_context import SecurityContext


class Role(StrEnum):
    """Role-based access control roles for EKCP (handbook 12)."""

    ADMIN = "admin"
    POWER_USER = "power_user"
    USER = "user"
    SERVICE = "service"
    AGENT = "agent"


class Principal(BaseModel):
    """An authenticated actor with roles, clearance, and ABAC attributes."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    tenant_id: str
    roles: frozenset[Role] = frozenset()
    clearance: ClassificationClearance = ClassificationClearance.PUBLIC
    attributes: dict[str, str] = Field(default_factory=dict)

    def has_role(self, role: Role) -> bool:
        """Return whether the principal holds ``role``."""
        return role in self.roles


def principal_from_security_context(
    context: SecurityContext, *, roles: frozenset[Role]
) -> Principal:
    """Build a principal from a validated security context and role assignment."""
    return Principal(
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        roles=roles,
        clearance=context.classification_clearance,
    )
