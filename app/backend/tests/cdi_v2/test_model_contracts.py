from hospital_ai.db.models import Base, Document, DocumentChunk


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
