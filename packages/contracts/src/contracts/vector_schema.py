"""Vector database collection schema published by EKIE."""

from pydantic import Field

from contracts.base import VersionedContract
from contracts.enums import ClassificationClearance, DistanceMetric


class VectorCollectionRecord(VersionedContract):
    """Mandatory metadata that must accompany every published vector payload."""

    document_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    classification_clearance: ClassificationClearance
    distance_metric: DistanceMetric
    source_path: str = Field(min_length=1)
    embedding_model: str = Field(min_length=1)
    embedding_version: int = Field(ge=1)
