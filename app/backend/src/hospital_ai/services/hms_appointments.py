"""HMS appointments evidence import service.
Dịch vụ nhập khẩu thông tin tóm tắt lịch hẹn khám bệnh từ hệ thống HMS vào kho dữ liệu tìm kiếm (evidence store).
"""

import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import NotFoundError, ValidationAppError
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, Patient, User
from hospital_ai.schemas.hms import HmsAppointmentSummaryImport
from hospital_ai.services.audit import AuditService
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.permissions import PermissionService

HMS_APPOINTMENT_DOCUMENT_TYPE = "hms_appointment_summary"
HMS_APPOINTMENT_SOURCE_FAMILY = "appointments"
HMS_SOURCE_SYSTEM = "hospital-management-system"
HMS_APPOINTMENT_IMPORT_CONTRACT = "phase3-hms-appointments-v1"


class HmsAppointmentEvidenceImporter:
    """Importer for HMS appointment summaries into the chatbot document store.
    Bộ xử lý nhập dữ liệu tóm tắt cuộc hẹn HMS thành tài liệu (Document/Chunk) để tra cứu trong chatbot.
    """

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Khởi tạo importer với phiên làm việc cơ sở dữ liệu AsyncSession và cấu hình hệ thống Settings."""
        self.session = session
        self.settings = settings

    async def import_summary(
        self,
        *,
        user: User,
        payload: HmsAppointmentSummaryImport,
        trace_id: str,
        ip_address: str | None = None,
    ) -> Document:
        """Import an appointment summary as a Document chunk, enforcing patient permissions and audit logs.
        Nhập tóm tắt cuộc hẹn khám bệnh thành tài liệu, kiểm tra quyền truy cập của
        người dùng và ghi nhận nhật ký kiểm tra (audit log).
        """
        if payload.patient_id != payload.source_patient_id:
            raise ValidationAppError("HMS appointment patient ownership mismatch.")

        patient = await self.session.get(Patient, payload.patient_id)
        if patient is None or patient.deleted_at is not None:
            raise NotFoundError("Patient for HMS appointment import was not found.")

        await PermissionService(self.session).require_upload_or_admin_role(
            user=user,
            patient_id=payload.patient_id,
            action="hms.appointment.import",
            trace_id=trace_id,
            object_type="hms_appointment",
            object_id=payload.source_appointment_id,
            ip_address=ip_address,
        )

        content = render_appointment_summary(payload)
        source_uri = hms_appointment_storage_uri(payload.source_appointment_id)
        title = f"HMS appointment summary {payload.source_appointment_id}"
        indexed_source_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()

        result = await self.session.execute(
            select(Document).where(
                Document.patient_id == payload.patient_id,
                Document.document_type == HMS_APPOINTMENT_DOCUMENT_TYPE,
                Document.storage_uri == source_uri,
            )
        )
        document = result.scalar_one_or_none()
        if document is None:
            document = Document(
                patient_id=payload.patient_id,
                uploaded_by=user.id,
                title=title,
                document_type=HMS_APPOINTMENT_DOCUMENT_TYPE,
                storage_uri=source_uri,
                mime_type="application/vnd.hospital-ai.hms-appointment-summary+text",
                status="indexed",
                page_count=1,
                indexed_source_sha256=indexed_source_sha256,
                index_generation=1,
            )
            self.session.add(document)
            await self.session.flush()
        else:
            document.uploaded_by = user.id
            document.title = title
            document.mime_type = "application/vnd.hospital-ai.hms-appointment-summary+text"
            document.status = "indexed"
            document.page_count = 1
            document.ocr_error = None
            document.deleted_at = None
            document.index_generation += 1
            document.indexed_source_sha256 = indexed_source_sha256
            await self.session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
            await self.session.execute(delete(DocumentPage).where(DocumentPage.document_id == document.id))
            await self.session.flush()

        page = DocumentPage(
            document_id=document.id,
            page_number=1,
            ocr_text=content,
            ocr_confidence=1.0,
        )
        self.session.add(page)
        await self.session.flush()

        self.session.add(
            DocumentChunk(
                document_id=document.id,
                page_id=page.id,
                patient_id=payload.patient_id,
                chunk_index=0,
                content=content,
                token_count=len(content.split()),
                embedding=await EmbeddingService(self.settings).embed(content),
                meta=build_appointment_metadata(payload),
            )
        )
        await AuditService(self.session).record(
            actor_user_id=user.id,
            action="hms.appointment.import",
            object_type="document",
            object_id=document.id,
            patient_id=payload.patient_id,
            outcome="allowed",
            trace_id=trace_id,
            ip_address=ip_address,
            metadata={
                "source_system": HMS_SOURCE_SYSTEM,
                "source_family": HMS_APPOINTMENT_SOURCE_FAMILY,
                "source_record_id": str(payload.source_appointment_id),
                "import_contract": HMS_APPOINTMENT_IMPORT_CONTRACT,
            },
        )
        await self.session.commit()
        await self.session.refresh(document)
        return document


def hms_appointment_storage_uri(source_appointment_id: uuid.UUID) -> str:
    """Tạo chuỗi URI định danh vị trí lưu trữ ảo cho cuộc hẹn (ví dụ: `hms://appointments/{id}`)."""
    return f"hms://appointments/{source_appointment_id}"


def render_appointment_summary(payload: HmsAppointmentSummaryImport) -> str:
    """Tạo văn bản tóm tắt nội dung cuộc hẹn (ngày, giờ, bác sĩ, triệu chứng, ghi chú) để nhúng vector (embedding)."""
    lines = [
        "HMS appointment summary",
        f"Appointment ID: {payload.source_appointment_id}",
        f"Appointment date: {payload.appointment_date.isoformat()}",
        f"Status: {payload.status}",
    ]
    optional_lines = [
        ("Department", payload.department),
        ("Doctor", payload.doctor_name),
        ("Start time", payload.start_time),
        ("End time", payload.end_time),
        ("Reason", payload.reason),
        ("Symptoms", payload.symptoms),
        ("Notes", payload.notes),
        ("Vital signs", payload.vital_signs_summary),
        ("Follow-up", payload.follow_up_summary),
    ]
    for label, value in optional_lines:
        normalized = value.strip() if isinstance(value, str) else None
        if normalized:
            lines.append(f"{label}: {normalized}")
    return "\n".join(lines)


def build_appointment_metadata(payload: HmsAppointmentSummaryImport) -> dict:
    """Tạo từ điển siêu dữ liệu (metadata) đầy đủ cho đoạn tài liệu cuộc hẹn, tuân thủ hợp đồng Phase 3."""
    metadata = {
        "source_system": HMS_SOURCE_SYSTEM,
        "source_family": HMS_APPOINTMENT_SOURCE_FAMILY,
        "source_record_id": str(payload.source_appointment_id),
        "source_path": f"/api/v1/appointments/{payload.source_appointment_id}",
        "source_patient_id": str(payload.source_patient_id),
        "import_contract": HMS_APPOINTMENT_IMPORT_CONTRACT,
        "source_lifecycle_state": "active",
        "approval_state": "synthetic_or_deidentified_only",
        "contains_phi": True,
        "patient_permission_required": True,
        "appointment_date": payload.appointment_date.isoformat(),
        "appointment_status": payload.status,
    }
    if payload.source_updated_at:
        metadata["source_updated_at"] = payload.source_updated_at.isoformat()
    metadata.update(payload.metadata)
    metadata["imported_at"] = datetime.now(UTC).isoformat()
    return metadata
