"""Deterministic vector identity (handbook 11.10, ADR-027).

A stable vector identifier derived from the collection, chunk, and embedding
version guarantees that republishing the same embedding overwrites the same
vector rather than creating duplicates, which is essential for idempotency,
replay, and recovery.
"""

from __future__ import annotations


def build_vector_id(collection: str, chunk_id: str, embedding_version: int) -> str:
    """Return a stable, deterministic identifier for a published vector."""
    return f"{collection}::{chunk_id}::e{embedding_version}"
