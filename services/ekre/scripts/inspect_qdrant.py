"""Inventory the live Qdrant collection to verify ingestion completeness.

Scrolls every point in the collection EKIE published into and aggregates the
points (chunks) by their source document, so an operator can confirm which
documents made it into the vector store and which are missing. Connection
details are read from the EKRE environment (no hardcoded host, port, or
collection) and can be overridden per run.

Prerequisites:
  * Qdrant is running and EKIE has published into the collection.
  * ``qdrant_client`` is installed in the active environment (it is an EKRE
    dependency).

Examples (PowerShell):
  services/ekre/.venv/Scripts/python.exe services/ekre/scripts/inspect_qdrant.py
  # Only documents whose source path matches a term (case-insensitive):
  services/ekre/.venv/Scripts/python.exe services/ekre/scripts/inspect_qdrant.py --filter integrity
  # Expect specific documents and fail if any are absent:
  ... inspect_qdrant.py --expect "integrity dashboard" --expect "ics integrity"
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from collections.abc import Iterable

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional convenience dependency
    load_dotenv = None

try:
    from qdrant_client import QdrantClient
except ImportError:  # pragma: no cover - guarded for a clearer message
    print("qdrant_client is not installed in this environment.", file=sys.stderr)
    raise SystemExit(2) from None


def _load_env() -> None:
    """Load the EKRE .env so connection settings match the running service."""
    if load_dotenv is None:
        return
    env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host",
        default=os.environ.get("EKRE_QDRANT__HOST", "localhost"),
        help="Qdrant host (default: EKRE_QDRANT__HOST or localhost).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("EKRE_QDRANT__PORT", "6333")),
        help="Qdrant port (default: EKRE_QDRANT__PORT or 6333).",
    )
    parser.add_argument(
        "--collection",
        default=os.environ.get("EKRE_RETRIEVAL__DEFAULT_COLLECTION", "enterprise_documents"),
        help="Collection name (default: EKRE_RETRIEVAL__DEFAULT_COLLECTION).",
    )
    parser.add_argument(
        "--metadata-key",
        default=os.environ.get("EKRE_QDRANT__PAYLOAD_METADATA_KEY", "metadata"),
        help='Nested payload key holding metadata ("" for flat payloads).',
    )
    parser.add_argument(
        "--filter",
        default="",
        help="Only show documents whose source path contains this term (case-insensitive).",
    )
    parser.add_argument(
        "--expect",
        action="append",
        default=[],
        metavar="TERM",
        help="Assert a document whose source path contains TERM exists; repeatable.",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=256,
        help="Scroll page size (default: 256).",
    )
    return parser.parse_args()


def _metadata(payload: dict[str, object], metadata_key: str) -> dict[str, object]:
    if metadata_key:
        nested = payload.get(metadata_key)
        if isinstance(nested, dict):
            return nested
    return payload


def _document_label(meta: dict[str, object]) -> str:
    for field in ("source_path", "document_id"):
        value = meta.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return "<unknown>"


def _iter_points(
    client: QdrantClient, collection: str, batch: int
) -> Iterable[dict[str, object]]:
    offset: object | None = None
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=batch,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            yield point.payload or {}
        if offset is None:
            break


def main() -> int:
    _load_env()
    args = _parse_args()

    client = QdrantClient(host=args.host, port=args.port)
    try:
        exists = client.collection_exists(args.collection)
    except Exception as exc:  # noqa: BLE001 - external client boundary
        print(f"Failed to reach Qdrant at {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 2
    if not exists:
        print(f"Collection '{args.collection}' does not exist.", file=sys.stderr)
        return 2

    per_document: Counter[str] = Counter()
    total_points = 0
    for payload in _iter_points(client, args.collection, args.batch):
        meta = _metadata(payload, args.metadata_key)
        per_document[_document_label(meta)] += 1
        total_points += 1

    needle = args.filter.lower()
    rows = sorted(
        (
            (label, count)
            for label, count in per_document.items()
            if not needle or needle in label.lower()
        ),
        key=lambda item: item[0].lower(),
    )

    print(f"Collection : {args.collection} @ {args.host}:{args.port}")
    print(f"Total points (chunks) : {total_points}")
    print(f"Distinct documents    : {len(per_document)}")
    if needle:
        print(f"Filter                : '{args.filter}' -> {len(rows)} matching document(s)")
    print("-" * 72)
    print(f"{'chunks':>7}  document")
    print("-" * 72)
    for label, count in rows:
        print(f"{count:>7}  {label}")

    exit_code = 0
    if args.expect:
        print("-" * 72)
        labels_lower = [label.lower() for label in per_document]
        for term in args.expect:
            found = any(term.lower() in label for label in labels_lower)
            status = "FOUND" if found else "MISSING"
            print(f"[{status}] expected document matching '{term}'")
            if not found:
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
