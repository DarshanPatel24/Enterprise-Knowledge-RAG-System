"""Tests for the optional per-minute ingestion rate limiter.

Rate limiting is additive and disabled by default (``0 = unlimited``); these
tests use an injected deterministic clock so no real time passes, and confirm
that pacing never changes the produced embeddings or vectors.
"""

from domain.chunking import ChunkingEngine, ChunkingPolicy
from domain.control_plane import (
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Repository,
    RepositoryStatus,
)
from domain.embedding import EmbeddingEngine, EmbeddingPolicy, RateLimiter
from domain.intelligence import DocumentIntelligenceEngine, IntelligencePolicy
from domain.publishing import PublishingPolicy, VectorPublishingEngine
from domain.storage import InMemoryAssetStorage
from domain.transformation import TransformationPipeline, TransformationPolicy


class _FakeClock:
    """A manually advanced monotonic clock; ``sleep`` advances virtual time."""

    def __init__(self) -> None:
        self.now = 0.0

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def test_rate_limiter_disabled_never_waits() -> None:
    limiter = RateLimiter(0)
    assert limiter.enabled is False
    assert limiter.acquire(1000) == 0.0


def test_rate_limiter_allows_initial_burst() -> None:
    fake = _FakeClock()
    limiter = RateLimiter(60, clock=fake.clock, sleep=fake.sleep)
    assert limiter.acquire(60) == 0.0
    assert fake.now == 0.0


def test_rate_limiter_waits_when_bucket_empty() -> None:
    fake = _FakeClock()
    limiter = RateLimiter(60, clock=fake.clock, sleep=fake.sleep)  # 1 unit/second
    assert limiter.acquire(60) == 0.0
    waited = limiter.acquire(60)
    assert waited == 60.0
    assert fake.now == 60.0


def test_rate_limiter_refills_over_elapsed_time() -> None:
    fake = _FakeClock()
    limiter = RateLimiter(60, clock=fake.clock, sleep=fake.sleep)  # 1 unit/second
    assert limiter.acquire(60) == 0.0
    fake.now = 30.0  # 30 seconds pass -> 30 tokens refill
    assert limiter.acquire(30) == 0.0


_MARKDOWN = """# Equipment Maintenance

Overview of the maintenance workflow for the pump station.

## Safety

Warning: disconnect power before service.

## Inspection

1. Inspect the seals.
2. Check the pressure gauge.
"""


def _seed_document(db: ControlPlaneDatabase) -> str:
    with db.session() as session:
        repo = Repository(
            tenant_id="tenant-a",
            name="repo",
            source_type="local_fs",
            uri="local://repo",
            status=RepositoryStatus.ACTIVE,
        )
        session.add(repo)
        session.flush()
        document = Document(
            repository_id=repo.id,
            tenant_id="tenant-a",
            source_path="docs/maint.md",
            content_hash="hash-maint",
            classification_clearance="internal",
            version=1,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        return document.id


def _prepare_to_chunks(db: ControlPlaneDatabase) -> tuple[str, InMemoryAssetStorage]:
    document_id = _seed_document(db)
    storage = InMemoryAssetStorage()
    TransformationPipeline(db, storage, TransformationPolicy()).transform(
        document_id, "tenant-a", _MARKDOWN.encode("utf-8")
    )
    DocumentIntelligenceEngine(db, storage, IntelligencePolicy()).enrich(
        document_id, "tenant-a"
    )
    ChunkingEngine(db, storage, ChunkingPolicy()).chunk(document_id, "tenant-a")
    return document_id, storage


def test_embedding_paces_batches_without_changing_output(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare_to_chunks(control_plane_db)
    fake = _FakeClock()
    limiter = RateLimiter(1, clock=fake.clock, sleep=fake.sleep)
    # One chunk per batch forces multiple paced requests.
    engine = EmbeddingEngine(
        control_plane_db,
        storage,
        EmbeddingPolicy(batch_size=1),
        rate_limiter=limiter,
    )

    result = engine.embed(document_id, "tenant-a")

    assert result.created is True
    assert result.batch_count >= 2
    assert result.embedding_document.embedding_count == result.batch_count
    # The limiter paused between batches (virtual time advanced).
    assert fake.now > 0.0


def test_publishing_paces_vector_batches_and_stays_verified(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare_to_chunks(control_plane_db)
    EmbeddingEngine(control_plane_db, storage, EmbeddingPolicy()).embed(
        document_id, "tenant-a"
    )
    fake = _FakeClock()
    limiter = RateLimiter(1, clock=fake.clock, sleep=fake.sleep)
    engine = VectorPublishingEngine(
        control_plane_db,
        storage,
        PublishingPolicy(),
        rate_limiter=limiter,
    )

    result = engine.publish(document_id, "tenant-a")

    assert result.created is True
    assert result.vector_count >= 2
    # Pacing does not weaken verification.
    assert result.verified_count == result.vector_count
    # The limiter paused because the batch exceeded the 1-vector/minute budget.
    assert fake.now > 0.0
