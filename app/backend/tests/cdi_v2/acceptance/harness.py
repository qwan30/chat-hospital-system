from __future__ import annotations

import dataclasses
import uuid

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings


@dataclasses.dataclass
class Evidence:
    passed: bool
    evidence: str | dict | None = None
    violated_invariant: str | None = None


class CDIv2Harness:
    def __init__(self, app: FastAPI, session: AsyncSession, settings: Settings):
        self.app = app
        self.session = session
        self.settings = settings
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def run(self, scenario: str) -> Evidence:
        method = getattr(self, f"run_{scenario}", None)
        if not method:
            return Evidence(passed=False, evidence=f"Not implemented: {scenario}")
        return await method()

    async def _setup_doctor_and_admin(self):
        from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
        from hospital_ai.db.models import PatientPermission, User

        doctor = await self.session.get(User, DOCTOR_ID)
        if not doctor:
            doctor = User(id=uuid.uuid4(), email="doc@test.com", full_name="Doc", role="doctor", is_active=True)
            self.session.add(doctor)
            await self.session.commit()

        admin = User(id=uuid.uuid4(), email="admin@test.com", full_name="Admin", role="admin", is_active=True)
        self.session.add(admin)
        self.session.add(PatientPermission(user_id=admin.id, patient_id=PATIENT_ALICE_ID, scope="admin"))
        await self.session.commit()
        return doctor, admin

    async def run_stale_if_match(self) -> Evidence:
        from sqlalchemy import select

        from hospital_ai.db.migrations import PATIENT_ALICE_ID
        from hospital_ai.db.models import DocumentPage
        from tests.conftest import create_indexed_document

        doctor, _ = await self._setup_doctor_and_admin()

        doc = await create_indexed_document(
            self.session,
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=doctor.id,
            title="Test Doc",
            content="stale match test",
        )

        # Get the first page's current revision
        (await self.session.scalars(select(DocumentPage).where(DocumentPage.document_id == doc.id))).first()
        from hospital_ai.db.clinical_documents import DocumentDraftHead, DocumentPageRevision

        head = await self.session.get(DocumentDraftHead, doc.id)
        if not head:
            # Create a head if missing (should not be missing in a real flow, but just in case)
            head = DocumentDraftHead(
                document_id=doc.id, lock_version=1, selected_pages={"1": str(doc.active_index_generation_id)}
            )  # Not exactly, we need actual revision ID.

        # Let's use the API to start a draft or save a page to make sure it's set up
        # Wait, if we use the API directly...
        # Wait, the `create_indexed_document` creates a Document, Page, PageRevision, RevisionSet, IndexGeneration.
        # It does NOT create a DocumentDraftHead.
        # Let's just create one manually.
        revs = list(
            await self.session.scalars(select(DocumentPageRevision).where(DocumentPageRevision.document_id == doc.id))
        )

        head = DocumentDraftHead(
            document_id=doc.id,
            lock_version=2,  # we simulate that someone else bumped the lock_version to 2
            selected_pages={"1": str(revs[0].id)},
            updated_by_user_id=doctor.id,
        )
        self.session.add(head)
        await self.session.commit()

        # Try to save a page draft with If-Match: 1 (stale)
        await self.client.patch(
            f"/api/v1/documents/{doc.id}/draft/pages/1",
            json={"text": "new text", "parent_revision_id": str(revs[0].id), "edit_reason": "test"},
            headers={"Authorization": "Bearer test-doctor-token", "Idempotency-Key": "test-key-1", "If-Match": "1"},
        )
        # Auth mock: we might need a real token or bypass auth.
        # Wait, how does `test_upload_api.py` bypass auth? It passes `current_user` directly to the router method!

        # Ah, if we use `client.patch()`, we will hit the auth middleware which might reject it.
        # Let's just use the router function directly like `test_upload_api.py` does!
        from fastapi import Request

        from hospital_ai.api.routes import document_revisions as rev_routes
        from hospital_ai.core.errors import ConflictError
        from hospital_ai.schemas.document_revisions import DraftPageWrite

        payload = DraftPageWrite(text="new text", parent_revision_id=revs[0].id, edit_reason="test")
        req = Request({"type": "http", "client": ("127.0.0.1", 8000), "method": "PATCH", "path": "/test"})

        try:
            await rev_routes.save_draft_page(
                document_id=doc.id,
                page_number=1,
                payload=payload,
                request=req,
                if_match=1,
                idempotency_key="idemp-key-1",
                current_user=doctor,
                session=self.session,
            )
            return Evidence(passed=False, violated_invariant="Stale If-Match did not raise ConflictError")
        except ConflictError as e:
            return Evidence(passed=True, evidence=str(e))
        except Exception as e:
            return Evidence(passed=False, violated_invariant="Stale If-Match raised wrong exception", evidence=str(e))

    async def run_wrong_patient_and_superseded_filtered(self) -> Evidence:
        import uuid

        from sqlalchemy import select

        from hospital_ai.db.clinical_documents import DocumentIndexGeneration
        from hospital_ai.db.migrations import PATIENT_ALICE_ID, PATIENT_BOB_ID
        from hospital_ai.db.models import DocumentChunk, DocumentPage, Patient
        from hospital_ai.services.retrieval import RetrievalService
        from tests.conftest import create_indexed_document

        doctor, _ = await self._setup_doctor_and_admin()

        # Ensure Bob exists
        if not await self.session.get(Patient, PATIENT_BOB_ID):
            self.session.add(Patient(id=PATIENT_BOB_ID, full_name="Bob", mrn="TEST-BOB"))
            await self.session.flush()

        doc = await create_indexed_document(
            self.session, patient_id=PATIENT_ALICE_ID, uploaded_by=doctor.id, title="Doc", content="test"
        )
        page = (await self.session.scalars(select(DocumentPage).where(DocumentPage.document_id == doc.id))).first()
        active_gen_id = doc.active_index_generation_id
        active_rev_id = doc.approved_revision_set_id

        # create a superseded generation
        superseded_gen = DocumentIndexGeneration(
            id=uuid.uuid4(),
            document_id=doc.id,
            revision_set_id=active_rev_id,
            state="superseded",
            revision_set_sha256="hash",
            generation_sha256="hash",
        )
        self.session.add(superseded_gen)
        await self.session.flush()

        # Add a superseded chunk
        c_sup = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc.id,
            page_id=page.id,
            patient_id=PATIENT_ALICE_ID,
            chunk_index=1,
            content="test match",
            embedding=[0.1] * 1024,
            generation_id=superseded_gen.id,
            revision_set_id=active_rev_id,
            page_revision_id=uuid.uuid4(),
            approval_state="approved",
        )
        # Add a wrong patient chunk but attached to active gen (just for testing isolation)
        c_wrong = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc.id,
            page_id=page.id,
            patient_id=PATIENT_BOB_ID,
            chunk_index=2,
            content="test match",
            embedding=[0.1] * 1024,
            generation_id=active_gen_id,
            revision_set_id=active_rev_id,
            page_revision_id=uuid.uuid4(),
            approval_state="approved",
        )
        self.session.add_all([c_sup, c_wrong])
        await self.session.commit()

        # Search
        res = await RetrievalService(self.session).hybrid_search(
            user_id=doctor.id,
            patient_id=PATIENT_ALICE_ID,
            query="match",
            query_embedding=[0.1] * 1024,
            top_k=10,
            mode="vector",
        )

        matched_ids = [c.chunk_id for c in res]
        if c_sup.id in matched_ids:
            return Evidence(passed=False, violated_invariant="Superseded chunk was retrieved")
        if c_wrong.id in matched_ids:
            return Evidence(passed=False, violated_invariant="Wrong patient chunk was retrieved")

        return Evidence(passed=True)

    async def run_production_self_approval(self) -> Evidence:
        import datetime
        import uuid

        from fastapi import Request

        from hospital_ai.api.routes import document_revisions as rev_routes
        from hospital_ai.core.errors import ConflictError
        from hospital_ai.db.clinical_documents import DocumentRevisionSet
        from hospital_ai.db.migrations import PATIENT_ALICE_ID
        from hospital_ai.schemas.document_revisions import ApproveRevisionRequest
        from tests.conftest import create_indexed_document

        doctor, admin = await self._setup_doctor_and_admin()

        doc = await create_indexed_document(
            self.session,
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=admin.id,
            title="Prod Doc",
            content="self approval test",
        )

        # Turn off demo mode for this test, since it's "production self-approval denied"
        old_demo = self.settings.demo_mode
        self.settings.demo_mode = False

        rev_set = DocumentRevisionSet(
            id=uuid.uuid4(),
            document_id=doc.id,
            revision_number=2,
            status="submitted",
            created_by_user_id=admin.id,
            submitted_at=datetime.datetime.now(datetime.UTC),
        )
        self.session.add(rev_set)
        await self.session.commit()

        req = Request({"type": "http", "client": ("127.0.0.1", 8000), "method": "POST", "path": "/test"})

        try:
            await rev_routes.approve_revision_set(
                document_id=doc.id,
                revision_set_id=rev_set.id,
                payload=ApproveRevisionRequest(demo_mode=False),
                request=req,
                idempotency_key="idemp-key-self-approve",
                current_user=admin,
                session=self.session,
            )
            return Evidence(passed=False, violated_invariant="Production self-approval did not raise ConflictError")
        except ConflictError as e:
            return Evidence(passed=True, evidence=str(e))
        except Exception as e:
            return Evidence(
                passed=False, violated_invariant="Production self-approval raised wrong exception", evidence=str(e)
            )
        finally:
            self.settings.demo_mode = old_demo

    async def run_failed_generation_preserves_active(self) -> Evidence:
        import datetime
        import uuid

        from hospital_ai.db.clinical_documents import DocumentIndexGeneration, DocumentRevisionSet
        from hospital_ai.db.migrations import PATIENT_ALICE_ID
        from hospital_ai.workers.generation_jobs import GenerationBuilder
        from tests.conftest import create_indexed_document

        doctor, _ = await self._setup_doctor_and_admin()

        doc = await create_indexed_document(
            self.session,
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=doctor.id,
            title="Gen Doc",
            content="generation test",
        )

        old_generation_id = doc.active_index_generation_id

        rev_set = DocumentRevisionSet(
            id=uuid.uuid4(),
            document_id=doc.id,
            revision_number=2,
            status="build_authorized",
            created_by_user_id=doctor.id,
            submitted_at=datetime.datetime.now(datetime.UTC),
        )
        self.session.add(rev_set)

        new_generation = DocumentIndexGeneration(
            id=uuid.uuid4(),
            document_id=doc.id,
            revision_set_id=rev_set.id,
            state="building",
            revision_set_sha256="fake-sha",
        )
        self.session.add(new_generation)
        await self.session.commit()

        try:
            builder = GenerationBuilder.from_settings(self.session, self.settings)

            async def injected_stage(stage, generation, revision_set, custom_metadata=None):
                if stage == "graph":
                    raise RuntimeError("Injected Failure")
                from hospital_ai.workers.generation_jobs import StageOutput

                return StageOutput(sha256="hash", row_count=1)

            builder.stage_runner.run = injected_stage

            try:
                await builder.build(new_generation.id)
            except RuntimeError:
                pass

            await self.session.refresh(doc)
            if doc.active_index_generation_id != old_generation_id:
                return Evidence(passed=False, violated_invariant="Active index generation changed after failed build")

            await self.session.refresh(new_generation)
            if new_generation.state != "failed":
                return Evidence(passed=False, violated_invariant="New generation did not fail")

            return Evidence(passed=True)
        except Exception as e:
            return Evidence(
                passed=False, violated_invariant="Failed generation test raised unknown error", evidence=str(e)
            )

    async def run_stale_geometry_not_exact_evidence(self) -> Evidence:
        from sqlalchemy import select

        from hospital_ai.core.errors import ConflictError
        from hospital_ai.db.clinical_documents import (
            DocumentDraftHead,
            DocumentPageRevision,
            OcrBlock,
            OcrLine,
            OcrSpan,
        )
        from hospital_ai.db.migrations import PATIENT_ALICE_ID
        from hospital_ai.services.revisions import RevisionService, SavePageCommand
        from tests.conftest import create_indexed_document

        doctor, _ = await self._setup_doctor_and_admin()

        doc = await create_indexed_document(
            self.session,
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=doctor.id,
            title="Geometry Doc",
            content="original text",
        )

        page_rev = list(
            await self.session.scalars(select(DocumentPageRevision).where(DocumentPageRevision.document_id == doc.id))
        )[0]
        page_rev.status = "machine_draft"

        self.session.add(
            DocumentDraftHead(
                document_id=doc.id,
                selected_pages={"1": str(page_rev.id)},
                lock_version=1,
                updated_by_user_id=doctor.id,
            )
        )

        # add geometry
        block = OcrBlock(
            page_revision_id=page_rev.id,
            text_start_offset=0,
            text_end_offset=len("original text"),
            polygon={"points": [[0, 0], [1, 1]]},
            confidence=0.99,
            reading_order=1,
            alignment_status="aligned",
        )
        self.session.add(block)
        await self.session.flush()

        line = OcrLine(
            block_id=block.id,
            page_revision_id=page_rev.id,
            text_start_offset=0,
            text_end_offset=len("original text"),
            polygon={"points": [[0, 0], [1, 1]]},
            confidence=0.99,
            reading_order=1,
            alignment_status="aligned",
        )
        self.session.add(line)
        await self.session.flush()

        span = OcrSpan(
            line_id=line.id,
            page_revision_id=page_rev.id,
            text_start_offset=0,
            text_end_offset=len("original text"),
            polygon={"points": [[0, 0], [1, 1]]},
            confidence=0.99,
            reading_order=1,
            alignment_status="aligned",
            normalized_text="original text",
            source_engine_metadata={"engine": "test"},
        )
        self.session.add(span)
        await self.session.commit()

        service = RevisionService(self.session)
        result = await service.save_page(
            doc.id,
            1,
            SavePageCommand(
                text="changed text",
                parent_revision_id=page_rev.id,
                lock_version=1,
                actor_id=doctor.id,
            ),
        )

        try:
            await service.serialize_exact_evidence(doc.id, result.page_revision_id)
            return Evidence(passed=False, violated_invariant="Stale geometry did not raise ConflictError")
        except ConflictError as e:
            if "stale" in str(e).lower():
                return Evidence(passed=True)
            return Evidence(
                passed=False, violated_invariant="ConflictError didn't mention stale geometry", evidence=str(e)
            )
        except Exception as e:
            return Evidence(passed=False, violated_invariant="Wrong exception raised", evidence=str(e))

    async def run_canonical_entity_multiple_sources(self) -> Evidence:
        from sqlalchemy import select

        from hospital_ai.db.clinical_graph import GraphEntity, GraphMention
        from hospital_ai.db.migrations import PATIENT_ALICE_ID
        from hospital_ai.db.models import DocumentChunk
        from hospital_ai.services.graph_index import GraphIndexService
        from hospital_ai.services.graph_rag import ExtractedEntity, GraphExtraction
        from tests.conftest import create_indexed_document

        doctor, _ = await self._setup_doctor_and_admin()

        doc1 = await create_indexed_document(
            self.session, patient_id=PATIENT_ALICE_ID, uploaded_by=doctor.id, title="Doc 1", content="text"
        )
        doc2 = await create_indexed_document(
            self.session, patient_id=PATIENT_ALICE_ID, uploaded_by=doctor.id, title="Doc 2", content="text"
        )

        chunk1 = (await self.session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == doc1.id))).first()
        chunk2 = (await self.session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == doc2.id))).first()

        extraction = GraphExtraction(
            entities=[ExtractedEntity(entity_type="medication", normalized_label="metformin")], relations=[]
        )

        service = GraphIndexService(self.session)
        await service.index_chunk(doc1.active_index_generation_id, chunk1, extraction)
        await service.index_chunk(doc2.active_index_generation_id, chunk2, extraction)

        entities = list(
            await self.session.scalars(
                select(GraphEntity).where(
                    GraphEntity.patient_id == PATIENT_ALICE_ID, GraphEntity.normalized_label == "metformin"
                )
            )
        )
        mentions = list(
            await self.session.scalars(select(GraphMention).where(GraphMention.entity_id == entities[0].id))
        )

        if len(entities) != 1:
            return Evidence(passed=False, violated_invariant=f"Expected 1 canonical entity, got {len(entities)}")

        if len({row.document_id for row in mentions}) != 2:
            return Evidence(
                passed=False, violated_invariant=f"Expected 2 sources, got {len({row.document_id for row in mentions})}"
            )

        return Evidence(passed=True)

    async def run_upload_integrity_before_ocr(self) -> Evidence:
        import io
        from unittest.mock import Mock

        from hospital_ai.core.errors import ValidationAppError
        from hospital_ai.db.clinical_documents import DocumentUpload
        from hospital_ai.db.migrations import PATIENT_ALICE_ID
        from hospital_ai.services.upload_sessions import StorageContentReader, UploadSessionService

        doctor, _ = await self._setup_doctor_and_admin()

        r2_client = Mock()
        r2_client.head_object.side_effect = FileNotFoundError
        from hospital_ai.services.storage import PresignedPut

        r2_client.create_presigned_put.return_value = PresignedPut(
            url="https://presigned", required_headers={"Content-Type": "application/pdf"}
        )
        r2_client.read_stream.return_value = io.BytesIO(b"%PDF-1.4\nx")

        class _CleanScanner:
            async def scan(self, reader, mime_type, file_size):
                from hospital_ai.services.upload_sessions import MalwareScanResult

                return MalwareScanResult(is_clean=True, virus_name=None, signature_version="1", scanner_version="1")

        service = UploadSessionService(
            self.session, r2_client, content_reader=StorageContentReader(r2_client), scanner=_CleanScanner()
        )
        created = await service.create(
            actor=doctor,
            patient_id=PATIENT_ALICE_ID,
            filename="scan.pdf",
            expected_size=12,
            expected_sha256="a" * 64,
            claimed_mime_type="application/pdf",
            idempotency_key="upload-integrity-test",
        )

        r2_client.head_object.return_value = {"ContentLength": 11, "ETag": '"etag"'}
        r2_client.head_object.side_effect = None

        try:
            await service.finalize(created.document_id, created.upload_id)
            return Evidence(passed=False, violated_invariant="Integrity failure did not raise ValidationAppError")
        except ValidationAppError:
            upload = await self.session.get(DocumentUpload, created.upload_id)
            if upload.state != "rejected":
                return Evidence(passed=False, violated_invariant=f"Expected state 'rejected', got {upload.state}")
            return Evidence(passed=True)
        except Exception as e:
            return Evidence(
                passed=False, violated_invariant="Wrong exception raised for integrity failure", evidence=str(e)
            )

    async def run_validated_sse_sequence_and_interrupt(self) -> Evidence:
        from sqlalchemy import select

        from hospital_ai.api.routes.chat_stream import StreamCompletion, _apply_stream_completion
        from hospital_ai.db.migrations import PATIENT_ALICE_ID
        from hospital_ai.db.models import AiQuery, AuditLog

        doctor, _ = await self._setup_doctor_and_admin()

        query = AiQuery(
            user_id=doctor.id,
            patient_id=PATIENT_ALICE_ID,
            question="What is the patient status?",
            status="streaming",
            model="stub",
        )
        self.session.add(query)
        await self.session.flush()

        await _apply_stream_completion(
            self.session,
            ai_query_id=query.id,
            user_id=doctor.id,
            patient_id=PATIENT_ALICE_ID,
            thread_id=None,
            question=query.question,
            evidence=[],
            retrieval_mode="vector",
            trace_id="trace-interrupted",
            ip_address="127.0.0.1",
            started=0.0,
            completion=StreamCompletion(
                validation_status="failed",
                answer="Patient is stable ",
                failure_reason="disconnected",
                last_emitted_sequence=3,
                validation_mode="sentence_buffered",
            ),
        )
        await self.session.commit()

        refreshed = await self.session.get(AiQuery, query.id)
        if refreshed.status != "interrupted":
            return Evidence(passed=False, violated_invariant=f"Expected 'interrupted', got '{refreshed.status}'")
        if refreshed.last_emitted_sequence != 3:
            return Evidence(passed=False, violated_invariant=f"Expected 3, got '{refreshed.last_emitted_sequence}'")
        if refreshed.validation_mode != "sentence_buffered":
            return Evidence(
                passed=False, violated_invariant=f"Expected 'sentence_buffered', got '{refreshed.validation_mode}'"
            )

        audit = (
            await self.session.execute(
                select(AuditLog).where(AuditLog.action == "chat.stream", AuditLog.object_id == query.id)
            )
        ).scalar_one()
        if audit.meta.get("reason") != "disconnected":
            return Evidence(passed=False, violated_invariant=f"Expected 'disconnected', got {audit.meta.get('reason')}")

        return Evidence(passed=True)

    async def run_legacy_synthetic_parity(self) -> Evidence:
        import uuid

        from hospital_ai.db.clinical_graph import LegacyGraphEntity
        from hospital_ai.db.migrations import PATIENT_ALICE_ID
        from hospital_ai.db.models import Document, DocumentChunk, DocumentPage
        from hospital_ai.migrations.cdi_v2_backfill import BackfillPolicy, CdiV2Backfill

        doctor, _ = await self._setup_doctor_and_admin()
        doc = Document(
            id=uuid.uuid4(),
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=doctor.id,
            title="Parity Clean Synth",
            document_type="progress_note",
            storage_uri="local://test/parity_clean.pdf",
            mime_type="application/pdf",
            status="ready",
            is_synthetic=True,
            indexed_source_sha256="0011223344556677889900112233445566778899001122334455667788990011",
        )
        self.session.add(doc)
        await self.session.flush()

        page = DocumentPage(
            id=uuid.uuid4(),
            document_id=doc.id,
            page_number=1,
            ocr_text="Clean parity text",
            ocr_confidence=1.0,
        )
        self.session.add(page)
        await self.session.flush()

        chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc.id,
            page_id=page.id,
            patient_id=PATIENT_ALICE_ID,
            chunk_index=0,
            content="Clean parity text",
            token_count=3,
            text_start_offset=0,
            text_end_offset=17,
        )
        self.session.add(chunk)
        await self.session.flush()

        entity1 = LegacyGraphEntity(
            id=uuid.uuid4(),
            source_document_id=doc.id,
            source_chunk_id=chunk.id,
            name="Hypertension",
            entity_type="Condition",
            confidence=1.0,
        )
        self.session.add(entity1)
        await self.session.flush()

        await self.session.commit()

        runner = CdiV2Backfill(self.session, policy=BackfillPolicy(autoapprove_synthetic=True))
        await runner.run_document(doc.id)

        parity_report = await runner.compute_parity_report([doc.id])
        if parity_report["status"] != "passed":
            return Evidence(passed=False, violated_invariant=f"Expected status 'passed', got {parity_report['status']}")

        return Evidence(passed=True)
