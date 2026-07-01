"""Base model for all versioned cross-engine contracts."""

from pydantic import BaseModel, ConfigDict, Field

from contracts.version import CONTRACTS_VERSION


class VersionedContract(BaseModel):
    """Base contract carrying the schema version for compatibility checks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = Field(default=CONTRACTS_VERSION)
