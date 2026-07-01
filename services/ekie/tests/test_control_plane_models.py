"""Tests for the Control Plane ORM models and database access."""

from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Lineage,
    ProcessingState,
    ProcessingStatus,
    Repository,
    Workflow,
    WorkflowStatus,
)


def test_full_lineage_graph_persists(control_plane_db: ControlPlaneDatabase) -> None:
    with control_plane_db.session() as session:
        repo = Repository(
            tenant_id="tenant-a",
            name="hr-policies",
            source_type="filesystem",
            uri="/data/hr",
        )
        document = Document(
            repository=repo,
            tenant_id="tenant-a",
            source_path="/data/hr/leave.pdf",
            content_hash="abc123",
            classification_clearance="internal",
        )
        markdown = Asset(
            document=document,
            tenant_id="tenant-a",
            asset_type=AssetType.MARKDOWN,
            version=1,
            storage_uri="ekie-assets/doc/markdown/1",
            content_hash="md5hash",
        )
        session.add_all([repo, document, markdown])
        session.flush()

        chunks = Asset(
            document=document,
            tenant_id="tenant-a",
            asset_type=AssetType.CHUNKS,
            version=1,
            storage_uri="ekie-assets/doc/chunks/1",
            content_hash="chunkhash",
        )
        session.add(chunks)
        session.flush()

        session.add(
            Lineage(asset_id=chunks.id, parent_asset_id=markdown.id, relation="derived_from")
        )
        session.add(
            Workflow(
                document=document,
                tenant_id="tenant-a",
                workflow_type="ingest",
                status=WorkflowStatus.SUCCEEDED,
            )
        )
        session.add(
            ProcessingState(
                document=document,
                tenant_id="tenant-a",
                stage="transform",
                status=ProcessingStatus.COMPLETED,
            )
        )

    with control_plane_db.session() as session:
        stored_doc = session.query(Document).one()
        assert stored_doc.status == DocumentStatus.ACTIVE
        assert stored_doc.version == 1
        assert len(stored_doc.assets) == 2
        assert len(stored_doc.workflows) == 1
        assert len(stored_doc.processing_states) == 1

        lineage = session.query(Lineage).one()
        assert lineage.relation == "derived_from"
