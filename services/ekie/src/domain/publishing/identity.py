"""Deterministic vector identity (handbook 11.10, ADR-027).

A stable vector identifier derived from the collection, document, chunk, and
embedding version guarantees that republishing the same embedding overwrites the
same vector rather than creating duplicates, which is essential for idempotency,
replay, and recovery. The document id MUST be part of the identity: chunk ids are
only unique within a document (``CHK-000000`` restarts per document), so omitting
it makes chunks from different documents collide and overwrite each other in the
shared collection.
"""

from __future__ import annotations


def build_vector_id(
    collection: str, document_id: str, chunk_id: str, embedding_version: int
) -> str:
    """Return a stable, deterministic, globally unique identifier for a vector."""
    return f"{collection}::{document_id}::{chunk_id}::e{embedding_version}"
