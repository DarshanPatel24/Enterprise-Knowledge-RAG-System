"""Security context contract injected by EKCP and enforced by EKRE."""

from pydantic import Field

from contracts.base import VersionedContract
from contracts.enums import ClassificationClearance


class SecurityContext(VersionedContract):
    """Identity and clearance used to filter candidates before ranking."""

    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    classification_clearance: ClassificationClearance
