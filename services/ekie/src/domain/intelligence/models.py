"""Document Intelligence output contract and value types (handbook 8.16).

These models form the enrichment contract consumed by the Intelligent Chunking
Framework (Chapter 9). They are EKIE-internal and intentionally not part of
packages/contracts, which carries only cross-service payloads.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class BlockType(StrEnum):
    """Structural block categories recognized in canonical Markdown."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    CODE = "code"
    IMAGE = "image"
    QUOTE = "quote"
    NOTE = "note"


class DocumentCategory(StrEnum):
    """Content classification categories (handbook 8.11)."""

    POLICY = "policy"
    PROCEDURE = "procedure"
    MANUAL = "manual"
    TECHNICAL_SPECIFICATION = "technical_specification"
    API_DOCUMENTATION = "api_documentation"
    MEETING_NOTES = "meeting_notes"
    MAINTENANCE_GUIDE = "maintenance_guide"
    TRAINING_MATERIAL = "training_material"
    SOURCE_CODE = "source_code"
    ARCHITECTURE = "architecture"
    GENERAL = "general"


class DocumentComplexity(StrEnum):
    """Relative document complexity (handbook 8.15)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SensitiveContentType(StrEnum):
    """Categories of sensitive content flagged for governance (handbook 8.12)."""

    EMAIL_ADDRESS = "email_address"
    PHONE_NUMBER = "phone_number"
    CREDIT_CARD = "credit_card"
    NATIONAL_ID = "national_id"
    API_KEY = "api_key"
    SECRET = "secret"  # noqa: S105 - enum label, not a credential value


class SectionNode(BaseModel):
    """A node in the document's logical section tree (handbook 8.6)."""

    model_config = {"frozen": True}

    section_id: str
    title: str
    level: int
    parent_id: str | None = None
    child_ids: list[str] = Field(default_factory=list)


class TableInfo(BaseModel):
    """Classified metadata for a detected table (handbook 8.7)."""

    model_config = {"frozen": True}

    table_id: str
    section_id: str | None
    rows: int
    columns: int
    header_confidence: float
    contains_numeric: bool
    contains_dates: bool
    contains_ids: bool


class FigureInfo(BaseModel):
    """Metadata for a detected figure or image (handbook 8.8)."""

    model_config = {"frozen": True}

    figure_id: str
    section_id: str | None
    caption: str
    reference: str


class CodeBlockInfo(BaseModel):
    """Metadata for a detected code block (handbook 8.9)."""

    model_config = {"frozen": True}

    block_id: str
    section_id: str | None
    language: str
    line_count: int


class SensitiveFinding(BaseModel):
    """An aggregated sensitive-content finding (handbook 8.12)."""

    model_config = {"frozen": True}

    finding_type: SensitiveContentType
    count: int


class SectionIntelligence(BaseModel):
    """Per-section semantic metadata used by chunking (handbook 8.13)."""

    model_config = {"frozen": True}

    section_id: str
    parent_id: str | None
    heading_level: int
    token_count: int
    reading_time_seconds: float
    contains_table: bool
    contains_image: bool
    contains_code: bool
    contains_warning: bool
    contains_procedure: bool


class QualityScore(BaseModel):
    """Document quality score with component breakdown (handbook 8.14)."""

    model_config = {"frozen": True}

    overall: int
    components: dict[str, int] = Field(default_factory=dict)


class SemanticMetadata(BaseModel):
    """Enriched semantic metadata unavailable from the source (handbook 8.15)."""

    model_config = {"frozen": True}

    primary_topic: str | None
    document_category: DocumentCategory
    language: str
    complexity: DocumentComplexity
    knowledge_density: float
    token_count: int
    section_count: int


class DocumentIntelligenceReport(BaseModel):
    """The complete enrichment contract for a document (handbook 8.16)."""

    model_config = {"frozen": True}

    document_id: str
    document_version: int
    language: str
    classification: DocumentCategory
    structure: list[SectionNode] = Field(default_factory=list)
    tables: list[TableInfo] = Field(default_factory=list)
    figures: list[FigureInfo] = Field(default_factory=list)
    code_blocks: list[CodeBlockInfo] = Field(default_factory=list)
    sections: list[SectionIntelligence] = Field(default_factory=list)
    sensitive_findings: list[SensitiveFinding] = Field(default_factory=list)
    quality: QualityScore
    semantic_metadata: SemanticMetadata

    def canonical_json(self) -> bytes:
        """Return deterministic UTF-8 JSON bytes for immutable asset storage."""
        return self.model_dump_json(indent=2).encode("utf-8")
