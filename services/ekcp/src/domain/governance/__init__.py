"""Governance, security, and policy domain (handbook Chapter 12)."""

from domain.governance.audit import (
    AuditAction,
    AuditRecord,
    AuditResult,
    AuditSink,
    InMemoryAuditSink,
    LoggingAuditSink,
    build_audit_record,
)
from domain.governance.authorization import (
    ROLE_PERMISSIONS,
    AccessRequest,
    Permission,
    PolicyDecision,
    PolicyEngine,
    granted_permissions,
)
from domain.governance.classification import (
    ensure_no_downgrade,
    is_cleared,
    parse_clearance,
    rank,
)
from domain.governance.errors import GovernanceError, GovernanceErrorType
from domain.governance.guard import GovernanceGuard
from domain.governance.identity import (
    Principal,
    Role,
    principal_from_security_context,
)
from domain.governance.masking import Masker, MaskingConfig
from domain.governance.policy import GovernancePolicy, GovernanceSettingsLike
from domain.governance.propagation import SecurityContextPropagator
from domain.governance.redaction import (
    RedactionFilter,
    SecretRegistry,
    install_log_redaction,
)

__all__ = [
    "ROLE_PERMISSIONS",
    "AccessRequest",
    "AuditAction",
    "AuditRecord",
    "AuditResult",
    "AuditSink",
    "GovernanceError",
    "GovernanceErrorType",
    "GovernanceGuard",
    "GovernancePolicy",
    "GovernanceSettingsLike",
    "InMemoryAuditSink",
    "LoggingAuditSink",
    "Masker",
    "MaskingConfig",
    "Permission",
    "PolicyDecision",
    "PolicyEngine",
    "Principal",
    "RedactionFilter",
    "Role",
    "SecretRegistry",
    "SecurityContextPropagator",
    "build_audit_record",
    "ensure_no_downgrade",
    "granted_permissions",
    "install_log_redaction",
    "is_cleared",
    "parse_clearance",
    "principal_from_security_context",
    "rank",
]
