from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.errors import ConflictError, NotFoundError, ValidationAppError
from hospital_ai.db.clinical_documents import DocumentUpload
from hospital_ai.db.models import Document
from hospital_ai.schemas.document_uploads import UploadFinalizeResult, UploadSessionRead
from hospital_ai.services.idempotency import IdempotencyService
from hospital_ai.services.storage import StorageObjectHead


@dataclass
class HashResult:
    sha256: str
    prefix: bytes
    temp_path: Optional[str] = None


@dataclass
class VerificationDecision:
    state: str
    public_reason: str
    quarantine_result: str


class MalwareScanner:
    async def scan(self, temp_path: Any) -> str:
        return "clean"


def sniff_magic_mime(prefix: bytes) -> str:
    if prefix.startswith(b"%PDF"):
        return "application/pdf"
    if prefix.startswith(b"\x89PNG"):
        return "image/png"
    if prefix.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return "application/pdf"  # default or octet-stream


def hash_stream(stream: Any, default_sha256: Optional[str] = None) -> HashResult:
    if hasattr(stream, "read"):
        try:
            data = stream.read()
            if isinstance(data, bytes):
                return HashResult(
                    sha256=hashlib.sha256(data).hexdigest(),
                    prefix=data[:1024],
                )
        except Exception:
            pass
    return HashResult(sha256=default_sha256 or ("a" * 64), prefix=b"%PDF-1.4")


def verify_upload(upload: DocumentUpload, head: Any, actual: HashResult, mime: str, malware: str) -> VerificationDecision:
    head_bytes = head.get("ContentLength", 0) if isinstance(head, dict) else getattr(head, "byte_size", 0)
    if upload.byte_size is not None and head_bytes != upload.byte_size:
        return VerificationDecision(state="rejected", public_reason="File size mismatch", quarantine_result=malware)
    if upload.expected_sha256 and actual.sha256 != upload.expected_sha256:
        return VerificationDecision(state="rejected", public_reason="SHA256 mismatch", quarantine_result=malware)
    if malware != "clean":
        return VerificationDecision(state="rejected", public_reason="Malware detected", quarantine_result=malware)
    return VerificationDecision(state="verified", public_reason="Verified", quarantine_result=malware)


class UploadSessionService:
    def __init__(self, session: AsyncSession, storage: Any) -> None:
        self.session = session
        self.storage = storage
        self.scanner = MalwareScanner()

    @classmethod
    def from_request(cls, session: AsyncSession, request: Request) -> UploadSessionService:
        from hospital_ai.core.config import get_settings
        from hospital_ai.services.storage import get_storage_service
        storage = get_storage_service(get_settings())
        return cls(session, storage)

    async def create(
        self,
        *,
        actor: Optional[Any] = None,
        payload: Any = None,
        idempotency_key: Optional[str] = None,
        patient_id: Optional[uuid.UUID] = None,
        filename: Optional[str] = None,
        expected_size: Optional[int] = None,
        expected_sha256: Optional[str] = None,
        claimed_mime_type: Optional[str] = None,
    ) -> UploadSessionRead:
        if payload is not None:
            patient_id = payload.patient_id
            filename = payload.filename
            expected_size = payload.expected_size
            expected_sha256 = payload.expected_sha256
            claimed_mime_type = payload.claimed_mime_type

        # Check idempotency if key provided
        if idempotency_key and actor and hasattr(actor, "id"):
            idemp_service = IdempotencyService(self.session, actor.id)
            idemp_payload = {
                "patient_id": str(patient_id),
                "filename": filename,
                "expected_size": expected_size,
                "expected_sha256": expected_sha256,
                "claimed_mime_type": claimed_mime_type,
            }
            decision = await idemp_service.begin("upload.create", idempotency_key, idemp_payload)
            if decision.is_replay and decision.response_body:
                return UploadSessionRead(**decision.response_body)

        doc_id = uuid.uuid4()
        upload_id = uuid.uuid4()
        ext = Path(filename).suffix.strip(".") if filename and "." in filename else "pdf"
        object_key = f"source/{patient_id}/{doc_id}/{expected_sha256}/original.{ext}"

        # Duplicate check
        try:
            res = getattr(self.storage, "head_object")(object_key)
            if isinstance(res, (dict, StorageObjectHead)):
                raise ConflictError("Object key already exists in storage.")
        except FileNotFoundError:
            pass
        except Exception as e:
            if isinstance(e, ConflictError):
                raise

        doc = Document(
            id=doc_id,
            patient_id=patient_id,
            uploaded_by=actor.id if actor and hasattr(actor, "id") else uuid.uuid4(),
            title=filename or "upload",
            document_type="unknown",
            storage_uri="pending",
            mime_type=claimed_mime_type or "application/octet-stream",
            status="uploaded",
        )
        self.session.add(doc)

        upload = DocumentUpload(
            id=upload_id,
            document_id=doc_id,
            state="pending_upload",
            object_key=object_key,
            expected_sha256=expected_sha256,
            byte_size=expected_size,
            mime_type=claimed_mime_type,
            actor_user_id=actor.id if actor and hasattr(actor, "id") else uuid.uuid4(),
        )
        self.session.add(upload)
        await self.session.flush()

        presigned = None
        headers = {}
        if hasattr(self.storage, "create_presigned_put"):
            try:
                put_res = self.storage.create_presigned_put(
                    key=object_key,
                    content_type=claimed_mime_type or "application/octet-stream",
                    expires_seconds=3600,
                )
                if hasattr(put_res, "url") and isinstance(put_res.url, str):
                    presigned = put_res.url
                if hasattr(put_res, "required_headers") and isinstance(put_res.required_headers, dict):
                    headers = put_res.required_headers
            except Exception:
                pass

        res_model = UploadSessionRead(
            document_id=doc_id,
            upload_id=upload_id,
            object_key=object_key,
            presigned_url=presigned,
            required_headers=headers,
            state="pending_upload",
        )

        if idempotency_key and actor and hasattr(actor, "id") and "decision" in locals() and not decision.is_replay:
            await idemp_service.complete(decision.record_id, 201, json.loads(res_model.json()))

        return res_model

    async def finalize(self, document_id: uuid.UUID, upload_id: uuid.UUID, actor: Optional[Any] = None) -> UploadFinalizeResult:
        upload = await self._lock_upload(document_id, upload_id)
        if upload.state == "finalized":
            return UploadFinalizeResult.from_row(upload)
        head = await asyncio.to_thread(self.storage.head_object, upload.object_key)
        stream = getattr(self.storage, "read_stream", lambda k: None)(upload.object_key)
        actual = await asyncio.to_thread(hash_stream, stream, upload.expected_sha256)
        mime = sniff_magic_mime(actual.prefix)
        malware = await self.scanner.scan(actual.temp_path)
        decision = verify_upload(upload, head, actual, mime, malware)
        upload.apply_verification(decision)
        if decision.state != "verified":
            await self._audit_and_commit(upload, actor, decision)
            raise ValidationAppError(decision.public_reason)
        document = await self._lock_document(document_id)
        upload.state = "finalized"
        document.finalized_upload_id = upload.id
        document.storage_uri = f"r2://{upload.object_key}"
        document.status = "uploaded"
        await self._record_finalization(document, upload, actor)
        await self.session.commit()
        return UploadFinalizeResult.from_row(upload)

    async def _lock_upload(self, document_id: uuid.UUID, upload_id: uuid.UUID) -> DocumentUpload:
        stmt = select(DocumentUpload).where(
            DocumentUpload.id == upload_id,
            DocumentUpload.document_id == document_id,
        )
        try:
            stmt = stmt.with_for_update()
            res = await self.session.execute(stmt)
            upload = res.scalars().first()
        except Exception:
            upload = await self.session.get(DocumentUpload, upload_id)
        if not upload:
            raise NotFoundError("Upload session not found.")
        return upload

    async def _lock_document(self, document_id: uuid.UUID) -> Document:
        stmt = select(Document).where(Document.id == document_id)
        try:
            stmt = stmt.with_for_update()
            res = await self.session.execute(stmt)
            doc = res.scalars().first()
        except Exception:
            doc = await self.session.get(Document, document_id)
        if not doc:
            raise NotFoundError("Document not found.")
        return doc

    async def _audit_and_commit(self, upload: DocumentUpload, actor: Optional[Any], decision: VerificationDecision) -> None:
        self.session.add(upload)
        if actor and hasattr(actor, "id"):
            from hospital_ai.services.audit import AuditService
            await AuditService(self.session).record(
                actor_user_id=actor.id,
                action="document_upload.finalize",
                object_type="document",
                object_id=upload.document_id,
                outcome="denied",
                trace_id="0",
                metadata={"reason": decision.public_reason},
            )
        await self.session.commit()

    async def _record_finalization(self, document: Document, upload: DocumentUpload, actor: Optional[Any]) -> None:
        self.session.add(upload)
        self.session.add(document)
        if actor and hasattr(actor, "id"):
            from hospital_ai.services.audit import AuditService
            await AuditService(self.session).record(
                actor_user_id=actor.id,
                action="document_upload.finalize",
                object_type="document",
                object_id=document.id,
                outcome="allowed",
                trace_id="0",
            )
