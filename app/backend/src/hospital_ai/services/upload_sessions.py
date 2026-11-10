from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Protocol

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.errors import ConflictError, NotFoundError, ValidationAppError
from hospital_ai.db.clinical_documents import DocumentUpload
from hospital_ai.db.models import Document
from hospital_ai.schemas.document_uploads import UploadFinalizeResult, UploadSessionRead
from hospital_ai.services.idempotency import IdempotencyService
from hospital_ai.services.storage import LocalStorageService, StorageObjectHead


@dataclass
class VerifiedObjectDigest:
    sha256: str
    byte_size: int
    mime_type: str


@dataclass
class MalwareScanResult:
    status: str


@dataclass
class VerificationDecision:
    state: str
    public_reason: str
    quarantine_result: str


class UploadContentReader(Protocol):
    async def hash_and_sniff(self, key: str) -> VerifiedObjectDigest: ...


class MalwareScanner(Protocol):
    async def scan(self, key: str) -> MalwareScanResult: ...


ALLOWED_MIME_TYPES = frozenset({"application/pdf", "image/png", "image/jpeg"})


def verify_upload(
    upload: DocumentUpload, head: Any, actual: VerifiedObjectDigest, malware: MalwareScanResult
) -> VerificationDecision:
    if not isinstance(head, (dict, StorageObjectHead)):
        return VerificationDecision(
            state="rejected", public_reason="Storage metadata unavailable", quarantine_result="unknown"
        )
    head_bytes = head.get("ContentLength") if isinstance(head, dict) else head.byte_size
    if not isinstance(head_bytes, int) or head_bytes != actual.byte_size:
        return VerificationDecision(
            state="rejected", public_reason="File size mismatch", quarantine_result=malware.status
        )
    if not upload.byte_size or actual.byte_size != upload.byte_size:
        return VerificationDecision(
            state="rejected", public_reason="File size mismatch", quarantine_result=malware.status
        )
    if not upload.expected_sha256 or actual.sha256 != upload.expected_sha256:
        return VerificationDecision(state="rejected", public_reason="SHA256 mismatch", quarantine_result=malware.status)
    if not upload.mime_type or upload.mime_type not in ALLOWED_MIME_TYPES or upload.mime_type != actual.mime_type:
        return VerificationDecision(
            state="rejected", public_reason="MIME type mismatch", quarantine_result=malware.status
        )
    if malware.status != "clean":
        return VerificationDecision(
            state="rejected", public_reason="Malware detected", quarantine_result=malware.status
        )
    return VerificationDecision(state="verified", public_reason="Verified", quarantine_result=malware.status)


class StorageContentReader:
    def __init__(self, storage: Any) -> None:
        self.storage = storage

    async def hash_and_sniff(self, key: str) -> VerifiedObjectDigest:
        stream = await asyncio.to_thread(self.storage.read_stream, key)
        if stream is None or not hasattr(stream, "read"):
            raise ValidationAppError("Unable to read uploaded object.")

        hasher = hashlib.sha256()
        byte_size = 0
        prefix = b""

        try:
            while True:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    break
                if not isinstance(chunk, bytes):
                    raise ValidationAppError("Unable to read uploaded object.")
                hasher.update(chunk)
                byte_size += len(chunk)
                if len(prefix) < 1024:
                    prefix += chunk[: 1024 - len(prefix)]
        except Exception as exc:
            raise ValidationAppError("Unable to read uploaded object.") from exc

        if byte_size == 0:
            raise ValidationAppError("Uploaded object is empty or unreadable.")

        if prefix.startswith(b"%PDF"):
            mime = "application/pdf"
        elif prefix.startswith(b"\x89PNG"):
            mime = "image/png"
        elif prefix.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg"
        else:
            raise ValidationAppError("Unable to detect a supported MIME type from the uploaded object.")

        return VerifiedObjectDigest(
            sha256=hasher.hexdigest(),
            byte_size=byte_size,
            mime_type=mime,
        )


class UnavailableMalwareScanner:
    async def scan(self, key: str) -> MalwareScanResult:
        raise ValidationAppError("Malware scanner unavailable.")


class SyntheticCleanMalwareScanner:
    """Deterministic scanner for explicitly enabled local/CI synthetic data."""

    async def scan(self, key: str) -> MalwareScanResult:
        return MalwareScanResult(status="clean")


def _extract_and_validate_create_params(
    *,
    payload: Any,
    patient_id: Optional[uuid.UUID],
    filename: Optional[str],
    expected_size: Optional[int],
    expected_sha256: Optional[str],
    claimed_mime_type: Optional[str],
    title: Optional[str],
    document_type: Optional[str],
) -> tuple[Optional[uuid.UUID], str, str, str, int, str, str]:
    if payload is not None:
        patient_id = payload.patient_id
        filename = payload.filename
        title = payload.title
        document_type = payload.document_type
        expected_size = payload.expected_size
        expected_sha256 = payload.expected_sha256
        claimed_mime_type = payload.claimed_mime_type

    if not filename or expected_size is None or expected_size <= 0:
        raise ValidationAppError("Upload filename and positive expected size are required.")
    if (
        not expected_sha256
        or len(expected_sha256) != 64
        or any(char not in "0123456789abcdefABCDEF" for char in expected_sha256)
    ):
        raise ValidationAppError("A valid expected SHA256 is required.")
    normalized_sha = expected_sha256.lower()
    if claimed_mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationAppError("Unsupported upload MIME type.")
    return (
        patient_id,
        filename,
        title or filename or "upload",
        document_type or "unknown",
        expected_size,
        normalized_sha,
        claimed_mime_type,
    )


def _assert_object_key_available(storage: Any, object_key: str) -> None:
    try:
        res = storage.head_object(object_key)
    except FileNotFoundError:
        return
    except ConflictError:
        raise
    except Exception as exc:
        raise ValidationAppError("Unable to verify storage object availability.") from exc
    if isinstance(res, (dict, StorageObjectHead)):
        raise ConflictError("Object key already exists in storage.")
    raise ValidationAppError("Unable to verify storage object availability.")


async def _create_presigned_put_or_rollback(
    session: AsyncSession, storage: Any, object_key: str, mime_type: str
) -> tuple[str, dict[str, str]]:
    if not hasattr(storage, "create_presigned_put"):
        await session.rollback()
        raise ValidationAppError("Storage upload session is unavailable.")
    try:
        put_res = storage.create_presigned_put(
            key=object_key,
            content_type=mime_type,
            expires_seconds=3600,
        )
    except Exception as exc:
        await session.rollback()
        raise ValidationAppError("Unable to create storage upload session.") from exc
    if not hasattr(put_res, "url") or not isinstance(put_res.url, str) or not put_res.url:
        await session.rollback()
        raise ValidationAppError("Storage upload session is invalid.")
    headers = put_res.required_headers if isinstance(put_res.required_headers, dict) else {}
    return put_res.url, headers


class UploadSessionService:
    def __init__(
        self, session: AsyncSession, storage: Any, content_reader: UploadContentReader, scanner: MalwareScanner
    ) -> None:
        self.session = session
        self.storage = storage
        self.content_reader = content_reader
        self.scanner = scanner

    @classmethod
    def from_request(cls, session: AsyncSession, request: Request) -> UploadSessionService:
        from hospital_ai.core.config import get_settings
        from hospital_ai.services.storage import get_storage_service

        settings = get_settings()
        storage = get_storage_service(settings)
        scanner: MalwareScanner = UnavailableMalwareScanner()
        if settings.allow_synthetic_malware_scan and settings.environment in ("local", "demo", "test"):
            scanner = SyntheticCleanMalwareScanner()
        return cls(session, storage, StorageContentReader(storage), scanner)

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
        title: Optional[str] = None,
        document_type: Optional[str] = None,
    ) -> UploadSessionRead:
        (
            patient_id,
            valid_filename,
            effective_title,
            effective_doc_type,
            valid_size,
            normalized_sha,
            valid_mime,
        ) = _extract_and_validate_create_params(
            payload=payload,
            patient_id=patient_id,
            filename=filename,
            expected_size=expected_size,
            expected_sha256=expected_sha256,
            claimed_mime_type=claimed_mime_type,
            title=title,
            document_type=document_type,
        )

        actor_id = getattr(actor, "id", None) if actor is not None else None
        idemp_service: Optional[IdempotencyService] = None
        decision: Optional[Any] = None
        if idempotency_key and actor_id is not None:
            idemp_service = IdempotencyService(self.session, actor_id)
            idemp_payload = {
                "patient_id": str(patient_id),
                "filename": valid_filename,
                "title": title,
                "document_type": document_type,
                "expected_size": valid_size,
                "expected_sha256": normalized_sha,
                "claimed_mime_type": valid_mime,
            }
            decision = await idemp_service.begin("upload.create", idempotency_key, idemp_payload)
            if decision.is_in_progress:
                raise ConflictError("Request is already in progress; retry later.")
            if decision.is_replay and decision.response_body:
                return UploadSessionRead(**decision.response_body)

        doc_id = uuid.uuid4()
        upload_id = uuid.uuid4()
        ext = Path(valid_filename).suffix.strip(".") if "." in valid_filename else "pdf"
        object_key = f"source/{patient_id}/{doc_id}/{upload_id}/original.{ext}"

        _assert_object_key_available(self.storage, object_key)

        effective_actor_id = actor_id if actor_id is not None else uuid.uuid4()
        doc = Document(
            id=doc_id,
            patient_id=patient_id,
            uploaded_by=effective_actor_id,
            title=effective_title,
            document_type=effective_doc_type,
            storage_uri="pending",
            mime_type=valid_mime,
            status="uploaded",
        )
        self.session.add(doc)
        await self.session.flush()

        upload = DocumentUpload(
            id=upload_id,
            document_id=doc_id,
            state="pending_upload",
            object_key=object_key,
            expected_sha256=normalized_sha,
            byte_size=valid_size,
            mime_type=valid_mime,
            actor_user_id=effective_actor_id,
        )
        self.session.add(upload)
        await self.session.flush()

        presigned, headers = await _create_presigned_put_or_rollback(self.session, self.storage, object_key, valid_mime)

        res_model = UploadSessionRead(
            document_id=doc_id,
            upload_id=upload_id,
            object_key=object_key,
            presigned_url=presigned,
            required_headers=headers,
            state="pending_upload",
        )

        if idemp_service is not None and decision is not None and not decision.is_replay:
            await idemp_service.complete(decision.record_id, 201, json.loads(res_model.json()))

        return res_model

    async def finalize(
        self,
        document_id: uuid.UUID,
        upload_id: uuid.UUID,
        actor: Optional[Any] = None,
        *,
        commit: bool = True,
    ) -> UploadFinalizeResult:
        upload = await self._lock_upload(document_id, upload_id)
        if upload.state == "finalized":
            return UploadFinalizeResult.from_row(upload)
        error: Optional[Exception] = None
        try:
            head = await asyncio.to_thread(self.storage.head_object, upload.object_key)
            actual = await self.content_reader.hash_and_sniff(upload.object_key)
            malware = await self.scanner.scan(upload.object_key)
            decision = verify_upload(upload, head, actual, malware)
        except ValidationAppError as exc:
            decision = VerificationDecision(state="rejected", public_reason=str(exc), quarantine_result="unavailable")
        except Exception as exc:
            decision = VerificationDecision(
                state="rejected", public_reason="Unable to verify uploaded object.", quarantine_result="unavailable"
            )
            error = exc
        upload.apply_verification(decision)
        if decision.state != "verified":
            await self._audit_and_commit(upload, actor, decision, commit=commit)
            if error is not None:
                raise ValidationAppError(decision.public_reason) from error
            raise ValidationAppError(decision.public_reason)
        document = await self._lock_document(document_id)
        upload.state = "finalized"
        document.finalized_upload_id = upload.id
        document.storage_uri = (
            upload.object_key if isinstance(self.storage, LocalStorageService) else f"r2://{upload.object_key}"
        )
        document.status = "uploaded"
        await self._record_finalization(document, upload, actor)
        if commit:
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

    async def _audit_and_commit(
        self, upload: DocumentUpload, actor: Optional[Any], decision: VerificationDecision, *, commit: bool = True
    ) -> None:
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
        if commit:
            await self.session.commit()
        else:
            await self.session.flush()

    async def _record_finalization(self, document: Document, upload: DocumentUpload, actor: Optional[Any]) -> None:
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
