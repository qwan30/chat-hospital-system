"""HMS data synchronization service.

Orchestrates fetching data from the HMS REST API and importing it as
searchable evidence into the chatbot's PostgreSQL/pgvector store.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import NotFoundError
from hospital_ai.db.models import Document, Patient
from hospital_ai.services.audit import AuditService
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.hms_connector import HmsApiClient

logger = logging.getLogger(__name__)

HMS_SOURCE_SYSTEM = "hospital-management-system"


class HmsSyncService:
    """Syncs clinical data from HMS into the chatbot evidence store."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.hms = HmsApiClient(settings)
        self.embedder = EmbeddingService(settings)

    async def sync_appointments(
        self,
        *,
        patient_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        jwt_token: Optional[str] = None,
        trace_id: str,
        ip_address: Optional[str] = None,
    ) -> list[Document]:
        """Fetch appointments from HMS and ingest as evidence documents."""
        patient = await self.session.get(Patient, patient_id)
        if patient is None or patient.deleted_at is not None:
            raise NotFoundError("Patient not found for HMS appointment sync.")

        hms_patient_id = patient.mrn or str(patient_id)
        raw_appointments = await self.hms.get_appointments(patient_id=hms_patient_id, jwt_token=jwt_token)

        documents: list[Document] = []
        for appt in raw_appointments:
            doc = await self._ingest_record(
                patient_id=patient_id,
                actor_user_id=actor_user_id,
                source_family="appointments",
                source_record_id=str(appt.get("id", "")),
                document_type="hms_appointment",
                title=f"Appointment — {appt.get('date', 'unknown date')}",
                content=_render_appointment(appt),
                metadata=_clean_metadata(appt),
                trace_id=trace_id,
                ip_address=ip_address,
            )
            documents.append(doc)

        await self.session.commit()
        return documents

    async def sync_lab_results(
        self,
        *,
        patient_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        jwt_token: Optional[str] = None,
        trace_id: str,
        ip_address: Optional[str] = None,
    ) -> list[Document]:
        """Fetch lab results from HMS and ingest as evidence documents."""
        patient = await self.session.get(Patient, patient_id)
        if patient is None or patient.deleted_at is not None:
            raise NotFoundError("Patient not found for HMS lab result sync.")

        hms_patient_id = patient.mrn or str(patient_id)
        raw_results = await self.hms.get_lab_results(patient_id=hms_patient_id, jwt_token=jwt_token)

        documents: list[Document] = []
        for lab in raw_results:
            doc = await self._ingest_record(
                patient_id=patient_id,
                actor_user_id=actor_user_id,
                source_family="lab_results",
                source_record_id=str(lab.get("id", "")),
                document_type="hms_lab_result",
                title=f"Lab Result — {lab.get('testName', lab.get('test_name', 'unknown'))}",
                content=_render_lab_result(lab),
                metadata=_clean_metadata(lab),
                trace_id=trace_id,
                ip_address=ip_address,
            )
            documents.append(doc)

        await self.session.commit()
        return documents

    async def sync_medical_records(
        self,
        *,
        patient_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        jwt_token: Optional[str] = None,
        trace_id: str,
        ip_address: Optional[str] = None,
    ) -> list[Document]:
        """Fetch medical records from HMS and ingest as evidence documents."""
        patient = await self.session.get(Patient, patient_id)
        if patient is None or patient.deleted_at is not None:
            raise NotFoundError("Patient not found for HMS medical record sync.")

        hms_patient_id = patient.mrn or str(patient_id)
        raw_records = await self.hms.get_medical_records(patient_id=hms_patient_id, jwt_token=jwt_token)

        documents: list[Document] = []
        for rec in raw_records:
            doc = await self._ingest_record(
                patient_id=patient_id,
                actor_user_id=actor_user_id,
                source_family="medical_records",
                source_record_id=str(rec.get("id", "")),
                document_type="hms_medical_record",
                title=f"Medical Record — {rec.get('date', rec.get('encounter_date', 'unknown'))}",
                content=_render_medical_record(rec),
                metadata=_clean_metadata(rec),
                trace_id=trace_id,
                ip_address=ip_address,
            )
            documents.append(doc)

        await self.session.commit()
        return documents

    async def sync_full(
        self,
        *,
        patient_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        jwt_token: Optional[str] = None,
        trace_id: str,
        ip_address: Optional[str] = None,
    ) -> dict[str, int]:
        """Run all sync operations for a patient."""
        kwargs = dict(
            patient_id=patient_id,
            actor_user_id=actor_user_id,
            jwt_token=jwt_token,
            trace_id=trace_id,
            ip_address=ip_address,
        )
        appts = await self.sync_appointments(**kwargs)
        labs = await self.sync_lab_results(**kwargs)
        records = await self.sync_medical_records(**kwargs)

        return {
            "appointments": len(appts),
            "lab_results": len(labs),
            "medical_records": len(records),
            "total": len(appts) + len(labs) + len(records),
        }

    # ── Internal helpers ───────────────────────────────────────────

    async def _ingest_record(
        self,
        *,
        patient_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        source_family: str,
        source_record_id: str,
        document_type: str,
        title: str,
        content: str,
        metadata: dict[str, Any],
        trace_id: str,
        ip_address: Optional[str] = None,
    ) -> Document:
        """Upsert a single HMS record as a Document with embedded chunks."""
        storage_uri = f"hms://{source_family}/{source_record_id}"
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        result = await self.session.execute(
            select(Document).where(
                Document.patient_id == patient_id,
                Document.document_type == document_type,
                Document.storage_uri == storage_uri,
            )
        )
        document = result.scalar_one_or_none()

        if document is not None and document.indexed_source_sha256 == content_hash:
            # Content unchanged — skip re-indexing.
            return document

        if document is None:
            document = Document(
                patient_id=patient_id,
                uploaded_by=actor_user_id,
                title=title,
                document_type=document_type,
                storage_uri=storage_uri,
                mime_type=f"application/vnd.hospital-ai.{document_type}+text",
                status="ready",
                page_count=1,
                indexed_source_sha256=content_hash,
                index_generation=0,
            )
            self.session.add(document)
            await self.session.flush()
        else:
            document.uploaded_by = actor_user_id
            document.title = title
            document.status = "ready"
            document.page_count = 1
            document.ocr_error = None
            document.deleted_at = None
            document.indexed_source_sha256 = content_hash
            await self.session.flush()

        from hospital_ai.workers.generation_jobs import import_synthetic_generation

        meta_dict = {
            "source_system": HMS_SOURCE_SYSTEM,
            "source_family": source_family,
            "source_record_id": source_record_id,
            "contains_phi": True,
            "patient_permission_required": True,
            "imported_at": datetime.now(UTC).isoformat(),
            **metadata,
        }
        await import_synthetic_generation(
            session=self.session,
            settings=self.settings,
            document=document,
            content=content,
            user_id=actor_user_id,
            metadata=meta_dict,
        )

        await AuditService(self.session).record(
            actor_user_id=actor_user_id,
            action=f"hms.{source_family}.sync",
            object_type="document",
            object_id=document.id,
            patient_id=patient_id,
            outcome="allowed",
            trace_id=trace_id,
            ip_address=ip_address,
            metadata={
                "source_system": HMS_SOURCE_SYSTEM,
                "source_family": source_family,
                "source_record_id": source_record_id,
            },
        )

        return document


# ── Rendering helpers ──────────────────────────────────────────────


def _render_appointment(appt: dict[str, Any]) -> str:
    lines = [
        "HMS Appointment Summary",
        f"Date: {appt.get('date', appt.get('appointmentDate', 'N/A'))}",
        f"Status: {appt.get('status', 'N/A')}",
    ]
    _add_optional(lines, "Department", appt.get("department", appt.get("departmentName")))
    _add_optional(lines, "Doctor", appt.get("doctorName", appt.get("doctor")))
    _add_optional(lines, "Reason", appt.get("reason"))
    _add_optional(lines, "Symptoms", appt.get("symptoms"))
    _add_optional(lines, "Notes", appt.get("notes"))
    _add_optional(lines, "Diagnosis", appt.get("diagnosis"))
    _add_optional(lines, "Treatment", appt.get("treatment"))
    return "\n".join(lines)


def _render_lab_result(lab: dict[str, Any]) -> str:
    lines = [
        "HMS Lab Result",
        f"Test: {lab.get('testName', lab.get('test_name', 'N/A'))}",
        f"Date: {lab.get('date', lab.get('testDate', 'N/A'))}",
        f"Result: {lab.get('result', lab.get('value', 'N/A'))}",
    ]
    _add_optional(lines, "Unit", lab.get("unit"))
    _add_optional(lines, "Reference Range", lab.get("referenceRange", lab.get("reference_range")))
    _add_optional(lines, "Status", lab.get("status"))
    _add_optional(lines, "Notes", lab.get("notes"))
    _add_optional(lines, "Ordered By", lab.get("orderedBy", lab.get("ordered_by")))
    return "\n".join(lines)


def _render_medical_record(rec: dict[str, Any]) -> str:
    lines = [
        "HMS Medical Record",
        f"Date: {rec.get('date', rec.get('encounter_date', rec.get('encounterDate', 'N/A')))}",
        f"Type: {rec.get('type', rec.get('recordType', 'N/A'))}",
    ]
    _add_optional(lines, "Diagnosis", rec.get("diagnosis"))
    _add_optional(lines, "Diagnosis Code", rec.get("diagnosisCode", rec.get("diagnosis_code")))
    _add_optional(lines, "Treatment", rec.get("treatment"))
    _add_optional(lines, "Notes", rec.get("notes"))
    _add_optional(lines, "Doctor", rec.get("doctorName", rec.get("doctor")))
    _add_optional(lines, "Department", rec.get("department", rec.get("departmentName")))
    return "\n".join(lines)


def _add_optional(lines: list[str], label: str, value: Any) -> None:
    if value is not None:
        text = str(value).strip()
        if text:
            lines.append(f"{label}: {text}")


def _clean_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    """Pick safe metadata fields — exclude large blobs and nested objects."""
    safe: dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, (str, int, float, bool)) and key not in {"password", "token", "secret"}:
            safe[key] = value
    return safe
