"""Maintenance tool to inspect and hard-delete documents from the Control Plane.

Deleting a document purges its published vectors (from the active vector
provider) and removes its Control Plane rows -- assets, workflows, and
processing state cascade automatically. Use this to clean up documents that the
poll-based sync worker can no longer reconcile, for example documents left
behind (orphaned) after the sync ``TARGET_DIRECTORY`` was pointed at a new
folder, or soft-deleted twins whose rows still linger.

Usage (from any directory):
    # Inspect current state
    python services/ekie/scripts/purge_documents.py --list

    # Delete one document by id or by source path
    python services/ekie/scripts/purge_documents.py --document-id <id>
    python services/ekie/scripts/purge_documents.py --source-path "New Text Document.txt"

    # Bulk cleanup
    python services/ekie/scripts/purge_documents.py --status deleted
    python services/ekie/scripts/purge_documents.py --repository auto-sync-test
    python services/ekie/scripts/purge_documents.py --orphaned          # repos != current target
    python services/ekie/scripts/purge_documents.py --drop-empty-repositories

Add --force to remove rows even when vector cleanup fails, --yes to skip the
confirmation prompt, and --tenant-id to override the configured tenant.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SERVICE_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.chdir(_SERVICE_ROOT)

from composition import build_asset_storage  # noqa: E402 - follows sys.path bootstrap
from config.settings import get_settings  # noqa: E402
from domain.control_plane import (  # noqa: E402
    ControlPlaneDatabase,
    Document,
    Repository,
)
from domain.publishing import (  # noqa: E402
    DocumentDeletionService,
    VectorCleanupService,
    cleanup_provider_registry,
)


def _build_deletion_service(
    settings: object, db: ControlPlaneDatabase
) -> DocumentDeletionService:
    storage = build_asset_storage(settings)  # type: ignore[arg-type]
    qdrant = settings.qdrant  # type: ignore[attr-defined]
    providers = cleanup_provider_registry(
        qdrant_host=qdrant.host,
        qdrant_port=qdrant.port,
        qdrant_timeout_seconds=qdrant.request_timeout_seconds,
    )
    publishing = settings.publishing  # type: ignore[attr-defined]
    return DocumentDeletionService(
        db,
        VectorCleanupService(
            db,
            storage,
            providers,
            fallback_provider=publishing.provider,
            fallback_collection=publishing.default_collection,
        ),
    )


def _list_documents(db: ControlPlaneDatabase, tenant_id: str) -> None:
    with db.session() as session:
        repos = {
            r.id: r
            for r in session.query(Repository).filter_by(tenant_id=tenant_id).all()
        }
        documents = (
            session.query(Document)
            .filter_by(tenant_id=tenant_id)
            .order_by(Document.repository_id, Document.source_path)
            .all()
        )
        print(f"Tenant: {tenant_id}")
        print(f"Repositories: {len(repos)}   Documents: {len(documents)}\n")
        for repo in repos.values():
            repo_docs = [d for d in documents if d.repository_id == repo.id]
            print(f"[{repo.name}] uri={repo.uri}  ({len(repo_docs)} documents)")
            for doc in repo_docs:
                print(
                    f"    - {doc.source_path}  "
                    f"status={doc.status}  id={doc.id}"
                )
            print()


def _select_documents(
    db: ControlPlaneDatabase,
    tenant_id: str,
    args: argparse.Namespace,
) -> list[tuple[str, str, str]]:
    """Return (document_id, source_path, repository_name) tuples matching filters."""
    with db.session() as session:
        repos = {
            r.id: r
            for r in session.query(Repository).filter_by(tenant_id=tenant_id).all()
        }
        query = session.query(Document).filter(Document.tenant_id == tenant_id)
        if args.document_id:
            query = query.filter(Document.id == args.document_id)
        if args.source_path:
            query = query.filter(Document.source_path == args.source_path)
        if args.status:
            query = query.filter(Document.status == args.status)
        if args.repository:
            repo_ids = [r.id for r in repos.values() if r.name == args.repository]
            query = query.filter(Document.repository_id.in_(repo_ids or ["__none__"]))
        rows = query.order_by(Document.source_path).all()
        if args.orphaned:
            target = (get_settings().sync.target_directory or "").rstrip("\\/")
            rows = [
                d
                for d in rows
                if (repos[d.repository_id].uri or "").rstrip("\\/") != target
            ]
        return [(d.id, d.source_path, repos[d.repository_id].name) for d in rows]


def _drop_empty_repositories(db: ControlPlaneDatabase, tenant_id: str) -> int:
    with db.session() as session:
        repos = session.query(Repository).filter_by(tenant_id=tenant_id).all()
        removed = 0
        for repo in repos:
            has_docs = (
                session.query(Document)
                .filter_by(repository_id=repo.id)
                .first()
                is not None
            )
            if not has_docs:
                session.delete(repo)
                removed += 1
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Purge documents from the Control Plane")
    parser.add_argument("--list", action="store_true", help="List documents and exit")
    parser.add_argument("--document-id", default=None)
    parser.add_argument("--source-path", default=None)
    parser.add_argument("--status", default=None, choices=["active", "archived", "deleted"])
    parser.add_argument("--repository", default=None, help="Repository name to purge")
    parser.add_argument(
        "--orphaned",
        action="store_true",
        help="Only documents whose repository uri differs from the current target",
    )
    parser.add_argument(
        "--drop-empty-repositories",
        action="store_true",
        help="Delete repositories that have no documents after purging",
    )
    parser.add_argument("--tenant-id", default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    settings = get_settings()
    tenant_id = args.tenant_id or settings.sync.tenant_id
    db = ControlPlaneDatabase(settings.control_plane)
    db.create_all()

    if args.list:
        _list_documents(db, tenant_id)
        return 0

    has_filter = any(
        [args.document_id, args.source_path, args.status, args.repository, args.orphaned]
    )
    if not has_filter and not args.drop_empty_repositories:
        parser.error(
            "specify a filter (--document-id/--source-path/--status/--repository/"
            "--orphaned) or --drop-empty-repositories, or use --list"
        )

    selected = _select_documents(db, tenant_id, args) if has_filter else []
    if has_filter and not selected:
        print("No documents matched the given filters.")
    if selected:
        print(f"About to hard-delete {len(selected)} document(s) for tenant {tenant_id}:")
        for doc_id, path, repo_name in selected:
            print(f"    - [{repo_name}] {path}  ({doc_id})")
        if not args.yes:
            confirm = input("Proceed? [y/N] ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Aborted.")
                return 1

        service = _build_deletion_service(settings, db)
        deleted = 0
        for doc_id, path, _repo in selected:
            result = service.delete_document(doc_id, tenant_id, force=args.force)
            if result.row_deleted:
                deleted += 1
                note = (
                    f" (vector cleanup warning: {result.vector_cleanup_error})"
                    if result.vector_cleanup_error
                    else ""
                )
                print(
                    f"  [DELETED] {path}  vectors_removed={result.vectors_deleted}{note}"
                )
            else:
                print(f"  [SKIPPED] {path}  (not found)")
        print(f"\nDeleted {deleted}/{len(selected)} document(s).")

    if args.drop_empty_repositories:
        removed = _drop_empty_repositories(db, tenant_id)
        print(f"Removed {removed} empty repository record(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
