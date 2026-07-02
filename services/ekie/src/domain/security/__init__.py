"""Security, governance, and classification enforcement for EKIE (EKIE-S8).

Provides zero-trust building blocks used across the ingestion pipeline:
authentication to a typed principal, RBAC + ABAC authorization, ephemeral secret
resolution with log redaction, append-only audit logging, and monotonic
classification propagation enforced per stage (handbook Chapter 17).
"""

from __future__ import annotations

from domain.security.audit import (
    AuditAction,
    AuditRecord,
    AuditResult,
    AuditSink,
    InMemoryAuditSink,
    LoggingAuditSink,
)
from domain.security.authentication import (
    AnonymousAuthenticator,
    ApiKeyAuthenticator,
    Authenticator,
)
from domain.security.authorization import (
    ROLE_PERMISSIONS,
    AccessDecision,
    AccessRequest,
    Permission,
    PolicyEngine,
)
from domain.security.classification import (
    Classification,
    ensure_no_downgrade,
    is_cleared,
    is_downgrade,
    parse_classification,
    rank,
)
from domain.security.enforcement import STAGE_PERMISSIONS, StagePolicyGuard
from domain.security.errors import SecurityError, SecurityErrorType
from domain.security.identity import AuthMethod, Principal, Role
from domain.security.policy import (
    GovernanceSettingsLike,
    SecurityPolicy,
    SecuritySettingsLike,
)
from domain.security.redaction import (
    REDACTED,
    RedactionFilter,
    install_log_redaction,
)
from domain.security.secrets import (
    EnvSecretProvider,
    SecretProvider,
    SecretRegistry,
)

__all__ = [
    "REDACTED",
    "ROLE_PERMISSIONS",
    "STAGE_PERMISSIONS",
    "AccessDecision",
    "AccessRequest",
    "AnonymousAuthenticator",
    "ApiKeyAuthenticator",
    "AuditAction",
    "AuditRecord",
    "AuditResult",
    "AuditSink",
    "AuthMethod",
    "Authenticator",
    "Classification",
    "EnvSecretProvider",
    "GovernanceSettingsLike",
    "InMemoryAuditSink",
    "LoggingAuditSink",
    "Permission",
    "PolicyEngine",
    "Principal",
    "RedactionFilter",
    "Role",
    "SecretProvider",
    "SecretRegistry",
    "SecurityError",
    "SecurityErrorType",
    "SecurityPolicy",
    "SecuritySettingsLike",
    "StagePolicyGuard",
    "ensure_no_downgrade",
    "install_log_redaction",
    "is_cleared",
    "is_downgrade",
    "parse_classification",
    "rank",
]
