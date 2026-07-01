from contracts import (
    CONTRACTS_VERSION,
    Citation,
    ClassificationClearance,
    DistanceMetric,
    EnterpriseDataPurgeEvent,
    ExecutionContext,
    RetrievalCandidate,
    RetrievalContextPackage,
    SecurityContext,
    VectorCollectionRecord,
)


def test_execution_context_defaults_version() -> None:
    ctx = ExecutionContext(
        request_id="req-1",
        correlation_id="corr-1",
        tenant_id="tenant-a",
    )
    assert ctx.schema_version == CONTRACTS_VERSION
    assert ctx.session_id is None


def test_security_context_requires_clearance() -> None:
    ctx = SecurityContext(
        user_id="user-1",
        tenant_id="tenant-a",
        classification_clearance=ClassificationClearance.INTERNAL,
    )
    assert ctx.classification_clearance == ClassificationClearance.INTERNAL


def test_vector_record_carries_mandatory_metadata() -> None:
    record = VectorCollectionRecord(
        document_id="doc-1",
        chunk_id="chunk-1",
        tenant_id="tenant-a",
        classification_clearance=ClassificationClearance.CONFIDENTIAL,
        distance_metric=DistanceMetric.COSINE,
        source_path="/policies/hr.md",
        embedding_model="text-embedding-3-large",
        embedding_version=1,
    )
    assert record.distance_metric == DistanceMetric.COSINE
    assert record.embedding_version == 1


def test_retrieval_package_preserves_citation() -> None:
    citation = Citation(
        document_id="doc-1",
        chunk_id="chunk-1",
        source_path="/policies/hr.md",
    )
    candidate = RetrievalCandidate(
        citation=citation,
        content="Remote work policy details.",
        relevance_score=0.87,
    )
    package = RetrievalContextPackage(
        query="What is the WFH policy?",
        tenant_id="tenant-a",
        candidates=[candidate],
    )
    assert package.candidates[0].citation.source_path == "/policies/hr.md"
    assert package.security_filtered is True


def test_purge_event_requires_user() -> None:
    event = EnterpriseDataPurgeEvent(
        user_id="user-1",
        tenant_id="tenant-a",
        correlation_id="corr-1",
    )
    assert event.user_id == "user-1"
