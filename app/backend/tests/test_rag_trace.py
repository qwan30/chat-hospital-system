"""Tests for RAG Trace Observability (Phase 3D).

Validates:
- RetrievedEvidence trace fields are stored correctly
- RagTraceResponse schema serialization
- RAG trace data flows end-to-end through the chat pipeline
"""
from __future__ import annotations


import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select, update

from hospital_ai.api.routes.rag_trace import get_rag_trace
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import AiQuery, DocumentChunk, DocumentPage, PatientPermission, RetrievedEvidence, User
from hospital_ai.schemas.chat import RagTraceEvidence, RagTraceResponse
from hospital_ai.services.chat import ChatService
from tests.conftest import create_indexed_document

# ── Schema tests ─────────────────────────────────────────────────────────


class TestRagTraceSchemas:
    def test_trace_evidence_schema(self):
        """RagTraceEvidence should serialize all fields."""
        evidence = RagTraceEvidence(
            evidence_id="E1",
            chunk_id=uuid.uuid4(),
            rank=1,
            retrieval_score=0.85,
            rerank_score=0.92,
            retrieval_method="hybrid_rrf",
            rerank_method="cross_encoder",
            citation_label="E1",
            content="Patient has allergy to penicillin.",
            document_title="allergy_note.pdf",
            page=1,
        )
        data = evidence.dict()
        assert data["retrieval_score"] == 0.85
        assert data["rerank_score"] == 0.92
        assert data["retrieval_method"] == "hybrid_rrf"
        assert data["rerank_method"] == "cross_encoder"

    def test_trace_evidence_optional_fields(self):
        """Optional trace fields should default to None."""
        evidence = RagTraceEvidence(
            evidence_id="E1",
            chunk_id=uuid.uuid4(),
            rank=1,
            retrieval_score=0.5,
            citation_label="E1",
        )
        data = evidence.dict()
        assert data["rerank_score"] is None
        assert data["retrieval_method"] is None
        assert data["rerank_method"] is None
        assert data["content"] is None

    def test_trace_response_schema(self):
        """RagTraceResponse should serialize the full trace."""
        response = RagTraceResponse(
            query_id=uuid.uuid4(),
            question="What allergies does the patient have?",
            answer="The patient has a documented allergy to penicillin. [E1]",
            status="completed",
            pipeline="simple_qa",
            model="stub",
            latency_ms=150,
            evidence=[
                RagTraceEvidence(
                    evidence_id="E1",
                    chunk_id=uuid.uuid4(),
                    rank=1,
                    retrieval_score=0.85,
                    rerank_score=0.92,
                    retrieval_method="vector",
                    rerank_method="keyword",
                    citation_label="E1",
                    content="Allergy to penicillin.",
                    document_title="note.pdf",
                    page=1,
                ),
            ],
            created_at="2026-04-29T12:00:00Z",
        )
        data = response.dict()
        assert data["status"] == "completed"
        assert len(data["evidence"]) == 1
        assert data["evidence"][0]["rerank_method"] == "keyword"


# ── RetrievedEvidence trace field tests ──────────────────────────────────


class TestRetrievedEvidenceTraceFields:
    @pytest.mark.asyncio
    async def test_trace_redacts_access_tag_denied_to_current_role(self, session_and_settings):
        session, settings = session_and_settings
        doctor = await session.get(User, DOCTOR_ID)
        document = await create_indexed_document(
            session, patient_id=PATIENT_ALICE_ID, uploaded_by=DOCTOR_ID, title="Tagged", content="Medication evidence."
        )
        response = await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_ALICE_ID,
            question="What evidence is available?",
            top_k=1,
            trace_id="trace-tag",
            ip_address="127.0.0.1",
        )
        doctor.role = "lab_staff"
        await session.execute(
            update(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .values(meta={"access_tags": ["medication"]})
        )
        await session.commit()
        assert (await get_rag_trace(query_id=response.query_id, user=doctor, db=session)).evidence == []

    @pytest.mark.asyncio
    async def test_trace_redacts_mismatched_page_document_chain(self, session_and_settings):
        session, settings = session_and_settings
        doctor = await session.get(User, DOCTOR_ID)
        document = await create_indexed_document(
            session, patient_id=PATIENT_ALICE_ID, uploaded_by=DOCTOR_ID, title="Chain", content="Chain evidence."
        )
        response = await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_ALICE_ID,
            question="What evidence is available?",
            top_k=1,
            trace_id="trace-chain",
            ip_address="127.0.0.1",
        )
        chunk = (await session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id))).one()
        other = await create_indexed_document(
            session, patient_id=PATIENT_ALICE_ID, uploaded_by=DOCTOR_ID, title="Other", content="Other evidence."
        )
        page = (await session.scalars(select(DocumentPage).where(DocumentPage.document_id == other.id))).one()
        chunk.page_id = page.id
        await session.commit()
        assert (await get_rag_trace(query_id=response.query_id, user=doctor, db=session)).evidence == []

    @pytest.mark.asyncio
    async def test_trace_redacts_evidence_after_permission_revocation(self, session_and_settings):
        """Trace visibility must be re-authorized at read time, not at retrieval time."""
        session, settings = session_and_settings
        doctor = await session.get(User, DOCTOR_ID)
        await create_indexed_document(
            session,
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=DOCTOR_ID,
            title="Revocable trace evidence",
            content="This evidence must disappear from a revoked trace.",
        )
        response = await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_ALICE_ID,
            question="What evidence is available?",
            top_k=1,
            trace_id="trace-revocation",
            ip_address="127.0.0.1",
        )
        await session.execute(
            update(PatientPermission)
            .where(PatientPermission.user_id == DOCTOR_ID, PatientPermission.patient_id == PATIENT_ALICE_ID)
            .values(deleted_at=datetime.now(UTC))
        )
        await session.commit()

        trace = await get_rag_trace(query_id=response.query_id, user=doctor, db=session)

        assert trace.evidence == []

    @pytest.mark.asyncio
    async def test_trace_fields_stored_on_chat(self, session_and_settings):
        """When chat.answer() is called, trace data should be stored in RetrievedEvidence."""
        session, settings = session_and_settings
        doctor = await session.get(User, DOCTOR_ID)

        await create_indexed_document(
            session,
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=DOCTOR_ID,
            title="Allergy report",
            content="Patient Alice has a documented allergy to penicillin.",
        )

        response = await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_ALICE_ID,
            question="What allergy is documented?",
            top_k=5,
            trace_id="trace-fields-test",
            ip_address="127.0.0.1",
        )

        # Verify evidence records were created with trace fields
        result = await session.execute(
            select(RetrievedEvidence)
            .where(RetrievedEvidence.ai_query_id == response.query_id)
            .order_by(RetrievedEvidence.rank)
        )
        evidence_rows = result.scalars().all()
        assert len(evidence_rows) >= 1

        first = evidence_rows[0]
        assert first.rank == 1
        assert first.score is not None
        # retrieval_method should be populated (default "vector" for vector-only mode)
        assert first.retrieval_method is not None

    @pytest.mark.asyncio
    async def test_trace_fields_nullable(self, session_and_settings):
        """Trace fields should be nullable for backward compatibility."""
        session, settings = session_and_settings

        # Create a RetrievedEvidence without trace fields
        ai_query = AiQuery(
            user_id=DOCTOR_ID,
            patient_id=PATIENT_ALICE_ID,
            question="test",
            status="completed",
            model="stub",
        )
        session.add(ai_query)
        await session.flush()

        # Create a document chunk to reference
        await create_indexed_document(
            session,
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=DOCTOR_ID,
            title="Test doc",
            content="Test content for trace nullable check.",
        )

        from sqlalchemy import select as sql_select

        from hospital_ai.db.models import DocumentChunk

        chunk_result = await session.execute(sql_select(DocumentChunk).limit(1))
        chunk = chunk_result.scalar_one()

        evidence = RetrievedEvidence(
            ai_query_id=ai_query.id,
            chunk_id=chunk.id,
            rank=1,
            score=0.85,
            citation_label="E1",
            # Trace fields intentionally omitted — should default to None
        )
        session.add(evidence)
        await session.commit()

        result = await session.get(RetrievedEvidence, evidence.id)
        assert result.rerank_score is None
        assert result.retrieval_method is None
        assert result.rerank_method is None


# ── Hybrid search integration in chat ────────────────────────────────────


class TestChatHybridSearchIntegration:
    @pytest.mark.asyncio
    async def test_vector_mode_default(self, session_and_settings):
        """Default retrieval_mode='vector' should work as before."""
        session, settings = session_and_settings
        assert settings.retrieval_mode == "vector"

        doctor = await session.get(User, DOCTOR_ID)
        await create_indexed_document(
            session,
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=DOCTOR_ID,
            title="BP reading",
            content="Blood pressure 140/90 mmHg recorded today.",
        )

        response = await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_ALICE_ID,
            question="What is the blood pressure?",
            top_k=5,
            trace_id="trace-vector-mode",
            ip_address="127.0.0.1",
        )
        assert response.answer
        assert response.query_id

    @pytest.mark.asyncio
    async def test_hybrid_mode_with_evidence(self, session_and_settings):
        """retrieval_mode='hybrid' should produce results using RRF."""
        session, settings = session_and_settings
        # Override to hybrid mode
        settings.retrieval_mode = "hybrid"

        doctor = await session.get(User, DOCTOR_ID)
        await create_indexed_document(
            session,
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=DOCTOR_ID,
            title="Metformin prescription",
            content="Patient prescribed Metformin 500mg twice daily for diabetes mellitus type 2.",
        )

        response = await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_ALICE_ID,
            question="Metformin 500mg",
            top_k=5,
            trace_id="trace-hybrid-mode",
            ip_address="127.0.0.1",
        )
        assert response.answer
        assert response.query_id
