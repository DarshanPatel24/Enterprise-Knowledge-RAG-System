"""Configuration-driven security and governance policy (handbook 17.11)."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

from domain.security.classification import Classification, parse_classification
from domain.security.identity import Role


class SecuritySettingsLike(Protocol):
    """Structural type for environment-backed security settings."""

    require_authentication: bool
    enforce_authorization: bool
    anonymous_role: str
    anonymous_clearance: str
    minimum_clearance: str


class GovernanceSettingsLike(Protocol):
    """Structural type for environment-backed governance settings."""

    enable_audit: bool
    audit_sink: str
    allow_classification_downgrade: bool


class SecurityPolicy(BaseModel):
    """Versioned, configuration-driven security and governance behavior."""

    model_config = {"frozen": True}

    require_authentication: bool = False
    enforce_authorization: bool = True
    anonymous_role: Role = Role.SERVICE_WORKER
    anonymous_clearance: Classification = Classification.RESTRICTED
    minimum_clearance: Classification = Classification.PUBLIC
    enable_audit: bool = True
    allow_classification_downgrade: bool = False

    @classmethod
    def from_settings(
        cls,
        security: SecuritySettingsLike,
        governance: GovernanceSettingsLike,
    ) -> SecurityPolicy:
        """Build a policy from environment-backed security and governance settings."""
        return cls(
            require_authentication=security.require_authentication,
            enforce_authorization=security.enforce_authorization,
            anonymous_role=Role(security.anonymous_role),
            anonymous_clearance=parse_classification(security.anonymous_clearance),
            minimum_clearance=parse_classification(security.minimum_clearance),
            enable_audit=governance.enable_audit,
            allow_classification_downgrade=governance.allow_classification_downgrade,
        )
