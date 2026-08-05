from __future__ import annotations

import uuid
import pytest
from datetime import datetime, UTC
from fastapi import Request, HTTPException

from hospital_ai.db.models import Document, User, PatientPermission
from hospital_ai.db.clinical_documents import DocumentIndexGeneration, DocumentRevisionSet, GenerationStageResult
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID


def _request(method="POST", path="/test") -> Request:
    return Request({"type": "http", "client": ("127.0.0.1", 8000), "method": method, "path": path, "headers": []})


@pytest.fixture
async def api_fixture(session_and_settings):
    session, _ = session_and_settings
    admin = await session.get(User, DOCTOR_ID)
    if not admin:
        admin = User(id=uuid.uuid4(), email="doc@test.com", full_name="Doc", role="admin", is_active=True)
        session.add(admin)
        await session.commit()
    else:
        admin.role = "admin"
        session.add(admin)
        await session.commit()
        
    session.add(PatientPermission(user_id=admin.id, patient_id=PATIENT_ALICE_ID, scope="admin"))
    
    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=admin.id,
        title="API Gen Test Doc",
        document_type="progress_note",
        storage_uri="local://test/apigen.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(doc)
    
    rev_set_a = DocumentRevisionSet(
        document_id=doc.id, revision_number=1, created_by_user_id=admin.id, status="approved",
        submitted_at=datetime.now(UTC), approved_by_user_id=admin.id, approved_at=datetime.now(UTC)
    )
    rev_set_b = DocumentRevisionSet(
        document_id=doc.id, revision_number=2, created_by_user_id=admin.id, status="approved",
        submitted_at=datetime.now(UTC), approved_by_user_id=admin.id, approved_at=datetime.now(UTC)
    )
    session.add_all([rev_set_a, rev_set_b])
    await session.flush()
    
    gen_a = DocumentIndexGeneration(id=uuid.uuid4(), document_id=doc.id, revision_set_id=rev_set_a.id, state="superseded", revision_set_sha256="r1"*32, generation_sha256="g1"*32)
    gen_b = DocumentIndexGeneration(id=uuid.uuid4(), document_id=doc.id, revision_set_id=rev_set_b.id, state="active", revision_set_sha256="r2"*32, generation_sha256="g2"*32, activated_at=datetime.now(UTC))
    session.add_all([gen_a, gen_b])
    await session.flush()
    
    for g in [gen_a, gen_b]:
        for stg in ("ocr_normalization", "facts", "chunks", "embeddings", "lexical_index", "graph", "timeline"):
            session.add(GenerationStageResult(generation_id=g.id, stage=stg, status="completed"))
            
    await session.commit()
    doc.active_index_generation_id = gen_b.id
    doc.approved_revision_set_id = rev_set_b.id
    session.add(doc)
    await session.commit()
    return session, doc, gen_a, gen_b, admin


@pytest.mark.asyncio
async def test_rollback_api_rejects_stale_active_pointer(api_fixture) -> None:
    session, doc, gen_a, gen_b, admin = api_fixture
    from hospital_ai.api.routes import document_generations as gen_routes
    from hospital_ai.schemas.document_generations import GenerationRollbackRequest

    payload = GenerationRollbackRequest(
        expected_active_generation_id=uuid.uuid4(),  # intentional wrong active id
        reason="Operational rollback",
    )
    with pytest.raises(HTTPException) as exc_info:
        await gen_routes.rollback_generation(
            document_id=doc.id,
            generation_id=gen_a.id,
            payload=payload,
            request=_request(method="POST", path=f"/api/v1/documents/{doc.id}/index-generations/{gen_a.id}/rollback"),
            idempotency_key="rollback-1",
            current_user=admin,
            session=session,
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_retry_api_creates_building_row(api_fixture, monkeypatch: pytest.MonkeyPatch) -> None:
    session, doc, gen_a, gen_b, admin = api_fixture
    from hospital_ai.api.routes import document_generations as gen_routes

    monkeypatch.setattr("hospital_ai.workers.generation_jobs.enqueue_build_generation_job", lambda *args, **kwargs: None, raising=False)
    monkeypatch.setattr("hospital_ai.services.generations.enqueue_build_generation_job", lambda *args, **kwargs: None, raising=False)

    res = await gen_routes.retry_generation(
        document_id=doc.id,
        generation_id=gen_b.id,
        request=_request(method="POST", path=f"/api/v1/documents/{doc.id}/index-generations/{gen_b.id}/retry"),
        current_user=admin,
        session=session,
    )
    assert res.state == "building"
    assert res.retry_of_generation_id == gen_b.id
