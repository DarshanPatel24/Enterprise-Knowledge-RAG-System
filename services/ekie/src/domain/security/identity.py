"""Principal identity, roles, and authentication methods (handbook 17.4-17.6)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from domain.security.classification import Classification


class AuthMethod(StrEnum):
    """Supported authentication methods (handbook 17.4)."""

    API_KEY = "api_key"
    OAUTH = "oauth"
    SERVICE_IDENTITY = "service_identity"
    ANONYMOUS = "anonymous"


class Role(StrEnum):
    """Role-based access control roles (handbook 17.5)."""

    ADMIN = "admin"
    ENGINEER = "engineer"
    DATA_SCIENTIST = "data_scientist"
    VIEWER = "viewer"
    SERVICE_WORKER = "service_worker"


class Principal(BaseModel):
    """An authenticated actor with roles, clearance, and ABAC attributes."""

    model_config = {"frozen": True}

    subject: str
    method: AuthMethod
    roles: frozenset[Role]
    clearance: Classification
    attributes: dict[str, str] = Field(default_factory=dict)

    def has_role(self, role: Role) -> bool:
        """Return ``True`` when the principal holds ``role``."""
        return role in self.roles
