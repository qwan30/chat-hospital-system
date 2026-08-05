from __future__ import annotations

from hospital_ai.db.models import AiQuery, Base, Document, DocumentChunk


def test_v2_lineage_tables_and_document_pointers_are_registered() -> None:
    expected = {
        "document_uploads",
        "document_extraction_runs",
        "document_page_revisions",
        "document_draft_heads",
        "document_revision_sets",
        "document_revision_pages",
        "document_revision_events",
        "document_index_generations",
        "generation_stage_results",
        "ocr_blocks",
        "ocr_lines",
        "ocr_spans",
        "idempotency_records",
        "claim_validation_results",
        "clinical_timeline_events",
    }
    assert expected <= set(Base.metadata.tables)
    assert "approved_revision_set_id" in Document.__table__.c
    assert "active_index_generation_id" in Document.__table__.c
    assert "generation_id" in DocumentChunk.__table__.c


def test_v2_status_checks_are_exact() -> None:
    from hospital_ai.db.clinical_documents import ALIGNMENT_STATES, DOCUMENT_UPLOAD_STATES, GENERATION_STATES

    assert DOCUMENT_UPLOAD_STATES == frozenset(
        {"pending_upload", "uploaded_unverified", "quarantined", "verified", "finalized", "rejected"}
    )
    assert GENERATION_STATES == frozenset({"building", "active", "failed", "superseded"})
    assert ALIGNMENT_STATES == frozenset({"aligned", "partially_aligned", "stale"})


def test_v2_metadata_keeps_legacy_tables_and_forward_schema_contract() -> None:
    from hospital_ai.db.clinical_documents import DocumentUpload

    expected_tables = {
        "legacy_graph_entities",
        "legacy_graph_relations",
        "system_settings",
        "metric_events",
        "user_feedback",
    }
    assert expected_tables <= set(Base.metadata.tables)
    assert {"quarantine_result"} <= set(DocumentUpload.__table__.c.keys())
    assert {"validation_mode", "last_emitted_sequence"} <= set(AiQuery.__table__.c.keys())

    chunk_constraint = next(
        constraint for constraint in DocumentChunk.__table__.constraints if constraint.name == "uq_document_chunk_index"
    )
    assert {column.name for column in chunk_constraint.columns} == {"document_id", "generation_id", "chunk_index"}

    graph_mentions = Base.metadata.tables["graph_mentions"]
    assert "fk_graph_mention_entity_patient" in {fk.name for fk in graph_mentions.foreign_key_constraints}
