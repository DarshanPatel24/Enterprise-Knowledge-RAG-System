"""Generate an EKIE acceptance report from live runtime checks.

This script performs the PM/operator acceptance flow in one command:
1. EKIE and Langfuse health probes.
2. Optional markdown creation + repository ingest call.
3. SQL Control Plane verification (document and asset types).
4. Qdrant verification (collection, points, payload metadata).
5. Workflow API verification for completed stages.

Usage:
    python services/ekie/scripts/acceptance_report.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

_SRC = Path(__file__).resolve().parents[1] / "src"
_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _SERVICE_ROOT.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config.settings import get_settings  # noqa: E402
from domain.control_plane import (  # noqa: E402
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Repository,
)
from domain.sync import (  # noqa: E402
    RepositoryConnectorConfig,
    RepositorySynchronizer,
    SyncPolicy,
    default_registry,
)


@dataclass(frozen=True)
class AcceptanceConfig:
    """Runtime options for acceptance execution."""

    tenant_id: str
    repository_id: str | None
    source_dir: str
    ekie_base_url: str
    qdrant_base_url: str
    langfuse_url: str
    report_path: Path
    max_documents: int
    skip_ingest: bool


def _now_iso() -> str:
    """Return UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


def _http_get_status(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    """Return a status summary for an HTTP GET request."""
    try:
        response = requests.get(url, headers=headers, timeout=20)
        return {
            "ok": response.ok,
            "status_code": response.status_code,
            "url": url,
            "body_preview": response.text[:400],
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "status_code": None,
            "url": url,
            "error": str(exc),
        }


def _resolve_repository_id(
    db: ControlPlaneDatabase,
    tenant_id: str,
    source_dir: str,
    explicit_repository_id: str | None,
) -> str:
    """Resolve repository id from explicit value or tenant+URI lookup."""
    if explicit_repository_id:
        return explicit_repository_id
    with db.session() as session:
        repo = (
            session.query(Repository)
            .filter(
                Repository.tenant_id == tenant_id,
                Repository.uri == source_dir,
            )
            .order_by(Repository.created_at.desc())
            .first()
        )
        if repo is None:
            raise RuntimeError(
                "No repository found for tenant/source_dir. "
                "Provide --repository-id or register/sync repository first."
            )
        return repo.id


def _create_markdown_file(source_dir: str) -> Path:
    """Create a deterministic markdown file used for acceptance validation."""
    directory = Path(source_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    target = directory / f"acceptance_{stamp}.md"
    target.write_text(
        "# EKIE Acceptance Validation\n\n"
        "This markdown file validates the end-to-end ingestion flow.\n\n"
        "## Checks\n"
        "- service health\n"
        "- workflow completion\n"
        "- SQL asset lineage\n"
        "- Qdrant vector publish\n",
        encoding="utf-8",
    )
    return target


def _synchronize_repository(db: ControlPlaneDatabase, repository_id: str, tenant_id: str) -> None:
    """Run one synchronization pass for the target repository."""
    with db.session() as session:
        repository = session.get(Repository, repository_id)
        if repository is None or repository.tenant_id != tenant_id:
            raise RuntimeError("Repository not found for tenant during sync step.")
        config = RepositoryConnectorConfig(
            repository_id=repository.id,
            tenant_id=repository.tenant_id,
            name=repository.name,
            connector_type=repository.source_type,
            root_uri=repository.uri,
        )
    connector = default_registry().create(config)
    RepositorySynchronizer(db, connector, SyncPolicy()).synchronize(repository_id, tenant_id)


def _find_document_id(
    db: ControlPlaneDatabase,
    repository_id: str,
    tenant_id: str,
    source_path: str,
) -> str:
    """Return document id by repository/tenant/source_path."""
    with db.session() as session:
        doc = (
            session.query(Document)
            .filter(
                Document.repository_id == repository_id,
                Document.tenant_id == tenant_id,
                Document.source_path == source_path,
            )
            .order_by(Document.updated_at.desc())
            .first()
        )
        if doc is None:
            raise RuntimeError("Synchronized markdown document not found in control plane.")
        return doc.id


def _call_document_ingest(
    ekie_base_url: str,
    document_id: str,
    tenant_id: str,
    source_bytes: bytes,
) -> dict[str, Any]:
    """Trigger single-document ingest and normalize to acceptance schema."""
    url = f"{ekie_base_url.rstrip('/')}/v1/documents/{document_id}/ingest?mime_type=text/markdown"
    response = requests.post(
        url,
        headers={"X-Tenant-ID": tenant_id, "Content-Type": "application/octet-stream"},
        data=source_bytes,
        timeout=180,
    )
    body = response.json() if response.text else {}
    status_value = str(body.get("status", ""))
    is_completed = status_value == "completed"
    normalized = {
        "attempted": 1,
        "completed": 1 if is_completed else 0,
        "dead_lettered": 0 if is_completed else 1,
        "results": [body] if body else [],
    }
    return {
        "ok": response.ok,
        "status_code": response.status_code,
        "url": url,
        "body": normalized,
    }


def _sql_evidence(
    db: ControlPlaneDatabase,
    tenant_id: str,
    document_id: str,
) -> dict[str, Any]:
    """Collect SQL evidence for document and asset lineage."""
    expected_types = {
        AssetType.MARKDOWN.value,
        AssetType.INTELLIGENCE.value,
        AssetType.CHUNKS.value,
        AssetType.EMBEDDING.value,
        AssetType.VECTOR.value,
    }
    with db.session() as session:
        doc = (
            session.query(Document)
            .filter(Document.id == document_id, Document.tenant_id == tenant_id)
            .first()
        )
        assets = (
            session.query(Asset)
            .filter(Asset.document_id == document_id, Asset.tenant_id == tenant_id)
            .all()
        )
    seen_types = sorted({str(asset.asset_type) for asset in assets})
    return {
        "document_exists": doc is not None,
        "document_status": None if doc is None else str(doc.status),
        "document_active": bool(doc is not None and doc.status == DocumentStatus.ACTIVE),
        "asset_types_seen": seen_types,
        "asset_types_expected": sorted(expected_types),
        "asset_types_complete": expected_types.issubset(set(seen_types)),
        "asset_count": len(assets),
    }


def _workflow_evidence(ekie_base_url: str, tenant_id: str, document_id: str) -> dict[str, Any]:
    """Collect workflow API evidence for completed stages."""
    url = f"{ekie_base_url.rstrip('/')}/v1/documents/{document_id}/workflow"
    response = requests.get(url, headers={"X-Tenant-ID": tenant_id}, timeout=30)
    body = response.json() if response.text else {}
    completed = set(body.get("completed_stages", []))
    expected = {"transform", "intelligence", "chunk", "embed", "publish"}
    return {
        "ok": response.ok,
        "status_code": response.status_code,
        "url": url,
        "status": body.get("status"),
        "completed_stages": sorted(completed),
        "expected_stages": sorted(expected),
        "all_expected_present": expected.issubset(completed),
        "correlation_id": body.get("correlation_id"),
    }


def _qdrant_evidence(
    qdrant_base_url: str,
    collection: str,
    document_id: str,
) -> dict[str, Any]:
    """Collect Qdrant evidence for collection count and doc payload presence."""
    count_url = f"{qdrant_base_url.rstrip('/')}/collections/{collection}/points/count"
    count_response = requests.post(count_url, json={"exact": True}, timeout=30)
    count_body = count_response.json() if count_response.text else {}

    scroll_url = f"{qdrant_base_url.rstrip('/')}/collections/{collection}/points/scroll"
    scroll_payload = {
        "filter": {
            "must": [
                {
                    "key": "metadata.document_id",
                    "match": {"value": document_id},
                }
            ]
        },
        "limit": 5,
        "with_payload": True,
        "with_vector": False,
    }
    scroll_response = requests.post(scroll_url, json=scroll_payload, timeout=30)
    scroll_body = scroll_response.json() if scroll_response.text else {}
    points = scroll_body.get("result", {}).get("points", [])

    payload_ok = False
    if points:
        metadata = points[0].get("payload", {}).get("metadata", {})
        payload_ok = all(
            key in metadata
            for key in (
                "document_id",
                "tenant_id",
                "embedding_model",
                "dimension",
                "repository_id",
            )
        )

    return {
        "count_ok": count_response.ok,
        "count_status_code": count_response.status_code,
        "point_count": count_body.get("result", {}).get("count"),
        "scroll_ok": scroll_response.ok,
        "scroll_status_code": scroll_response.status_code,
        "matched_points": len(points),
        "payload_metadata_complete": payload_ok,
    }


def _acceptance_decision(report: dict[str, Any]) -> dict[str, Any]:
    """Calculate final acceptance decision from evidence sections."""
    ingest_body = report.get("ingestion", {}).get("body", {})
    completed_count = int(ingest_body.get("completed", 0) or 0)
    dead_lettered_count = int(ingest_body.get("dead_lettered", 0) or 0)
    checks: dict[str, bool] = {
        "ekie_live_ok": bool(report["health"].get("ekie_live", {}).get("ok")),
        "ekie_ready_ok": bool(report["health"].get("ekie_ready", {}).get("ok")),
        "langfuse_ok": bool(report["health"].get("langfuse", {}).get("ok")),
        "ingest_ok": bool(
            report.get("ingestion", {}).get("ok")
            and completed_count > 0
            and dead_lettered_count == 0
        ),
        "sql_document_active": bool(report.get("sql", {}).get("document_active")),
        "sql_assets_complete": bool(report.get("sql", {}).get("asset_types_complete")),
        "workflow_complete": bool(report.get("workflow", {}).get("all_expected_present")),
        "qdrant_points_found": bool((report.get("qdrant", {}).get("matched_points", 0) or 0) > 0),
        "qdrant_payload_complete": bool(
            report.get("qdrant", {}).get("payload_metadata_complete")
        ),
    }
    return {
        "accepted": all(checks.values()),
        "checks": checks,
    }


def build_config(args: argparse.Namespace) -> AcceptanceConfig:
    """Build acceptance config from CLI args and EKIE settings defaults."""
    settings = get_settings()
    source_dir = args.source_dir or settings.sync.target_directory or str(Path.cwd())
    qdrant_base_url = args.qdrant_url or (
        f"http://{settings.qdrant.host}:{settings.qdrant.port}"
    )
    report_dir = Path(args.report_dir)
    if not report_dir.is_absolute():
        report_dir = (_REPO_ROOT / report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    report_name = f"acceptance_report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
    return AcceptanceConfig(
        tenant_id=args.tenant_id,
        repository_id=args.repository_id,
        source_dir=source_dir,
        ekie_base_url=args.ekie_url,
        qdrant_base_url=qdrant_base_url,
        langfuse_url=args.langfuse_url,
        report_path=report_dir / report_name,
        max_documents=args.max_documents,
        skip_ingest=args.skip_ingest,
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Generate EKIE acceptance report")
    parser.add_argument("--tenant-id", default="tenant-default")
    parser.add_argument("--repository-id", default=None)
    parser.add_argument("--source-dir", default=None)
    parser.add_argument("--ekie-url", default="http://localhost:8001")
    parser.add_argument("--qdrant-url", default=None)
    parser.add_argument("--langfuse-url", default="http://localhost:3000")
    parser.add_argument("--report-dir", default="services/ekie/storage")
    parser.add_argument("--max-documents", type=int, default=1)
    parser.add_argument("--skip-ingest", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run acceptance checks and write JSON report to disk."""
    # Ensure Pydantic settings env_file=.env resolves to services/ekie/.env.
    os.chdir(_SERVICE_ROOT)
    args = parse_args()
    config = build_config(args)
    settings = get_settings()
    db = ControlPlaneDatabase(settings.control_plane)

    report: dict[str, Any] = {
        "generated_at": _now_iso(),
        "config": {
            "tenant_id": config.tenant_id,
            "repository_id": config.repository_id,
            "source_dir": config.source_dir,
            "ekie_base_url": config.ekie_base_url,
            "qdrant_base_url": config.qdrant_base_url,
            "langfuse_url": config.langfuse_url,
            "skip_ingest": config.skip_ingest,
        },
        "health": {
            "ekie_live": _http_get_status(f"{config.ekie_base_url.rstrip('/')}/health/live"),
            "ekie_ready": _http_get_status(f"{config.ekie_base_url.rstrip('/')}/health/ready"),
            "langfuse": _http_get_status(config.langfuse_url),
        },
    }

    if config.skip_ingest:
        report["ingestion"] = {"ok": False, "skipped": True}
    else:
        markdown_path = _create_markdown_file(config.source_dir)
        repository_id = _resolve_repository_id(
            db,
            config.tenant_id,
            config.source_dir,
            config.repository_id,
        )
        _synchronize_repository(db, repository_id, config.tenant_id)
        document_id = _find_document_id(
            db,
            repository_id,
            config.tenant_id,
            markdown_path.name,
        )
        ingest = _call_document_ingest(
            config.ekie_base_url,
            document_id,
            config.tenant_id,
            markdown_path.read_bytes(),
        )
        report["ingestion"] = ingest
        report["ingestion"]["markdown_file"] = str(markdown_path)
        report["ingestion"]["repository_id"] = repository_id
        report["ingestion"]["document_id"] = document_id

        result_list = ingest.get("body", {}).get("results", [])
        if result_list:
            completed_results = [
                item for item in result_list if item.get("status") == "completed"
            ]
            selected = completed_results[0] if completed_results else result_list[0]
            selected_document_id = selected.get("document_id", document_id)
            report["workflow"] = _workflow_evidence(
                config.ekie_base_url, config.tenant_id, selected_document_id
            )
            report["sql"] = _sql_evidence(db, config.tenant_id, selected_document_id)
            collection = settings.publishing.default_collection
            report["qdrant"] = _qdrant_evidence(
                config.qdrant_base_url, collection, selected_document_id
            )
            report["document_id"] = selected_document_id

    report["decision"] = _acceptance_decision(report)
    config.report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({"accepted": report["decision"]["accepted"], "report": str(config.report_path)}, indent=2))
    return 0 if report["decision"]["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
