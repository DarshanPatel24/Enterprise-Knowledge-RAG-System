"""Governance policy resolved from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict

from domain.governance.identity import Role


class GovernanceSettingsLike(Protocol):
    """Structural view of the governance settings the policy depends on."""

    enforce_authorization: bool
    enable_audit: bool
    audit_sink: str
    enable_masking: bool
    mask_email: bool
    mask_phone: bool
    mask_ssn: bool
    mask_credit_card: bool
    allow_classification_downgrade: bool
    policy_version: str
    default_role: str


class GovernancePolicy(BaseModel):
    """Immutable governance policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    enforce_authorization: bool = True
    enable_audit: bool = True
    audit_sink: str = "memory"
    enable_masking: bool = True
    mask_email: bool = True
    mask_phone: bool = True
    mask_ssn: bool = True
    mask_credit_card: bool = True
    allow_classification_downgrade: bool = False
    policy_version: str = "v1"
    default_role: Role = Role.POWER_USER

    @classmethod
    def from_settings(cls, settings: GovernanceSettingsLike) -> GovernancePolicy:
        """Build the governance policy from the governance settings."""
        return cls(
            enforce_authorization=settings.enforce_authorization,
            enable_audit=settings.enable_audit,
            audit_sink=settings.audit_sink,
            enable_masking=settings.enable_masking,
            mask_email=settings.mask_email,
            mask_phone=settings.mask_phone,
            mask_ssn=settings.mask_ssn,
            mask_credit_card=settings.mask_credit_card,
            allow_classification_downgrade=settings.allow_classification_downgrade,
            policy_version=settings.policy_version,
            default_role=Role(settings.default_role),
        )
