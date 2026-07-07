"""Offline demonstration of the EKRE-S0 retrieval foundations.

Runs fully offline (no Qdrant, no models): validates a security context, resolves
an inherited embedding profile from a sample collection schema, measures a stage
latency timeline, and formats retrieved candidates via the LCEL seam.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap sys.path so `src/` and the contracts package import when run directly.
_SRC = Path(__file__).resolve().parents[1] / "src"
_CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "src"
for _path in (_SRC, _CONTRACTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from contracts.enums import DistanceMetric  # noqa: E402
from domain.inheritance import (  # noqa: E402
    CollectionSchema,
    InheritanceResolver,
)
from domain.integrations import format_candidates  # noqa: E402
from domain.observability import (  # noqa: E402
    LatencyRecorder,
    correlation_scope,
)
from domain.security import SecurityContextValidator  # noqa: E402


class _SampleReader:
    """A schema reader that returns a fixed EKIE-published collection schema."""

    def read(self, collection: str) -> CollectionSchema:
        return CollectionSchema(
            collection=collection,
            dimension=1024,
            distance_metric=DistanceMetric.COSINE,
            embedding_model="ekie-published-embedding-model",
            embedding_version=2,
        )


class _SampleDoc:
    def __init__(self, content: str) -> None:
        self.page_content = content


def main() -> None:
    """Run the offline EKRE-S0 foundations demo."""
    with correlation_scope(tenant_id="tenant-a", correlation_id="demo-corr", query_id="demo-q"):
        validator = SecurityContextValidator(require_security_context=True)
        context = validator.validate(
            {
                "user_id": "analyst-1",
                "tenant_id": "tenant-a",
                "classification_clearance": "internal",
            },
            expected_tenant_id="tenant-a",
        )
        print("Security context:", context)

        resolver = InheritanceResolver(_SampleReader())
        recorder = LatencyRecorder()
        with recorder.stage("query_understanding"):
            profile = resolver.resolve("enterprise_documents")
        print("Inherited profile:", profile)

        with recorder.stage("assembly"):
            merged = format_candidates(
                [_SampleDoc("candidate one"), _SampleDoc("candidate two")]
            )
        print("Formatted context:\n", merged)

        breakdown = recorder.breakdown()
        print("Latency timeline (ms):", breakdown.stages, "total:", breakdown.total_ms)


if __name__ == "__main__":
    main()
